#!/usr/bin/env python3
"""Transcode files or folders with Compressor settings, wait, and report.

    python3 cmp-encode.py SRC... --setting NAME|PATH [--setting ...] [layout] [options]

Sources are files or folders (video files inside; --recursive descends).
Every source is encoded with every --setting, all in one Compressor batch.

Layout (default: next to each source):
  --out-dir DIR        write into DIR (subfolders mirrored with --recursive)
  --suffix TEXT        appended to the source name; repeat once per --setting,
                       in the same order. Default: _<setting name slug>
                       e.g. clip.mov + "Apple ProRes 422 Proxy" → clip_apple-prores-422-proxy.mov

Options:
  --batch-name NAME    shown in Compressor's Activity window (default cmp-<time>)
  --priority low|medium|high
  --force              re-encode even if the output exists (Compressor itself
                       overwrites silently, so the default is to skip)
  --timeout SEC        stop the batch after SEC seconds (exit 124)
  --poll SEC           status interval (default 2)
  --lost-after SEC     give up when the batch is not visible to -monitor for SEC
                       seconds (default 90; it was lost by a service reset)
  --no-wait            submit, print the batch id, and exit
  --summary FILE       write the JSON summary there (cmp-verify.py reads it)
  --json               print the JSON summary instead of one line per job
  --dry-run            print the jobs and the Compressor command, submit nothing

Exit: 0 all jobs Successful/skipped · 1 a job failed or was cancelled · 2 bad
arguments or submission rejected · 124 timeout · 130 interrupted. On timeout or
Ctrl-C the batch is killed in Compressor too (Compressor deletes the partial files).
"""

import argparse
import json
import os
import re
import signal
import sys
import time

from cmp_lib import (VIDEO_EXTS, CmpError, file_url, find_cli, is_active, kill,
                     media_facts, monitor_once, resolve_setting, submit)


def slug(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def collect(sources, recursive):
    """Yield (path, relative_dir, explicit) for every video file in the sources."""
    for src in sources:
        src = os.path.abspath(os.path.expanduser(src))
        if os.path.isfile(src):
            yield src, "", True
        elif os.path.isdir(src):
            for root, dirs, files in os.walk(src):
                dirs[:] = sorted(d for d in dirs if not d.startswith(".")) if recursive else []
                for f in sorted(files):
                    if not f.startswith(".") and os.path.splitext(f)[1].lower() in VIDEO_EXTS:
                        yield os.path.join(root, f), os.path.relpath(root, src), False
        else:
            raise CmpError("source not found: %s" % src)


def complete(out, setting, src):
    """True if an existing output looks finished (non-empty, about full length)."""
    if setting["image_sequence"]:
        return os.path.isdir(out) and len(os.listdir(out)) > 0
    if not os.path.isfile(out) or os.path.getsize(out) == 0:
        return False
    try:
        a, b = media_facts(out)["duration"], media_facts(src)["duration"]
    except CmpError:
        return False
    return bool(a and b and abs(a - b) <= 0.5)


def plan(a):
    settings = [resolve_setting(q) for q in a.setting]
    if a.suffix and len(a.suffix) != len(settings):
        raise CmpError("give one --suffix per --setting (%d vs %d)" % (len(a.suffix), len(settings)))
    suffixes = a.suffix or ["_" + slug(s["name"]) for s in settings]
    jobs, seen = [], {}
    own = [(suf.lower(), "." + (s["ext"] or "mov").lower()) for s, suf in zip(settings, suffixes)]
    for src, rel, explicit in collect(a.sources, a.recursive):
        stem, ext0 = os.path.splitext(os.path.basename(src))
        # A folder scan must not pick up this plan's own earlier outputs (clip_proxy.mov
        # next to clip.mov), or every re-run would encode the outputs again.
        if not explicit and any(stem.lower().endswith(suf) and ext0.lower() == e for suf, e in own):
            continue
        base = os.path.join(os.path.abspath(a.out_dir), rel) if a.out_dir else os.path.dirname(src)
        for s, suf in zip(settings, suffixes):
            ext = s["ext"] or "mov"
            loc = os.path.normpath(os.path.join(base, "%s%s.%s" % (stem, suf, ext)))
            # Image sequences: Compressor makes a folder named after the location's stem.
            out = os.path.splitext(loc)[0] if s["image_sequence"] else loc
            if os.path.abspath(out) == src:
                raise CmpError("output would overwrite its source: %s" % src)
            if out in seen:
                raise CmpError("%s and %s both map to %s — use --suffix or separate --out-dir"
                               % (seen[out], src, out))
            seen[out] = src
            jobs.append({"source": src, "setting": s["name"], "setting_path": s["path"],
                         "location": loc, "output": out, "image_sequence": s["image_sequence"],
                         "status": "pending", "_s": s})
    if not jobs:
        raise CmpError("no video files found in the sources (extensions: %s)"
                       % " ".join(sorted(VIDEO_EXTS)))
    return jobs


def write_summary(path, summary, as_json):
    text = json.dumps(summary, indent=2)
    if path:
        with open(path, "w") as fh:
            fh.write(text + "\n")
    if as_json:
        print(text)
        return
    for j in summary["jobs"]:
        print("%-22s %s  ←  %s  [%s]" % (j["status"], j["output"], os.path.basename(j["source"]),
                                        j["setting"]))
    print("batch %s: %s" % (summary.get("batch_id") or "-", summary.get("batch_status") or "-"))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("sources", nargs="+")
    ap.add_argument("--setting", action="append", required=True)
    ap.add_argument("--out-dir")
    ap.add_argument("--suffix", action="append")
    ap.add_argument("--recursive", action="store_true")
    ap.add_argument("--batch-name")
    ap.add_argument("--priority", choices=["low", "medium", "high"])
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--timeout", type=float)
    ap.add_argument("--poll", type=float, default=2.0)
    ap.add_argument("--lost-after", type=int, default=90)
    ap.add_argument("--no-wait", action="store_true")
    ap.add_argument("--summary")
    ap.add_argument("--json", action="store_true", help="print the JSON summary to stdout")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    try:
        jobs = plan(a)
    except CmpError as e:
        print("error: %s" % e, file=sys.stderr)
        return 2

    todo = []
    for j in jobs:
        if not a.force and complete(j["output"], j["_s"], j["source"]):
            j["status"] = "skipped (exists)"
        else:
            todo.append(j)
    name = a.batch_name or time.strftime("cmp-%Y%m%d-%H%M%S")
    summary = {"batch_name": name, "batch_id": None, "jobs": jobs}

    def public():
        return dict(summary, jobs=[{k: v for k, v in j.items() if k != "_s"} for j in jobs])

    if a.dry_run:
        cmd = [find_cli(), "-batchname", name]
        for j in todo:
            cmd += ["-jobpath", file_url(j["source"]), "-settingpath", j["setting_path"],
                    "-locationpath", j["location"]]
        for j in jobs:
            print("%-18s %s\n%18s → %s  [%s]" % (j["status"] if j not in todo else "encode",
                  j["source"], "", j["output"], j["setting"]), file=sys.stderr)
        print(" ".join("'%s'" % c if " " in c else c for c in cmd + ["-outputformat", "json"]))
        return 0
    if not todo:
        write_summary(a.summary, public(), a.json)
        return 0

    for j in todo:
        os.makedirs(os.path.dirname(j["location"]), exist_ok=True)
        if a.force and os.path.isfile(j["output"]):
            os.remove(j["output"])
    try:
        batch_id, job_ids = submit([(j["source"], j["setting_path"], j["location"]) for j in todo],
                                   name, a.priority)
    except CmpError as e:
        print("error: %s" % e, file=sys.stderr)
        return 2
    summary["batch_id"] = batch_id
    for j, jid in zip(todo, job_ids):
        j["job_id"], j["status"] = jid, "submitted"
    print("submitted batch %s (%d jobs)" % (batch_id, len(todo)), file=sys.stderr)
    if a.no_wait:
        write_summary(a.summary, public(), a.json)
        return 0

    stop = {"why": None}

    def on_signal(signum, _frame):
        stop["why"] = "interrupted"

    signal.signal(signal.SIGINT, on_signal)
    signal.signal(signal.SIGTERM, on_signal)
    start, last, bs = time.time(), None, None
    last_seen = start
    while True:
        if a.timeout and time.time() - start > a.timeout:
            stop["why"] = "timeout"
        if stop["why"]:
            kill(batch_id)
            for j in todo:
                if is_active(j["status"]) or j["status"] == "submitted":
                    j["status"] = "Cancelled (%s)" % stop["why"]
            print("stopped batch %s (%s)" % (batch_id, stop["why"]), file=sys.stderr)
            write_summary(a.summary, public(), a.json)
            return 124 if stop["why"] == "timeout" else 130
        bs = monitor_once(batch_id)
        if not bs and time.time() - last_seen > a.lost_after:
            # The batch never showed up (or vanished): typically someone ran
            # -resetBackgroundProcessing or the service restarted. Don't wait out --timeout.
            kill(batch_id)
            for j in todo:
                if is_active(j["status"]) or j["status"] == "submitted":
                    j["status"] = "lost (not in -monitor for %ds)" % a.lost_after
            print("batch %s is not visible to -monitor; Compressor's background service was "
                  "probably reset by another client. Re-run the same command." % batch_id,
                  file=sys.stderr)
            break
        if bs:
            last_seen = time.time()
            by_id = {js.get("jobid"): js for js in bs["jobs"]}
            for j in todo:
                js = by_id.get(j.get("job_id"))
                if js:
                    j["status"] = js.get("status", "")
                    j["seconds"] = float(js.get("timeElapsedSeconds") or 0)
            line = "%s %s%%" % (bs.get("status"), bs.get("percentComplete"))
            if line != last:
                print("  " + line, file=sys.stderr)
                last = line
            if not any(is_active(j["status"]) or j["status"] == "submitted" for j in todo):
                break
            # -monitor does not always list every job (a failed batch shows only the
            # failed one), so stop on the batch status and settle the unlisted jobs.
            if not is_active(bs.get("status")):
                for j in todo:
                    if is_active(j["status"]) or j["status"] == "submitted":
                        done = os.path.exists(j["output"]) and bs.get("status") == "Successful"
                        j["status"] = "Successful" if done else "unknown (batch %s)" % bs.get("status")
                break
        time.sleep(a.poll)

    summary["batch_status"] = bs.get("status") if bs else None
    summary["elapsed_seconds"] = round(time.time() - start, 1)
    for j in todo:
        if j["status"] == "Successful" and not (os.path.isdir(j["output"]) if j["image_sequence"]
                                                 else os.path.isfile(j["output"])):
            j["status"] = "Successful but output missing"
    write_summary(a.summary, public(), a.json)
    return 0 if all(j["status"] == "Successful" for j in todo) else 1


if __name__ == "__main__":
    sys.exit(main())
