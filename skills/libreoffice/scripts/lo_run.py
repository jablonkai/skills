#!/usr/bin/env python3
"""Shared plumbing for the LibreOffice scripts: find soffice, keep a private profile,
run one lo_ops.py operation inside a headless soffice, and return its JSON result.

Each call is one short `soffice --headless` process on the skill's own profile
(LO_PROFILE, default $TMPDIR/libreoffice-skill/profile). lo_ops.py is copied into that
profile's Scripts/python folder and invoked as a Python macro; the request travels in a
private JSON file named by LO_REQ, the result comes back the same way. Nothing listens
on a socket or pipe. Calls are serialized by a lock on the profile, because a second
soffice on the same profile hands its command line to the running one.

Also a small CLI:
  python3 lo_run.py --version       soffice path, version, profile
  python3 lo_run.py --stop          kill soffice processes running on the skill profile
  python3 lo_run.py --script FILE [--arg JSON]   run a UNO snippet inside soffice
  python3 lo_run.py --ops OP JSON   run one raw operation (debugging)

Standard library only; runs on the macOS system python3 (3.9) and on Linux.
"""
import fcntl
import json
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
OPS = os.path.join(HERE, "lo_ops.py")
TIMEOUT = int(os.environ.get("LO_TIMEOUT", "300"))
PROFILE = os.path.abspath(os.path.expanduser(os.environ.get(
    "LO_PROFILE", os.path.join(tempfile.gettempdir(), "libreoffice-skill", "profile"))))

# Lines soffice prints on every start that carry no signal.
NOISE = ("Fontconfig warning", "Fontconfig error")


class LOError(Exception):
    pass


def find_soffice():
    env = os.environ.get("LO_SOFFICE")
    candidates = [env] if env else []
    candidates += [
        "/Applications/LibreOffice.app/Contents/MacOS/soffice",
        os.path.expanduser("~/Applications/LibreOffice.app/Contents/MacOS/soffice"),
        shutil.which("soffice"), shutil.which("libreoffice"),
        "/usr/lib/libreoffice/program/soffice", "/opt/libreoffice/program/soffice",
    ]
    for c in candidates:
        if c and os.path.isfile(c) and os.access(c, os.X_OK):
            return c
    raise LOError("LibreOffice not found — install it (brew install --cask libreoffice) "
                  "or set LO_SOFFICE to the soffice binary")


def file_url(path):
    from urllib.parse import quote
    return "file://" + quote(os.path.abspath(path))


def real(path):
    """Absolute path with the folder resolved (/tmp -> /private/tmp); the file itself
    may not exist yet."""
    path = os.path.abspath(os.path.expanduser(path))
    return os.path.join(os.path.realpath(os.path.dirname(path)), os.path.basename(path))


# Container each extension must have. LibreOffice imports anything it can't parse as
# plain text and "converts" it with exit code 0, so a corrupt .docx becomes a PDF of
# garbage; checking the container first turns that into a reported failure.
ZIP_EXTS = {"docx", "docm", "dotx", "dotm", "xlsx", "xlsm", "xltx", "xltm", "pptx",
            "pptm", "potx", "ppsx", "odt", "ott", "ods", "ots", "odp", "otp", "odg",
            "otg", "odf", "epub", "vsdx"}
OLE_EXTS = {"doc", "dot", "xls", "xlt", "ppt", "pot", "pps", "vsd", "pub"}
OLE_MAGIC = b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"


def sniff(path, password=False):
    """None when the file looks like what its extension says, else the reason.
    password: a password was given, so an encrypted OOXML (an OLE container) is fine."""
    import zipfile
    ext = os.path.splitext(path)[1].lower().lstrip(".")
    if not os.path.isfile(path):
        return "not found"
    if os.path.getsize(path) == 0:
        return "empty file"
    with open(path, "rb") as f:
        head = f.read(8)
    if head == OLE_MAGIC and ext in ZIP_EXTS | {"rtf", "txt", "csv", "html", "htm"}:
        # A password-protected OOXML file is an OLE container.
        if password and ext in ZIP_EXTS:
            return None
        return ("password-protected (pass --password) or a legacy OLE file named .%s"
                % ext)
    if ext in ZIP_EXTS:
        if not zipfile.is_zipfile(path):
            return "not a valid .%s (not a zip container — corrupt or mislabelled)" % ext
        try:
            with zipfile.ZipFile(path) as z:
                names = set(z.namelist())
        except zipfile.BadZipFile as e:
            return "corrupt .%s: %s" % (ext, e)
        if not ({"[Content_Types].xml", "mimetype", "META-INF/manifest.xml"} & names):
            return "zip without an office manifest — not a .%s document" % ext
    elif ext in OLE_EXTS and head != OLE_MAGIC:
        if ext in ("doc", "xls") and head[:5] in (b"{\\rtf", b"<html", b"<?xml", b"<!DOC"):
            return None  # legacy extension on RTF/HTML/XML — LibreOffice handles it
        return "not a valid .%s (no OLE header — corrupt or mislabelled)" % ext
    elif ext == "pdf" and not head.startswith(b"%PDF"):
        return "not a PDF"
    return None


def pdf_info(path):
    """{"pdfa": "2B" or None, "encrypted": bool} from the raw bytes (XMP is uncompressed
    in LibreOffice output)."""
    import re
    with open(path, "rb") as f:
        data = f.read()
    part = re.search(rb"pdfaid:part(?:>|=\")(\d)", data)
    conf = re.search(rb"pdfaid:conformance(?:>|=\")([A-Za-z])", data)
    return {"pdfa": (part.group(1) + (conf.group(1).upper() if conf else b"")).decode()
            if part else None, "encrypted": b"/Encrypt" in data}


def parse_typed(value):
    """'true'/'false', integers and floats become JSON types; anything else stays text."""
    low = value.lower()
    if low in ("true", "false"):
        return low == "true"
    try:
        return int(value)
    except ValueError:
        pass
    try:
        return float(value)
    except ValueError:
        return value


def pdf_options(pdfa=None, ua=False, opts=()):
    """FilterData for the PDF export filters: --pdfa 1|2|3|4, --pdf-ua, KEY=VALUE."""
    data = {}
    if pdfa:
        data["SelectPdfVersion"] = int(pdfa)
    if ua:
        data["PDFUACompliance"] = True
        data["UseTaggedPDF"] = True
    for kv in opts:
        if "=" not in kv:
            raise LOError("--pdf-opt wants KEY=VALUE, got %r" % kv)
        k, v = kv.split("=", 1)
        data[k.strip()] = parse_typed(v.strip())
    return data


def add_pdf_args(ap):
    g = ap.add_argument_group("PDF export")
    g.add_argument("--pdfa", choices=["1", "2", "3", "4"],
                   help="PDF/A-1b, 2b, 3b or PDF/A-4 (fonts embedded, no encryption)")
    g.add_argument("--pdf-ua", action="store_true", help="PDF/UA (tagged, accessible)")
    g.add_argument("--pdf-opt", action="append", default=[], metavar="KEY=VALUE",
                   help="any writer_pdf_Export FilterData key, e.g. PageRange=1-3, "
                        "ExportNotes=true, Quality=80, EncryptFile=true "
                        "(see references/filters.md)")


def profile_pids():
    """PIDs of soffice processes running on the skill profile (never the user's GUI)."""
    try:
        out = subprocess.run(["pgrep", "-f", "UserInstallation=" + file_url(PROFILE)],
                             capture_output=True, text=True).stdout
    except FileNotFoundError:
        return []
    return [int(p) for p in out.split() if int(p) != os.getpid()]


def stop():
    pids = profile_pids()
    for pid in pids:
        try:
            os.kill(pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    return pids


def deploy_ops():
    """Copy lo_ops.py into the profile's user Python script folder."""
    dst_dir = os.path.join(PROFILE, "user", "Scripts", "python")
    os.makedirs(dst_dir, exist_ok=True)
    dst = os.path.join(dst_dir, "lo_ops.py")
    with open(OPS, "rb") as f:
        src = f.read()
    if not os.path.exists(dst) or open(dst, "rb").read() != src:
        with open(dst, "wb") as f:
            f.write(src)


LOCALE = os.environ.get("LO_LOCALE", "en-US")
XCU_HEAD = ('<?xml version="1.0" encoding="UTF-8"?>\n<oor:items '
            'xmlns:oor="http://openoffice.org/2001/registry" '
            'xmlns:xs="http://www.w3.org/2001/XMLSchema" '
            'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">\n')


def pin_locale():
    """Pin the profile's UI language and locale setting (LO_LOCALE, default en-US).
    Otherwise they follow the system: under hu-HU, CSV export writes "1,5", shown
    values read "1370,5", errors "#ZÉRÓOSZTÓ!", and a new TOC is titled
    "Tartalomjegyzék"."""
    import re
    path = os.path.join(PROFILE, "user", "registrymodifications.xcu")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    text = open(path, encoding="utf-8").read() if os.path.exists(path) else XCU_HEAD + "</oor:items>\n"
    # UILocale is the user's UI language choice (ooLocale is derived from it at start,
    # so writing ooLocale alone is overwritten); ooSetupSystemLocale is the locale
    # setting that drives number formats.
    items = (("/org.openoffice.Office.Linguistic/General", "UILocale"),
             ("/org.openoffice.Setup/L10N", "ooSetupSystemLocale"))
    want = "".join(
        '<item oor:path="%s"><prop oor:name="%s" oor:op="fuse">'
        "<value>%s</value></prop></item>\n" % (path_, name, LOCALE) for path_, name in items)
    if all(w in text for w in want.splitlines()):
        return
    for path_, name in items:
        text = re.sub(r'<item oor:path="%s"><prop oor:name="%s".*?</item>\n?'
                      % (re.escape(path_), name), "", text)
    text = text.replace("</oor:items>", want + "</oor:items>")
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def run_ops(op, args=None, timeout=None):
    """Run one lo_ops operation; returns its result dict or raises LOError."""
    soffice = find_soffice()
    os.makedirs(PROFILE, exist_ok=True)
    lock = open(os.path.join(os.path.dirname(PROFILE), "profile.lock"), "w")
    fcntl.flock(lock, fcntl.LOCK_EX)
    work = tempfile.mkdtemp(prefix="lo-req-")
    try:
        if profile_pids():
            raise LOError("an soffice is already running on the skill profile %s — "
                          "a killed run left it; stop it with: bash lo.sh --stop" % PROFILE)
        deploy_ops()
        pin_locale()
        req = os.path.join(work, "request.json")
        res = os.path.join(work, "result.json")
        fd = os.open(req, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump({"op": op, "args": args or {}, "result": res}, f, ensure_ascii=False)
        env = dict(os.environ, LO_REQ=req, PYTHONDONTWRITEBYTECODE="1")
        cmd = [soffice, "-env:UserInstallation=" + file_url(PROFILE), "--headless",
               "--invisible", "--nologo", "--norestore", "--nodefault", "--nolockcheck",
               "vnd.sun.star.script:lo_ops.py$main?language=Python&location=user"]
        proc = subprocess.Popen(cmd, env=env, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, start_new_session=True)
        try:
            out, _ = proc.communicate(timeout=timeout or TIMEOUT)
        except subprocess.TimeoutExpired:
            os.killpg(proc.pid, signal.SIGKILL)
            proc.wait()
            raise LOError("soffice did not finish within %ss (LO_TIMEOUT) and was killed"
                          % (timeout or TIMEOUT))
        lines = [line for line in out.decode("utf-8", "replace").splitlines()
                 if line.strip() and not line.startswith(NOISE)]
        # A crash prints a 50-frame stack; the head and the frames naming the failing
        # office call are enough.
        if len(lines) > 12:
            lines = lines[:3] + [ln for ln in lines[3:] if "lo.dylib" in ln and "Sw" in ln
                                 or "Sc" in ln or "Sd" in ln][:6]
        log = "\n".join(lines)
        if not os.path.exists(res):
            raise LOError("soffice exited (%s) without a result%s"
                          % (proc.returncode, (":\n" + log) if log else ""))
        with open(res, encoding="utf-8") as f:
            result = json.load(f)
        if not result.get("ok"):
            raise LOError(result.get("error") or "operation failed")
        return result
    finally:
        # A macro that returned leaves soffice exiting; make sure it is gone.
        deadline = time.time() + 10
        while profile_pids() and time.time() < deadline:
            time.sleep(0.2)
        stop()
        shutil.rmtree(work, ignore_errors=True)
        lock.close()


def version():
    soffice = find_soffice()
    out = subprocess.run([soffice, "--version"], capture_output=True, text=True,
                         timeout=60).stdout
    line = next((ln for ln in out.splitlines() if ln.startswith(("LibreOffice", "Collabora"))),
                out.strip())
    return soffice, line


def main():
    if len(sys.argv) >= 2 and sys.argv[1] == "--version":
        soffice, line = version()
        print("soffice: %s\nversion: %s\nprofile: %s" % (soffice, line, PROFILE))
    elif len(sys.argv) >= 2 and sys.argv[1] == "--stop":
        pids = stop()
        print("killed %s" % (" ".join(map(str, pids)) if pids else "nothing"))
    elif len(sys.argv) >= 3 and sys.argv[1] == "--script":
        args = {"path": real(sys.argv[2])}
        if len(sys.argv) >= 5 and sys.argv[3] == "--arg":
            args["args"] = json.loads(sys.argv[4])
        if not os.path.isfile(args["path"]):
            raise LOError("not found: %s" % args["path"])
        print(json.dumps(run_ops("script", args)["result"], ensure_ascii=False, indent=1))
    elif len(sys.argv) >= 3 and sys.argv[1] == "--ops":
        args = json.loads(sys.argv[3]) if len(sys.argv) > 3 else {}
        print(json.dumps(run_ops(sys.argv[2], args), ensure_ascii=False, indent=1))
    else:
        print(__doc__.split("Also a small CLI:")[1].split("Standard library")[0].strip(),
              file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except LOError as e:
        print("error: %s" % e, file=sys.stderr)
        sys.exit(1)
