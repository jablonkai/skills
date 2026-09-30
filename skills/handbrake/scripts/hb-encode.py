#!/usr/bin/env python3
"""Encode one file, a folder batch or disc titles with HandBrakeCLI — safely.

    python3 hb-encode.py SOURCE... (--out-dir DIR | -o FILE) [options] [-- extra HandBrakeCLI args]

Every source is scanned first, so track and title choices are validated (and
languages resolved to track numbers) before anything is encoded. Each output is
written to a hidden `.NAME.hbpart.EXT` file and renamed only when HandBrakeCLI
succeeds, so a failed, stopped or timed-out encode never leaves a half file
behind. Existing outputs are skipped unless --force when ffprobe shows a full
duration; a truncated or unreadable one (e.g. from an earlier raw HandBrakeCLI run
that was killed) is re-encoded. Running the same command again resumes a batch.

Settings (any omitted one comes from the preset, or HandBrake's defaults):
  --preset NAME           built-in or imported preset (case-sensitive; hb-preset.py lists them)
  --preset-file FILE      import presets from a JSON export (repeatable)
  --encoder E             x265, x265_10bit, vt_h265, x264, svt_av1, ... (-e)
  --quality Q             constant quality / RF (-q); lower = better and bigger
  --max-res 1080p         resolution class, orientation-aware: landscape fits 1920x1080,
                          portrait fits 1080x1920 (also 480p 576p 720p 1440p 2160p/4k)
  --max-height H / --max-width W   fixed box instead: scale down to fit, never up (-Y / -X)
  --keep-anamorphic       keep the preset's anamorphic mode; by default square
                          pixels are forced (--non-anamorphic --keep-display-aspect)
  --format mp4|mkv|mov|webm        container; default from -o, then the preset, then mp4
  --audio SPEC            e.g. "1,3", "eng,hun" (first track of each language),
                          "eng*" (every eng track), "all", "none"; order is kept
  --aencoder E            audio encoder for every selected track (copy, ca_aac, opus, ...)
  --subtitle SPEC         same syntax as --audio (default: the preset's behaviour)
  --burn                  burn the first --subtitle track into the picture
  --default-subtitle      flag the first --subtitle track as default
Sources:
  --title N[,N...] | --main-feature | --min-duration SEC   (DVD/Blu-ray/ISO only)
  --recursive             descend into subfolders (their layout is mirrored in --out-dir)
  --ext mp4,mkv,...       file extensions to pick up from folders (default: common video)
Run control:
  --force                 replace existing outputs
  --dry-run               scan and print the HandBrakeCLI commands, encode nothing
  --timeout SEC           stop the whole batch after SEC seconds (exit 124)
  --summary FILE          also write the JSON summary to FILE (hb-verify.py reads it)

Ctrl-C / SIGTERM stops the running encode, deletes its partial output, and exits
130. The JSON summary (one entry per job: status done|skipped|failed|stopped|
pending, exit code, output, source duration) goes to stdout; progress goes to
stderr. Exit 1 if any job failed, 2 on usage or scan errors.
"""

import argparse
import json
import os
import shlex
import signal
import subprocess
import sys
import tempfile
import threading
import time

from hb_lib import (EXT_FOR_FORMAT, FORMATS, HBError, collect_sources, ffprobe,
                    find_cli, is_disc, json_blocks, resolve_preset, scan, seconds)

STOP = {"signal": None, "proc": None}


def on_signal(signum, _frame):
    STOP["signal"] = signum
    proc = STOP["proc"]
    if proc and proc.poll() is None:
        try:
            os.killpg(proc.pid, signal.SIGINT)
        except ProcessLookupError:
            pass


RES_CLASSES = {"480p": (854, 480), "576p": (1024, 576), "720p": (1280, 720),
               "1080p": (1920, 1080), "1440p": (2560, 1440), "2160p": (3840, 2160),
               "4k": (3840, 2160)}


def select_tracks(spec, tracks, kind):
    """Resolve an --audio/--subtitle spec to 1-based track numbers, in order."""
    if spec is None:
        return None
    spec = spec.strip().lower()
    if spec == "none":
        return []
    if spec == "all":
        return [t["track"] for t in tracks]
    picked = []
    for token in (t.strip() for t in spec.split(",") if t.strip()):
        if token.isdigit():
            n = int(token)
            if not 1 <= n <= len(tracks):
                raise HBError(f"{kind} track {n} does not exist (source has {len(tracks)})")
            matches = [n]
        else:
            every = token.endswith("*")
            lang = token.rstrip("*")
            matches = [t["track"] for t in tracks if (t["lang"] or "und").lower() == lang]
            if not matches:
                have = ", ".join(sorted({t["lang"] or "und" for t in tracks})) or "none"
                raise HBError(f"no {kind} track in language {lang!r} (have: {have})")
            if not every:
                matches = matches[:1]
        picked += [m for m in matches if m not in picked]
    return picked


def disc_label(src):
    path = os.path.normpath(src)
    if os.path.basename(path).upper() in ("VIDEO_TS", "BDMV"):
        path = os.path.dirname(path)
    return os.path.splitext(os.path.basename(path))[0] or "disc"


def plan_jobs(args, cli, fmt_default):
    """Scan every source and return the job list (one per output)."""
    sources = collect_sources(args.sources, args.recursive,
                              args.ext.split(",") if args.ext else None)
    if not sources:
        raise HBError("no video files found in the given sources")
    if args.output and len(sources) != 1:
        raise HBError("-o takes exactly one source; use --out-dir for batches")
    jobs = []
    for src, root in sources:
        disc = is_disc(src)
        if disc and (args.main_feature or not args.title):
            ts = scan(cli, src, 0, args.min_duration)
            titles = [ts.get("MainFeature") or ts["TitleList"][0]["Index"]]
            if not args.main_feature and len(ts["TitleList"]) > 1:
                print(f"note: {src} has {len(ts['TitleList'])} titles; encoding the "
                      f"main feature (title {titles[0]}). Use --title to choose.",
                      file=sys.stderr)
        elif disc:
            titles = [int(t) for t in args.title.split(",")]
            ts = scan(cli, src, 0, args.min_duration)
        else:
            titles = [1]
            ts = scan(cli, src, 1)
        by_index = {t["Index"]: t for t in ts["TitleList"]}
        for n in titles:
            if n not in by_index:
                raise HBError(f"{src}: title {n} not found (have: "
                              f"{', '.join(str(i) for i in sorted(by_index))})")
            t = by_index[n]
            audio = [{"track": i, "lang": a.get("LanguageCode")}
                     for i, a in enumerate(t.get("AudioList", []), 1)]
            subs = [{"track": i, "lang": s.get("LanguageCode")}
                    for i, s in enumerate(t.get("SubtitleList", []), 1)]
            try:
                a_sel = select_tracks(args.audio, audio, "audio")
                s_sel = select_tracks(args.subtitle, subs, "subtitle")
            except HBError as e:
                raise HBError(f"{src}: {e}") from None
            if args.burn and not s_sel:
                raise HBError(f"{src}: --burn needs a --subtitle track to burn")
            geo = t.get("Geometry", {})
            jobs.append({"source": src, "root": root, "disc": disc, "title": n,
                         "portrait": geo.get("Height", 0) > geo.get("Width", 0),
                         "source_duration_s": round(seconds(t["Duration"]), 3),
                         "audio": a_sel, "subtitle": s_sel})
    for job in jobs:
        job["output"] = output_path(args, job, fmt_default)
    seen = {}
    for job in jobs:
        out = os.path.realpath(job["output"])
        if out == os.path.realpath(job["source"]):
            raise HBError(f"output would overwrite its source: {job['source']}")
        if out in seen:
            raise HBError(f"{job['source']} and {seen[out]} would both write {job['output']}")
        seen[out] = job["source"]
    return jobs


def output_path(args, job, fmt):
    if args.output:
        return args.output
    ext = EXT_FOR_FORMAT[fmt]
    src = job["source"]
    if job["disc"]:
        stem = f"{disc_label(src)}-t{job['title']:02d}"
    else:
        stem = os.path.splitext(os.path.basename(src))[0]
    parent = os.path.dirname(os.path.normpath(src))
    rel_dir = os.path.relpath(parent, job["root"]) if job["root"] else ""
    return os.path.normpath(os.path.join(args.out_dir, rel_dir, stem + ext))


def build_cmd(cli, args, job, fmt, partial):
    cmd = [cli, "--json"]
    for f in args.preset_file:
        cmd += ["--preset-import-file", f]
    if args.preset:
        cmd += ["-Z", args.preset]
    cmd += ["-i", job["source"], "-t", str(job["title"]), "-o", partial, "-f", fmt]
    if args.encoder:
        cmd += ["-e", args.encoder]
    if args.quality is not None:
        cmd += ["-q", f"{args.quality:g}"]
    if args.max_res:
        # Scan geometry is already rotation-applied, so phone clips report portrait.
        long_, short = RES_CLASSES[args.max_res]
        w, h = (short, long_) if job["portrait"] else (long_, short)
        cmd += ["-X", str(w), "-Y", str(h)]
    if args.max_height:
        cmd += ["-Y", str(args.max_height)]
    if args.max_width:
        cmd += ["-X", str(args.max_width)]
    if not args.keep_anamorphic:
        # Without these, -X/-Y (and even built-in presets on portrait sources)
        # produce anamorphic storage such as 3840x1080 at PAR 1:2.
        cmd += ["--non-anamorphic", "--keep-display-aspect"]
    if job["audio"] is not None:
        cmd += ["-a", ",".join(map(str, job["audio"])) or "none"]
        if args.aencoder and job["audio"]:
            cmd += ["-E", ",".join([args.aencoder] * len(job["audio"]))]
    elif args.aencoder:
        cmd += ["-E", args.aencoder]
    if job["subtitle"] is not None:
        cmd += ["-s", ",".join(map(str, job["subtitle"])) or "none"]
        if args.burn:
            cmd += ["--subtitle-burned=1"]
        elif args.default_subtitle and job["subtitle"]:
            cmd += ["--subtitle-default=1"]
    return cmd + args.extra


def reader(stream, sink, label):
    """Collect stdout and report progress every 10% on stderr."""
    last = -1
    for line in stream:
        sink.append(line)
        s = line.strip()
        if s.startswith('"Progress":'):
            try:
                pct = int(float(s.split(":", 1)[1].rstrip(",")) * 100)
            except ValueError:
                continue
            if pct // 10 > last // 10 and pct < 100:
                last = pct
                print(f"  {label}  {pct}%", file=sys.stderr, flush=True)


def log_tail(path, n=6):
    try:
        with open(path, errors="replace") as fh:
            lines = [l.rstrip() for l in fh if l.strip()]
    except OSError:
        return ""
    errs = [l for l in lines if any(w in l.lower() for w in ("error", "invalid", "fail", "unknown"))]
    return " | ".join((errs or lines)[-n:])


def run_job(cli, args, job, fmt, deadline, logdir, label):
    out = job["output"]
    replacing = None
    if os.path.exists(out) and not args.force:
        problem = existing_problem(out, job["source_duration_s"])
        if not problem:
            return {"status": "skipped", "reason": "complete output exists (use --force)"}
        replacing = f"replaced broken existing output ({problem})"
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    base, ext = os.path.splitext(os.path.basename(out))
    partial = os.path.join(os.path.dirname(os.path.abspath(out)), f".{base}.hbpart{ext}")
    cmd = build_cmd(cli, args, job, fmt, partial)
    job["command"] = shlex.join(cmd).replace(partial, out)
    if args.dry_run:
        print(job["command"])
        return {"status": "dry-run"}
    log = os.path.join(logdir, f"{len(os.listdir(logdir)):03d}-{base}.log")
    started = time.time()
    lines = []
    with open(log, "w") as logfh:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=logfh, text=True,
                                errors="replace", start_new_session=True)
        STOP["proc"] = proc
        t = threading.Thread(target=reader, args=(proc.stdout, lines, label), daemon=True)
        t.start()
        timed_out = False
        while proc.poll() is None:
            if deadline and time.time() > deadline and not timed_out:
                timed_out = True
                STOP["signal"] = "timeout"
                os.killpg(proc.pid, signal.SIGINT)
            try:
                proc.wait(timeout=0.5)
            except subprocess.TimeoutExpired:
                if STOP["signal"] and _grace_over(proc):
                    os.killpg(proc.pid, signal.SIGKILL)
        t.join(timeout=5)
        STOP["proc"] = None
    rc = proc.returncode
    work_error = None
    for label_, obj in json_blocks("".join(lines)):
        if label_ == "Progress" and obj.get("State") == "WORKDONE":
            work_error = obj.get("WorkDone", {}).get("Error")
    result = {"exit_code": rc, "seconds": round(time.time() - started, 1)}
    ok = (not STOP["signal"] and rc == 0 and work_error in (0, None)
          and os.path.exists(partial) and os.path.getsize(partial) > 0)
    if ok:
        os.replace(partial, out)
        result["status"] = "done"
        result["size_mb"] = round(os.path.getsize(out) / 1e6, 2)
    else:
        if os.path.exists(partial):
            os.remove(partial)
        if STOP["signal"] == "timeout":
            result["status"] = "stopped"
            result["reason"] = "batch --timeout reached"
        elif STOP["signal"]:
            result["status"] = "stopped"
            result["reason"] = "interrupted"
        else:
            result["status"] = "failed"
            result["reason"] = log_tail(log)
            result["log"] = log
    if "log" not in result:
        os.remove(log)  # keep logs of failed jobs only
    if replacing and result["status"] == "done":
        result["reason"] = replacing
    return result


def existing_problem(path, source_duration):
    """Why an existing output is not a finished encode, or None if it is.

    A run killed without cleanup (raw HandBrakeCLI and Ctrl-C) leaves a file with
    no duration, so 'the output exists' alone must not count as done."""
    try:
        d = ffprobe(path)
    except (HBError, ValueError):
        return "unreadable"
    if not any(s.get("codec_type") == "video" for s in d.get("streams", [])):
        return "no video stream"
    try:
        dur = float(d.get("format", {}).get("duration"))
    except (TypeError, ValueError):
        return "no duration"
    if abs(dur - source_duration) > max(1.0, 0.02 * source_duration):
        return f"{dur:.1f}s of {source_duration:.1f}s"
    return None


_GRACE = {}


def _grace_over(proc, seconds_=20):
    """After a stop request, give HandBrake this long to exit before SIGKILL."""
    first = _GRACE.setdefault(proc.pid, time.time())
    return time.time() - first > seconds_


def main():
    argv = sys.argv[1:]
    extra = []
    if "--" in argv:
        i = argv.index("--")
        argv, extra = argv[:i], argv[i + 1:]
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("sources", nargs="+")
    ap.add_argument("-o", "--output")
    ap.add_argument("--out-dir")
    ap.add_argument("--preset")
    ap.add_argument("--preset-file", action="append", default=[])
    ap.add_argument("--encoder")
    ap.add_argument("--quality", type=float)
    ap.add_argument("--max-res", type=str.lower, choices=sorted(RES_CLASSES))
    ap.add_argument("--max-height", type=int)
    ap.add_argument("--max-width", type=int)
    ap.add_argument("--keep-anamorphic", action="store_true")
    ap.add_argument("--format", choices=sorted(FORMATS))
    ap.add_argument("--audio")
    ap.add_argument("--aencoder")
    ap.add_argument("--subtitle")
    ap.add_argument("--burn", action="store_true")
    ap.add_argument("--default-subtitle", action="store_true")
    ap.add_argument("--title")
    ap.add_argument("--main-feature", action="store_true")
    ap.add_argument("--min-duration", type=int)
    ap.add_argument("--recursive", action="store_true")
    ap.add_argument("--ext")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--timeout", type=float)
    ap.add_argument("--summary")
    args = ap.parse_args(argv)
    args.extra = extra
    if args.max_res and (args.max_height or args.max_width):
        ap.error("use --max-res or --max-height/--max-width, not both")
    if bool(args.output) == bool(args.out_dir):
        ap.error("give exactly one of -o FILE or --out-dir DIR")
    if args.preset_file and not args.preset:
        ap.error("--preset-file imports presets; also pass --preset NAME to use one "
                 "(hb-preset.py FILE lists the names)")

    try:
        cli = find_cli()
        for f in args.preset_file:
            if not os.path.isfile(f):
                raise HBError(f"preset file not found: {f}")
        if args.format:
            fmt = FORMATS[args.format]
        elif args.output and os.path.splitext(args.output)[1].lower().lstrip(".") in FORMATS:
            fmt = FORMATS[os.path.splitext(args.output)[1].lower().lstrip(".")]
        elif args.preset:
            fmt = resolve_preset(cli, args.preset, args.preset_file).get("FileFormat", "av_mp4")
        else:
            fmt = "av_mp4"
        if fmt not in EXT_FOR_FORMAT:
            fmt = "av_mp4"
        jobs = plan_jobs(args, cli, fmt)
    except (HBError, subprocess.TimeoutExpired) as e:
        print(f"error: {e}", file=sys.stderr)
        return 2

    signal.signal(signal.SIGINT, on_signal)
    signal.signal(signal.SIGTERM, on_signal)
    deadline = time.time() + args.timeout if args.timeout else None
    # Logs live outside the output folder and survive only for failed jobs.
    logdir = tempfile.mkdtemp(prefix="hb-logs-")
    for i, job in enumerate(jobs, 1):
        label = f"[{i}/{len(jobs)}] {os.path.basename(job['output'])}"
        if STOP["signal"]:
            job["status"] = "pending"
            continue
        print(label, file=sys.stderr, flush=True)
        job.update(run_job(cli, args, job, fmt, deadline, logdir, label))
        print(f"  {label}  {job['status']}"
              + (f": {job['reason']}" if job.get("reason") else ""),
              file=sys.stderr, flush=True)
    if not os.listdir(logdir):
        os.rmdir(logdir)
    for job in jobs:
        job.pop("root", None)
    summary = {"cli": cli, "format": fmt, "jobs": jobs}
    text = json.dumps(summary, indent=1, ensure_ascii=False)
    print(text)
    if args.summary:
        with open(args.summary, "w", encoding="utf-8") as fh:
            fh.write(text + "\n")
    if STOP["signal"] == "timeout":
        return 124
    if STOP["signal"]:
        return 130
    return 1 if any(j.get("status") == "failed" for j in jobs) else 0


if __name__ == "__main__":
    sys.exit(main())
