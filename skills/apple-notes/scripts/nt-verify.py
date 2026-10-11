#!/usr/bin/env python3
"""Verification oracle: compare a note with Markdown, or an export folder with Notes.

  nt-verify.py note --note REF --md FILE [--append]
      The note's body (read back through AppleScript) against the Markdown it was made
      from: headings, list items with checklist state, table rows, code and text lines.
      --append: only require the Markdown's content to be present.
  nt-verify.py export --dir OUT --folder "iCloud/Recipes" [--no-recursive]
      Every unlocked note in the folder has a .md (matched by the `id:` front matter),
      every text line of the note's plaintext and every table cell appears in it, every
      image link resolves to a non-empty file, and each saveable attachment was exported.

JSON report on stdout; exit 0 when everything matches, 4 on any mismatch.
"""
import argparse
import hashlib
import re
import sys
import tempfile
from collections import Counter
from pathlib import Path
from urllib.parse import unquote

import notes_lib as L
import notes_md as M


def _plain(s):
    s = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", s)
    s = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", s)
    s = re.sub(r"(\*\*|__|~~|`)", "", s)
    s = re.sub(r"(?<!\w)[*_](?=\S)|(?<=\S)[*_](?!\w)", "", s)
    s = s.replace("\\|", "|")
    return re.sub(r"\s+", " ", s).strip()


def items(md):
    """Structural items of Markdown: a Counter of (kind, text)."""
    out = Counter()
    in_code = False
    lines = md.replace("\r\n", "\n").split("\n")
    if lines and lines[0].strip() == "---":
        end = next((j for j in range(1, len(lines)) if lines[j].strip() == "---"), 0)
        lines = lines[end + 1:]
    for line in lines:
        st = line.strip()
        if st.startswith(("```", "~~~")):
            in_code = not in_code
            continue
        if in_code:
            if st:
                out[("code", st)] += 1
            continue
        if not st or re.fullmatch(r"\|?\s*:?-{2,}.*", st) or re.fullmatch(r"([-*_]\s*){3,}", st):
            continue
        m = re.match(r"^(#{1,6})\s+(.*?)\s*#*$", st)
        if m:
            out[("heading", _plain(m.group(2)))] += 1
            continue
        m = re.match(r"^([-*+]|\d+[.)])\s+(\[[ xX]\]\s+)?(.*)$", st)
        if m:
            state = "" if not m.group(2) else "[x]" if m.group(2)[1] in "xX" else "[ ]"
            text = _plain(m.group(3))
            if text:
                out[("item", (state + " " + text).strip())] += 1
            continue
        if st.startswith("|"):
            out[("row", " | ".join(_plain(c) for c in M._cells(st)))] += 1
            continue
        text = _plain(re.sub(r"^>\s?", "", st))
        if text:
            out[("text", text)] += 1
    return out


def compare_md(source_md, note_md, title=None):
    want, got = items(source_md), items(note_md)
    if title and not any(k == "heading" for k, _ in want):
        want[("heading", title)] += 1
    missing = sorted(f"{k}: {t}" for k, t in (want - got).elements())
    extra = sorted(f"{k}: {t}" for k, t in (got - want).elements())
    return {"ok": not missing and not extra, "items": sum(want.values()),
            "missing": missing, "extra": extra}


def verify_note(a):
    note = L.find_note(a.note)
    src = Path(a.md).read_text(encoding="utf-8")
    res = compare_md(src, M.html_to_md(note["body"], lambda uri: "image"))
    if a.append:
        res["extra"], res["ok"] = [], not res["missing"]
    res.update(note=note["name"], id=note["id"], attachments=note["attachmentCount"])
    return res


def _front_matter(text):
    fm = {}
    if text.startswith("---\n"):
        for line in text.split("\n---", 1)[0].splitlines()[1:]:
            k, _, v = line.partition(":")
            fm[k.strip()] = v.strip().strip('"')
    return fm


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def verify_export(a):
    out_dir = Path(a.dir).expanduser()
    fs = L.folders()
    root = L.resolve_folder(a.folder, fs)
    scope = [root] if a.no_recursive else L.subtree(root, fs)
    notes = L.jxa("list_notes", {"folderIds": [f["id"] for f in scope], "text": False})
    by_id = {}
    for md in out_dir.rglob("*.md"):
        fm = _front_matter(md.read_text(encoding="utf-8"))
        if fm.get("id"):
            by_id[fm["id"]] = md
    problems, checked = [], 0
    for n in notes:
        if n["locked"]:
            continue
        md = by_id.get(n["id"])
        if md is None:
            problems.append(f"{n['name']}: no exported .md")
            continue
        checked += 1
        text = md.read_text(encoding="utf-8")
        plain_md = {_plain(re.sub(r"^\s*(#{1,6}\s+|>\s?|([-*+]|\d+[.)])\s+(\[[ xX]\]\s+)?)", "", l))
                    for l in text.splitlines()}
        plain_md |= {_plain(c) for l in text.splitlines() if l.strip().startswith("|") for c in M._cells(l)}
        full = L.jxa("note_get", {"id": n["id"]})
        for line in full["plaintext"].splitlines():
            line = re.sub(r"\s+", " ", line.replace("￼", "")).strip()
            line = re.sub(r"^[☐☑]\s*", "", line)
            if line and line not in plain_md and _plain(line) not in plain_md:
                problems.append(f"{n['name']}: text line missing: {line[:80]!r}")
        for cell in re.findall(r"<td[^>]*>(.*?)</td>", full["body"], re.S):
            c = re.sub(r"<[^>]+>", "", cell).strip()
            if c and _plain(c) not in plain_md:
                problems.append(f"{n['name']}: table cell missing: {c[:60]!r}")
        linked = [md.parent / unquote(p.strip("<>")) for p in re.findall(r"!\[[^\]]*\]\(([^)]+)\)", text)]
        for p in linked:
            if not p.is_file() or p.stat().st_size == 0:
                problems.append(f"{n['name']}: image link broken: {p}")
        exported = {_sha(p) for p in linked if p.is_file()}
        exported |= {_sha(p) for ref in re.findall(r"\]\(([^)]+)\)", text)
                     for p in [md.parent / unquote(ref.strip("<>"))] if p.is_file() and "attachments" in p.parts}
        with tempfile.TemporaryDirectory() as tmp:
            for r in L.jxa("save_attachments", {"noteId": n["id"], "dir": tmp}):
                if r["path"] and _sha(r["path"]) not in exported:
                    problems.append(f"{n['name']}: attachment not exported: {r['name']}")
    return {"ok": not problems, "folder": root["path"], "notes": len(notes), "checked": checked,
            "locked": [n["name"] for n in notes if n["locked"]], "problems": problems}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("note")
    p.add_argument("--note", required=True)
    p.add_argument("--md", required=True)
    p.add_argument("--append", action="store_true")
    p = sub.add_parser("export")
    p.add_argument("--dir", required=True)
    p.add_argument("--folder", required=True)
    p.add_argument("--no-recursive", action="store_true")
    a = ap.parse_args()
    res = verify_note(a) if a.cmd == "note" else verify_export(a)
    L.dump(res)
    sys.exit(0 if res["ok"] else 4)


if __name__ == "__main__":
    main()
