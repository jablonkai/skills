"""Shared helpers for the gyroflow skill scripts. Standard library only.

Gyroflow's CLI has sharp edges this module absorbs:

- The Mac App Store build is sandboxed. It reads and writes only under
  ~/Library/Application Support/Gyroflow/, so inputs are staged there (APFS
  clones, near-free) and outputs are moved back afterwards.
- The exit code is 0 even when a file is missing or a render fails, and an
  unreadable input makes the process hang. Success is judged from the log and
  the files, and a watchdog kills a stalled process.
- Inputs must be absolute paths to files (a folder is read as one bad video).
- -p/-s/--preset take JSON; the codec belongs in -p, because a preset's codec
  does not change the output file extension.
"""

import json
import os
import re
import shutil
import signal
import subprocess
import threading
import time
import uuid

APP_BIN = "/Applications/Gyroflow.app/Contents/MacOS/gyroflow"
SANDBOX_ROOT = os.path.expanduser("~/Library/Application Support/Gyroflow")
RUNS_DIR = os.path.join(SANDBOX_ROOT, "agent-runs")
VIDEO_EXTS = {".mp4", ".mov", ".m4v", ".mxf", ".mkv", ".avi", ".insv", ".360",
              ".braw", ".r3d", ".mts", ".m2ts"}
# Output extension Gyroflow picks per codec (when given through -p).
CODEC_EXT = {"H.264/AVC": ".mp4", "H.265/HEVC": ".mp4", "ProRes": ".mov",
             "DNxHD": ".mov", "CineForm": ".mov", "AV1": ".mp4",
             "EXR Sequence": "_%05d.exr", "PNG Sequence": "_%05d.png"}
CODEC_ALIASES = {"h264": "H.264/AVC", "avc": "H.264/AVC", "h.264": "H.264/AVC",
                 "h265": "H.265/HEVC", "hevc": "H.265/HEVC", "h.265": "H.265/HEVC",
                 "prores": "ProRes", "dnxhd": "DNxHD", "dnxhr": "DNxHD",
                 "cineform": "CineForm", "exr": "EXR Sequence",
                 "png": "PNG Sequence", "av1": "AV1"}

RE_QUEUE = re.compile(r"- \[(\w+)\] (\S+) -> (.+?), (\d+)x(\d+) ([\d.]+)fps")
RE_PROGRESS = re.compile(r"\[(\w+)\] Rendering progress: (\d+)/(\d+) frames")
RE_DONE_JOB = re.compile(r"\[(\w+)\] Rendering completed: (?:\x1b\[[\d;]*m)?(.+?)(?:\x1b\[0m)?$")
RE_JOB_ERROR = re.compile(r"\[(\w+)\] Error: (.+)$")
RE_MISSING = re.compile(r"\[ERROR\] File (.+) doesn't exist\.")
RE_FINISHED = re.compile(r"\[INFO\] Done in ([\d.]+)s")
RE_ANSI = re.compile(r"\x1b\[[\d;]*m|</?font[^>]*>")


class GFError(Exception):
    pass


def find_bin():
    """Return the gyroflow CLI path, or raise GFError with install hints."""
    for candidate in (os.environ.get("GYROFLOW_BIN"), APP_BIN,
                      shutil.which("gyroflow")):
        if candidate and os.access(candidate, os.X_OK):
            return candidate
    raise GFError("gyroflow CLI not found. Install Gyroflow (Mac App Store or "
                  "https://gyroflow.xyz/download), or set GYROFLOW_BIN to "
                  "<Gyroflow.app>/Contents/MacOS/gyroflow")


def is_sandboxed(binary):
    """True when the binary carries the App Sandbox entitlement."""
    if os.environ.get("GYROFLOW_SANDBOX") in ("0", "1"):
        return os.environ["GYROFLOW_SANDBOX"] == "1"
    app = binary.split("/Contents/MacOS/")[0] if "/Contents/MacOS/" in binary else binary
    try:
        out = subprocess.run(["codesign", "-d", "--entitlements", "-", app],
                             capture_output=True, text=True, timeout=20)
    except (OSError, subprocess.TimeoutExpired):
        return True  # assume the restrictive case
    return "com.apple.security.app-sandbox" in (out.stdout + out.stderr)


def version(binary):
    out = subprocess.run([binary, "--version"], capture_output=True, text=True,
                         timeout=60)
    m = re.search(r"Gyroflow v?(\d+\.\d+\.\d+\S*)", out.stdout + out.stderr)
    return m.group(1) if m else "unknown"


def normalize_codec(name):
    if not name:
        return None
    if name in CODEC_EXT:
        return name
    key = name.strip().lower()
    if key in CODEC_ALIASES:
        return CODEC_ALIASES[key]
    raise GFError(f"unknown codec {name!r}; use one of: {', '.join(CODEC_EXT)}")


def collect_inputs(paths, recursive=False):
    """Expand files and folders to absolute video file paths (sorted, unique)."""
    found = []
    for path in paths:
        path = os.path.abspath(os.path.expanduser(path))
        if os.path.isfile(path):
            found.append(path)
        elif os.path.isdir(path):
            walker = os.walk(path) if recursive else [(path, [], os.listdir(path))]
            for root, _dirs, files in walker:
                for name in sorted(files):
                    if name.startswith("."):
                        continue
                    if os.path.splitext(name)[1].lower() in VIDEO_EXTS:
                        found.append(os.path.join(root, name))
        else:
            raise GFError(f"input not found: {path}")
    seen, unique = set(), []
    for f in found:
        if f not in seen:
            seen.add(f)
            unique.append(f)
    return unique


def ffprobe(path):
    """Return ffprobe's format+streams JSON for path, or None if unreadable."""
    exe = shutil.which("ffprobe")
    if not exe:
        raise GFError("ffprobe not found (brew install ffmpeg)")
    out = subprocess.run([exe, "-v", "error", "-show_format", "-show_streams",
                          "-of", "json", path], capture_output=True, text=True)
    if out.returncode != 0:
        return None
    data = json.loads(out.stdout or "{}")
    return data if data.get("streams") else None


def video_info(path, count_frames=False):
    """Summarize the first video stream: codec, profile, size, fps, frames, duration."""
    data = ffprobe(path)
    if not data:
        return None
    video = next((s for s in data["streams"] if s.get("codec_type") == "video"), None)
    if not video:
        return None
    info = {"codec": video.get("codec_name"), "profile": video.get("profile"),
            "width": video.get("width"), "height": video.get("height"),
            "pix_fmt": video.get("pix_fmt"),
            "frames": int(video["nb_frames"]) if str(video.get("nb_frames", "")).isdigit() else None,
            "duration": float(data["format"].get("duration") or video.get("duration") or 0),
            "fps": None,
            "audio": sum(1 for s in data["streams"] if s.get("codec_type") == "audio"),
            "gyro_tracks": [s.get("codec_tag_string") for s in data["streams"]
                            if s.get("codec_tag_string") in ("gpmd", "camm", "djmd", "dbgi")]}
    num, _, den = (video.get("avg_frame_rate") or "0/1").partition("/")
    if den and float(den):
        info["fps"] = round(float(num) / float(den), 3)
    if count_frames and info["frames"] is None:
        out = subprocess.run([shutil.which("ffprobe"), "-v", "error", "-count_packets",
                              "-select_streams", "v:0", "-show_entries",
                              "stream=nb_read_packets", "-of", "csv=p=0", path],
                             capture_output=True, text=True)
        if out.stdout.strip().isdigit():
            info["frames"] = int(out.stdout.strip())
    return info


def load_json_arg(value):
    """Accept a JSON string or a path to a JSON file (preset, project, params)."""
    if value is None:
        return None
    if os.path.isfile(os.path.expanduser(value)):
        with open(os.path.expanduser(value), encoding="utf-8") as fh:
            return json.load(fh)
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        try:  # Gyroflow's own help shows single-quoted pseudo-JSON
            return json.loads(value.replace("'", '"'))
        except json.JSONDecodeError as exc:
            raise GFError(f"not a JSON file or JSON text: {value[:80]}") from exc


def deep_merge(base, extra):
    out = dict(base)
    for key, value in (extra or {}).items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = deep_merge(out[key], value)
        else:
            out[key] = value
    return out


def set_smoothing(stab, name, value):
    params = [p for p in stab.get("smoothing_params", []) if p.get("name") != name]
    params.append({"name": name, "value": float(value)})
    stab["smoothing_params"] = params


def add_stab_args(parser):
    """CLI flags that map onto preset['stabilization'] (shared by render/export/preset)."""
    g = parser.add_argument_group("stabilization (override the preset)")
    g.add_argument("--preset", help="preset or .gyroflow project: file path or JSON text")
    g.add_argument("--smoothing", type=float, help="smoothness 0.001-1 (Default method; GUI default 0.5)")
    g.add_argument("--method", help='smoothing method, e.g. "Default", "Plain 3D", "Fixed camera", "No smoothing"')
    g.add_argument("--fov", type=float, help="FOV factor, >1 zooms out (default 1.0)")
    g.add_argument("--max-zoom", type=float, help="max zoom in percent (default 130)")
    g.add_argument("--horizon-lock", type=float, metavar="PCT",
                   help="horizon lock amount in percent, 0-100 (100 = fully level)")
    g.add_argument("--horizon-roll", type=float, help="horizon roll offset in degrees")
    g.add_argument("--lens-correction", type=float, metavar="0-1",
                   help="lens distortion correction amount 0-1 (default 1)")
    return g


def build_preset(args):
    """Merge --preset with the stabilization flags into a version-2 preset dict."""
    preset = load_json_arg(getattr(args, "preset", None)) or {}
    if "stabilization" not in preset and "output" not in preset and preset:
        raise GFError("--preset JSON has neither 'stabilization' nor 'output'; "
                      "is it a lens profile? pass lens profiles with --lens")
    preset.setdefault("version", 2)
    stab = dict(preset.get("stabilization") or {})
    if args.smoothing is not None:
        if not 0 < args.smoothing <= 1:
            raise GFError("--smoothing must be in (0, 1]")
        set_smoothing(stab, "smoothness", args.smoothing)
    if args.method:
        stab["method"] = args.method
    if args.fov is not None:
        stab["fov"] = args.fov
    if args.max_zoom is not None:
        stab["max_zoom"] = args.max_zoom
    if args.horizon_lock is not None:
        if not 0 <= args.horizon_lock <= 100:
            raise GFError("--horizon-lock is a percentage, 0-100")
        stab["horizon_lock_amount"] = args.horizon_lock
    if args.horizon_roll is not None:
        stab["horizon_lock_roll"] = args.horizon_roll
    if args.lens_correction is not None:
        stab["lens_correction_amount"] = args.lens_correction
    if stab:
        preset["stabilization"] = stab
    # Gyroflow applies horizon lock only when amount AND roll are both present.
    if ("horizon_lock_amount" in stab) != ("horizon_lock_roll" in stab):
        stab.setdefault("horizon_lock_amount", 100.0)
        stab.setdefault("horizon_lock_roll", 0.0)
    return preset


def split_output(preset):
    """Pull the output section out of a preset: its codec must travel in -p,
    because a preset codec does not change the file extension (ProRes in .mp4 fails)."""
    preset = dict(preset)
    output = dict(preset.pop("output", None) or {})
    for key in ("output_folder", "output_filename", "input_filename", "input_url",
                "output_folder_bookmark"):
        output.pop(key, None)
    return preset, output


def pjson(obj):
    return json.dumps(obj, separators=(", ", ": "))


class Stage:
    """A private run folder inside the sandbox: in/ (cloned inputs) and out/.

    Used for every run, sandboxed or not, so outputs only reach the user's folder
    once they are complete."""

    def __init__(self, sandboxed=True, keep=False):
        base = RUNS_DIR if sandboxed else os.path.join(
            os.environ.get("TMPDIR", "/tmp"), "gyroflow-agent-runs")
        self.root = os.path.join(base, time.strftime("%Y%m%d-%H%M%S-") + uuid.uuid4().hex[:6])
        self.inp = os.path.join(self.root, "in")
        self.out = os.path.join(self.root, "out")
        os.makedirs(self.inp)
        os.makedirs(self.out)
        self.keep = keep
        self.map = {}  # staged path -> original path

    def add(self, src, name=None):
        """Clone src into in/ (APFS clone; falls back to a copy) and return the staged path."""
        name = name or os.path.basename(src)
        stem, ext = os.path.splitext(name)
        dst, n = os.path.join(self.inp, name), 1
        while os.path.exists(dst):
            dst = os.path.join(self.inp, f"{stem}-{n}{ext}")
            n += 1
        if subprocess.run(["cp", "-c", src, dst], capture_output=True).returncode != 0:
            shutil.copy2(src, dst)
        self.map[dst] = src
        return dst

    def write_pid(self, pid):
        with open(os.path.join(self.root, "pid"), "w") as fh:
            fh.write(str(pid))

    def cleanup(self):
        if not self.keep:
            shutil.rmtree(self.root, ignore_errors=True)


def stage_or_direct(paths, sandboxed, stage):
    """Return the paths Gyroflow should see: staged clones in the sandbox,
    or the originals when the binary is not sandboxed."""
    return [stage.add(p) for p in paths] if sandboxed else list(paths)


class Job:
    def __init__(self, job_id):
        self.id = job_id
        self.input = None
        self.output = None
        self.size = None
        self.fps = None
        self.frames_done = 0
        self.frames_total = None
        self.completed = False
        self.error = None


class RunResult:
    def __init__(self):
        self.jobs = {}
        self.errors = []         # error lines not tied to a queued job
        self.missing = []        # "File X doesn't exist"
        self.finished = False    # saw "Done in"
        self.killed = None       # None | "stalled" | "timeout" | "interrupted"
        self.returncode = None
        self.log_tail = []

    def job(self, job_id):
        if job_id not in self.jobs:
            self.jobs[job_id] = Job(job_id)
        return self.jobs[job_id]


def run_gyroflow(binary, argv, stage=None, timeout=None, stall=90, on_progress=None,
                 log_path=None):
    """Run gyroflow, parse its log, and kill it if it stalls.

    stall: seconds without any progress/queue/completion line after an error, or
    without any output at all, before the process is killed (Gyroflow hangs after
    an unreadable input instead of exiting). on_progress(job) is called on each
    progress line."""
    res = RunResult()
    cmd = [binary] + argv
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            stdin=subprocess.DEVNULL, start_new_session=True)
    if stage:
        stage.write_pid(proc.pid)
    last_activity = [time.monotonic()]
    saw_error = [False]
    log = open(log_path, "a", encoding="utf-8") if log_path else None

    def reader():
        for raw in proc.stdout:
            line = RE_ANSI.sub("", raw.decode("utf-8", "replace").rstrip("\n"))
            if log:
                log.write(line + "\n")
            if "DEBUG" in line or not line.strip():
                continue
            res.log_tail = (res.log_tail + [line])[-40:]
            m = RE_PROGRESS.search(line)
            if m:
                j = res.job(m.group(1))
                j.frames_done, j.frames_total = int(m.group(2)), int(m.group(3))
                last_activity[0] = time.monotonic()
                if on_progress:
                    on_progress(j)
                continue
            m = RE_QUEUE.search(line)
            if m:
                j = res.job(m.group(1))
                j.input = m.group(2)
                j.output = m.group(3)
                j.size = (int(m.group(4)), int(m.group(5)))
                j.fps = float(m.group(6))
                last_activity[0] = time.monotonic()
                continue
            m = RE_DONE_JOB.search(line)
            if m:
                j = res.job(m.group(1))
                j.completed = True
                last_activity[0] = time.monotonic()
                continue
            m = RE_JOB_ERROR.search(line)
            if m:
                res.job(m.group(1)).error = m.group(2)
                saw_error[0] = True
                continue
            m = RE_MISSING.search(line)
            if m:
                res.missing.append(m.group(1))
                saw_error[0] = True
                continue
            if RE_FINISHED.search(line):
                res.finished = True
            elif "[ERROR]" in line and "bookmark" not in line:
                res.errors.append(line)
            if "Rendering" not in line and not saw_error[0]:
                last_activity[0] = time.monotonic()

    t = threading.Thread(target=reader, daemon=True)
    t.start()
    start = time.monotonic()
    try:
        while proc.poll() is None:
            time.sleep(0.5)
            now = time.monotonic()
            if timeout and now - start > timeout:
                res.killed = "timeout"
            elif now - last_activity[0] > (min(stall, 20) if saw_error[0] else stall):
                res.killed = "stalled"
            if res.killed:
                _kill(proc)
                break
    except KeyboardInterrupt:
        res.killed = "interrupted"
        _kill(proc)
    proc.wait()
    t.join(timeout=5)
    if log:
        log.close()
    res.returncode = proc.returncode
    return res


def _kill(proc):
    try:
        os.killpg(proc.pid, signal.SIGTERM)
        proc.wait(timeout=5)
    except (ProcessLookupError, subprocess.TimeoutExpired):
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass


def stop_runs():
    """Kill every gyroflow process started by these scripts and drop its run folder."""
    stopped = []
    for base in (RUNS_DIR, os.path.join(os.environ.get("TMPDIR", "/tmp"), "gyroflow-agent-runs")):
        if not os.path.isdir(base):
            continue
        for name in sorted(os.listdir(base)):
            pidfile = os.path.join(base, name, "pid")
            if not os.path.isfile(pidfile):
                continue
            pid = int(open(pidfile).read().strip() or 0)
            alive = False
            if pid:
                try:
                    os.killpg(pid, signal.SIGTERM)
                    alive = True
                except (ProcessLookupError, PermissionError):
                    pass
            stopped.append({"run": os.path.join(base, name), "pid": pid, "was_running": alive})
            shutil.rmtree(os.path.join(base, name), ignore_errors=True)
    return stopped


def move_out(src, dest_dir, force=False):
    """Move a finished output (file or sequence folder) into dest_dir."""
    os.makedirs(dest_dir, exist_ok=True)
    dst = os.path.join(dest_dir, os.path.basename(src.rstrip("/")))
    if os.path.exists(dst):
        if not force:
            raise GFError(f"exists, not overwritten (use --force): {dst}")
        if os.path.isdir(dst):
            shutil.rmtree(dst)
        else:
            os.remove(dst)
    shutil.move(src, dst)
    return dst
