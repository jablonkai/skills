#!/usr/bin/env python3
"""Check an osxphotos export folder against the query that produced it. Read-only.

  ph-verify-export.py DEST [--library LIB] [--sidecar xmp|json] [--edited] -- QUERY ARGS

Uses DEST/.osxphotos_export.db to map each matched item to its files (falls back to
original-file-name matching without it) and checks: every matched item exported, no
exported item outside the query, files present with the recorded size, and with
--sidecar each media file has a parseable sidecar carrying the date and, when the item
has a location, GPS. With --edited, edited items must have an edited version exported.
Exit 0 when everything matches, 1 otherwise.
"""
import argparse
import json
import shutil
import sqlite3
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

from ph_lib import die, library_args, osxphotos, split_query

SIDECAR_EXT = {".xmp", ".json"}
TEMPLATE = "{uuid}|{photo.original_filename}|{created.strftime,%Y-%m-%d}|{photo.latitude}|{photo.hasadjustments}"


def sidecar_problem(media, kind, date, has_gps):
    cands = [media.with_name(media.name + "." + kind), media.with_suffix("." + kind)]
    side = next((c for c in cands if c.exists()), None)
    if side is None:
        return "no sidecar"
    text = side.read_text(errors="replace")
    try:
        if kind == "json":
            json.loads(text)
        else:
            ET.fromstring(text[text.index("<x:xmpmeta"):text.index("</x:xmpmeta>") + len("</x:xmpmeta>")])
    except (ValueError, ET.ParseError) as e:
        return f"unparseable sidecar ({e})"
    if date not in text:
        return f"sidecar lacks date {date}"
    if has_gps and "GPSLatitude" not in text and "latitude" not in text.lower():
        return "sidecar lacks GPS"
    return None


def read_export_db(db):
    """Rows (filepath, uuid, dest_size). Reads a temp copy when read-only mode can't open
    a WAL database (no -shm file yet), so the export folder is never written to."""
    sql = "select filepath, uuid, dest_size from export_data"
    try:
        return sqlite3.connect(f"file:{db.resolve()}?mode=ro", uri=True).execute(sql).fetchall()
    except sqlite3.OperationalError:
        with tempfile.TemporaryDirectory() as tmp:
            for suffix in ("", "-wal"):
                if Path(f"{db}{suffix}").exists():
                    shutil.copy2(f"{db}{suffix}", Path(tmp) / f"export.db{suffix}")
            return sqlite3.connect(Path(tmp) / "export.db").execute(sql).fetchall()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("dest")
    ap.add_argument("--library")
    ap.add_argument("--sidecar", choices=["xmp", "json"])
    ap.add_argument("--edited", action="store_true", help="edited items must have an edited file")
    own, query = split_query(sys.argv[1:])
    a = ap.parse_args(own)
    dest = Path(a.dest).expanduser()
    if not dest.is_dir():
        die(f"not a folder: {dest}")

    expected = {}
    for line in osxphotos(["query", *library_args(a.library), *query, "--quiet", "--print", TEMPLATE]).splitlines():
        uuid, name, date, lat, edited = line.split("|")
        expected[uuid] = dict(name=name, date=date, gps=lat != "_", edited=edited != "_")

    files = {}  # uuid -> [Path]
    db = dest / ".osxphotos_export.db"
    if db.exists():
        for rel, uuid, size in read_export_db(db):
            p = dest / rel
            if p.suffix.lower() not in SIDECAR_EXT:
                files.setdefault(uuid, []).append((p, size))
    else:
        by_stem = {}
        for uuid, e in expected.items():
            by_stem.setdefault(Path(e["name"]).stem.lower(), []).append(uuid)
        for p in dest.rglob("*"):
            if p.is_file() and p.suffix.lower() not in SIDECAR_EXT and not p.name.startswith("."):
                stem = p.stem.lower().split(" (")[0].removesuffix("_edited")
                for uuid in by_stem.get(stem, ["?" + p.name]):
                    files.setdefault(uuid, []).append((p, None))

    problems = []
    for uuid, e in expected.items():
        got = files.get(uuid, [])
        if not got:
            problems.append(f"{e['name']}: not exported")
            continue
        for p, size in got:
            if not p.exists():
                problems.append(f"{e['name']}: {p.name} recorded but missing on disk")
            elif size is not None and p.stat().st_size != size:
                problems.append(f"{e['name']}: {p.name} size differs from the export record")
            elif a.sidecar:
                err = sidecar_problem(p, a.sidecar, e["date"], e["gps"])
                if err:
                    problems.append(f"{e['name']}: {p.name}: {err}")
        if a.edited and e["edited"] and not any("_edited" in p.stem for p, _ in got):
            problems.append(f"{e['name']}: edited version not exported")
    extra = sorted({p.name for u, fs in files.items() if u not in expected for p, _ in fs})

    print(json.dumps({"dest": str(dest), "expected": len(expected),
                      "exported_items": sum(1 for u in expected if u in files),
                      "outside_query": extra, "problems": problems}, indent=1))
    if problems or extra:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
