"""Shared helpers for the gridcraft scripts: locate gridcraft-cli, run it, parse its JSON lines."""
import json
import os
import shutil
import subprocess
import sys

XLSX_EXT = {".xlsx", ".xlsm"}


def cli_path():
    """Return the gridcraft-cli executable, or exit with a hint."""
    found = shutil.which("gridcraft-cli")
    if found:
        return found
    local = os.path.expanduser("~/.local/bin/gridcraft-cli")
    if os.access(local, os.X_OK):
        return local
    sys.exit("gridcraft-cli not found on PATH or in ~/.local/bin")


def cli(*args, check=False):
    """Run gridcraft-cli with args; return the CompletedProcess (text mode)."""
    proc = subprocess.run([cli_path(), *args], capture_output=True, text=True)
    if check and proc.returncode != 0:
        sys.exit(f"gridcraft-cli {' '.join(args[:1])} failed (exit {proc.returncode}): "
                 f"{(proc.stderr or proc.stdout).strip()}")
    return proc


def json_lines(text):
    """Parse every line of text that is a JSON object; skip `wrote …` and other plain lines."""
    out = []
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("{"):
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return out


def run_commands(path, steps, sheet=None):
    """Run read-only commands against a workbook in one process; return their results in order.

    steps is a list of (command_id, params). Nothing is saved (no --out).
    """
    args = ["run", "--in", path]
    for cmd, params in steps:
        if sheet and "sheet" not in params:
            params = {**params, "sheet": sheet}
        args += ["--cmd", f"{cmd}={json.dumps(params)}"]
    proc = cli(*args)
    if proc.returncode != 0:
        sys.exit(f"read failed: {(proc.stderr or proc.stdout).strip()}")
    return [line.get("result") for line in json_lines(proc.stdout)]


def info(path):
    """Return `gridcraft-cli info --json` as a dict."""
    proc = cli("info", path, "--json", check=True)
    return json.loads(proc.stdout)


def emit(report, ok):
    """Print a JSON report and exit 0 when ok, 1 otherwise."""
    report["ok"] = bool(ok)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    sys.exit(0 if ok else 1)
