"""Plan, back up, apply and verify metadata edits on many books in a calibre library.

    # who is in the library under which spelling?
    bash calibre.sh py bulk_metadata.py --variants "Jane Doe"
    # dry run (default): show every change as old -> new, write nothing
    bash calibre.sh py bulk_metadata.py --search 'title:"=Gale Warning" or authors:"=J. Doe"' \
        --set authors="Jane Doe" --set series="Harbor Lights" --series-order pubdate
    # same command + --apply: back up the touched fields, write, read back
    bash calibre.sh py bulk_metadata.py ... --apply [--backup before.json]
    # undo
    bash calibre.sh py bulk_metadata.py --restore before.json --apply

Selection: --search (calibre's search language) and/or --ids 1,2,3. --library takes a
path or a Content server URL; default is the configured library. When the GUI or
calibre-server holds the library, the script routes through a running Content server
on this machine automatically (exit 6 if there is none it can write through).

Edits: --set FIELD=VALUE (repeatable; title, authors, author_sort, series,
series_index, tags, publisher, languages, pubdate, rating, comments, identifiers,
#custom). Setting authors also sets author_sort (calibredb leaves the old sort).
--rename-author OLD=NEW replaces one author in multi-author books. --series-order
pubdate|title|id|timestamp numbers the selected books 1..n (--series-start).
"""
import argparse
import datetime as dt
import json
import os
import re
import sys
import urllib.request
from urllib.parse import quote

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cal_common import LOCK_MSG, calibredb, default_library, emit, fail, tool  # noqa: E402

LIST_FIELDS = ["title", "authors", "author_sort", "series", "series_index", "tags", "publisher",
               "languages", "pubdate", "rating", "comments", "identifiers", "timestamp"]


# ---------------------------------------------------------------- library routing
def server_urls():
    import subprocess
    out = subprocess.run(["lsof", "-nP", "-iTCP", "-sTCP:LISTEN"], capture_output=True, text=True).stdout
    ports = sorted({line.split()[8].rsplit(":", 1)[1] for line in out.splitlines()[1:]
                    if line.lower().startswith("calibre")})
    return [f"http://127.0.0.1:{p}" for p in ports]


def resolve_library(lib):
    """Return something calibredb can write through: the path itself when it is free,
    else the URL#library_id of a local Content server serving that library."""
    if lib.startswith("http"):
        return lib, "server"
    if not os.path.isfile(os.path.join(lib, "metadata.db")):
        fail(3, f"not a calibre library (no metadata.db): {lib}")
    rc, out, err = tool("calibredb", "--with-library", lib, "list", "--limit", "1", "-f", "title",
                        check=False)
    if LOCK_MSG not in out + err:
        return lib, "direct"
    want = os.path.basename(os.path.normpath(lib))
    served = {}
    for url in server_urls():
        try:
            info = json.load(urllib.request.urlopen(url + "/ajax/library-info", timeout=3))
        except Exception:
            continue
        for lib_id, name in info.get("library_map", {}).items():
            served[f"{url}/#{lib_id}"] = name
            if name == want:
                return f"{url}/#{lib_id}", "server"
    fail(6, "calibre (the GUI or calibre-server) is running, and while it runs calibredb refuses "
            "every local library, not only the one open in it. No local Content server serves "
            f"'{want}'. Ask the user to close calibre, or to open this library in calibre and start "
            "its Content server (Preferences > Sharing over the net) with 'Allow un-authenticated "
            "local connections to make changes', then rerun. Do not kill calibre.",
         library=lib, served_libraries=served)


# ---------------------------------------------------------------- reading
def list_books(lib, search=None, ids=None):
    args = ["list", "--for-machine", "--limit", "100000", "-f", ",".join(LIST_FIELDS)]
    query = []
    if search:
        query.append(f"({search})")
    if ids:
        query.append("(" + " or ".join(f"id:={i}" for i in ids) + ")")
    if query:
        args += ["--search", " and ".join(query)]
    rc, out, err = calibredb(lib, *args, check=False)
    if rc != 0 and not out.strip():
        if "No books matching" in out + err:
            return []
        fail(5, "calibredb list failed", stderr=(err or out)[-1500:])
    start = out.find("[")
    return json.loads(out[start:]) if start >= 0 else []


def custom_columns(lib):
    rc, out, _ = calibredb(lib, "custom_columns", check=False)
    return [line.split(" (")[0].strip() for line in out.splitlines() if line.strip()]


# ---------------------------------------------------------------- author variants
def name_key(name):
    name = re.sub(r"\s+", " ", name).strip()
    if "," in name:                       # "Doe, Jane" -> "Jane Doe"
        last, _, first = name.partition(",")
        name = f"{first.strip()} {last.strip()}"
    parts = [p for p in re.split(r"[\s.]+", name.lower()) if p]
    return parts


def variant_kind(cand, target):
    c, t = name_key(cand), name_key(target)
    if not c or not t or c[-1] != t[-1]:
        return None
    if c == t:
        return "exact" if cand == target else "same name, different spelling/case/spacing"
    cf, tf = c[:-1], t[:-1]
    if cf and tf and all(len(x) == 1 for x in cf) and cf[0][0] == tf[0][0]:
        return "initials only - verify by title/series, could be someone else"
    if cf and tf and cf[0] != tf[0]:
        return None                        # John Doe is not Jane Doe
    return "same surname - verify"


def variants(lib, target):
    rows = []
    for b in list_books(lib):
        for a in [x.strip() for x in b["authors"].split("&")]:
            kind = variant_kind(a, target)
            if kind:
                rows.append({"author": a, "match": kind, "id": b["id"], "title": b["title"],
                             "series": b.get("series"), "series_index": b.get("series_index"),
                             "pubdate": (b.get("pubdate") or "")[:10]})
    return sorted(rows, key=lambda r: (r["match"] != "exact", r["author"], r["pubdate"]))


# ---------------------------------------------------------------- planning
def norm_date(v):
    # calibredb stores a bare "1995-03-01" as 1995-03-02 (local midnight -> UTC);
    # noon UTC is what the GUI uses and survives every timezone
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", v):
        return v + "T12:00:00+00:00"
    return v


def current_value(book, field):
    v = book.get(field)
    if field == "authors":
        return v or ""
    if field in ("tags", "languages"):
        return ",".join(v or [])
    if field == "identifiers":
        return ",".join(f"{k}:{x}" for k, x in sorted((v or {}).items()))
    if field == "series_index":
        return float(v) if v is not None and book.get("series") else None
    if field == "pubdate":
        return (v or "")[:10] if v and not v.startswith("0101") else ""
    return "" if v is None else v


def same(field, old, new):
    if field == "series_index":
        return old is not None and new not in ("", None) and float(old) == float(new)
    if field == "pubdate":
        return str(old)[:10] == str(new)[:10]
    if field in ("tags", "languages"):
        return sorted(x.strip() for x in str(old).split(",") if x.strip()) == \
            sorted(x.strip() for x in str(new).split(",") if x.strip())
    return str(old) == str(new)


def plan(books, args):
    from calibre.ebooks.metadata import author_to_author_sort
    sets = {}
    for s in args.set or []:
        if "=" not in s:
            fail(2, f"--set wants FIELD=VALUE, got {s!r}")
        k, v = s.split("=", 1)
        sets[k.strip()] = v
    if args.series_order:
        key = {"pubdate": lambda b: (b.get("pubdate") or "", b["id"]),
               "title": lambda b: (b["title"].lower(), b["id"]),
               "id": lambda b: b["id"],
               "timestamp": lambda b: (b.get("timestamp") or "", b["id"])}[args.series_order]
        order = {b["id"]: args.series_start + n for n, b in enumerate(sorted(books, key=key))}
    out = []
    for b in books:
        new = dict(sets)
        if args.rename_author:
            old_a, _, new_a = args.rename_author.partition("=")
            names = [x.strip() for x in b["authors"].split("&")]
            if old_a.strip() in names:
                new["authors"] = " & ".join(new_a.strip() if x == old_a.strip() else x for x in names)
        if "authors" in new and "author_sort" not in new:
            new["author_sort"] = " & ".join(author_to_author_sort(a.strip()) for a in new["authors"].split("&"))
        if args.series_order:
            new["series_index"] = order[b["id"]]
        if "pubdate" in new:
            new["pubdate"] = norm_date(new["pubdate"])
        changes = {}
        for f, v in new.items():
            old = current_value(b, f) if not f.startswith("#") else b.get(f)
            if not same(f, old, v):
                changes[f] = [old, v]
        out.append({"id": b["id"], "title": b["title"], "authors": b["authors"], "changes": changes})
    return out


# ---------------------------------------------------------------- applying
def apply(lib, items, books_by_id, backup_path):
    touched = [i for i in items if i["changes"]]
    backup = {"library": lib, "created": dt.datetime.now().isoformat(timespec="seconds"),
              "books": [{"id": i["id"], "title": i["title"],
                         "fields": {f: (current_value(books_by_id[i["id"]], f)
                                        if f != "pubdate" else books_by_id[i["id"]].get("pubdate") or "")
                                    for f in i["changes"]}} for i in touched]}
    with open(backup_path, "w") as f:
        json.dump(backup, f, indent=1, ensure_ascii=False)
    for n, i in enumerate(touched):
        rc, out, err = tool("calibredb", "--with-library", lib, "set_metadata", str(i["id"]),
                            *field_args(i["changes"]), check=False)
        if rc != 0 or LOCK_MSG in out + err:
            if n == 0:
                os.remove(backup_path)  # nothing was written, so there is nothing to undo
                calibredb(lib, "set_metadata", str(i["id"]), *field_args(i["changes"]))  # exits 6/5 with the reason
            fail(5, f"write failed on book {i['id']} after {n} books were changed; "
                    f"undo with --restore {backup_path} --apply",
                 stderr=(err or out)[-1500:], backup=backup_path)
    return touched


def field_args(changes):
    args = []
    # series before series_index, so a new series and its number land together
    for f in sorted(changes, key=lambda k: (k == "series_index", k)):
        v = changes[f][1]
        if f == "series_index" and v in ("", None):
            continue  # no series: calibredb rejects an empty index, clearing series is enough
        args += ["-f", f"{f}:{'' if v is None else v}"]
    return args


def verify(lib, touched):
    after = {b["id"]: b for b in list_books(lib, ids=[i["id"] for i in touched])} if touched else {}
    bad = []
    for i in touched:
        b = after.get(i["id"])
        for f, (_, v) in i["changes"].items():
            got = (current_value(b, f) if not f.startswith("#") else b.get(f)) if b else None
            if v in ("", None) and got in ("", None, []):
                continue
            if not same(f, got, v):
                bad.append({"id": i["id"], "field": f, "expected": v, "got": got})
    return bad


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--library", help="library folder or http://host:port/#library_id")
    ap.add_argument("--search", help="calibre search expression selecting the books")
    ap.add_argument("--ids", help="comma separated book ids")
    ap.add_argument("--set", action="append", metavar="FIELD=VALUE")
    ap.add_argument("--rename-author", metavar="OLD=NEW")
    ap.add_argument("--series-order", choices=("pubdate", "title", "id", "timestamp"))
    ap.add_argument("--series-start", type=float, default=1)
    ap.add_argument("--variants", metavar="AUTHOR", help="list spellings of this author and their books")
    ap.add_argument("--apply", action="store_true", help="write (default is a dry run)")
    ap.add_argument("--backup", help="where to save the old values (default ./calibre-backup-<time>.json)")
    ap.add_argument("--restore", metavar="BACKUP.json", help="write the values from a backup back")
    args = ap.parse_args()

    lib_path = args.library or default_library()
    if not lib_path:
        fail(2, "no library: pass --library")
    lib, route = resolve_library(lib_path)

    if args.variants:
        emit({"ok": True, "library": lib, "route": route, "target": args.variants,
              "variants": variants(lib, args.variants)})

    if args.restore:
        data = json.load(open(args.restore))
        items = [{"id": b["id"], "title": b["title"], "authors": "",
                  "changes": {f: [None, v] for f, v in b["fields"].items()}} for b in data["books"]]
        if not args.apply:
            emit({"ok": True, "dry_run": True, "library": lib, "restore": items})
        for i in items:
            calibredb(lib, "set_metadata", str(i["id"]), *field_args(i["changes"]))
        emit({"ok": True, "restored": len(items), "library": lib})

    if not args.search and not args.ids:
        fail(2, "select books with --search and/or --ids (or use --variants / --restore)")
    if not (args.set or args.rename_author or args.series_order):
        fail(2, "nothing to change: use --set, --rename-author or --series-order")
    for s in args.set or []:
        f = s.split("=", 1)[0].strip()
        if f.startswith("#") and f not in custom_columns(lib):
            fail(2, f"no custom column {f} in this library")
    ids = [int(x) for x in args.ids.split(",")] if args.ids else None
    books = list_books(lib, args.search, ids)
    if not books:
        fail(4, "the selection matched no books", search=args.search, ids=ids)
    items = plan(books, args)
    summary = {"selected": len(books), "to_change": sum(1 for i in items if i["changes"])}
    if not args.apply:
        emit({"ok": True, "dry_run": True, "library": lib, "route": route, **summary, "plan": items,
              "next": "check the selection and every old -> new pair, then rerun with --apply"})
    backup = args.backup or os.path.abspath(f"calibre-backup-{dt.datetime.now():%Y%m%d-%H%M%S}.json")
    touched = apply(lib, items, {b["id"]: b for b in books}, backup)
    bad = verify(lib, touched)
    result = {"ok": not bad, "library": lib, "route": route, **summary, "backup": backup,
              "applied": [{"id": i["id"], "title": i["title"],
                           "changes": {f: v[1] for f, v in i["changes"].items()}} for i in touched],
              "undo": f"bulk_metadata.py --library {quote(lib, safe=':/#')} --restore {backup} --apply"}
    if bad:
        result["mismatches"] = bad
        emit(result, 4)
    emit(result)


if __name__ == "__main__":
    main()
