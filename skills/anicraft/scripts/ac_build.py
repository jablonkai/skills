#!/usr/bin/env python3
"""Build or edit an .anicraft document from a JSON step spec, in one headless session.

Runs the spec's steps through `anicraft-cli serve`, so a step can use the ids an earlier
step returned (`run` can't). Stops at the first failing step and saves nothing then.

Spec (paths in it are relative to the spec's folder):

  {
    "new": {"width": 1080, "height": 1080, "fps": 30, "background": "#ffffff"},
    "source": "in.anicraft",          # instead of "new": edit a copy of an existing file
    "out": "ball.anicraft",            # never the source; --overwrite replaces it and
                                     # any existing export files
    "frames": "timeline",              # default: frame numbers in the spec are 1-based
                                       # (as in the timeline); "engine": 0-based, as sent
    "steps": [
      {"cmd": "draw.ellipse", "params": {"x": 100, "y": 100, "w": 120, "h": 120,
                                         "fill": "#ee3333"}, "as": "ball"},
      {"cmd": "modify.convert_to_symbol", "params": {"name": "Ball"}, "as": "sym"},
      {"cmd": "timeline.insert_frame", "params": {"layer": "$sym.layer", "frame": 30}},
      {"cmd": "draw.rect", "on": {"layer": "$layer:Ground", "frame": 1}, "params": {...}}
    ],
    "renders": {"dir": "renders", "frames": [1, 15, 30], "scale": 0.5}
  }

Step keys:
  cmd     command id (look it up: ac_commands.py)
  params  its params. A string "$name.key.0" is the result of the step saved `as` name
          (dotted path, list indexes allowed); "$layer:Name" is that layer's id.
  as      keep this step's result under a name
  on      {"layer", "frame"}: make the layer active and move the playhead first
          (layer.select + timeline.goto). draw.*, text.create, file.import, library.place
          and paste work on the active layer at the playhead and take no frame param.

In "timeline" mode `frame` (top level of params and in `on`) and `from`/`to` of
file.export_* and timeline.move_keyframes are converted 1-based -> 0-based. Frames nested
inside other params (e.g. actions' goto targets) are passed unchanged.

Prints a JSON report (named results, saved file, layers with 1-based keyframe ranges,
renders) and exits 0; on a failing step prints {"ok": false, "step": N, ...} and exits 1.
"""
import argparse
import copy
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import aclib  # noqa: E402


def lookup(results, ref):
    name, _, path = ref.partition(".")
    if name not in results:
        raise aclib.StepError("$%s: no earlier step saved as %r" % (ref, name))
    value = results[name]
    for part in [p for p in path.split(".") if p]:
        if isinstance(value, list):
            value = value[int(part)]
        elif isinstance(value, dict) and part in value:
            value = value[part]
        else:
            raise aclib.StepError("$%s: no %r in %s" % (ref, part, json.dumps(value)[:200]))
    return value


def resolve(value, results, session):
    if isinstance(value, str) and value.startswith("$"):
        if value.startswith("$layer:"):
            return session.layer_id(value[len("$layer:"):])
        return lookup(results, value[1:])
    if isinstance(value, list):
        return [resolve(v, results, session) for v in value]
    if isinstance(value, dict):
        return {k: resolve(v, results, session) for k, v in value.items()}
    return value


def to_engine(n, where):
    if isinstance(n, str):
        return n  # a $ref, converted after resolving
    if not isinstance(n, int) or n < 1:
        raise aclib.StepError("%s: frame %r is not a 1-based timeline frame" % (where, n))
    return n - 1


def convert_frames(cmd, params, where):
    params = dict(params)
    keys = ["frame"] + (["from", "to"] if cmd in aclib.FRAME_RANGE_COMMANDS else [])
    for key in keys:
        if key in params and params[key] is not None:
            params[key] = to_engine(params[key], "%s %s" % (where, key))
    return params


def layer_summary(info):
    out = []
    for layer in info.get("layers", []):
        keys = []
        for k in layer.get("keyframes", []):
            span = "%d-%d" % (k["start"] + 1, k["start"] + k["duration"])
            kind = ("motion" if k.get("motion") else k.get("tween")) or ""
            keys.append(" ".join(x for x in (span, kind, "%del" % k["elements"],
                                               "script" if k.get("script") else "") if x))
        out.append({"id": layer["id"], "name": layer["name"], "keyframes": keys})
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("spec")
    ap.add_argument("--overwrite", action="store_true",
                    help="replace an existing out file and existing export files")
    ap.add_argument("--dry-run", action="store_true",
                    help="print the steps with frames converted; run nothing")
    ap.add_argument("--plugins", help="WebAssembly plug-in folder (off by default)")
    args = ap.parse_args()

    spec_path = os.path.abspath(args.spec)
    with open(spec_path, encoding="utf-8") as fh:
        spec = json.load(fh)
    base = os.path.dirname(spec_path)
    os.chdir(base)
    mode = spec.get("frames", "timeline")
    if mode not in ("timeline", "engine"):
        sys.exit('"frames" must be "timeline" or "engine"')
    if ("new" in spec) == ("source" in spec):
        sys.exit('give exactly one of "new" and "source"')
    out = os.path.abspath(spec.get("out") or sys.exit('"out" is required'))
    if "source" in spec and os.path.abspath(spec["source"]) == out:
        sys.exit("out must not be the source file: edit a copy")
    if os.path.exists(out) and not args.overwrite and not args.dry_run:
        sys.exit("%s exists (pass --overwrite to replace it)" % out)

    steps = spec.get("steps", [])
    if args.dry_run:
        shown = []
        for i, step in enumerate(steps, 1):
            p = step.get("params", {})
            if mode == "timeline":
                p = convert_frames(step["cmd"], p, "step %d" % i)
            shown.append({"step": i, "cmd": step["cmd"], "params": p,
                          "on": step.get("on"), "as": step.get("as")})
        print(json.dumps(shown, indent=1))
        return

    os.makedirs(os.path.dirname(out), exist_ok=True)
    tmp = None
    if "new" in spec:
        new = spec["new"]
        fd, tmp = tempfile.mkstemp(suffix=".anicraft", dir=os.path.dirname(out))
        os.close(fd)
        os.unlink(tmp)
        cmd = ["new", "--out", tmp]
        for key in ("width", "height", "fps"):
            if key in new:
                cmd += ["--%s" % key, str(new[key])]
        aclib.run_cli(cmd)
        source = tmp
    else:
        source = os.path.abspath(spec["source"])
        if not os.path.isfile(source):
            sys.exit("source %s not found" % source)

    results, log = {}, []
    report = {"ok": True}
    try:
        with aclib.Serve(source, plugins=args.plugins) as s:
            if "new" in spec and spec["new"].get("background"):
                s.call("doc.set_stage", {"background": spec["new"]["background"]})
            for i, step in enumerate(steps, 1):
                cmd = step.get("cmd")
                try:
                    if not cmd:
                        raise aclib.StepError("missing cmd")
                    on = step.get("on") or {}
                    if "layer" in on:
                        s.call("layer.select", {"layer": resolve(on["layer"], results, s)})
                    if "frame" in on:
                        f = on["frame"]
                        if mode == "timeline":
                            f = to_engine(f, "step %d on.frame" % i)
                        s.call("timeline.goto", {"frame": resolve(f, results, s)})
                    params = step.get("params", {})
                    if mode == "timeline":  # $refs to frames are engine values already
                        params = convert_frames(cmd, params, "step %d" % i)
                    params = resolve(copy.deepcopy(params), results, s)
                    if args.overwrite and cmd.startswith("file.export_"):
                        params.setdefault("confirm", True)  # re-runs replace old exports
                    if cmd.startswith("file.export_") or cmd in ("file.save_as", "file.save"):
                        # exports and saves don't create missing folders
                        target = params.get("dir") or os.path.dirname(params.get("path") or "")
                        if target:
                            os.makedirs(target, exist_ok=True)
                    result = s.call(cmd, params)
                except aclib.StepError as exc:
                    print(json.dumps({"ok": False, "step": i, "cmd": cmd,
                                      "error": str(exc), "done": log}, indent=1))
                    sys.exit(1)
                if step.get("as"):
                    results[step["as"]] = result
                log.append("%d %s" % (i, cmd))
            s.call("file.save_as", {"path": out, "confirm": True})
            report["info"] = s.call("doc.info")
    finally:
        if tmp and os.path.exists(tmp):
            os.unlink(tmp)

    info = report.pop("info")
    report.update({
        "saved": out,
        "steps": len(log),
        "results": results,
        "stage": info.get("stage"),
        "frames": info.get("frames"),
        "layers": layer_summary(info),
    })
    renders = spec.get("renders")
    if renders:
        rdir = os.path.abspath(renders.get("dir", "renders"))
        os.makedirs(rdir, exist_ok=True)
        report["renders"] = []
        for n in renders.get("frames", [1]):
            png = os.path.join(rdir, "frame_%04d.png" % n)
            cmd = ["render", out, "--out", png, "--frame", str(n)]
            if renders.get("scale"):
                cmd += ["--scale", str(renders["scale"])]
            aclib.run_cli(cmd)
            report["renders"].append(png)
    print(json.dumps(report, indent=1))


if __name__ == "__main__":
    main()
