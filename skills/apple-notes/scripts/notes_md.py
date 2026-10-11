"""Markdown <-> Apple Notes HTML, for the subset Notes actually keeps (stdlib only).

What Notes keeps when HTML is written through `body` (verified on Notes 4.13):
  h1/h2/h3            -> bold system font, 24px / 18px / no size (read back as #, ##, ###)
  b i u strike a      -> kept (links come back wrapped in <u>)
  tt / pre            -> Courier lines, one <div> per line
  ul / ol / nested    -> kept, but two adjacent lists merge unless a block sits between
  table               -> kept, wrapped in <object> and counted as an attachment
  img data: URI       -> becomes an image attachment (and then disappears from `body`)
  checklists          -> NOT scriptable: written as "☐ item" / "☑ item" bullets
  blockquote, hr      -> plain text

  md_to_html(text, base_dir)  -> HTML for `body`
  html_to_md(html, images)    -> Markdown; `images(data_uri) -> relative path or None`

CLI:  python3 notes_md.py to-html FILE.md   |   python3 notes_md.py to-md FILE.html
"""
import base64
import html
import mimetypes
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

BOX_OPEN, BOX_DONE = "☐", "☑"   # ☐ ☑
SEP = "<div><br></div>"

# ---------------------------------------------------------------- Markdown -> HTML

def _inline(text, base_dir, images=None):
    """Inline Markdown -> HTML. Code spans are protected from the other rules."""
    parts = re.split(r"(`[^`]+`)", text)
    out = []
    for part in parts:
        if part.startswith("`") and part.endswith("`") and len(part) > 1:
            out.append("<tt>" + html.escape(part[1:-1], quote=False) + "</tt>")
            continue
        s = html.escape(part, quote=False)

        def img(m):
            alt, src = m.group(1), m.group(2).strip()
            path = (Path(base_dir) / src) if base_dir and not re.match(r"[a-z]+:", src) else None
            if path and path.is_file() and images is not None:
                images.append(path)     # attached separately (see nt-write.py)
                return ""
            if path and path.is_file():
                mime = mimetypes.guess_type(str(path))[0] or "image/png"
                data = base64.b64encode(path.read_bytes()).decode()
                return f'<img src="data:{mime};base64,{data}">'
            return f'<a href="{html.escape(src)}">{alt or src}</a>'

        s = re.sub(r"!\[([^\]]*)\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)", img, s)
        s = re.sub(r"\[([^\]]+)\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)",
                   lambda m: f'<a href="{m.group(2)}">{m.group(1)}</a>', s)
        s = re.sub(r"(?<![\w*])\*\*(?=\S)(.+?)(?<=\S)\*\*", r"<b>\1</b>", s)
        s = re.sub(r"(?<![\w_])__(?=\S)(.+?)(?<=\S)__", r"<b>\1</b>", s)
        s = re.sub(r"(?<![\w*])\*(?=\S)(.+?)(?<=\S)\*(?!\*)", r"<i>\1</i>", s)
        s = re.sub(r"(?<![\w_])_(?=\S)(.+?)(?<=\S)_(?![\w_])", r"<i>\1</i>", s)
        s = re.sub(r"~~(?=\S)(.+?)(?<=\S)~~", r"<strike>\1</strike>", s)
        out.append(s)
    return "".join(out)


_LIST_RE = re.compile(r"^(\s*)([-*+]|\d+[.)])\s+(.*)$")
_TASK_RE = re.compile(r"^\[([ xX])\]\s+(.*)$")
_TABLE_SEP = re.compile(r"^\s*\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)*\|?\s*$")


def _cells(line):
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|") and not line.endswith("\\|"):
        line = line[:-1]
    return [c.strip().replace("\\|", "|") for c in re.split(r"(?<!\\)\|", line)]


def _render_list(items, base_dir, images=None):
    """items: [(indent, ordered, text)] -> nested <ul>/<ol> HTML."""
    out, stack = [], []          # stack of (indent, tag)
    for indent, ordered, text in items:
        tag = "ol" if ordered else "ul"
        while stack and indent < stack[-1][0]:
            out.append(f"</li></{stack.pop()[1]}>")
        if not stack or indent > stack[-1][0]:
            out.append(f"<{tag}>")
            stack.append((indent, tag))
        else:
            out.append("</li>")
        m = _TASK_RE.match(text)
        if m:
            text = (BOX_DONE if m.group(1) in "xX" else BOX_OPEN) + " " + m.group(2)
        out.append("<li>" + _inline(text, base_dir, images))
    while stack:
        out.append(f"</li></{stack.pop()[1]}>")
    return "".join(out)


def md_to_html(text, base_dir=None, title=None, images=None):
    """Markdown -> Notes HTML. Local images are inlined as data URIs, or, when `images`
    is a list, left out of the HTML and appended to it (to be added as attachments)."""
    lines = text.replace("\r\n", "\n").split("\n")
    # YAML front matter (e.g. from nt-export.py) is metadata, not note text
    if lines and lines[0].strip() == "---":
        for j in range(1, len(lines)):
            if lines[j].strip() == "---":
                lines = lines[j + 1:]
                break
    blocks = []                  # (kind, html)
    i = 0
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            i += 1
            continue
        if line.lstrip().startswith(("```", "~~~")):
            fence = line.lstrip()[:3]
            code = []
            i += 1
            while i < len(lines) and not lines[i].lstrip().startswith(fence):
                code.append(lines[i])
                i += 1
            i += 1
            blocks.append(("code", "".join(
                f"<div><tt>{html.escape(c, quote=False) or '&nbsp;'}</tt></div>" for c in code)))
            continue
        m = re.match(r"^(#{1,6})\s+(.*?)\s*#*\s*$", line)
        if m:
            level = len(m.group(1))
            inner = _inline(m.group(2), base_dir, images)
            blocks.append(("heading", f"<div><h{level}>{inner}</h{level}></div>" if level <= 3
                           else f"<div><b>{inner}</b></div>"))
            i += 1
            continue
        if "|" in line and i + 1 < len(lines) and _TABLE_SEP.match(lines[i + 1]):
            rows = [_cells(line)]
            i += 2
            while i < len(lines) and "|" in lines[i] and lines[i].strip():
                rows.append(_cells(lines[i]))
                i += 1
            width = len(rows[0])
            body = "".join("<tr>" + "".join(
                f"<td>{_inline(c, base_dir, images)}</td>" for c in (r + [""] * width)[:width]) + "</tr>"
                for r in rows)
            blocks.append(("table", f"<div><table><tbody>{body}</tbody></table></div>"))
            continue
        if _LIST_RE.match(line):
            items = []
            while i < len(lines):
                lm = _LIST_RE.match(lines[i])
                if lm:
                    items.append((len(lm.group(1).expandtabs(4)), lm.group(2)[0].isdigit(), lm.group(3)))
                elif lines[i].strip() and lines[i].startswith((" ", "\t")) and items:
                    ind, ordd, txt = items[-1]
                    items[-1] = (ind, ordd, txt + " " + lines[i].strip())
                else:
                    break
                i += 1
            blocks.append(("list", _render_list(items, base_dir, images)))
            continue
        if re.match(r"^\s*([-*_])\s*(\1\s*){2,}$", line):
            blocks.append(("hr", ""))
            i += 1
            continue
        para = []
        while i < len(lines) and lines[i].strip() and not _LIST_RE.match(lines[i]) \
                and not re.match(r"^#{1,6}\s", lines[i]) and not lines[i].lstrip().startswith(("```", "~~~")):
            para.append(re.sub(r"^\s*>\s?", "", lines[i]).rstrip())
            i += 1
        html_lines = [_inline(p, base_dir, images) for p in para]
        if any(h.strip() for h in html_lines):
            blocks.append(("para", "".join(f"<div>{h}</div>" for h in html_lines if h.strip())))

    if title and not (blocks and blocks[0][0] == "heading"):
        blocks.insert(0, ("heading", f"<div><h1>{html.escape(title, quote=False)}</h1></div>"))

    out = []
    prev = None
    for kind, h in blocks:
        # A blank line between blocks, except straight after a heading. It also keeps two
        # consecutive lists from merging into one.
        if prev is not None and (prev != "heading" or kind == "list" and prev == "list"):
            out.append(SEP)
        if kind != "hr":
            out.append(h)
        prev = kind
    return "".join(out)


# ---------------------------------------------------------------- HTML -> Markdown

class _Node:
    __slots__ = ("tag", "attrs", "children", "parent")

    def __init__(self, tag, attrs=None, parent=None):
        self.tag, self.attrs, self.children, self.parent = tag, dict(attrs or {}), [], parent


_VOID = {"br", "img", "hr", "meta", "input"}


class _Tree(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = self.cur = _Node("root")

    def handle_starttag(self, tag, attrs):
        node = _Node(tag, attrs, self.cur)
        self.cur.children.append(node)
        if tag not in _VOID:
            self.cur = node

    def handle_endtag(self, tag):
        n = self.cur
        while n is not self.root and n.tag != tag:
            n = n.parent
        if n is not self.root:
            self.cur = n.parent

    def handle_data(self, data):
        self.cur.children.append(data)


def _attr_chain(node, stop):
    """Font sizes, faces and tags on the path from node up to stop."""
    tags, sizes, faces = set(), [], []
    while node is not None and node is not stop:
        if isinstance(node, _Node):
            tags.add(node.tag)
            st = node.attrs.get("style") or ""
            m = re.search(r"font-size:\s*(\d+)px", st)
            if m:
                sizes.append(int(m.group(1)))
            if node.attrs.get("face"):
                faces.append(node.attrs["face"])
        node = node.parent
    return tags, sizes, faces


def _text_leaves(node):
    for c in node.children:
        if isinstance(c, str):
            if c.strip("\n"):
                yield c, node
        elif c.tag not in ("table", "object", "ul", "ol"):
            yield from _text_leaves(c)


class _Renderer:
    def __init__(self, images):
        self.images = images or (lambda uri: None)

    def inline(self, node):
        out = []
        for c in node.children:
            if isinstance(c, str):
                out.append(c.replace("\n", ""))
                continue
            t = c.tag
            if t == "br":
                out.append("\n")
            elif t == "img":
                src = c.attrs.get("src", "")
                path = self.images(src) if src.startswith("data:") else src
                if path:
                    out.append(f"![]({path})")
            elif t in ("ul", "ol", "table", "object"):
                continue
            else:
                inner = self.inline(c)
                if not inner.strip():
                    out.append(inner)
                    continue
                lead = inner[:len(inner) - len(inner.lstrip())]
                trail = inner[len(inner.rstrip()):]
                core = inner.strip()
                if t in ("b", "strong") and not core.startswith("**"):
                    core = f"**{core}**"
                elif t in ("i", "em"):
                    core = f"*{core}*"
                elif t in ("strike", "s", "del"):
                    core = f"~~{core}~~"
                elif t == "a" and c.attrs.get("href"):
                    core = f"[{core}]({c.attrs['href']})"
                elif t == "tt" or (t == "font" and (c.attrs.get("face") or "").lower().startswith("courier")):
                    if not core.startswith("`"):
                        core = f"`{core}`"
                out.append(lead + core + trail)
        return "".join(out)

    def line_kind(self, div):
        """Classify a top-level <div> line: heading level, code, or text."""
        leaves = [(t, p) for t, p in _text_leaves(div) if t.strip()]
        if not leaves:
            return "blank", 0
        infos = [_attr_chain(p, div) for _, p in leaves]
        if all("tt" in tg or any(f.lower().startswith("courier") for f in fc) for tg, _, fc in infos):
            return "code", 0
        if all("b" in tg for tg, _, _ in infos) and \
                all(any("Bold" in f for f in fc) for _, _, fc in infos):
            size = max((max(sz) for _, sz, _ in infos if sz), default=0)
            return "heading", 1 if size >= 22 else 2 if size >= 17 else 3
        return "text", 0

    def plain(self, node):
        return re.sub(r"\s+", " ", "".join(t for t, _ in _text_leaves(node))).strip()

    def list_md(self, node, indent=""):
        out, n, sub_indent = [], 0, indent + "  "
        for li in node.children:
            if isinstance(li, _Node) and li.tag in ("ul", "ol"):
                # Notes writes a nested list as a sibling of the <li> it belongs to
                out.extend(self.list_md(li, sub_indent))
                continue
            if not isinstance(li, _Node) or li.tag != "li":
                continue
            n += 1
            text = self.inline(li).strip().replace("\n", " ")
            text = re.sub(r"^(?:`)?([☐☑])(?:`)?\s*", r"\1 ", text)
            bullet = f"{n}." if node.tag == "ol" else "-"
            if text.startswith(BOX_OPEN):
                text = "[ ] " + text[1:].lstrip()
            elif text.startswith(BOX_DONE):
                text = "[x] " + text[1:].lstrip()
            out.append(f"{indent}{bullet} {text}")
            sub_indent = indent + " " * (len(bullet) + 1)
            for sub in li.children:
                if isinstance(sub, _Node) and sub.tag in ("ul", "ol"):
                    out.extend(self.list_md(sub, indent + " " * (len(bullet) + 1)))
        return out

    def table_md(self, table):
        rows = []

        def walk(n):
            for c in n.children:
                if isinstance(c, _Node):
                    if c.tag == "tr":
                        rows.append([self.inline(td).strip().replace("\n", " ").replace("|", "\\|")
                                     for td in c.children if isinstance(td, _Node) and td.tag in ("td", "th")])
                    else:
                        walk(c)
        walk(table)
        if not rows:
            return []
        width = max(len(r) for r in rows)
        rows = [r + [""] * (width - len(r)) for r in rows]
        lines = ["| " + " | ".join(rows[0]) + " |", "|" + "---|" * width]
        lines += ["| " + " | ".join(r) + " |" for r in rows[1:]]
        return lines

    def render(self, root):
        blocks = []          # list of (kind, [lines])

        def add(kind, lines):
            if kind == "code" and blocks and blocks[-1][0] == "code":
                blocks[-1][1].extend(lines)
            else:
                blocks.append((kind, lines))

        def visit(node):
            for c in node.children:
                if isinstance(c, str):
                    if c.strip():
                        add("text", [c.strip()])
                    continue
                if c.tag in ("ul", "ol"):
                    add("list", self.list_md(c))
                elif c.tag == "table":
                    add("table", self.table_md(c))
                elif c.tag in ("div", "p", "h1", "h2", "h3", "h4", "h5", "h6", "object", "blockquote", "pre"):
                    if any(isinstance(g, _Node) and g.tag in ("table", "ul", "ol", "object") for g in c.children):
                        # a block wrapper (Notes puts tables in <div><object>): recurse, and keep
                        # any images that sit beside the table
                        visit(c)
                        continue
                    elems = [g for g in c.children if isinstance(g, _Node)]
                    htag = c.tag if re.fullmatch(r"h[1-6]", c.tag) else \
                        elems[0].tag if len(elems) == 1 and re.fullmatch(r"h[1-6]", elems[0].tag) else None
                    if htag:
                        add("heading", ["#" * int(htag[1]) + " " + self.plain(c)])
                        continue
                    kind, level = self.line_kind(c)
                    if kind == "blank":
                        imgs = self.inline(c).strip()
                        add("image" if imgs else "blank", [imgs] if imgs else [])
                    elif kind == "heading":
                        add("heading", ["#" * level + " " + self.plain(c)])
                    elif kind == "code":
                        add("code", ["".join(t for t, _ in _text_leaves(c)).rstrip("\n")])
                    else:
                        add("text", [self.inline(c).strip()])
                else:
                    s = self.inline(_wrap(c)).strip()
                    if s:
                        add("text", [s])

        visit(root)
        out = []
        prev = None
        for kind, lines in blocks:
            if kind == "blank":
                prev = "blank"
                continue
            if kind == "code":
                lines = ["```"] + lines + ["```"]
            if out and (prev == "blank" or kind != "text" or prev != "text"):
                out.append("")
            out.extend(lines)
            prev = kind
        return "\n".join(out).strip() + "\n"


def _wrap(node):
    w = _Node("span")
    w.children = [node]
    return w


def html_to_md(body, images=None):
    tree = _Tree()
    tree.feed(body or "")
    tree.close()
    return _Renderer(images).render(tree.root)


if __name__ == "__main__":
    if len(sys.argv) != 3 or sys.argv[1] not in ("to-html", "to-md"):
        sys.exit(__doc__.split("CLI:")[1].strip())
    src = Path(sys.argv[2])
    text = src.read_text(encoding="utf-8")
    sys.stdout.write(md_to_html(text, src.parent) if sys.argv[1] == "to-html" else html_to_md(text))
