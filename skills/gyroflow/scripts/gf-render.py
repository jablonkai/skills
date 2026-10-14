#!/usr/bin/env python3
"""Stabilize clips with the Gyroflow CLI: one file, several, or whole folders.

  gf-render.py CLIP|FOLDER... --out-dir DIR [--codec ProRes --profile HQ]
               [--smoothing 0.8 --fov 1.1 --horizon-lock 100] [--preset FILE]
               [-j 2] [--gyro-file LOG] [--lens PROFILE.json] [--summary FILE]
  gf-render.py --stop       kill renders started by this skill and drop their runs

What it adds over the raw CLI:
- stages inputs into the sandbox folder the App Store build can read, and moves
  finished outputs to --out-dir;
- checks each clip first (ffprobe + Gyroflow's own motion parse) and leaves out
  unreadable clips and clips without gyro data, because one unreadable input
  stalls the whole queue;
- judges success per clip from the log and the files (the exit code is always 0)
  and kills a stalled process;
- prints progress per clip, and writes a JSON summary that gf-verify.py checks.

Exit: 0 all done, 1 some failed, 2 setup error, 124 --timeout, 130 interrupted.
Existing outputs in --out-dir are skipped (re-run resumes), unless --force.
"""

import argparse
import glob
import json
import os
import sys
import time
import urllib.parse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gf_lib as gf  # noqa: E402

def load_probe():
    import importlib.util
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gf-probe.py")
    spec = importlib.util.spec_from_file_location("gf_probe", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def parse_size(text):
    w, _, h = (text or "").lower().partition("x")
    if not (w.isdigit() and h.isdigit()):
        raise gf.GFError(f"--size must be WIDTHxHEIGHT, got {text!r}")
    return int(w), int(h)


def expected_name(src, suffix, codec):
    stem = os.path.splitext(os.path.basename(src))[0]
    ext = gf.CODEC_EXT.get(codec or "H.265/HEVC", ".mp4")
    return stem + suffix + ext


def build_params(args, preset_output):
    params = dict(preset_output)
    params.update(gf.load_json_arg(args.params) or {})
    codec = gf.normalize_codec(args.codec) or gf.normalize_codec(params.get("codec")) or None
    if codec:
        params["codec"] = codec
    if args.profile:
        params["codec_options"] = args.profile
    if args.bitrate:
        params["bitrate"] = args.bitrate
    if args.size:
        params["output_width"], params["output_height"] = parse_size(args.size)
    if args.no_audio:
        params["audio"] = False
    return params


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("inputs", nargs="*", help="clips and/or folders")
    ap.add_argument("--out-dir", help="where finished files go (default: next to each source)")
    ap.add_argument("--recursive", action="store_true", help="descend into subfolders")
    o = ap.add_argument_group("output")
    o.add_argument("--codec", help="ProRes | H.264/AVC | H.265/HEVC | DNxHD | CineForm | AV1 | "
                   "EXR Sequence | PNG Sequence (aliases: prores, h264, hevc, dnxhr, exr, png)")
    o.add_argument("--profile", help="codec_options: ProRes Proxy|LT|Standard|HQ|4444|4444XQ; "
                   "DNxHD 'DNxHR SQ'|'DNxHR HQ'|'DNxHR HQX'|...; PNG 8-bit|16-bit")
    o.add_argument("--bitrate", type=float, help="Mbps (H.264/H.265/AV1)")
    o.add_argument("--size", help="output WIDTHxHEIGHT (default: source size)")
    o.add_argument("--no-audio", action="store_true")
    o.add_argument("--suffix", default="_stabilized", help="output name suffix (default _stabilized)")
    o.add_argument("--params", help="extra -p output params as JSON (keys in references/cli-reference.md)")
    gf.add_stab_args(ap)
    m = ap.add_argument_group("motion data")
    m.add_argument("-g", "--gyro-file", help="external gyro log for every clip (.gcsv, blackbox, ...)")
    m.add_argument("--lens", help="lens profile .json to use for every clip")
    m.add_argument("--sync", help='-s sync params JSON, e.g. \'{"search_size": 3}\'')
    m.add_argument("--no-autosync", action="store_true",
                   help="with an external log: don't auto-sync gyro and video (default: on)")
    m.add_argument("--allow-no-gyro", action="store_true",
                   help="render clips without gyro data anyway (they come out unstabilized)")
    r = ap.add_argument_group("run")
    r.add_argument("-j", "--parallel", type=int, default=1, help="parallel renders (default 1)")
    r.add_argument("--no-gpu-decoding", action="store_true")
    r.add_argument("--timeout", type=float, help="stop the whole run after SEC seconds (exit 124)")
    r.add_argument("--stall", type=float, default=120, help="kill when silent this long (default 120 s)")
    r.add_argument("--force", action="store_true", help="re-render outputs that already exist")
    r.add_argument("--dry-run", action="store_true", help="print the plan and the gyroflow command")
    r.add_argument("--progress-json", action="store_true",
                   help="also print one JSON line per 10%% step to stdout")
    r.add_argument("--summary", help="write a JSON summary here (input for gf-verify.py)")
    r.add_argument("--keep-stage", action="store_true", help="keep the sandbox run folder (debugging)")
    r.add_argument("--log", help="write the full gyroflow log here")
    r.add_argument("--stop", action="store_true", help="stop renders started by this skill and exit")
    args = ap.parse_args()

    if args.stop:
        print(json.dumps(gf.stop_runs(), indent=2))
        return 0
    if not args.inputs:
        ap.error("no inputs")

    try:
        binary = gf.find_bin()
        sandboxed = gf.is_sandboxed(binary)
        clips = gf.collect_inputs(args.inputs, args.recursive)
        if not clips:
            raise gf.GFError("no video files found in the inputs")
        preset, preset_output = gf.split_output(gf.build_preset(args))
        params = build_params(args, preset_output)
        codec = params.get("codec")
        if sandboxed and codec in ("PNG Sequence", "EXR Sequence"):
            raise gf.GFError(
                f"{codec} does not work in the sandboxed (App Store) build: it writes one empty "
                "file named '..._%2505d.*'. Render --codec ProRes --profile 4444 and extract "
                "frames with ffmpeg, or use the gyroflow.xyz DMG build (GYROFLOW_BIN=...)")
        sync = gf.load_json_arg(args.sync) or {}
        for f in (args.gyro_file, args.lens):
            if f and not os.path.isfile(f):
                raise gf.GFError(f"not found: {f}")
    except gf.GFError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    summary = {"tool": "gf-render", "gyroflow": gf.version(binary), "sandboxed": sandboxed,
               "codec": codec or "H.265/HEVC (GUI default)", "codec_options": params.get("codec_options"),
               "preset": preset, "params": params, "jobs": []}
    jobs = []
    names_seen = {}
    for src in clips:
        dest_dir = os.path.abspath(args.out_dir) if args.out_dir else os.path.dirname(src)
        name = expected_name(src, args.suffix, codec)
        dest = os.path.join(dest_dir, name.split("_%05d")[0] if "%05d" in name else name)
        job = {"source": src, "output": dest, "status": "pending"}
        if dest in names_seen:
            job.update(status="failed", reason=f"same output name as {names_seen[dest]}")
        elif os.path.abspath(dest) == src:
            job.update(status="failed", reason="output would overwrite the source")
        elif os.path.exists(dest) and not args.force:
            job.update(status="skipped", reason="output exists (use --force to re-render)")
        names_seen[dest] = src
        jobs.append(job)

    todo = [j for j in jobs if j["status"] == "pending"]
    if args.dry_run:
        for j in jobs:
            print(f"{j['status']:8} {j['source']} -> {j['output']}" + (f"  ({j['reason']})" if j.get("reason") else ""))
        argv = build_argv([j["source"] for j in todo], "<stage>/out/", params, preset, sync, args)
        print("\ngyroflow " + " ".join(_q(a) for a in argv))
        return 0

    probe = load_probe()
    for j in todo:
        info = gf.video_info(j["source"])
        if not info:
            j.update(status="failed", reason="unreadable: ffprobe finds no video stream")
            continue
        j["source_info"] = info
        motion = probe.probe_motion(binary, sandboxed, j["source"], args.gyro_file)
        j["motion"] = motion
        if not motion.get("readable"):
            j.update(status="failed", reason=f"Gyroflow cannot read it: {motion.get('error')}")
        elif not motion.get("gyro_ok") and not args.allow_no_gyro:
            j.update(status="failed", reason="no gyro data in the clip; pass --gyro-file LOG "
                     "(or put LOG.gcsv next to it), or --allow-no-gyro")
        elif motion.get("gyro_file") and not args.gyro_file:
            j["sidecar"] = motion["gyro_file"]
    todo = [j for j in jobs if j["status"] == "pending"]

    # -g applies to every clip of a Gyroflow run, so a clip with its own sidecar
    # log runs on its own; clips with embedded gyro (or the shared --gyro-file) share one.
    groups = {}
    for j in todo:
        groups.setdefault(j.get("sidecar") or args.gyro_file, []).append(j)
    rc = 0
    for gyro_file, group in groups.items():
        group_sync = dict(sync)
        if gyro_file and not args.no_autosync:
            group_sync.setdefault("do_autosync", True)
        rc = render(binary, sandboxed, group, params, preset, group_sync, args, gyro_file) or rc
        if rc in (124, 130):
            break
    summary["jobs"] = jobs
    counts = {s: sum(1 for j in jobs if j["status"] == s) for s in ("done", "skipped", "failed", "pending")}
    summary["counts"] = counts
    for j in jobs:
        line = f"{j['status']:8} {os.path.basename(j['source'])}"
        if j["status"] == "done":
            out = j.get("output_info") or {}
            line += f" -> {j['output']} ({out.get('codec')} {out.get('profile') or ''} {out.get('width')}x{out.get('height')}, {out.get('frames')} frames)"
        elif j.get("reason"):
            line += f": {j['reason']}"
        print(line, file=sys.stderr)
    print(f"done {counts['done']}, skipped {counts['skipped']}, failed {counts['failed']}"
          + (f", not run {counts['pending']}" if counts["pending"] else ""), file=sys.stderr)
    if args.summary:
        os.makedirs(os.path.dirname(os.path.abspath(args.summary)), exist_ok=True)
        with open(args.summary, "w", encoding="utf-8") as fh:
            json.dump(summary, fh, indent=2)
    if rc:
        return rc
    return 1 if counts["failed"] or counts["pending"] else 0


def _q(a):
    return a if all(c.isalnum() or c in "/._-:=" for c in a) else "'" + a.replace("'", "'\\''") + "'"


def build_argv(clips, out_folder, params, preset, sync, args, gyro=None, lens=None):
    p = dict(params)
    p["output_folder"] = out_folder
    argv = list(clips)
    if lens:
        argv.append(lens)
    argv += ["-f", "--stdout-progress", "-t", args.suffix, "-j", str(max(1, args.parallel)),
             "-p", gf.pjson(p)]
    if preset.get("stabilization") or len(preset) > 1:
        argv += ["--preset", gf.pjson(preset)]
    if sync:
        argv += ["-s", gf.pjson(sync)]
    if gyro:
        argv += ["-g", gyro]
    if args.no_gpu_decoding:
        argv.append("--no-gpu-decoding")
    return argv


def render(binary, sandboxed, todo, params, preset, sync, args, gyro_file=None):
    stage = gf.Stage(sandboxed, keep=args.keep_stage)
    try:
        staged = {}
        for j in todo:
            path = stage.add(j["source"]) if sandboxed else j["source"]
            staged[path] = j
        gyro = lens = None
        if gyro_file:
            gyro = stage.add(gyro_file) if sandboxed else os.path.abspath(gyro_file)
        if args.lens:
            lens = stage.add(args.lens) if sandboxed else os.path.abspath(args.lens)
        argv = build_argv(list(staged), stage.out + "/", params, preset, sync, args, gyro, lens)
        by_name = {os.path.basename(p): j for p, j in staged.items()}
        reported = {}

        def on_progress(job):
            if not job.frames_total:
                return
            step = int(job.frames_done * 10 / job.frames_total)
            if reported.get(job.id, -1) >= step:
                return
            reported[job.id] = step
            name = os.path.basename(urllib.parse.unquote(job.input or "")) or job.id
            pct = round(100.0 * job.frames_done / job.frames_total, 1)
            print(f"[{name}] {pct:5.1f}% ({job.frames_done}/{job.frames_total} frames)",
                  file=sys.stderr, flush=True)
            if args.progress_json:
                print(json.dumps({"file": name, "percent": pct, "frames": job.frames_done,
                                  "total": job.frames_total, "t": round(time.time(), 1)}), flush=True)

        print(f"rendering {len(todo)} clip(s), -j {args.parallel}...", file=sys.stderr, flush=True)
        res = gf.run_gyroflow(binary, argv, stage, timeout=args.timeout, stall=args.stall,
                              on_progress=on_progress, log_path=args.log)

        for gjob in res.jobs.values():
            if not gjob.input:
                continue
            j = by_name.get(os.path.basename(urllib.parse.unquote(gjob.input)))
            if not j:
                continue
            j["gyroflow_job"] = gjob.id
            if gjob.error:
                j.update(status="failed", reason=gjob.error)
            elif gjob.completed and gjob.output:
                collect(j, gjob.output, stage, args)
            else:
                j.update(status="failed" if res.killed is None else "pending",
                         reason=f"no completion ({res.killed or 'renderer ended early'}); "
                                f"{gjob.frames_done}/{gjob.frames_total or '?'} frames")
        for j in todo:
            if j["status"] == "pending" and not res.killed:
                j.update(status="failed", reason="not queued by Gyroflow: "
                         + (res.errors[-1] if res.errors else "see --log"))
            elif j["status"] == "pending":
                j["reason"] = f"run {res.killed} before this clip finished"
        if res.killed == "timeout":
            return 124
        if res.killed == "interrupted":
            return 130
        return 0
    finally:
        stage.cleanup()


def collect(j, out_path, stage, args):
    """Move a finished output to its destination and record ffprobe facts."""
    if "%05d" in out_path:  # image sequence: gather frames into a folder
        frames = sorted(glob.glob(out_path.replace("%05d", "?" * 5)))
        if not frames:
            j.update(status="failed", reason="sequence reported complete but no frames found")
            return
        dest = j["output"]
        os.makedirs(dest, exist_ok=True)
        for f in frames:
            gf.move_out(f, dest, force=True)
        first = os.path.join(dest, os.path.basename(frames[0]))
        info = gf.video_info(first) or {}
        info["frames"] = len(frames)
        j.update(status="done", output_info=info)
        return
    if not os.path.isfile(out_path) or os.path.getsize(out_path) == 0:
        j.update(status="failed", reason="Gyroflow reported completion but the file is missing or empty")
        return
    info = gf.video_info(out_path, count_frames=True)
    if not info:
        j.update(status="failed", reason="output is not a readable video")
        return
    try:
        final = gf.move_out(out_path, os.path.dirname(j["output"]), force=True)
    except gf.GFError as exc:
        j.update(status="failed", reason=str(exc))
        return
    if os.path.basename(final) != os.path.basename(j["output"]):
        os.replace(final, j["output"])
    j.update(status="done", output_info=info)


if __name__ == "__main__":
    sys.exit(main())
