#!/usr/bin/env python3
"""Locate and run FontForge headless.

    ff.py check                              # binary, version, Python, WOFF2 support
    ff.py run SCRIPT.py [ARGS...]            # fontforge -lang=py -script SCRIPT.py ARGS
    ff.py iconfont|subset|validate|inspect [ARGS...]   # bundled ff_<name>.py helpers
    ff.py specimen FONT -o OUT.png [--text "Hamburgefonts"] [--pixelsize 48]

Runs with any python3 (stdlib only); the scripts it launches run inside FontForge's
embedded Python, where `import fontforge` works. The FontForge banner and known
harmless warnings are filtered from stderr. Exit codes: the script's own code, 2 when
the run printed a Python traceback (FontForge itself often exits 0 then), 124 on
timeout, 127 when FontForge cannot be found.

Binary lookup order: $FONTFORGE, `fontforge` on PATH, the FontForge.app bundle
(/Applications or ~/Applications), then the Homebrew prefix.
"""
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
HELPERS = ("iconfont", "subset", "validate", "inspect")
APP_BIN = "FontForge.app/Contents/Resources/opt/local/bin"
NOISE = (
    "Copyright (c) 2000-",
    " License GPLv3+",
    " with many parts BSD",
    " Version: ",
    " Based on source",
    " Based on sources",
    "Core python package 'pkg_resources' not found",
    "Compressed ",  # WOFF2 encoder statistics
)
# Generating a one-glyph WOFF2 is the only reliable test that WOFF2 support is built in.
CHECK_PROBE = """
import fontforge, os, sys, tempfile
print("fontforge", fontforge.version())
print("python", sys.version.split()[0])
f = fontforge.font()
p = f.createChar(0x41, "A").glyphPen()
p.moveTo((0, 0)); p.lineTo((500, 0)); p.lineTo((250, 700)); p.closePath()
out = os.path.join(tempfile.mkdtemp(), "probe.woff2")
f.generate(out)
print("woff2", "ok" if os.path.getsize(out) > 0 else "FAILED")
"""


def find_fontforge():
    env = os.environ.get("FONTFORGE")
    candidates = [env] if env else []
    candidates.append(shutil.which("fontforge"))
    for base in ("/Applications", os.path.expanduser("~/Applications")):
        candidates.append(os.path.join(base, APP_BIN, "fontforge"))
    for prefix in ("/opt/homebrew", "/usr/local"):
        candidates.append(os.path.join(prefix, "bin", "fontforge"))
    for path in candidates:
        if path and os.path.isfile(path) and os.access(path, os.X_OK):
            return path
    return None


def run_ff(binary, argv, timeout):
    """Run FontForge, filter the banner, map tracebacks to exit 2."""
    try:
        proc = subprocess.run([binary, *argv], capture_output=True, text=True,
                              timeout=timeout, stdin=subprocess.DEVNULL)
    except subprocess.TimeoutExpired:
        print(f"ff.py: FontForge timed out after {timeout}s", file=sys.stderr)
        return 124
    sys.stdout.write(proc.stdout)
    err = [line for line in proc.stderr.splitlines()
           if line.strip() and not line.startswith(NOISE)]
    if err:
        print("\n".join(err), file=sys.stderr)
    if proc.returncode == 0 and any(line.startswith("Traceback") for line in err):
        return 2
    return proc.returncode


def main():
    args = sys.argv[1:]
    timeout = int(os.environ.get("FF_TIMEOUT", "300"))
    if not args or args[0] in ("-h", "--help"):
        print(__doc__.strip())
        return 0
    binary = find_fontforge()
    if not binary:
        print("ff.py: FontForge not found. Install the FontForge.app from "
              "https://fontforge.org or `brew install fontforge`, or set $FONTFORGE.",
              file=sys.stderr)
        return 127
    cmd, rest = args[0], args[1:]
    if cmd == "check":
        print("binary", binary)
        return run_ff(binary, ["-lang=py", "-c", CHECK_PROBE], 60)
    if cmd == "run":
        if not rest:
            print("ff.py run: missing SCRIPT.py", file=sys.stderr)
            return 64
        return run_ff(binary, ["-lang=py", "-script", *rest], timeout)
    if cmd in HELPERS:
        script = os.path.join(HERE, f"ff_{cmd}.py")
        return run_ff(binary, ["-lang=py", "-script", script, *rest], timeout)
    if cmd == "specimen":
        return specimen(binary, rest)
    print(f"ff.py: unknown command {cmd!r}; see ff.py --help", file=sys.stderr)
    return 64


def specimen(binary, rest):
    """Render a PNG specimen with FontForge's bundled fontimage script.

    The app ships fontimage with a shebang pointing at the CI build path, so it is
    run through the real binary instead of being executed directly.
    """
    import argparse
    ap = argparse.ArgumentParser(prog="ff.py specimen")
    ap.add_argument("font")
    ap.add_argument("-o", "--output", required=True)
    ap.add_argument("--text", action="append",
                    help="a line of text (repeatable); default: the font's own sample")
    ap.add_argument("--pixelsize", type=int, default=48)
    ap.add_argument("--width", type=int)
    opt = ap.parse_args(rest)
    script = os.path.join(os.path.dirname(binary), "fontimage")
    if not os.path.isfile(script):
        print(f"ff.py: fontimage not found next to {binary}", file=sys.stderr)
        return 127
    argv = ["-lang=ff", "-script", script, "-o", opt.output,
            "--pixelsize", str(opt.pixelsize)]
    if opt.width:
        argv += ["--width", str(opt.width)]
    for line in opt.text or []:
        argv += ["--text", line]
    argv.append(opt.font)
    code = run_ff(binary, argv, 120)
    if code == 0 and not os.path.isfile(opt.output):
        print("ff.py: fontimage produced no PNG", file=sys.stderr)
        return 1
    return code


if __name__ == "__main__":
    sys.exit(main())
