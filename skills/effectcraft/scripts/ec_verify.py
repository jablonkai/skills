#!/usr/bin/env python3
"""Read EffectCraft projects, templates and renders back and check them.

Prints JSON {"ok": bool, "checks": [...]} and exits 1 when any check fails.

  project F.ecproj --comp LT [--size 1920x1080] [--duration 5] [--fps 25]
          [--layer Name:Text Bar:Shape] [--text Name="Jane Doe"]
          [--value Bar:transform/opacity=90] [--value Name:transform/position@0.6=[160,900]]
          [--animated Name:transform/position] [--min-keys 2]
          [--key Name:transform/position@0.6=[160,900]]
          [--effect Bar="Drop Shadow"] [--expression Bar:transform/rotation]
  render FILE… [--codec prores] [--profile 4444] [--alpha] [--duration 5] [--size 1920x1080]
         [--fps 25] [--count 3]
  template T.ectemplate [--controls Name Title]
  hash PATH… [--compare manifest.json]      (no --compare: print a manifest)
  differ A B                                 (the two files are not byte-identical)

Times are comp seconds. Vectors compare on the given components ([160,900] matches
[160,900,0]) with a 0.01 tolerance; colours are 0–1 floats or #hex.
"""
import argparse
import hashlib
import json
import os
import sys

from eclib import ffprobe, run_cli

TOL = 0.01


class Checks:
    def __init__(self):
        self.items = []

    def add(self, name, ok, detail=None):
        self.items.append({"check": name, "ok": bool(ok), "detail": detail})

    def finish(self, extra=None):
        out = {"ok": all(c["ok"] for c in self.items), "checks": self.items}
        if extra:
            out.update(extra)
        print(json.dumps(out, indent=2))
        sys.exit(0 if out["ok"] else 1)


def hex_rgb(s):
    s = s.lstrip("#")
    return [int(s[i:i + 2], 16) / 255.0 for i in (0, 2, 4)]


def same(actual, expected):
    if isinstance(expected, str) and expected.startswith("#") and isinstance(actual, list):
        expected = hex_rgb(expected)
    if isinstance(expected, (int, float)) and isinstance(actual, (int, float)):
        return abs(actual - expected) <= TOL
    if isinstance(expected, list) and isinstance(actual, list):
        return len(actual) >= len(expected) and all(
            same(a, e) for a, e in zip(actual, expected))
    return actual == expected


def split_target(spec):
    """'Layer:path@T=VALUE' -> (layer, path, time, value-json-or-None)."""
    target, eq, value = spec.partition("=")
    layer, _, path = target.partition(":")
    time = None
    if "@" in path:
        path, _, t = path.partition("@")
        time = float(t)
    return layer, path, time, (value if eq else None)


def parse_value(text):
    try:
        return json.loads(text)
    except ValueError:
        return text


def get(project, comp, layer, path, time=None):
    args = ["get", comp, layer, path, "--project", project, "--json"]
    if time is not None:
        args += ["--time", str(time)]
    return json.loads(run_cli(args).stdout)


def effect_names(project, comp, layer):
    tree = json.loads(run_cli(["props", comp, layer, "--project", project, "--json"]).stdout)
    names = []

    def walk(node):
        if isinstance(node, dict):
            if node.get("effect") and node.get("path", "").startswith("effects/#"):
                names.append(node.get("name"))
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)
    walk(tree)
    return names


def cmd_project(a):
    c = Checks()
    comp = json.loads(run_cli(["exec", "comp.info", "--params", json.dumps({"comp": a.comp}),
                               "--project", a.file, "--json"]).stdout)
    layers = {l["name"]: l for l in comp.get("layers", [])}
    summary = {"comp": comp.get("name"), "size": [comp.get("width"), comp.get("height")],
               "duration": comp.get("duration"), "fps": comp.get("frameRate"),
               "layers": [[l["index"], l["name"], l["type"]] for l in comp.get("layers", [])]}
    if a.size:
        w, h = (int(x) for x in a.size.lower().split("x"))
        c.add("size %s" % a.size, (comp["width"], comp["height"]) == (w, h),
              [comp["width"], comp["height"]])
    if a.duration is not None:
        c.add("duration %s" % a.duration, abs(comp["duration"] - a.duration) <= TOL,
              comp["duration"])
    if a.fps is not None:
        c.add("fps %s" % a.fps, abs(comp["frameRate"] - a.fps) <= TOL, comp["frameRate"])
    for spec in a.layer or []:
        name, _, kind = spec.partition(":")
        l = layers.get(name)
        ok = l is not None and (not kind or l["type"].lower() == kind.lower())
        c.add("layer %s" % spec, ok, l and l["type"])
    for spec in a.text or []:
        layer, _, want = spec.partition("=")
        r = get(a.file, a.comp, layer, "text/sourceText")
        c.add("text %s" % layer, r.get("value") == want, r.get("value"))
    for spec in a.value or []:
        layer, path, time, want = split_target(spec)
        r = get(a.file, a.comp, layer, path, time)
        got = r.get("evaluated", r.get("value"))
        c.add("value %s" % spec, same(got, parse_value(want)), got)
    for spec in a.animated or []:
        layer, path, _, _ = split_target(spec)
        keys = get(a.file, a.comp, layer, path).get("keys") or []
        values = [k["value"] for k in keys]
        moves = len(values) >= 2 and any(not same(v, values[0]) for v in values[1:])
        c.add("animated %s (>= %d keys, values change)" % (spec, a.min_keys),
              len(keys) >= a.min_keys and moves,
              [[k.get("compTime", k.get("time")), k["value"]] for k in keys])
    for spec in a.key or []:
        layer, path, time, want = split_target(spec)
        keys = get(a.file, a.comp, layer, path).get("keys") or []
        hit = [k for k in keys if abs(k.get("compTime", k.get("time")) - time) <= TOL]
        c.add("key %s" % spec, bool(hit) and same(hit[0]["value"], parse_value(want)),
              [[k.get("compTime", k.get("time")), k["value"]] for k in keys])
    for spec in a.effect or []:
        layer, _, name = spec.partition("=")
        names = effect_names(a.file, a.comp, layer)
        c.add("effect %s" % spec, any(n.lower() == name.lower() for n in names), names)
    for spec in a.expression or []:
        layer, path, _, _ = split_target(spec)
        r = get(a.file, a.comp, layer, path)
        c.add("expression %s" % spec, bool(r.get("expression")) and not r.get("expressionError"),
              {"expression": r.get("expression"), "error": r.get("expressionError")})
    c.finish({"summary": summary})


def cmd_render(a):
    c = Checks()
    c.add("count %d" % a.count if a.count is not None else "files exist",
          all(os.path.isfile(f) for f in a.files) and (a.count is None or len(a.files) == a.count),
          len(a.files))
    report = []
    for f in a.files:
        if not os.path.isfile(f):
            c.add("exists %s" % f, False)
            continue
        p = ffprobe(f)
        v = next((s for s in p["streams"] if s.get("codec_type") == "video"), {})
        dur = float(p["format"].get("duration") or v.get("duration") or 0)
        num, _, den = (v.get("avg_frame_rate") or v.get("r_frame_rate") or "0/1").partition("/")
        fps = float(num) / float(den or 1) if float(den or 1) else 0
        row = {"file": f, "codec": v.get("codec_name"), "profile": v.get("profile"),
               "pix_fmt": v.get("pix_fmt"), "size": [v.get("width"), v.get("height")],
               "duration": dur, "fps": round(fps, 3), "frames": v.get("nb_read_frames")}
        report.append(row)
        if a.codec:
            c.add("%s codec %s" % (os.path.basename(f), a.codec), row["codec"] == a.codec, row["codec"])
        if a.profile:
            c.add("%s profile %s" % (os.path.basename(f), a.profile),
                  a.profile.lower() in (row["profile"] or "").lower(), row["profile"])
        if a.alpha:
            pf = row["pix_fmt"] or ""
            c.add("%s alpha" % os.path.basename(f),
                  pf.startswith(("yuva", "rgba", "bgra", "argb", "abgr", "gbrap", "ya")), pf)
        if a.size:
            w, h = (int(x) for x in a.size.lower().split("x"))
            c.add("%s size %s" % (os.path.basename(f), a.size), row["size"] == [w, h], row["size"])
        if a.duration is not None and dur:
            frame = 1.0 / fps if fps else 0.05
            c.add("%s duration %s" % (os.path.basename(f), a.duration),
                  abs(dur - a.duration) <= frame + TOL, dur)
        if a.fps is not None:
            c.add("%s fps %s" % (os.path.basename(f), a.fps), abs(fps - a.fps) <= TOL, fps)
    c.finish({"files": report})


def template_info(path):
    return json.loads(run_cli(["--empty", "exec", "essential.templateInfo", "--params",
                               json.dumps({"path": os.path.abspath(path)}), "--json"]).stdout)


def cmd_template(a):
    c = Checks()
    t = template_info(a.file)
    controls = [{"name": x.get("name"), "type": x.get("type") or x.get("kind"),
                 "value": x.get("value")} for x in t.get("controls", [])]
    names = [x["name"].lower() for x in controls if x["name"]]
    for want in a.controls or []:
        c.add("control %s" % want, want.lower() in names)
    c.finish({"template": {"name": t.get("name"), "size": [t.get("width"), t.get("height")],
                           "duration": t.get("duration"), "fps": t.get("frameRate"),
                           "controls": controls, "media": t.get("media")}})


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def walk_files(paths):
    for p in paths:
        if os.path.isdir(p):
            for root, _, files in os.walk(p):
                for f in sorted(files):
                    yield os.path.join(root, f)
        else:
            yield p


def cmd_hash(a):
    manifest = {os.path.abspath(f): sha(f) for f in walk_files(a.paths)}
    if not a.compare:
        print(json.dumps(manifest, indent=2))
        return
    with open(a.compare) as f:
        before = json.load(f)
    c = Checks()
    for path, digest in before.items():
        c.add("unchanged %s" % path, manifest.get(path) == digest)
    c.finish()


def cmd_differ(a):
    c = Checks()
    c.add("%s differs from %s" % (a.a, a.b), sha(a.a) != sha(a.b))
    c.finish()


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("project", help="comp, layers, values, keyframes, effects")
    p.add_argument("file")
    p.add_argument("--comp", required=True)
    p.add_argument("--size")
    p.add_argument("--duration", type=float)
    p.add_argument("--fps", type=float)
    p.add_argument("--layer", nargs="+", help="Name or Name:Type")
    p.add_argument("--text", nargs="+", help="Layer=text")
    p.add_argument("--value", nargs="+", help="Layer:path[@time]=json")
    p.add_argument("--animated", nargs="+", help="Layer:path")
    p.add_argument("--min-keys", type=int, default=2)
    p.add_argument("--key", nargs="+", help="Layer:path@time=json")
    p.add_argument("--effect", nargs="+", help="Layer=Effect Name")
    p.add_argument("--expression", nargs="+", help="Layer:path")
    p.set_defaults(fn=cmd_project)

    p = sub.add_parser("render", help="ffprobe checks on rendered files")
    p.add_argument("files", nargs="+")
    p.add_argument("--codec")
    p.add_argument("--profile")
    p.add_argument("--alpha", action="store_true")
    p.add_argument("--size")
    p.add_argument("--duration", type=float)
    p.add_argument("--fps", type=float)
    p.add_argument("--count", type=int)
    p.set_defaults(fn=cmd_render)

    p = sub.add_parser("template", help="an .ectemplate's manifest and controls")
    p.add_argument("file")
    p.add_argument("--controls", nargs="+")
    p.set_defaults(fn=cmd_template)

    p = sub.add_parser("hash", help="sha256 manifest, or compare against one")
    p.add_argument("paths", nargs="+")
    p.add_argument("--compare")
    p.set_defaults(fn=cmd_hash)

    p = sub.add_parser("differ", help="two files are not byte-identical")
    p.add_argument("a")
    p.add_argument("b")
    p.set_defaults(fn=cmd_differ)

    a = ap.parse_args()
    try:
        a.fn(a)
    except RuntimeError as e:
        sys.exit("ec_verify: %s" % e)


if __name__ == "__main__":
    main()
