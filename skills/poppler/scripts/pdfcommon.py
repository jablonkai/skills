"""Shared helpers for the poppler skill scripts (stdlib only, Python 3.9+).

Every tool call goes through `run()` with an argument list, never a shell. Passwords
are read from an environment variable or a file and reach qpdf through a private
@argfile, so they never appear on a command line (visible in `ps`) or in logs.
"""
import contextlib
import json
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile

INSTALL = {
    "qpdf": "brew install qpdf  (Debian/Ubuntu: apt install qpdf)",
    "poppler": "brew install poppler  (Debian/Ubuntu: apt install poppler-utils)",
}
POPPLER = {"pdfinfo", "pdffonts", "pdftotext", "pdfimages", "pdftoppm", "pdftocairo", "pdfseparate", "pdfunite"}

PAPER = {  # portrait sizes in points
    "A3": (841.89, 1190.55), "A4": (595.28, 841.89), "A5": (419.53, 595.28),
    "Letter": (612, 792), "Legal": (612, 1008), "Tabloid": (792, 1224),
}


def die(msg, code=2):
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(code)


def tool(name):
    path = shutil.which(name)
    if not path:
        die(f"{name} not found. Install: {INSTALL['poppler' if name in POPPLER else name]}", 3)
    return path


def run(cmd, ok=(0,), capture=True):
    """Run a tool; returns CompletedProcess. Exits with its stderr unless rc is in ok."""
    proc = subprocess.run([tool(cmd[0])] + list(cmd[1:]), capture_output=capture, text=True,
                          errors="replace")
    if proc.returncode not in ok:
        die(f"{cmd[0]} exited {proc.returncode}: {(proc.stderr or proc.stdout or '').strip()[:800]}")
    return proc


def emit(obj):
    print(json.dumps(obj, indent=2, ensure_ascii=False))


# --- passwords ---------------------------------------------------------------

def add_password_args(ap, prefix="", what="password of the input"):
    ap.add_argument(f"--{prefix}password-file", metavar="PATH", help=f"file whose first line is the {what}")
    ap.add_argument(f"--{prefix}password-env", metavar="VAR", help=f"environment variable holding the {what}")


def read_password(path=None, env=None, required=False, label="password"):
    if path:
        with open(path, encoding="utf-8") as fh:
            return fh.readline().rstrip("\r\n")
    if env:
        if env not in os.environ:
            die(f"environment variable {env} is not set")
        return os.environ[env]
    if required:
        die(f"{label} required: pass --{label.replace(' ', '-')}-file or --{label.replace(' ', '-')}-env")
    return None


@contextlib.contextmanager
def argfile(lines):
    """A 0600 qpdf @argfile holding secret arguments; deleted on exit."""
    fd, path = tempfile.mkstemp(prefix="qpdf-args-", suffix=".txt")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write("\n".join(lines) + "\n")
        yield "@" + path
    finally:
        os.unlink(path)


def qpdf(args, secret_lines=None, fatal=False):
    """Run qpdf; secret_lines (e.g. ['--password=x']) fill every '@SECRET' slot via one argfile.

    Exit 3 (warnings) counts as success. With fatal=True, exit 2 ends the script.
    """
    ok = (0, 3) if fatal else (0, 2, 3)
    if secret_lines and "@SECRET" in args:
        with argfile(secret_lines) as af:
            return run(["qpdf"] + [af if a == "@SECRET" else a for a in args], ok=ok)
    return run(["qpdf"] + [a for a in args if a != "@SECRET"], ok=ok)


@contextlib.contextmanager
def readable(path, password=None):
    """Yield a path poppler can open: the file itself, or a decrypted temp copy.

    poppler only takes passwords on argv (-upw), so encrypted inputs are decrypted
    by qpdf into a private temp file instead.
    """
    if not is_encrypted(path):
        yield path
        return
    tmpdir = tempfile.mkdtemp(prefix="pdf-dec-")
    os.chmod(tmpdir, 0o700)
    out = os.path.join(tmpdir, "decrypted.pdf")
    try:
        proc = qpdf(["--decrypt", "@SECRET", path, out], [f"--password={password or ''}"])
        if proc.returncode == 2 or not os.path.exists(out):
            die(f"cannot open {path}: wrong or missing password ({proc.stderr.strip()[:200]})", 4)
        yield out
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


# --- facts about a PDF -------------------------------------------------------

def is_encrypted(path):
    return run(["qpdf", "--is-encrypted", path], ok=(0, 2)).returncode == 0


def needs_password(path):
    """True when the file can't be opened without a user password."""
    return run(["qpdf", "--requires-password", path], ok=(0, 2, 3)).returncode == 0


def page_count(path, password=None):
    proc = qpdf(["--show-npages", "@SECRET", path], [f"--password={password}"] if password else None)
    if proc.returncode == 2:
        die(f"cannot read {path}: {proc.stderr.strip()[:200]}", 4)
    return int(proc.stdout.split()[0])


def check(path, password=None):
    """qpdf --check -> {'status': ok|warnings|errors, 'messages': [...]}."""
    proc = qpdf(["--check", "@SECRET", path], [f"--password={password}"] if password else None)
    status = {0: "ok", 3: "warnings"}.get(proc.returncode, "errors")
    msgs = [l for l in (proc.stdout + proc.stderr).splitlines() if re.match(r"(WARNING|ERROR|qpdf: )", l)]
    return {"status": status, "messages": msgs[:20]}


def page_sizes(path):
    """[(width_pt, height_pt, rotation)] per page, as poppler sees them (crop box)."""
    n = page_count(path)
    out = run(["pdfinfo", "-f", "1", "-l", str(n), path]).stdout
    sizes = {int(m[0]): [float(m[1]), float(m[2]), 0]
             for m in re.findall(r"^Page\s+(\d+) size:\s+([\d.]+) x ([\d.]+)", out, re.M)}
    for p, r in re.findall(r"^Page\s+(\d+) rot:\s+(\d+)", out, re.M):
        sizes[int(p)][2] = int(r)
    return [tuple(sizes[i]) for i in range(1, n + 1)]


def paper_name(w, h, rot=0):
    if rot in (90, 270):
        w, h = h, w
    for name, (pw, ph) in PAPER.items():
        if abs(w - pw) <= 2 and abs(h - ph) <= 2:
            return name
        if abs(w - ph) <= 2 and abs(h - pw) <= 2:
            return f"{name} landscape"
    return "custom"


def pixels(points, dpi):
    return math.ceil(points * dpi / 72 - 1e-6)


# --- page ranges (qpdf syntax) -------------------------------------------------

def parse_range(spec, n):
    """Expand a qpdf page range ('1-3,x2,r1,z', '2-z:even') into a list of 1-based pages."""
    spec = spec.strip()
    parity = None
    m = re.search(r":(odd|even)$", spec)
    if m:
        parity, spec = m.group(1), spec[: m.start()]

    def num(tok):
        tok = tok.strip()
        if tok == "z":
            return n
        if tok.startswith("r"):
            v = n - int(tok[1:]) + 1
        else:
            v = int(tok)
        if not 1 <= v <= n:
            die(f"page {tok} out of range 1-{n}")
        return v

    def group(g):
        if "-" in g:
            a, b = g.split("-", 1)
            a, b = num(a), num(b)
            return list(range(a, b + 1)) if a <= b else list(range(a, b - 1, -1))
        return [num(g)]

    pages, last = [], []
    for g in [g for g in spec.split(",") if g.strip()]:
        g = g.strip()
        if g.startswith("x"):
            drop = set(group(g[1:]))
            kept = [p for p in last if p not in drop]
            pages = pages[: len(pages) - len(last)] + kept
            last = kept
        else:
            last = group(g)
            pages += last
    if parity == "odd":
        pages = pages[0::2]
    elif parity == "even":
        pages = pages[1::2]
    if not pages:
        die(f"page range {spec!r} selects no pages")
    return pages


def compact(pages):
    """[1,2,3,5] -> '1-3,5' (qpdf accepts it; keeps argv short for big documents)."""
    out, i = [], 0
    while i < len(pages):
        j = i
        while j + 1 < len(pages) and pages[j + 1] == pages[j] + 1:
            j += 1
        out.append(str(pages[i]) if i == j else f"{pages[i]}-{pages[j]}")
        i = j + 1
    return ",".join(out)


def text_pages(path, pages, mode="layout"):
    """pdftotext per page -> list of strings (path must be readable without password)."""
    flag = {"layout": ["-layout"], "raw": ["-raw"], "plain": []}[mode]
    return [run(["pdftotext", *flag, "-f", str(p), "-l", str(p), "-enc", "UTF-8", path, "-"]).stdout
            for p in pages]


def norm(text):
    return re.sub(r"\s+", " ", text).strip()
