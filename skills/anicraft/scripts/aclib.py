"""Shared helpers for the anicraft skill scripts (stdlib only, Python 3.9+).

`Serve` drives `anicraft-cli serve FILE` (JSON lines on stdin/stdout): one stateful,
headless session in which each command's result (element, instance, bone, layer ids) is
available to the next one. `run` can't do that, so every multi-step build goes through
`Serve`.

Frame bases (verified on 0.2.1):
- CLI flags (`render --frame`, `render-seq/gif --from/--to`) are 1-based, like the timeline.
- Command params (`frame`, export `from`/`to`), `info` and the file are 0-based.
"""
import json
import os
import shutil
import subprocess
import sys

PINNED_VERSION = "0.2.1"

# Commands whose `from` / `to` params are frames (in all others `from`/`to` are ids,
# e.g. bone.add). `frame` is a frame index in every command that takes it at top level.
FRAME_RANGE_COMMANDS = {
    "file.export_video", "file.export_gif", "file.export_png_sequence",
    "file.export_sprite_sheet", "file.export_lottie", "file.export_audio",
    "timeline.move_keyframes",
}


def cli():
    """Path of anicraft-cli, or exit with a hint."""
    path = shutil.which("anicraft-cli") or os.path.expanduser("~/.local/bin/anicraft-cli")
    if not os.path.isfile(path):
        sys.exit("anicraft-cli not found (expected on PATH or in ~/.local/bin)")
    return path


def run_cli(args, check=True):
    """Run anicraft-cli with args; return the CompletedProcess (text mode)."""
    proc = subprocess.run([cli()] + list(args), capture_output=True, text=True)
    if check and proc.returncode != 0:
        raise RuntimeError("anicraft-cli %s failed: %s" % (
            " ".join(args[:2]), proc.stderr.strip() or proc.stdout.strip()))
    return proc


def info(path):
    """`anicraft-cli info FILE` as a dict. Never pass nothing: --sample is the demo."""
    return json.loads(run_cli(["info", path]).stdout)


def load_document(path):
    """The saved .anicraft file (JSON) as a dict: {format, version, paths, document}."""
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    if data.get("format") != "anicraft":
        raise RuntimeError("%s is not an .anicraft file" % path)
    return data


def walk_layers(timeline):
    """Yield every layer of a timeline, folders' children included."""
    for layer in timeline.get("layers", []):
        yield layer
        if layer.get("layers"):
            yield from walk_layers(layer)


def element_kind(element):
    """('Text', {...}) / ('Symbol', {...}) / ('Shape', {...}) / ('Camera', None)."""
    kind = element.get("kind")
    if isinstance(kind, dict):
        name = next(iter(kind))
        return name, kind[name]
    return kind, None


def ffprobe(path):
    """ffprobe streams + format of a media file (frames counted) as a dict."""
    exe = shutil.which("ffprobe")
    if not exe:
        raise RuntimeError("ffprobe not found (brew install ffmpeg)")
    proc = subprocess.run(
        [exe, "-v", "error", "-count_frames", "-show_streams", "-show_format",
         "-of", "json", path], capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError("ffprobe %s: %s" % (path, proc.stderr.strip()))
    return json.loads(proc.stdout)


class StepError(RuntimeError):
    pass


class Serve:
    """A headless AniCraft session on one document (`serve FILE`).

    `call()` raises StepError on `ok: false` — serve itself keeps going after an error,
    which would leave later steps working on the wrong state.
    """

    def __init__(self, path, plugins=None):
        args = [cli()]
        if plugins:
            args += ["--plugins", plugins]
        args += ["serve", path]
        self.proc = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE, text=True, bufsize=1)
        self._id = 0
        hello = self._read()
        if not hello.get("ready"):
            raise RuntimeError("anicraft-cli serve did not start: %s" % hello)
        self.version = hello.get("version")
        self.frame = 0

    def _read(self):
        line = self.proc.stdout.readline()
        if not line:
            err = self.proc.stderr.read() if self.proc.stderr else ""
            raise RuntimeError("anicraft-cli serve exited: %s" % err.strip())
        return json.loads(line)

    def call(self, cmd, params=None):
        self._id += 1
        msg = {"id": self._id, "cmd": cmd, "params": params or {}}
        self.proc.stdin.write(json.dumps(msg) + "\n")
        self.proc.stdin.flush()
        reply = self._read()
        if not reply.get("ok"):
            raise StepError("%s: %s" % (cmd, reply.get("error", reply)))
        self.frame = reply.get("frame", self.frame)
        return reply.get("result")

    def layer_id(self, name):
        """Id of the layer named `name` in the current timeline (exact, then case-insensitive)."""
        layers = self.call("doc.info").get("layers", [])
        for test in (lambda n: n == name, lambda n: n.lower() == name.lower()):
            hits = [l["id"] for l in layers if test(l["name"])]
            if len(hits) == 1:
                return hits[0]
            if len(hits) > 1:
                raise StepError("layer name %r is ambiguous (ids %s)" % (name, hits))
        raise StepError("no layer named %r (have: %s)" % (
            name, ", ".join(l["name"] for l in layers)))

    def close(self):
        try:
            self.proc.stdin.close()
            self.proc.wait(timeout=10)
        except Exception:
            self.proc.kill()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()
