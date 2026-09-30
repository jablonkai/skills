#!/usr/bin/env python3
"""Fill a Pages template and export it, without touching the template.

  pages-fill.py SOURCE [--out filled.pages] [--export out.pdf]...
                [--set key=value]... [--data values.json] [--token '{{%s}}']
                [--image key=pic.png]... [--add-image 'page,x,y,width=pic.png']...
                [export options] [--force] [--allow-leftover]

SOURCE is a .pages file (copied first, never edited) or template:<id> for a Pages
template (ids from `pages.sh --templates`; names are localized, ids are not).

--set/--data replace each token (default {{key}}) everywhere: body text, text boxes,
shapes and table cells, keeping the token's own font and style. --image swaps every
image whose accessibility description is key (Format > Image > Description) for a
new file fitted into the same frame; --add-image places a new one on a page, x/y/width
in points from the page's top-left. --export may repeat; the extension picks the
format (pdf, docx, epub, rtf, txt).

Exit 0 ok, 1 failed (including an unreplaced token left in the document), 2 usage.
Prints one JSON summary line.
"""
import argparse
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pages_osa as po  # noqa: E402


def parse_args(argv):
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("source", help=".pages file or template:<id>")
    ap.add_argument("--out", help="keep the filled document at this .pages path")
    ap.add_argument("--export", action="append", default=[], help="export path (repeatable)")
    ap.add_argument("--set", action="append", default=[], metavar="KEY=VALUE")
    ap.add_argument("--data", help="JSON object of key -> value")
    ap.add_argument("--token", default="{{%s}}", help="token pattern, %%s = key")
    ap.add_argument("--image", action="append", default=[], metavar="KEY=PATH")
    ap.add_argument("--add-image", action="append", default=[], metavar="PAGE,X,Y,W=PATH")
    ap.add_argument("--force", action="store_true", help="overwrite existing outputs")
    ap.add_argument(
        "--allow-leftover", action="store_true", help="an unreplaced token is not an error"
    )
    po.add_export_args(ap)
    ns = ap.parse_args(argv)
    if not ns.out and not ns.export:
        ap.error("give --out and/or --export")
    return ns


def split_kv(item, what):
    if "=" not in item:
        raise po.PagesError("%s needs KEY=VALUE, got %r" % (what, item))
    k, v = item.split("=", 1)
    return k, v


def values_from(ns):
    values = {}
    if ns.data:
        with open(ns.data, encoding="utf-8") as fh:
            data = json.load(fh)
        if not isinstance(data, dict):
            raise po.PagesError("--data must hold a JSON object")
        values.update({str(k): "" if v is None else str(v) for k, v in data.items()})
    for item in ns.set:
        k, v = split_kv(item, "--set")
        values[k] = v
    return values


def check_outputs(paths, force):
    for p in paths:
        if os.path.exists(p) and not force:
            raise po.PagesError("exists (use --force): %s" % p)
        if os.path.exists(p):
            po.remove_path(p)
        parent = os.path.dirname(os.path.abspath(p))
        os.makedirs(parent, exist_ok=True)


def main(argv):
    ns = parse_args(argv)
    try:
        values = values_from(ns)
        images = [split_kv(i, "--image") for i in ns.image]
        adds = [split_kv(i, "--add-image") for i in ns.add_image]
        for _, path in images + adds:
            if not os.path.isfile(path):
                raise po.PagesError("image not found: %s" % path)
        exports = [os.path.abspath(p) for p in ns.export]
        for p in exports:
            po.format_of(p)
        outs = exports + ([os.path.abspath(ns.out)] if ns.out else [])
        if ns.out and not ns.out.endswith(".pages"):
            raise po.PagesError("--out must end in .pages")
        if not ns.source.startswith("template:") and ns.out and \
                os.path.abspath(ns.out) == os.path.abspath(ns.source):
            raise po.PagesError("--out must differ from the source; the source is never edited")
        check_outputs(outs, ns.force)
        tmp = None
        if ns.out:
            work = os.path.abspath(ns.out)
        else:
            tmp = tempfile.mkdtemp(prefix="pages-fill-")
            work = os.path.join(tmp, "work.pages")
        try:
            res = po.fill(ns.source, work, values, ns.token, images, adds, exports,
                       po.export_opt_args(ns), save=bool(ns.out))
        finally:
            if tmp:
                po.remove_path(tmp)
    except po.PagesError as e:
        print(json.dumps({"ok": False, "error": str(e)}, ensure_ascii=False))
        return 1
    missing = [t for t, n in res["counts"].items() if n == 0]
    ok = not (res["leftover"] and not ns.allow_leftover)
    summary = dict(ok=ok, out=ns.out, **res)
    if missing:
        summary["not_found"] = missing
    print(json.dumps(summary, ensure_ascii=False))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
