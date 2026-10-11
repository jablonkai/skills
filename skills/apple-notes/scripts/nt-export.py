#!/usr/bin/env python3
"""Export notes to Markdown files with their images and attachments. Read-only for Notes.

  nt-export.py --folder "iCloud/Recipes" --out ~/Export/Recipes      # subfolders included
  nt-export.py --folder "iCloud/Recipes" --out DIR --no-recursive
  nt-export.py --note x-coredata://... --out DIR                     # one note
  nt-export.py --ids-from search.json --out DIR                      # nt-search.py --json output

Layout: OUT/<subfolder path>/<Title>.md, attachments in OUT/<subfolder>/attachments/<Title>/.
Each .md starts with YAML front matter (title, id, folder, created, modified) so a re-export
or nt-verify.py can match files to notes. A note exported earlier into OUT (same id) is
skipped unless --force; notes with the same title get "Title-2.md", "Title-3.md".
Images that sit inline in the body (older notes) are placed where they appear; newer
attachments, which the body doesn't show, are linked under "## Attachments" at the end.
Locked notes are skipped and listed. JSON summary on stdout.
"""
import argparse
import hashlib
import json
import re
import sys
import tempfile
from pathlib import Path
from urllib.parse import quote, unquote

import notes_lib as L
import notes_md as M


def yaml_str(s):
    return json.dumps(s or "", ensure_ascii=False)


def export_note(note, md_path, rel_folder, folder_path, out, taken):
    att_dir_rel = Path(rel_folder) / "attachments" / md_path.stem
    att_dir = out / att_dir_rel
    saved, seen = [], {}

    def store(data, name_hint):
        digest = hashlib.sha256(data).hexdigest()
        if digest in seen:
            return seen[digest]
        ext = L.sniff_ext(data, Path(name_hint).suffix.lstrip(".") or "bin")
        stem = L.slug(Path(name_hint).stem if "." in name_hint else name_hint)
        att_dir.mkdir(parents=True, exist_ok=True)
        dest = L.unique_path(att_dir / f"{stem}.{ext}", taken)
        dest.write_bytes(data)
        rel = quote(dest.relative_to(md_path.parent).as_posix())   # spaces -> %20
        seen[digest] = rel
        saved.append(rel)
        return rel

    # Save the attachments first so inline body images that are the same file (same
    # bytes) take the attachment's real name instead of a generic one.
    files, skipped, nameless = [], [], 0
    with tempfile.TemporaryDirectory() as tmp:
        for r in L.jxa("save_attachments", {"noteId": note["id"], "dir": tmp}):
            if r["path"]:
                files.append((r["name"], Path(r["path"]).read_bytes()))
            elif r["name"] is None:
                nameless += 1
            else:
                skipped.append(r["name"])
    names = {hashlib.sha256(d).hexdigest(): n for n, d in files}
    counter = [0]

    def inline_image(uri):
        data = L.data_uri_bytes(uri)
        if not data:
            return None
        counter[0] += 1
        return store(data, names.get(hashlib.sha256(data).hexdigest(), f"image-{counter[0]}"))

    body_md = M.html_to_md(note["body"], inline_image)
    first = body_md.split("\n", 1)
    if first[0].strip() and not first[0].startswith("#") and first[0].strip() == note["name"].strip():
        # Notes' title is just the first line
        body_md = "# " + first[0] + "\n\n" + (first[1].lstrip("\n") if len(first) > 1 else "")
    extra = []
    for name, data in files:
        if hashlib.sha256(data).hexdigest() not in seen:
            extra.append((name, store(data, name)))
    if extra:
        lines = ["", "## Attachments", ""]
        for name, rel in extra:
            label = Path(unquote(rel)).name
            is_img = Path(rel).suffix.lower() in (".png", ".jpg", ".gif", ".heic", ".tiff", ".webp")
            lines.append(f"![{label}]({rel})" if is_img else f"- [{name}]({rel})")
            lines.append("")
        body_md = body_md.rstrip("\n") + "\n" + "\n".join(lines)

    front = ["---", f"title: {yaml_str(note['name'])}", f"id: {note['id']}",
             f"folder: {yaml_str(folder_path)}", f"created: {note['created']}",
             f"modified: {note['modified']}", "---", ""]
    md_path.write_text("\n".join(front) + body_md.rstrip("\n") + "\n", encoding="utf-8")
    # Nameless attachments are tables (exported as Markdown tables) or images that were
    # inserted through scripting as data URIs, which AppleScript can't hand back.
    imgs, tables = L.body_media_counts(note["body"])
    return {"title": note["name"], "file": str(md_path), "attachments": saved,
            "not_exportable": max(0, nameless - tables - imgs), "failed": skipped}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--folder")
    src.add_argument("--note", help="note id or 'Account/Folder/Title'")
    src.add_argument("--ids-from", help="JSON from nt-search.py --json")
    ap.add_argument("--out", required=True)
    ap.add_argument("--no-recursive", action="store_true")
    ap.add_argument("--force", action="store_true", help="re-export notes already exported into OUT")
    ap.add_argument("--timeout", type=int, default=L.DEFAULT_TIMEOUT)
    a = ap.parse_args()
    L.DEFAULT_TIMEOUT = a.timeout

    out = Path(a.out).expanduser().resolve()
    fs = L.folders()
    paths = {f["id"]: f["path"] for f in fs}
    if a.folder:
        root = L.resolve_folder(a.folder, fs)
        scope = [root] if a.no_recursive else L.subtree(root, fs)
        listing = L.jxa("list_notes", {"folderIds": [f["id"] for f in scope], "text": False})
        base = root["path"]
    elif a.note:
        listing = [L.find_note(a.note, fs)]
        base = paths[listing[0]["folderId"]]
    else:
        ids = [r["id"] for r in json.loads(Path(a.ids_from).read_text())["results"]]
        listing = [L.jxa("note_get", {"id": i}) for i in ids]
        base = None

    out.mkdir(parents=True, exist_ok=True)
    taken = {str(p).lower() for p in out.rglob("*")}
    # .md files from an earlier export, by the note id in their front matter
    previous = {}
    for p in out.rglob("*.md"):
        m = re.search(r"^id: (\S+)$", p.read_text(encoding="utf-8", errors="replace")[:600], re.M)
        if m:
            previous[m.group(1)] = p
    exported, locked, existing, missing_atts = [], [], [], 0
    for n in listing:
        fpath = paths.get(n["folderId"], "")
        if n["locked"]:
            locked.append(f"{fpath}/{n['name']}")
            continue
        rel = fpath[len(base):].strip("/") if base and fpath.startswith(base) else \
            ("" if base else fpath.replace("/", "_"))
        (out / rel).mkdir(parents=True, exist_ok=True)
        if n["id"] in previous:
            if not a.force:
                existing.append(str(previous[n["id"]]))
                continue
            md_path = previous[n["id"]]          # --force: refresh the same file
        else:
            # duplicate titles are normal in Notes: "Meeting.md", "Meeting-2.md", ...
            md_path = L.unique_path(out / rel / f"{L.slug(n['name'])}.md", taken)
        note = n if "body" in n else L.jxa("note_get", {"id": n["id"]})
        res = export_note(note, md_path, rel, fpath, out, taken)
        missing_atts += res["not_exportable"]
        exported.append(res)
    summary = {"out": str(out), "exported": len(exported),
               "attachments": sum(len(e["attachments"]) for e in exported),
               "locked_skipped": locked, "existing_skipped": existing,
               "attachments_not_exportable": missing_atts, "notes": exported}
    L.dump(summary)
    if existing:
        print(f"note: {len(existing)} note(s) were already exported here and were kept; --force refreshes",
              file=sys.stderr)


if __name__ == "__main__":
    main()
