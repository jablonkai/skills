#!/usr/bin/env python3
"""Export messages (.eml / Markdown) and their attachments to a folder. Read-only on Mail.

  mail-export.py --from billing@acme.test --since 30d --attachments-only --out ~/Invoices
  mail-export.py --ids-from hits.json --out DIR                    # .eml + .md + attachments
  mail-export.py --mailbox "Google/receipts" --format md --out DIR
  mail-export.py --id "Google/INBOX#4711" --format eml --out DIR

Layout (default --format both):
  DIR/2026-10-01 Subject.eml           raw RFC 822 source, byte-exact
  DIR/2026-10-01 Subject.md            front matter (from, to, date, subject, ref) + text body
  DIR/attachments/2026-10-01 Subject/file.pdf
With --attachments-only every attachment goes straight into DIR; name clashes get -2, -3.
DIR/manifest.json lists every message and file (with sha256), plus anything not exported.
Attachments come from the message source; ones Mail has not downloaded yet are saved
through Mail itself, which fetches them.
"""
import argparse
import email
import email.policy
import hashlib
import json
import shutil
import tempfile
from pathlib import Path

import mail_lib as L


def parts(msg):
    """(filename, bytes) for every attachment part in a parsed message."""
    out = []
    for p in msg.walk():
        if p.is_multipart():
            continue
        fn = p.get_filename()
        disp = (p.get_content_disposition() or "")
        if not fn and disp != "attachment":
            continue
        data = p.get_payload(decode=True) or b""
        out.append((L.nfc(fn) if fn else f"attachment.{p.get_content_subtype()}", data))
    return out


def text_body(msg):
    b = msg.get_body(preferencelist=("plain", "html"))
    if b is not None and b.get_content_type() == "text/plain" and not b.get_content().strip():
        b = msg.get_body(preferencelist=("html",)) or b   # Mail drafts: empty plain part
    if not b:
        return ""
    txt = b.get_content()
    if b.get_content_type() == "text/html":
        import html
        import re
        txt = re.sub(r"(?is)<(script|style).*?</\1>", "", txt)
        txt = re.sub(r"(?i)<br\s*/?>|</p>|</div>|</tr>", "\n", txt)
        txt = html.unescape(re.sub(r"<[^>]+>", "", txt))
        txt = re.sub(r"\n\s*\n\s*\n+", "\n\n", txt)
    return txt.strip() + "\n"


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    L.add_filter_args(ap)
    ap.add_argument("--out", required=True)
    ap.add_argument("--format", choices=["both", "eml", "md"], default="both")
    ap.add_argument("--attachments-only", action="store_true", help="only the attachments, flat in --out")
    ap.add_argument("--no-attachments", action="store_true")
    ap.add_argument("--match-attachment", help="only attachments whose name contains this (e.g. .pdf)")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    L.DEFAULT_TIMEOUT = a.timeout
    rows = L.search(a)
    out = Path(a.out).expanduser().resolve()
    if a.dry_run:
        L.dump({"would_export": len(rows), "out": str(out),
                "messages": [{k: r.get(k) for k in ("date", "from", "subject", "ref")} for r in rows]})
        return
    out.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp(prefix="apple-mail-src-"))
    taken = {str(out / "manifest.json").lower()}
    manifest = {"out": str(out), "messages": [], "not_exported": []}
    try:
        det = L.jxa("details", {"refs": [r["ref"] for r in rows], "sourceDir": str(tmp)},
                    timeout=a.timeout) if rows else []
        for r, d in zip(rows, det):
            if d.get("error"):
                manifest["not_exported"].append({"ref": r["ref"], "reason": f"error {d['error']}"})
                continue
            src = Path(d["source"]).read_bytes()
            msg = email.message_from_bytes(src, policy=email.policy.default)
            base = L.slug(f"{(r['date'] or '')[:10]} {d['subject'] or '(no subject)'}")
            entry = {"ref": r["ref"], "date": r["date"], "from": d["from"], "subject": d["subject"],
                     "files": [], "attachments": []}
            if not a.attachments_only:
                if a.format in ("both", "eml"):
                    p = L.unique_path(out / f"{base}.eml", taken)
                    p.write_bytes(src)
                    entry["files"].append(str(p.relative_to(out)))
                if a.format in ("both", "md"):
                    p = L.unique_path(out / f"{base}.md", taken)
                    fm = {"subject": d["subject"], "from": d["from"], "to": d["to"], "cc": d["cc"],
                          "date": r["date"], "message_id": d["messageId"], "ref": r["ref"]}
                    head = "---\n" + "".join(f"{k}: {json.dumps(v, ensure_ascii=False)}\n" for k, v in fm.items()) + "---\n\n"
                    p.write_text(head + text_body(msg), encoding="utf-8")
                    entry["files"].append(str(p.relative_to(out)))
            if not a.no_attachments:
                adir = out if a.attachments_only else out / "attachments" / base
                found = parts(msg)
                names = [x["name"] for x in d.get("attachments", [])]
                for i, name in enumerate(names):
                    if a.match_attachment and L.fold(a.match_attachment) not in L.fold(name):
                        continue
                    adir.mkdir(parents=True, exist_ok=True)
                    dest = L.unique_path(adir / L.slug(L.nfc(name), 150), taken)
                    hit = next((j for j, (fn, _) in enumerate(found) if fn == L.nfc(name)), None)
                    if hit is not None:
                        dest.write_bytes(found.pop(hit)[1])
                    else:
                        res = L.jxa("save_attachments", {"ref": r["ref"], "items": [{"index": i, "path": str(dest)}]})
                        if not res[0]["ok"] or not dest.exists():
                            manifest["not_exported"].append({"ref": r["ref"], "attachment": name,
                                                             "reason": f"save failed {res[0].get('error')}"})
                            taken.discard(str(dest).lower())
                            continue
                    entry["attachments"].append({"name": name, "file": str(dest.relative_to(out)),
                                                 "size": dest.stat().st_size, "sha256": sha(dest)})
            manifest["messages"].append(entry)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    (out / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    L.dump({"exported_messages": len(manifest["messages"]),
            "attachments": sum(len(m["attachments"]) for m in manifest["messages"]),
            "not_exported": manifest["not_exported"], "out": str(out),
            "manifest": str(out / "manifest.json")})


if __name__ == "__main__":
    main()
