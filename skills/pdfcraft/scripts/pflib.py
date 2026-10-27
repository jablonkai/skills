"""Shared helpers for the pdfcraft scripts: locate pdfcraft-cli, fix its OCR model
path, and run subcommands or tool scripts with JSON results."""

import json
import os
import shutil
import subprocess
import sys
import tempfile

APP_MODELS = "/Applications/PdfCraft.app/Contents/Resources/models"

# Tools that put a new document in the session; each takes the next doc id.
OPENERS = {"doc_open", "doc_create"}
OPEN_FLAG = {"doc_combine", "page_extract", "doc_open_revision"}


def die(msg, code=2):
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(code)


def cli():
    found = shutil.which("pdfcraft-cli")
    if found:
        return found
    home = os.path.expanduser("~/.local/bin/pdfcraft-cli")
    if os.path.exists(home):
        return home
    die("pdfcraft-cli not found (expected on PATH or at ~/.local/bin/pdfcraft-cli)")


def env():
    """The CLI looks for OCR models next to its symlink, not inside the app, so
    point it at the app bundle unless the caller already chose a folder."""
    e = dict(os.environ)
    if not e.get("PDFCRAFT_MODELS") and os.path.isdir(APP_MODELS):
        e["PDFCRAFT_MODELS"] = APP_MODELS
    return e


def run_cli(args, check=False):
    p = subprocess.run([cli(), *args], capture_output=True, text=True, env=env())
    if check and p.returncode != 0:
        die(f"pdfcraft-cli {args[0]} failed: {(p.stderr or p.stdout).strip()}")
    return p


def run_json(args):
    p = run_cli(args)
    try:
        return json.loads(p.stdout), p
    except json.JSONDecodeError:
        die(f"pdfcraft-cli {args[0]} gave no JSON: {(p.stderr or p.stdout).strip()[:300]}")


def opens_doc(step):
    tool = step.get("tool")
    return tool in OPENERS or (tool in OPEN_FLAG and step.get("args", {}).get("open"))


def run_steps(steps, root=None):
    """Run steps through `run --script --report`; returns the report dict."""
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        json.dump(steps, f)
        path = f.name
    try:
        args = ["run", "--script", path, "--report"]
        if root:
            args += ["--root", root]
        p = run_cli(args)
    finally:
        os.unlink(path)
    try:
        return json.loads(p.stdout)
    except json.JSONDecodeError:
        die(f"tool script gave no report: {(p.stderr or p.stdout).strip()[:300]}")


def first(result):
    """Tool results arrive as a one-element list; unwrap it."""
    if isinstance(result, list) and len(result) == 1:
        return result[0]
    return result


def step_failures(report):
    return [s for s in report.get("steps", []) if s.get("status") != "ok"]


def doc_info(path, password=None):
    """doc_info for a file (it has per-page rotation, which `info` lacks)."""
    args = {"path": os.path.abspath(path)}
    if password:
        args["password"] = password
    rep = run_steps([{"tool": "doc_open", "args": args},
                     {"tool": "doc_info", "args": {"doc": 1}}])
    bad = step_failures(rep)
    if bad:
        die(f"{path}: {bad[0].get('error', 'doc_info failed')}")
    return first(rep["steps"][1]["result"])


def page_texts(path, count=None):
    """Text of every page; `text` separates pages with form feeds. Pass the page
    count to keep a trailing blank page from being mistaken for the separator."""
    p = run_cli(["text", path], check=True)
    pages = p.stdout.split("\f")
    if count is None:
        if len(pages) > 1 and not pages[-1].strip():
            pages = pages[:-1]
    else:
        pages = (pages + [""] * count)[:count]
    return pages


def audit(path):
    data, p = run_json(["audit", path])
    return data, p.returncode
