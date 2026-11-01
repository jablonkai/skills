"""Shared helpers for the wordcraft skill scripts (stdlib only, Python 3.9+).

`Session` drives `wordcraft-cli mcp` over stdio as a minimal JSON-RPC client: headless,
or bridged to a running WordCraft app with `connect="127.0.0.1:PORT"`. No MCP client
configuration is needed.
"""
import json
import os
import re
import shutil
import subprocess
import sys
import zipfile

PINNED_VERSION = "0.14.0"
PLACEHOLDER = re.compile(r"\{\{\s*([^{}]+?)\s*\}\}")


def cli():
    """Path of wordcraft-cli, or exit with a hint."""
    path = shutil.which("wordcraft-cli") or os.path.expanduser("~/.local/bin/wordcraft-cli")
    if not os.path.isfile(path):
        sys.exit("wordcraft-cli not found (expected on PATH or in ~/.local/bin)")
    return path


def run_cli(args, check=True, stdin=None):
    """Run wordcraft-cli; return CompletedProcess. Raise with stderr when check fails."""
    proc = subprocess.run([cli()] + args, capture_output=True, text=True, input=stdin)
    if check and proc.returncode != 0:
        raise RuntimeError("wordcraft-cli %s failed: %s" % (
            " ".join(args[:2]), (proc.stderr or proc.stdout).strip()))
    return proc


def inspect(path):
    """`wordcraft-cli inspect FILE` as a dict."""
    return json.loads(run_cli(["inspect", path]).stdout)


def info(path):
    """`wordcraft-cli info FILE` as a dict."""
    return json.loads(run_cli(["info", path]).stdout)


def run_script(script, author=None):
    """`wordcraft-cli run --script -` with a script dict; return stdout lines."""
    args = ["run", "--script", "-"]
    if author:
        args += ["--author", author]
    return run_cli(args, stdin=json.dumps(script)).stdout.splitlines()


def story_texts(doc):
    """[(where, text)] for every body paragraph, table cell and part (header, footer, comment…)."""
    out = []

    def walk(blocks, where):
        for b in blocks:
            if b.get("type") == "table":
                for r, row in enumerate(b.get("cells") or []):
                    for c, cell in enumerate(row):
                        out.append(("%s table %d r%d c%d" % (where, b.get("index", 0), r, c), cell))
            else:
                out.append(("%s block %d" % (where, b.get("index", 0)), b.get("text", "")))

    walk(doc.get("blocks", []), "body")
    for p in doc.get("parts", []):
        out.append(("%s part %d" % (p.get("kind"), p.get("id")), p.get("text", "")))
    return out


def placeholders(doc, skip_kinds=("comment",)):
    """{name: [where…]} of {{placeholders}} left anywhere in an inspected document."""
    found = {}
    for where, text in story_texts(doc):
        if where.split(" ")[0] in skip_kinds:
            continue
        for m in PLACEHOLDER.finditer(text):
            found.setdefault(m.group(1), []).append(where)
    return found


def _texts(xml):
    return "".join(re.findall(r"<w:(?:t|delText)(?: [^>]*)?>([^<]*)</w:(?:t|delText)>", xml))


def review_marks(path):
    """Tracked changes and comments with their authors, read from the .docx XML.

    `inspect` shows revisions (run prop `ins`/`del`) and comment parts but no authors;
    the authors live only in the package. Returns {"revisions": […], "comments": […]}.
    """
    out = {"revisions": [], "comments": []}
    with zipfile.ZipFile(path) as z:
        names = z.namelist()
        doc = z.read("word/document.xml").decode("utf8")
        for kind in ("ins", "del"):
            for m in re.finditer(r'<w:%s ([^>]*?)(/?)>' % kind, doc):
                attrs = dict(re.findall(r'w:(\w+)="([^"]*)"', m.group(1)))
                text = ""
                if not m.group(2):
                    end = doc.find("</w:%s>" % kind, m.end())
                    text = _texts(doc[m.end():end])
                out["revisions"].append({"type": kind, "author": attrs.get("author"),
                                         "date": attrs.get("date"), "text": text})
        anchors = {}
        for m in re.finditer(r'<w:commentRangeStart w:id="(\d+)"/>(.*?)<w:commentRangeEnd w:id="\1"/>', doc, re.S):
            anchors[m.group(1)] = _texts(m.group(2))
        if "word/comments.xml" in names:
            cx = z.read("word/comments.xml").decode("utf8")
            for m in re.finditer(r'<w:comment ([^>]*)>(.*?)</w:comment>', cx, re.S):
                attrs = dict(re.findall(r'w:(\w+)="([^"]*)"', m.group(1)))
                out["comments"].append({"id": int(attrs.get("id", -1)), "author": attrs.get("author"),
                                        "text": _texts(m.group(2)), "anchor": anchors.get(attrs.get("id"))})
    # a paragraph-mark revision is empty; keep only the ones that carry text or say so
    out["revisions"] = [r for r in out["revisions"] if r["text"]] or out["revisions"]
    return out


def pdf_pages(path):
    with open(path, "rb") as f:
        return len(re.findall(rb"/Type\s*/Page(?![s\w])", f.read()))


def refuse_existing(paths, overwrite):
    if overwrite:
        return
    existing = [p for p in paths if os.path.exists(p)]
    if existing:
        sys.exit("refusing to overwrite (pass --overwrite): " + ", ".join(existing))


def same_file(a, b):
    return os.path.exists(a) and os.path.exists(b) and os.path.samefile(a, b)


class ToolError(RuntimeError):
    pass


class Session:
    """A WordCraft MCP session: headless (file access confined to the roots) or live."""

    def __init__(self, read_root=None, write_root=None, connect=None, author=None):
        args = [cli(), "mcp"]
        if connect:
            args += ["--connect", connect]
        else:
            args += ["--automation-read-root", os.path.realpath(read_root or os.getcwd()),
                     "--automation-write-root", os.path.realpath(write_root or read_root or os.getcwd())]
            if author:
                args += ["--author", author]
        self._id = 0
        self.proc = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                     stderr=subprocess.DEVNULL, text=True, bufsize=1)
        self._rpc("initialize", {"protocolVersion": "2025-06-18", "capabilities": {},
                                 "clientInfo": {"name": "wordcraft-skill", "version": "1"}})
        self._send({"jsonrpc": "2.0", "method": "notifications/initialized"})
        if connect and author:
            self.cmd("file.setAuthor", {"name": author})

    def _send(self, msg):
        self.proc.stdin.write(json.dumps(msg) + "\n")
        self.proc.stdin.flush()

    def _rpc(self, method, params):
        self._id += 1
        self._send({"jsonrpc": "2.0", "id": self._id, "method": method, "params": params})
        while True:
            line = self.proc.stdout.readline()
            if not line:
                raise ToolError("wordcraft-cli mcp exited unexpectedly")
            msg = json.loads(line)
            if msg.get("id") == self._id:
                if "error" in msg:
                    raise ToolError(json.dumps(msg["error"]))
                return msg["result"]

    def tool(self, name, args=None):
        """Call an MCP tool; return its parsed JSON text (or the text); raise on isError."""
        res = self._rpc("tools/call", {"name": name, "arguments": args or {}})
        texts = [c.get("text", "") for c in res.get("content", []) if c.get("type") == "text"]
        images = [c for c in res.get("content", []) if c.get("type") == "image"]
        text = "\n".join(texts)
        if res.get("isError"):
            raise ToolError("%s: %s" % (name, text))
        if images and not texts:
            return {"images": images}
        try:
            return json.loads(text) if text else None
        except ValueError:
            return text

    def cmd(self, command_id, params=None):
        return self.tool("execute", {"command": command_id, "params": params or {}})

    def close(self):
        try:
            self.proc.stdin.close()
            self.proc.wait(timeout=10)
        except Exception:  # noqa: BLE001 - best effort shutdown
            self.proc.kill()


def absolutize(value, keys=("path", "file", "template")):
    """Make the values of path-like keys absolute (the session rejects relative paths)."""
    if isinstance(value, list):
        return [absolutize(v, keys) for v in value]
    if isinstance(value, dict):
        out = {}
        for k, v in value.items():
            if k in keys and isinstance(v, str) and not v.startswith("/"):
                v = os.path.abspath(os.path.expanduser(v))
            out[k] = absolutize(v, keys)
        return out
    return value
