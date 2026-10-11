#!/usr/bin/env python3
"""Create a note from Markdown, or append Markdown to an existing note, then read it back.

  nt-write.py create --folder "iCloud/Projects" --md plan.md [--title T] [--make-folder]
  nt-write.py append --note "iCloud/Journal/Log" --md today.md [--reattach]
  nt-write.py replace --note x-coredata://... --md new.md          # explicit only
  add --dry-run to print the HTML and the target without touching Notes

Never deletes a note. Local images referenced by the Markdown are added as real
attachments at the end of the note (Notes can't place them mid-text through scripting).
Notes can only append by rewriting the whole body, which deletes or degrades attachments,
so append/replace refuse a note with file attachments unless --reattach (the files are
saved first and re-added as real attachments at the END of the note), and always refuse
one whose attachments can't be saved.
Prints a JSON report: note id/title/folder, attachments, and a read-back diff against
the source (the same check nt-verify.py runs). Exit 4 if the read-back does not match.
"""
import argparse
import hashlib
import re
import sys
import tempfile
from pathlib import Path

import notes_lib as L
import notes_md as M
import importlib

verify = importlib.import_module("nt-verify")


def target_folder(path, make, all_folders):
    try:
        return L.resolve_folder(path, all_folders)
    except SystemExit:
        if not make:
            raise
    parts = path.strip("/").split("/")
    accounts = sorted({f["account"] for f in all_folders})
    if parts[0] not in accounts:
        parts.insert(0, L.jxa("default_account"))
    parent = None
    for depth in range(2, len(parts) + 1):
        sub = "/".join(parts[:depth])
        hit = next((f for f in all_folders if f["path"].lower() == sub.lower()), None)
        if hit is None:
            L.jxa("make_folder", {"account": parts[0], "parentId": parent and parent["id"],
                                  "name": parts[depth - 1]})
            all_folders[:] = L.folders()
            hit = next(f for f in all_folders if f["path"].lower() == sub.lower())
        parent = hit
    return parent


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("mode", choices=["create", "append", "replace"])
    ap.add_argument("--md", required=True, help="Markdown file ('-' for stdin)")
    ap.add_argument("--folder", help="create: target folder 'Account/Folder[/Sub]'")
    ap.add_argument("--make-folder", action="store_true", help="create: create a missing folder")
    ap.add_argument("--title", help="create: title if the Markdown has no leading heading")
    ap.add_argument("--note", help="append/replace: note id or 'Account/Folder/Title'")
    ap.add_argument("--reattach", action="store_true",
                    help="append/replace a note with file attachments: re-add them at the end")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--timeout", type=int, default=L.DEFAULT_TIMEOUT)
    a = ap.parse_args()
    L.DEFAULT_TIMEOUT = a.timeout

    if a.md == "-":
        text, base = sys.stdin.read(), Path.cwd()
    else:
        src = Path(a.md).expanduser()
        if not src.is_file():
            L.die(f"no such file: {src}", 2)
        text, base = src.read_text(encoding="utf-8"), src.parent
    images = []
    html = M.md_to_html(text, base, title=a.title if a.mode == "create" else None, images=images)
    if a.mode == "append":
        html = M.SEP + html
    fs = L.folders()
    reattach = []

    report = {"mode": a.mode, "images": [str(p) for p in images], "warnings": []}
    if a.mode == "create":
        if not a.folder:
            L.die("create needs --folder", 2)
        if a.dry_run:
            folder = {"path": a.folder + (" (would be created)" if a.make_folder else "")}
        else:
            folder = target_folder(a.folder, a.make_folder, fs)
        report["folder"] = folder["path"]
    else:
        if not a.note:
            L.die(f"{a.mode} needs --note", 2)
        note = L.find_note(a.note, fs)
        if note["locked"]:
            L.die("the note is locked; Notes doesn't let scripts read or write locked notes", 3)
        tmp = tempfile.mkdtemp(prefix="nt-write-")
        saved = [r for r in L.jxa("save_attachments", {"noteId": note["id"], "dir": tmp}) if r["path"]]
        for i, r in enumerate(saved):   # back to the original file name, so re-adding keeps it
            dest = Path(tmp, str(i), r["name"].replace("/", "-"))
            dest.parent.mkdir()
            r["path"] = str(Path(r["path"]).rename(dest))
        imgs, tables = L.body_media_counts(note["body"])
        unsaveable = note["attachmentCount"] - len(saved) - tables - imgs
        if unsaveable > 0:
            L.die(f"refusing to {a.mode}: {note['name']!r} has {unsaveable} attachment(s) that scripting "
                  "can neither see in the body nor save, so rewriting the body would delete them. "
                  "Create a new note instead, or paste the text in Notes by hand.", 3)
        if saved and not a.reattach:
            L.die(f"refusing to {a.mode}: {note['name']!r} has {len(saved)} file attachment(s) "
                  f"({', '.join(r['name'] for r in saved)}). Rewriting the body would delete or degrade "
                  "them. Options: --reattach (they are re-added as real attachments, moved to the end "
                  "of the note), or create a new note instead.", 3)
        body = note["body"]
        if saved:
            # drop the inline copies of the files we re-add; legacy data-URI images stay put
            hashes = {hashlib.sha256(Path(r["path"]).read_bytes()).hexdigest() for r in saved}
            body = re.sub(r'<img[^>]+src="(data:[^"]+)"[^>]*>',
                          lambda m: "" if hashlib.sha256(L.data_uri_bytes(m.group(1))).hexdigest() in hashes
                          else m.group(0), body)
            reattach = [Path(r["path"]) for r in saved]
            report["warnings"].append(f"{len(saved)} attachment(s) re-added at the end of the note")
        else:
            reattach = []
        legacy = L.body_media_counts(body)[0]
        if legacy:
            report["warnings"].append(
                f"{legacy} legacy inline image(s) are re-embedded by the rewrite: still visible, but "
                "Notes can no longer export them through scripting")
        if a.mode == "append":
            # trailing blank lines (or the empty block left where an image was) would pile up
            body = re.sub(r"(\s*<div>\s*(<br>\s*)*</div>\s*)+$", "", body)
            html = body + html
        report["note"] = {"id": note["id"], "name": note["name"]}

    if a.dry_run:
        report["html"] = html
        L.dump(report)
        return

    if a.mode == "create":
        res = L.jxa("note_write", {"mode": "create", "folderId": folder["id"], "html": html})
    else:
        res = L.jxa("note_write", {"mode": "replace", "noteId": note["id"], "html": html})
    for img in reattach + images:       # the note's own files first, then the new ones
        r = L.jxa("add_attachment", {"noteId": res["id"], "path": str(img)})
        if r["added"] == 0:
            report["warnings"].append(f"{img.name}: NOT attached (scripting can only attach images; "
                                      "drag the file into the note by hand)")
        elif r["added"] != 1:
            report["warnings"].append(f"{img.name}: Notes added {r['added']} attachment(s)")

    back = L.jxa("note_get", {"id": res["id"]})
    if a.mode != "create" and back["attachmentCount"] < note["attachmentCount"]:
        report["warnings"].append(
            f"attachment count dropped {note['attachmentCount']} -> {back['attachmentCount']}")
    report.update(id=back["id"], title=back["name"], attachments=back["attachmentCount"],
                  modified=back["modified"])
    check = verify.compare_md(text, M.html_to_md(back["body"], lambda uri: "image"),
                              title=a.title if a.mode == "create" else None)
    if a.mode == "append":
        check["extra"] = []                 # the note's earlier text is expected to be there
        check["ok"] = not check["missing"]
    report["readback"] = check
    L.dump(report)
    sys.exit(0 if check["ok"] else 4)


if __name__ == "__main__":
    main()
