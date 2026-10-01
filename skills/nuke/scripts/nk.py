#!/usr/bin/env python3
"""Headless Nuke (Non-commercial) helper: find, check, render, batch, template, verify.

  nk.py find                                  Nuke binary + version + licence mode
  nk.py check  SCRIPT.nk                      lint .nk text against Non-commercial limits
  nk.py render SCRIPT.nk [-F 1001-1048] [-X W1,W2] [--set Node.knob=value ...] [--py HOOK.py]
  nk.py batch  DIR [-r] [-F a-b]              render every .nk/.nknc, one Nuke at a time
  nk.py template NAME|FILE -o OUT.nk [--plate KEY=PATH ...] [--set KEY=VALUE ...]
  nk.py template --list                       bundled templates and their placeholders
  nk.py verify PATTERN [--frames a-b] [--size WxH]   frames on disk, size, pix_fmt

Exit codes: 0 ok, 1 render/verify failure, 2 usage or setup error, 3 licence error.
Add --json to check/render/batch/verify for machine-readable output.
"""
import argparse
import json
import os
import re
import signal
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import nk_lib as L  # noqa: E402

TEMPLATES = os.path.join(os.path.dirname(HERE), "assets", "templates")
PLACEHOLDER = re.compile(r"@@([A-Z][A-Z0-9_]*)(?::([^@]*))?@@")


def die(msg, code=2):
    sys.stderr.write("nk: %s\n" % msg)
    sys.exit(code)


def nuke_bin():
    exe = L.find_nuke()
    if not exe:
        die("Nuke not found. Install Nuke Non-commercial (foundry.com) or set NUKE_BIN.")
    return exe


def nc_flags(args):
    return [] if getattr(args, "licensed", False) else ["--nc"]


def parse_range(spec):
    m = re.match(r"^\s*(-?\d+)(?:\s*-\s*(-?\d+))?(?:x(\d+))?\s*$", spec or "")
    if not m:
        die("bad frame range %r (use 1001-1048, 1001 or 1-100x2)" % spec)
    a = int(m.group(1))
    b = int(m.group(2)) if m.group(2) else a
    return a, b, int(m.group(3) or 1)


def load_script(path):
    if not os.path.isfile(path):
        die("no such script: %s" % path)
    if path.endswith(".nknc"):
        return None  # encrypted: cannot be parsed as text
    with open(path, encoding="utf-8", errors="replace") as fh:
        text = fh.read()
    try:
        return L.parse_nk(text)
    except ValueError as e:
        die("%s: .nk parse error: %s" % (path, e))


# ---------------------------------------------------------------- check
def check_nodes(nodes, licensed=False):
    """Return (errors, warnings) for parsed .nk nodes."""
    errors, warnings = [], []
    root = L.root_info(nodes)
    if not licensed and root["width"] and (root["width"] > L.NC_MAX_W or root["height"] > L.NC_MAX_H):
        warnings.append("Root format %sx%s is over the Non-commercial 1920x1080 cap — Writes must "
                        "see ≤1920x1080 (add a Reformat before each Write)" % (root["width"], root["height"]))
    has_reformat = any(n["class"] in ("Reformat", "Crop") for n in nodes)
    for n in nodes:
        k, cls = n["knobs"], n["class"]
        if cls == "Read":
            f = k.get("file", "")
            if f and "[" not in f:
                if L.is_movie(f):
                    if not os.path.exists(f):
                        errors.append("%s (line %d): file not found: %s" % (n["name"], n["line"], f))
                else:
                    frames, _, _ = L.find_frames(f)
                    if not frames and not os.path.exists(f):
                        errors.append("%s (line %d): no frames on disk for %s" % (n["name"], n["line"], f))
                    elif frames and not licensed and not has_reformat:
                        p = L.ffprobe(L.frame_path(f, frames[0]) if L.SEQ_TOKEN.search(os.path.basename(f)) else f)
                        if p and (p.get("width", 0) > L.NC_MAX_W or p.get("height", 0) > L.NC_MAX_H):
                            warnings.append("%s: plate is %sx%s — over the Non-commercial cap; Reformat it to "
                                            "≤1920x1080 before any Write" % (n["name"], p["width"], p["height"]))
        elif cls == "Text":
            font = k.get("font", "")
            if not font:
                warnings.append("%s (line %d): no font set — the default /Library/Fonts/Arial.ttf is often "
                                "missing on macOS and the text renders blank" % (n["name"], n["line"]))
            elif "[" not in font and not os.path.exists(font):
                errors.append("%s (line %d): font not found: %s" % (n["name"], n["line"], font))
        elif cls == "Write":
            if not k.get("file"):
                errors.append("%s (line %d): Write has no file" % (n["name"], n["line"]))
            codec = k.get("mov64_codec", "").lower()
            if not licensed and any(c in codec for c in L.NC_DISABLED_CODECS):
                errors.append("%s (line %d): codec %s is disabled in Non-commercial Nuke — use ProRes "
                              "(mov64_codec appr/apch/ap4h) or an image sequence" % (n["name"], n["line"], codec))
    if not [w for w in L.writes(nodes) if not w["disabled"]]:
        errors.append("no enabled Write node")
    return errors, warnings


def trailing_comments(text):
    """Line numbers where a '#' comment follows code — Nuke's loader rejects those."""
    return [i for i, line in enumerate(text.splitlines(), 1)
            if re.match(r'^[^#"]*[}\w]\s+#', line) and not line.lstrip().startswith("#")]


def cmd_check(args):
    nodes = load_script(args.script)
    if nodes is None:
        die("%s is an encrypted .nknc — it cannot be linted as text" % args.script)
    errors, warnings = check_nodes(nodes, args.licensed)
    for ln in trailing_comments(open(args.script, encoding="utf-8", errors="replace").read()):
        errors.append("line %d: '#' comment after code — Nuke fails to load the script; "
                      "put comments on their own line" % ln)
    info = {"script": args.script, "nodes": len(nodes), "root": L.root_info(nodes),
            "writes": L.writes(nodes), "errors": errors, "warnings": warnings}
    if args.json:
        print(json.dumps(info, indent=2))
    else:
        r = info["root"]
        print("%s: %d nodes, frames %d-%d, format %s" % (args.script, len(nodes), r["first"], r["last"],
                                                         r["format"] or "(default)"))
        for w in info["writes"]:
            print("  Write %-20s %-5s %s%s" % (w["name"], w["file_type"] or "?", w["file"],
                                               "  [disabled]" if w["disabled"] else ""))
        for e in errors:
            print("ERROR   " + e)
        for w in warnings:
            print("WARNING " + w)
        print("OK" if not errors else "FAILED (%d error%s)" % (len(errors), "" if len(errors) == 1 else "s"))
    return 1 if errors else 0


# ---------------------------------------------------------------- render
def expected_frames(w, first, last, step):
    return list(range(first, last + 1, step))


def verify_output(path, frames):
    """Check a Write's output on disk. Returns dict with found/missing."""
    if not path or "[" in path:
        return {"checked": False}
    if L.is_movie(path):
        p = L.ffprobe(path, count_frames=True)
        n = int(p.get("nb_read_frames") or 0) if p else 0
        return {"checked": True, "file": path, "frames": n, "expected": len(frames),
                "missing": max(0, len(frames) - n), "size": p and "%sx%s" % (p.get("width"), p.get("height"))}
    if not L.SEQ_TOKEN.search(os.path.basename(path)):
        ok = os.path.exists(path)
        return {"checked": True, "file": path, "frames": int(ok), "expected": 1, "missing": int(not ok)}
    on_disk, _, _ = L.find_frames(path)
    have = set(on_disk)
    missing = [f for f in frames if f not in have]
    first = next((f for f in frames if f in have), None)
    p = L.ffprobe(L.frame_path(path, first)) if first is not None else None
    return {"checked": True, "file": path, "frames": len(frames) - len(missing), "expected": len(frames),
            "missing": len(missing), "missing_list": missing[:20],
            "size": p and "%sx%s" % (p.get("width"), p.get("height"))}


def run_nuke(args, script, write_jobs, sets, timeout, frange=None, hooks=()):
    """Run one Nuke -t process; return (events, exit_code, tail_of_log)."""
    job = {"script": os.path.abspath(script), "writes": write_jobs, "set": sets,
           "frames": list(frange) if frange else None, "py": [os.path.abspath(h) for h in hooks]}
    fd, job_path = tempfile.mkstemp(prefix="nkjob-", suffix=".json")
    with os.fdopen(fd, "w") as fh:
        json.dump(job, fh)
    cmd = [nuke_bin()] + nc_flags(args) + ["-t", os.path.join(HERE, "nk_driver.py"), job_path]
    events, log = [], []
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                            errors="replace", start_new_session=True)
    deadline = time.time() + timeout
    try:
        for line in proc.stdout:
            line = line.rstrip("\n")
            pos = line.find("NKJOB {")
            if pos >= 0:
                # Nuke's progress dots (".9") can share the line with our marker.
                ev = json.loads(line[pos + 6:])
                line = line[:pos]
                events.append(ev)
                if args.verbose and ev["kind"] == "write":
                    sys.stderr.write("  %s %s\n" % ("ok  " if ev["ok"] else "FAIL", ev["name"]))
            if line.strip() and line.strip() not in (".9", "."):
                log.append(line)
                if args.verbose:
                    sys.stderr.write("  | %s\n" % line)
            if time.time() > deadline:
                raise subprocess.TimeoutExpired(cmd, timeout)
        code = proc.wait(timeout=max(1, deadline - time.time()))
    except subprocess.TimeoutExpired:
        os.killpg(proc.pid, signal.SIGKILL)
        proc.wait()
        events.append({"kind": "timeout", "seconds": timeout})
        code = 124
    except KeyboardInterrupt:
        # Nuke runs in its own session, so Ctrl-C does not reach it; take it down with us.
        os.killpg(proc.pid, signal.SIGKILL)
        proc.wait()
        raise
    finally:
        os.unlink(job_path)
    return events, code, log


def render_one(args, script, frange=None, only=None, sets=(), hooks=()):
    """Render one script; return a result dict."""
    t0 = time.time()
    res = {"script": script, "ok": False, "writes": [], "error": None}
    nodes = load_script(script)
    if nodes is not None:
        errors, warnings = check_nodes(nodes, args.licensed)
        res["warnings"] = ["preflight: " + e for e in errors] + warnings
        root = L.root_info(nodes)
        targets = [w for w in L.writes(nodes) if not w["disabled"]]
    else:  # encrypted .nknc: the driver discovers Writes and ranges inside Nuke
        root, targets = None, None
    if only:
        known = {w["name"]: w for w in targets or []}
        targets = [known.get(n, {"name": n, "file": "", "use_limit": False}) for n in only]
    if targets is not None and not targets:
        res["error"] = "no enabled Write node"
        return res
    jobs = None if targets is None else []
    for w in targets or []:
        if frange:
            a, b, step = frange
        elif w.get("use_limit") and w.get("first") is not None:
            a, b, step = w["first"], w["last"], 1
        elif root:
            a, b, step = root["first"], root["last"], 1
        else:
            a = b = step = None  # .nknc with -X: the driver uses the Root range
        f = w.get("file", "")
        if f and "[" not in f:
            os.makedirs(os.path.dirname(os.path.abspath(f)), exist_ok=True)
        job = {"name": w["name"], "file": f}
        if a is not None:
            job.update(first=a, last=b, step=step)
        jobs.append(job)
    events, code, log = run_nuke(args, script, jobs, list(sets), args.timeout, frange, hooks)
    plan = next((e for e in events if e["kind"] == "plan"), None)
    if plan:
        jobs = plan["writes"]
        if not jobs:
            res["error"] = res["error"] or "no enabled Write node"
    by_name = {e["name"]: e for e in events if e["kind"] == "write"}
    load = next((e for e in events if e["kind"] == "load"), None)
    if code == 100 or any("No license" in l or "LICENSE" in l for l in log[:40]) and not load:
        res["error"] = "Nuke found no licence — run with Non-commercial mode (default) or check --licensed"
        res["licence_error"] = True
    elif any(e["kind"] == "timeout" for e in events):
        res["error"] = "timed out after %ss (Nuke killed)" % args.timeout
    elif load and not load["ok"]:
        res["error"] = "load failed: " + load["error"]
    elif any(e["kind"] == "py" and not e["ok"] for e in events):
        e = next(e for e in events if e["kind"] == "py" and not e["ok"])
        res["error"] = "--py %s failed: %s" % (e["file"], e["error"])
    elif any(e["kind"] == "set" and not e["ok"] for e in events):
        e = next(e for e in events if e["kind"] == "set" and not e["ok"])
        res["error"] = "--set %s failed: %s" % (e["target"], e["error"])
    elif not load:
        res["error"] = "Nuke exited %s before loading the script: %s" % (code, " / ".join(log[-5:]))
    for j in jobs or []:
        ev = by_name.get(j["name"])
        entry = {"name": j["name"], "frames": "%d-%d" % (j["first"], j["last"]),
                 "ok": bool(ev and ev["ok"]), "error": ev and ev.get("error"),
                 "seconds": ev and ev.get("seconds")}
        if entry["ok"]:
            v = verify_output(j["file"], expected_frames(j, j["first"], j["last"], j["step"]))
            entry["output"] = v
            if v.get("checked") and v.get("missing"):
                entry["ok"] = False
                entry["error"] = "%d of %d frames missing on disk" % (v["missing"], v["expected"])
        res["writes"].append(entry)
    if load:
        res["nuke"], res["nc"] = load.get("nuke"), load.get("nc")
    res["ok"] = res["error"] is None and all(w["ok"] for w in res["writes"])
    res["seconds"] = round(time.time() - t0, 1)
    return res


def print_result(res):
    status = "OK " if res["ok"] else "ERR"
    print("%s %s  (%ss)" % (status, res["script"], res.get("seconds", "?")))
    if res.get("error"):
        print("    error: %s" % res["error"])
    for w in res["writes"]:
        out = w.get("output") or {}
        detail = ""
        if out.get("checked"):
            detail = "%d/%d frames %s" % (out["frames"], out["expected"], out.get("size") or "")
        print("    %s %-22s %-11s %s%s" % ("ok  " if w["ok"] else "FAIL", w["name"], w["frames"], detail,
                                          ("  — " + w["error"]) if w.get("error") else ""))
    for warn in res.get("warnings", []):
        print("    warning: %s" % warn)


def parse_sets(items):
    sets = []
    for s in items or []:
        if "=" not in s or "." not in s.split("=", 1)[0]:
            die("--set expects Node.knob=value, got %r" % s)
        t, v = s.split("=", 1)
        sets.append({"target": t, "value": v})
    return sets


def cmd_render(args):
    frange = parse_range(args.frames) if args.frames else None
    only = [x.strip() for x in args.writes.split(",")] if args.writes else None
    for h in args.py or []:
        if not os.path.isfile(h):
            die("no such hook: %s" % h)
    res = render_one(args, args.script, frange, only, parse_sets(args.set), args.py or [])
    print(json.dumps(res, indent=2)) if args.json else print_result(res)
    return 3 if res.get("licence_error") else (0 if res["ok"] else 1)


def cmd_batch(args):
    if not os.path.isdir(args.dir):
        die("not a directory: %s" % args.dir)
    scripts = []
    for root, dirs, files in os.walk(args.dir):
        dirs[:] = sorted(d for d in dirs if not d.startswith(".")) if args.recursive else []
        scripts += [os.path.join(root, f) for f in sorted(files)
                    if f.endswith((".nk", ".nknc")) and not f.startswith(".") and not f.endswith("~")]
    if not scripts:
        die("no .nk/.nknc scripts in %s%s" % (args.dir, "" if args.recursive else " (try -r)"))
    frange = parse_range(args.frames) if args.frames else None
    results = []
    for i, s in enumerate(scripts, 1):
        if not args.json:
            sys.stderr.write("[%d/%d] %s\n" % (i, len(scripts), s))
        res = render_one(args, s, frange)
        results.append(res)
        if not args.json:
            print_result(res)
        if res.get("licence_error"):
            break
    bad = [r for r in results if not r["ok"]]
    if args.json:
        print(json.dumps({"scripts": len(results), "failed": len(bad), "results": results}, indent=2))
    else:
        print("\n%d script(s), %d ok, %d failed" % (len(results), len(results) - len(bad), len(bad)))
        for r in bad:
            names = [w["name"] for w in r["writes"] if not w["ok"]]
            print("  FAILED %s%s: %s" % (r["script"], (" [" + ", ".join(names) + "]") if names else "",
                                         r["error"] or "; ".join(w["error"] for w in r["writes"] if w.get("error"))))
    return 3 if any(r.get("licence_error") for r in results) else (1 if bad else 0)


# ---------------------------------------------------------------- template
def resolve_template(name):
    if os.path.isfile(name):
        return name
    p = os.path.join(TEMPLATES, name if name.endswith(".nk") else name + ".nk")
    if os.path.isfile(p):
        return p
    die("no template %r (see nk.py template --list)" % name)


def plate_vars(key, path):
    """Variables for a plate: KEY, KEY_FIRST, KEY_LAST, KEY_SLATE, KEY_W, KEY_H, KEY_FIT_W, KEY_FIT_H."""
    path = os.path.abspath(path)
    if L.is_movie(path):
        p = L.ffprobe(path, count_frames=True)
        if not p:
            die("cannot probe %s" % path)
        first, last, pattern = 1, int(p.get("nb_read_frames") or 1), path
    else:
        frames, _, pattern = L.find_frames(path)
        if not frames:
            if not os.path.exists(path):
                die("plate %s=%s: no frames found" % (key, path))
            frames, pattern = [1], path
        first, last = frames[0], frames[-1]
        if len(frames) != last - first + 1:
            sys.stderr.write("nk: warning: %s has gaps (%d frames in %d-%d)\n" % (path, len(frames), first, last))
        probe_path = L.frame_path(pattern, first) if pattern != path or "#" in pattern else path
        p = L.ffprobe(probe_path)
        if not p:
            die("cannot probe %s (is ffprobe installed?)" % probe_path)
    w, h = int(p["width"]), int(p["height"])
    fw, fh = L.fit_nc(w, h)
    if (fw, fh) != (w, h):
        sys.stderr.write("nk: note: %s is %dx%d; @@%s_FIT_W@@x@@%s_FIT_H@@ = %dx%d fits the "
                         "Non-commercial cap\n" % (key, w, h, key, key, fw, fh))
    return {key: pattern, key + "_FIRST": str(first), key + "_LAST": str(last), key + "_W": str(w),
            key + "_H": str(h), key + "_FIT_W": str(fw), key + "_FIT_H": str(fh),
            key + "_SLATE": str(first - 1), key + "_MID": str((first + last) // 2)}


def template_placeholders(text):
    seen = {}
    for m in PLACEHOLDER.finditer(text):
        seen.setdefault(m.group(1), m.group(2))
    return seen


def cmd_template(args):
    if args.list:
        for f in sorted(os.listdir(TEMPLATES)):
            if f.endswith(".nk"):
                text = open(os.path.join(TEMPLATES, f)).read()
                doc = [l[2:].strip() for l in text.splitlines() if l.startswith("# ") and "@@" not in l][:2]
                print("%s — %s" % (f[:-3], " ".join(doc)))
                for k, d in template_placeholders(text).items():
                    print("    @@%s@@%s" % (k, "" if d is None else "  (default: %s)" % d))
        return 0
    if not args.template or not args.out:
        die("usage: nk.py template NAME|FILE -o OUT.nk [--plate KEY=PATH] [--set KEY=VALUE]")
    text = open(resolve_template(args.template)).read()
    values = {}
    for item in args.plate or []:
        k, _, v = item.partition("=")
        values.update(plate_vars(k.strip().upper(), v))
    for item in args.set or []:
        k, sep, v = item.partition("=")
        if not sep:
            die("--set expects KEY=VALUE, got %r" % item)
        values[k.strip().upper()] = v
    missing = []

    def sub(m):
        k, default = m.group(1), m.group(2)
        if k in values:
            return values[k]
        if default is not None:
            return default
        missing.append(k)
        return m.group(0)

    out = PLACEHOLDER.sub(sub, text)
    if missing:
        die("unfilled placeholders: %s" % ", ".join(sorted(set(missing))))
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w") as fh:
        fh.write(out)
    print(args.out)
    errors, warnings = check_nodes(L.parse_nk(out), args.licensed)
    for e in errors:
        print("ERROR   " + e)
    for w in warnings:
        print("WARNING " + w)
    return 1 if errors else 0


# ---------------------------------------------------------------- verify
def cmd_verify(args):
    path = os.path.abspath(args.pattern)
    want = None
    if args.frames:
        a, b, step = parse_range(args.frames)
        want = list(range(a, b + 1, step))
    if L.is_movie(path) or not L.seq_regex(path):  # movie or single file
        v = verify_output(path, want or [1])
        if L.is_movie(path) and not want and v.get("frames"):
            v["expected"], v["missing"] = v["frames"], 0
        if not os.path.exists(path):
            v["error"] = "file not found"
    else:
        on_disk, _, pattern = L.find_frames(path)
        if not on_disk:
            v = {"file": pattern, "frames": 0, "expected": len(want or []), "error": "no frames found"}
        else:
            v = verify_output(pattern, want or list(range(on_disk[0], on_disk[-1] + 1)))
            v["range_on_disk"] = "%d-%d" % (on_disk[0], on_disk[-1])
            first = L.ffprobe(L.frame_path(pattern, on_disk[0]))
            last = L.ffprobe(L.frame_path(pattern, on_disk[-1]))
            if first:
                v["codec"], v["pix_fmt"] = first.get("codec_name"), first.get("pix_fmt")
            if first and last and (first["width"], first["height"]) != (last["width"], last["height"]):
                v["error"] = "size changes: first %sx%s, last %sx%s" % (
                    first["width"], first["height"], last["width"], last["height"])
    if args.size and v.get("size") != args.size and not v.get("error"):
        v["error"] = "expected %s, got %s" % (args.size, v.get("size"))
    v["ok"] = not v.get("error") and not v.get("missing")
    if args.json:
        print(json.dumps(v, indent=2))
        return 0 if v["ok"] else 1
    print("%s %s: %s/%s frames%s%s%s" % (
        "OK " if v["ok"] else "ERR", v.get("file", path), v.get("frames", 0), v.get("expected", 0),
        (" (on disk %s)" % v["range_on_disk"]) if v.get("range_on_disk") else "",
        (", %s" % v["size"]) if v.get("size") else "",
        "".join(" " + v[k] for k in ("codec", "pix_fmt") if v.get(k))))
    if v.get("missing_list"):
        print("    missing: %s%s" % (", ".join(map(str, v["missing_list"])),
                                    " …" if v["missing"] > len(v["missing_list"]) else ""))
    if v.get("error"):
        print("    " + v["error"])
    return 0 if v["ok"] else 1


# ---------------------------------------------------------------- find
def cmd_find(args):
    exe = nuke_bin()
    print(exe)
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as fh:
        fh.write("import nuke\nprint('NKVER', nuke.NUKE_VERSION_STRING, 'nc=%s' % bool(nuke.env.get('nc')))\n")
    try:
        r = subprocess.run([exe] + nc_flags(args) + ["-t", fh.name], capture_output=True, text=True,
                           timeout=180, errors="replace")
    finally:
        os.unlink(fh.name)
    ver = [l for l in r.stdout.splitlines() if l.startswith("NKVER")]
    if ver:
        print(ver[0][6:])
        return 0
    print("Nuke did not start (exit %s)%s" % (r.returncode, " — no licence; Non-commercial needs --nc "
                                               "(the default here)" if r.returncode == 100 else ""))
    print("\n".join(r.stdout.splitlines()[-8:]))
    return 3 if r.returncode == 100 else 2


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--licensed", action="store_true",
                    help="commercial licence: skip --nc and the Non-commercial checks")
    sub = ap.add_subparsers(dest="cmd")

    p = sub.add_parser("find")
    p.set_defaults(fn=cmd_find)

    p = sub.add_parser("check")
    p.add_argument("script")
    p.add_argument("--json", action="store_true")
    p.set_defaults(fn=cmd_check)

    for name, fn in (("render", cmd_render), ("batch", cmd_batch)):
        p = sub.add_parser(name)
        if name == "render":
            p.add_argument("script")
            p.add_argument("-X", "--writes", help="comma-separated Write names (default: all enabled)")
            p.add_argument("--set", action="append", metavar="NODE.KNOB=VALUE",
                           help="override a knob before rendering (TCL value syntax); repeatable")
            p.add_argument("--py", action="append", metavar="HOOK.py",
                           help="Python run inside Nuke after load, before --set (e.g. Roto shapes); repeatable")
        else:
            p.add_argument("dir")
            p.add_argument("-r", "--recursive", action="store_true")
        p.add_argument("-F", "--frames", help="frame range a-b[xstep] (default: Root range or Write limit)")
        p.add_argument("--timeout", type=int, default=1800, help="seconds per script (default 1800)")
        p.add_argument("-v", "--verbose", action="store_true", help="stream Nuke's log to stderr")
        p.add_argument("--json", action="store_true")
        p.set_defaults(fn=fn)

    p = sub.add_parser("template")
    p.add_argument("template", nargs="?")
    p.add_argument("-o", "--out")
    p.add_argument("--plate", action="append", metavar="KEY=PATH",
                   help="plate path (####, %%04d or one frame of the sequence); sets KEY, KEY_FIRST, "
                        "KEY_LAST, KEY_SLATE (first-1), KEY_W, KEY_H, KEY_FIT_W, KEY_FIT_H")
    p.add_argument("--set", action="append", metavar="KEY=VALUE")
    p.add_argument("--list", action="store_true")
    p.set_defaults(fn=cmd_template)

    p = sub.add_parser("verify")
    p.add_argument("pattern")
    p.add_argument("--frames")
    p.add_argument("--size", help="expected WxH")
    p.add_argument("--json", action="store_true")
    p.set_defaults(fn=cmd_verify)

    args = ap.parse_args()
    if not getattr(args, "fn", None):
        ap.print_help()
        return 2
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
