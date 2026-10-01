#!/usr/bin/env python3
"""Headless Scribus helper: run layout jobs, export .sla to PDF/X, inspect and verify.

  scribus.py find                                   app path, version, bundled Python
  scribus.py run JOB.py [-- ARG ...] [--timeout S]  run a job inside headless Scribus
  scribus.py export DOC.sla -o OUT.pdf [--preset x4|x1a|x3|print|screen]
                    [--bleed MM] [--marks] [--force] [--allow-problems]
  scribus.py inspect DOC.sla                        pages, frames, styles, fonts, images
  scribus.py verify OUT.pdf [--pages N] [--trim WxH] [--bleed MM] [--pdfx4]
                    [--min-ppi N] [--text FILE]     pdfinfo/pdffonts/pdfimages checks
  scribus.py render OUT.pdf -o DIR [--dpi 100]      PNG per page for a visual check

Exit codes: 0 ok, 1 job/check failed, 2 usage error, 3 setup error or timeout.
Runs with the system python3 (stdlib only); verify/render need poppler.
"""
import argparse
import json
import os
import plistlib
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
APP_CANDIDATES = ["/Applications/Scribus.app", os.path.expanduser("~/Applications/Scribus.app")]
PT_PER_MM = 72.0 / 25.4
NOISE = re.compile(r"^(Path = |\"scpaths:|QPixmap::|Fontconfig|qt\.|$)")

WRAPPER = r'''
import json, os, runpy, sys, traceback
sys.dont_write_bytecode = True  # keep the skill folder free of __pycache__
sys.path.insert(0, %(libdir)r)
payload = {"ok": False}
try:
    sys.argv = [%(job)r] + json.loads(os.environ["SCRIBUS_SKILL_ARGS"])
    ns = runpy.run_path(%(job)r, run_name="__main__")
    payload["ok"] = True
    payload["result"] = ns.get("RESULT")
except SystemExit as e:
    payload["ok"] = e.code in (0, None)
    if not payload["ok"]:
        payload["error"] = "SystemExit(%%r)" %% (e.code,)
except BaseException as e:
    payload["error"] = "%%s: %%s" %% (type(e).__name__, e)
    payload["traceback"] = traceback.format_exc()
try:
    import scribus_lib
    payload["doc"] = scribus_lib.doc_summary()
except BaseException as e:
    payload["doc_error"] = "%%s: %%s" %% (type(e).__name__, e)
with open(os.environ["SCRIBUS_SKILL_RESULT"], "w", encoding="utf-8") as fh:
    json.dump(payload, fh, indent=2, ensure_ascii=False, default=str)
'''


def die(msg, code=3):
    sys.stderr.write("scribus: %s\n" % msg)
    sys.exit(code)


def emit(obj, as_json):
    if as_json:
        print(json.dumps(obj, indent=2, ensure_ascii=False))


# ---------------------------------------------------------------- locating Scribus
def find_app():
    env = os.environ.get("SCRIBUS_APP")
    for app in ([env] if env else []) + APP_CANDIDATES:
        if app and os.path.isfile(os.path.join(app, "Contents/MacOS/Scribus")):
            return app
    return None


def app_info():
    app = find_app()
    if not app:
        die("Scribus.app not found. Install it (brew install --cask scribus) or set SCRIBUS_APP.")
    with open(os.path.join(app, "Contents/Info.plist"), "rb") as fh:
        plist = plistlib.load(fh)
    pyroot = os.path.join(app, "Contents/Frameworks/Python.framework/Versions")
    pyver = sorted(v for v in os.listdir(pyroot) if v[0].isdigit()) if os.path.isdir(pyroot) else []
    return {"app": app, "binary": os.path.join(app, "Contents/MacOS/Scribus"),
            "version": plist.get("CFBundleShortVersionString"),
            "python": pyver[-1] if pyver else None,
            "bundled_scripts": os.path.join(app, "Contents/share/scribus/scripts")}


# ---------------------------------------------------------------- running a job
def run_job(job, job_args, timeout, env_extra=None):
    """Run ``job`` inside headless Scribus; return (payload, stderr_lines, seconds)."""
    info = app_info()
    job = os.path.abspath(job)
    if not os.path.isfile(job):
        die("no such job script: %s" % job, 2)
    tmp = tempfile.mkdtemp(prefix="scribus-job-")
    wrapper = os.path.join(tmp, "wrapper.py")
    result = os.path.join(tmp, "result.json")
    with open(wrapper, "w", encoding="utf-8") as fh:
        fh.write(WRAPPER % {"libdir": HERE, "job": job})
    env = dict(os.environ, SCRIBUS_SKILL_ARGS=json.dumps(job_args),
               SCRIBUS_SKILL_RESULT=result, **(env_extra or {}))
    # Arguments go through the environment: Scribus parses its own argv, and a "--"
    # or "-x" after the script would be taken as a document or an option.
    cmd = [info["binary"], "-g", "-ns", "-py", wrapper]
    t0 = time.time()
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            env=env, cwd=os.getcwd(), start_new_session=True)
    try:
        out, _ = proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        os.killpg(proc.pid, signal.SIGKILL)
        proc.communicate()
        die("timed out after %ss (job killed). A modal dialog — missing font or image "
            "in an opened .sla — can block a headless run." % timeout, 3)
    secs = round(time.time() - t0, 1)
    lines = [ln for ln in out.decode("utf-8", "replace").splitlines() if not NOISE.match(ln)]
    payload = None
    if os.path.isfile(result):
        with open(result, encoding="utf-8") as fh:
            payload = json.load(fh)
    shutil.rmtree(tmp, ignore_errors=True)
    if payload is None:
        payload = {"ok": False, "error": "Scribus exited (code %s) without running the job"
                   % proc.returncode}
    return payload, lines, secs


def problems(payload):
    doc = payload.get("doc") or {}
    out = []
    for o in doc.get("overflow", []):
        out.append("text overflows on page %(page)s (frame %(frame)s)" % o)
    for m in doc.get("missing_images", []):
        out.append("image missing on page %(page)s: %(file)s" % m)
    result = payload.get("result")
    if isinstance(result, dict):
        for f in result.get("substituted_fonts") or []:
            out.append("font not installed, Scribus substituted it: %s" % f)
    return out


def report_job(payload, lines, secs, as_json, strict):
    issues = problems(payload)
    ok = payload.get("ok") and not (strict and issues)
    if as_json:
        emit(dict(payload, seconds=secs, issues=issues, log=lines[-30:] if not ok else []), True)
    else:
        doc = payload.get("doc") or {}
        status = "ok" if ok else ("PROBLEMS" if payload.get("ok") else "FAILED")
        print("%s in %ss" % (status, secs))
        if payload.get("error"):
            print("error: %s" % payload["error"])
            if payload.get("traceback"):
                print(payload["traceback"].rstrip())
        if doc:
            sizes = sorted({"x".join("%g" % v for v in p["size_mm"]) for p in doc["page_list"]})
            print("document: %d page(s), %s mm, masters %s, styles %s"
                  % (doc["pages"], ", ".join(sizes), doc.get("masters"),
                     doc.get("paragraph_styles")))
        if payload.get("result") is not None:
            print("result: %s" % json.dumps(payload["result"], ensure_ascii=False))
        for i in issues:
            print("WARNING: %s" % i)
        if not payload.get("ok") and lines:
            print("--- scribus log (filtered) ---")
            print("\n".join(lines[-30:]))
    return 0 if ok else 1


def cmd_run(a):
    payload, lines, secs = run_job(a.job, a.args, a.timeout)
    return report_job(payload, lines, secs, a.json, a.strict)


def cmd_export(a):
    out = os.path.abspath(a.output)
    if os.path.exists(out) and not a.force:
        die("%s exists (use --force to overwrite)" % out, 2)
    sla = os.path.abspath(a.sla)
    if not os.path.isfile(sla):
        die("no such document: %s" % sla, 2)
    job_args = [sla, out, a.preset, "" if a.bleed is None else str(a.bleed),
                "1" if a.marks else "0", str(a.mark_offset)]
    payload, lines, secs = run_job(os.path.join(HERE, "export_job.py"), job_args, a.timeout)
    code = report_job(payload, lines, secs, a.json, strict=not a.allow_problems)
    if code == 0 and not a.json:
        print("wrote %s — check it with: scribus.py verify %s%s"
              % (out, out, " --pdfx4" if a.preset == "x4" else ""))
    return code


# ---------------------------------------------------------------- inspect (.sla XML)
def cmd_inspect(a):
    try:
        root = ET.parse(a.sla).getroot()
    except (ET.ParseError, OSError) as e:
        die("cannot parse %s: %s" % (a.sla, e), 1)
    doc = root.find("DOCUMENT")
    if doc is None:
        die("%s is not a Scribus .sla (no DOCUMENT element)" % a.sla, 1)
    pt = lambda v: round(float(v or 0) / PT_PER_MM, 2)  # noqa: E731
    pages = []
    for pg in doc.findall("PAGE"):
        pages.append({"num": int(pg.get("NUM", 0)) + 1, "size_mm": [pt(pg.get("PAGEWIDTH")),
                      pt(pg.get("PAGEHEIGHT"))], "master": pg.get("MNAM")})
    kinds = {"2": "image", "4": "text", "6": "polygon", "5": "line", "12": "group", "16": "table"}
    objs = {}
    images, fonts = [], set()
    base = os.path.dirname(os.path.abspath(a.sla))
    for o in doc.iter("PAGEOBJECT"):
        k = kinds.get(o.get("PTYPE"), "other:" + str(o.get("PTYPE")))
        page = int(o.get("OwnPage", -1)) + 1
        objs.setdefault(page, {}).setdefault(k, 0)
        objs[page][k] += 1
        if o.get("PFILE"):
            path = o.get("PFILE")
            full = path if os.path.isabs(path) else os.path.join(base, path)
            images.append({"page": page, "file": path, "exists": os.path.isfile(full)})
    for el in doc.iter():
        if el.get("FONT"):
            fonts.add(el.get("FONT"))
    info = {
        "file": os.path.abspath(a.sla),
        "version": root.get("Version"),
        "unit": {"0": "pt", "1": "mm", "2": "in", "3": "p", "4": "cm"}.get(doc.get("UNITS"),
                                                                             doc.get("UNITS")),
        "pages": pages,
        "bleed_mm": [pt(doc.get(k)) for k in ("BleedTop", "BleedLeft", "BleedRight",
                                               "BleedBottom")],
        "masters": [m.get("NAM") for m in doc.findall("MASTERPAGE")],
        "objects_per_page": {str(k): v for k, v in sorted(objs.items())},
        "paragraph_styles": [s.get("NAME") for s in doc.findall("STYLE")],
        "char_styles": [s.get("CNAME") for s in doc.findall("CHARSTYLE")],
        "fonts": sorted(fonts),
        "images": images,
        "colors": [c.get("NAME") for c in doc.findall("COLOR")],
    }
    if a.json:
        emit(info, True)
    else:
        print("%s (Scribus %s, unit %s)" % (info["file"], info["version"], info["unit"]))
        for p in pages:
            print("  page %d: %sx%s mm, master %s, objects %s" % (
                p["num"], p["size_mm"][0], p["size_mm"][1], p["master"],
                info["objects_per_page"].get(str(p["num"]), {})))
        print("  bleed (t,l,r,b) mm: %s" % info["bleed_mm"])
        print("  masters: %s" % info["masters"])
        print("  paragraph styles: %s" % info["paragraph_styles"])
        print("  fonts: %s" % info["fonts"])
        for im in images:
            print("  image p%s: %s%s" % (im["page"], im["file"], "" if im["exists"] else "  MISSING"))
    return 1 if any(not i["exists"] for i in images) else 0


# ---------------------------------------------------------------- verify (poppler)
def tool(name):
    exe = shutil.which(name)
    if not exe:
        die("%s not found (brew install poppler)" % name)
    return exe


def sh(args):
    p = subprocess.run(args, capture_output=True, text=True, errors="replace")
    if p.returncode != 0:
        die("%s failed: %s" % (os.path.basename(args[0]), p.stderr.strip()[:300]), 1)
    return p.stdout


def parse_boxes(text):
    """pdfinfo -box output → list of per-page {box: (x0,y0,x1,y1)}."""
    pages = {}
    for m in re.finditer(r"^Page\s+(\d+)\s+(\w+Box|size):\s+(.+)$", text, re.M):
        num, kind, vals = int(m.group(1)), m.group(2), m.group(3)
        nums = [float(v) for v in re.findall(r"-?\d+(?:\.\d+)?", vals)]
        pages.setdefault(num, {})[kind] = nums
    return pages


def cmd_verify(a):
    pdf = a.pdf
    if not os.path.isfile(pdf):
        die("no such PDF: %s" % pdf, 2)
    info = sh([tool("pdfinfo"), pdf])
    n = int(re.search(r"^Pages:\s+(\d+)", info, re.M).group(1))
    boxes = parse_boxes(sh([tool("pdfinfo"), "-box", "-f", "1", "-l", str(n), pdf]))
    checks = []

    def check(name, ok, detail):
        checks.append({"check": name, "ok": bool(ok), "detail": detail})

    if a.pages is not None:
        check("page count", n == a.pages, "%d page(s), expected %d" % (n, a.pages))
    trims = []
    for p in range(1, n + 1):
        b = boxes.get(p, {})
        trim = b.get("TrimBox") or b.get("MediaBox")
        trims.append([round((trim[2] - trim[0]) / PT_PER_MM, 2),
                      round((trim[3] - trim[1]) / PT_PER_MM, 2)])
    if a.trim:
        w, h = (float(v) for v in a.trim.lower().split("x"))
        bad = [i + 1 for i, (tw, th) in enumerate(trims)
               if abs(tw - w) > a.tolerance or abs(th - h) > a.tolerance]
        check("trim size", not bad, "expected %gx%g mm; pages off: %s (first page %sx%s mm)"
              % (w, h, bad or "none", trims[0][0], trims[0][1]))
    if a.bleed is not None:
        bad = []
        for p in range(1, n + 1):
            b = boxes.get(p, {})
            if "BleedBox" not in b or "TrimBox" not in b:
                bad.append(p)
                continue
            t, bl = b["TrimBox"], b["BleedBox"]
            d = [(t[0] - bl[0]), (t[1] - bl[1]), (bl[2] - t[2]), (bl[3] - t[3])]
            if any(abs(v / PT_PER_MM - a.bleed) > a.tolerance for v in d):
                bad.append(p)
        check("bleed", not bad, "expected %g mm each side; pages off: %s" % (a.bleed, bad or "none"))
    if a.marks:
        b = boxes.get(1, {})
        mb, bb = b.get("MediaBox"), b.get("BleedBox")
        check("printer marks space", mb and bb and (mb[2] - mb[0]) > (bb[2] - bb[0]) + 1,
              "MediaBox wider than BleedBox on page 1" if mb and bb else "boxes missing")
    with open(pdf, "rb") as fh:
        raw = fh.read()
    pdfx = re.search(rb"/GTS_PDFXVersion\s*\(([^)]*)\)", raw)
    intent = b"/OutputIntents" in raw
    if a.pdfx4:
        check("PDF/X-4 marker", pdfx and pdfx.group(1) == b"PDF/X-4",
              "GTS_PDFXVersion=%s" % (pdfx.group(1).decode() if pdfx else None))
        check("output intent", intent, "OutputIntents present" if intent else "no OutputIntents")
        tb = all("TrimBox" in boxes.get(p, {}) for p in range(1, n + 1))
        check("TrimBox on every page", tb, "PDF/X requires a TrimBox per page")
    fonts = [ln.split() for ln in sh([tool("pdffonts"), pdf]).splitlines()[2:] if ln.strip()]
    unembedded = []
    for cols in fonts:
        # columns: name type... encoding emb sub uni object ID -> emb is 5th from end
        if len(cols) >= 7 and cols[-5] != "yes":
            unembedded.append(cols[0])
    check("fonts embedded", not unembedded, "%d font(s); not embedded: %s"
          % (len(fonts), unembedded or "none"))
    imgs = []
    for ln in sh([tool("pdfimages"), "-list", pdf]).splitlines()[2:]:
        c = ln.split()
        if len(c) >= 14 and c[2] == "image":
            imgs.append({"page": int(c[0]), "w": int(c[3]), "h": int(c[4]),
                         "ppi": min(float(c[12]), float(c[13]))})
    if a.min_images is not None:
        check("image count", len(imgs) >= a.min_images, "%d image(s), expected >= %d"
              % (len(imgs), a.min_images))
    if a.min_ppi is not None:
        low = [i for i in imgs if i["ppi"] < a.min_ppi]
        check("image resolution", not low, "%d image(s) under %d ppi: %s"
              % (len(low), a.min_ppi, low[:5]))
    if a.text:
        with open(a.text, encoding="utf-8") as fh:
            want = re.findall(r"\w+", fh.read().lower())
        got = set(re.findall(r"\w+", sh([tool("pdftotext"), "-enc", "UTF-8", pdf, "-"]).lower()))
        # Words hyphenated across lines may appear split; count only words of 4+ letters.
        want = [w for w in want if len(w) >= 4]
        missing = sorted({w for w in want if w not in got})
        cover = 1 - len([w for w in want if w not in got]) / max(len(want), 1)
        check("text coverage", cover >= a.min_coverage, "%.1f%% of words found; missing: %s"
              % (cover * 100, missing[:15]))
    summary = {"pdf": os.path.abspath(pdf), "pages": n, "trim_mm": trims[0] if trims else None,
               "pdfx": pdfx.group(1).decode() if pdfx else None, "images": len(imgs),
               "fonts": len(fonts), "checks": checks,
               "ok": all(c["ok"] for c in checks)}
    if a.json:
        emit(summary, True)
    else:
        print("%s: %d page(s), trim %s mm, PDF/X %s, %d font(s), %d image(s)" % (
            summary["pdf"], n, "x".join("%g" % v for v in summary["trim_mm"] or []),
            summary["pdfx"], len(fonts), len(imgs)))
        for c in checks:
            print("  [%s] %s — %s" % ("ok" if c["ok"] else "FAIL", c["check"], c["detail"]))
    return 0 if summary["ok"] else 1


def cmd_render(a):
    os.makedirs(a.output, exist_ok=True)
    prefix = os.path.join(a.output, os.path.splitext(os.path.basename(a.pdf))[0])
    sh([tool("pdftoppm"), "-png", "-r", str(a.dpi), a.pdf, prefix])
    files = sorted(f for f in os.listdir(a.output) if f.endswith(".png"))
    print("\n".join(os.path.join(a.output, f) for f in files))
    return 0 if files else 1


def cmd_find(a):
    info = app_info()
    if a.json:
        emit(info, True)
    else:
        for k, v in info.items():
            print("%-16s %s" % (k, v))
    return 0


def main():
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0],
                                formatter_class=argparse.RawDescriptionHelpFormatter,
                                epilog=__doc__.split("\n", 2)[2])
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("find")
    s.add_argument("--json", action="store_true")
    s.set_defaults(fn=cmd_find)

    s = sub.add_parser("run", help="run a job script inside headless Scribus")
    s.add_argument("job")
    s.add_argument("args", nargs="*", help="job arguments (put them after --)")
    s.add_argument("--timeout", type=int, default=180)
    s.add_argument("--strict", action="store_true", help="exit 1 on overflow or missing images")
    s.add_argument("--json", action="store_true")
    s.set_defaults(fn=cmd_run)

    s = sub.add_parser("export", help="export an existing .sla to PDF")
    s.add_argument("sla")
    s.add_argument("-o", "--output", required=True)
    s.add_argument("--preset", default="x4", choices=["x4", "x1a", "x3", "print", "screen"])
    s.add_argument("--bleed", type=float, help="mm on each side (default: document bleeds)")
    s.add_argument("--marks", action="store_true", help="crop/bleed/registration marks, colour bars")
    s.add_argument("--mark-offset", type=float, default=3.0)
    s.add_argument("--force", action="store_true")
    s.add_argument("--allow-problems", action="store_true",
                   help="exit 0 despite missing images, substituted fonts or overflow")
    s.add_argument("--timeout", type=int, default=180)
    s.add_argument("--json", action="store_true")
    s.set_defaults(fn=cmd_export)

    s = sub.add_parser("inspect", help="summarise a .sla without starting Scribus")
    s.add_argument("sla")
    s.add_argument("--json", action="store_true")
    s.set_defaults(fn=cmd_inspect)

    s = sub.add_parser("verify", help="check a PDF with poppler")
    s.add_argument("pdf")
    s.add_argument("--pages", type=int)
    s.add_argument("--trim", help="expected trim size WxH in mm, e.g. 148x210")
    s.add_argument("--bleed", type=float, help="expected bleed in mm on each side")
    s.add_argument("--marks", action="store_true", help="expect printer marks outside the bleed")
    s.add_argument("--pdfx4", action="store_true")
    s.add_argument("--min-images", type=int)
    s.add_argument("--min-ppi", type=int)
    s.add_argument("--text", help="UTF-8 source text whose words must appear in the PDF")
    s.add_argument("--min-coverage", type=float, default=0.98)
    s.add_argument("--tolerance", type=float, default=0.5, help="mm")
    s.add_argument("--json", action="store_true")
    s.set_defaults(fn=cmd_verify)

    s = sub.add_parser("render", help="rasterise pages to PNG for a visual check")
    s.add_argument("pdf")
    s.add_argument("-o", "--output", required=True)
    s.add_argument("--dpi", type=int, default=100)
    s.set_defaults(fn=cmd_render)

    # Job arguments after "--" often look like options; keep them away from argparse.
    argv = sys.argv[1:]
    extra = []
    if "--" in argv:
        i = argv.index("--")
        argv, extra = argv[:i], argv[i + 1:]
    a = p.parse_args(argv)
    if hasattr(a, "args"):
        a.args = list(a.args) + extra
    elif extra:
        p.error("unexpected arguments after --")
    sys.exit(a.fn(a))


if __name__ == "__main__":
    main()
