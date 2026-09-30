#!/usr/bin/env python3
"""Edit a copy of a Keynote deck: replace {{tokens}}, skip, delete and reorder slides,
then save and export.

  keynote-fill.py SRC.key --out OUT.key [--set KEY=VALUE]... [--data VALUES.json]
                  [--token '{{%s}}'] [--skip SPEC] [--unskip SPEC] [--delete SPEC]
                  [--order N,N,...] [--move N=POS]... [--export FILE]...
                  [export options] [--allow-leftover] [--force]

Tokens are replaced in titles, bodies, text boxes, shapes, table cells, grouped
objects and presenter notes, keeping each token's own character style. Matching is
exact and case-sensitive. An unreplaced token prefix ("{{") left anywhere fails the
run unless --allow-leftover.

Slides are always named by their number in SRC (or "title:TEXT", an exact title),
whatever else the run changes:
  --skip / --unskip SPEC   comma list, e.g. 3,7 or "title:Appendix"
  --delete SPEC            remove slides
  --order 1,3,2,4          new order of the remaining slides (all of them)
  --move 9=2               slide 9 ends up at position 2 (after --order)

SRC is never modified: it is copied to OUT first. Prints JSON: counts per token,
not_found, leftover, final slide count, exports. Exit 0 on success.
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import keynote_osa as ko  # noqa: E402


def slide_titles(path):
    return [r[5].strip() for r in ko.rows(ko.run_ops("info", [ko.real(path)], docs=[path]))
            if r[0] == "SLIDE"]


def parse_spec(spec, n, titles_of):
    out = []
    for part in [p.strip() for p in spec.split(",") if p.strip()]:
        if part.startswith("title:"):
            want = part[len("title:"):].strip()
            hits = [i for i, t in enumerate(titles_of(), 1) if t == want]
            if not hits:
                raise ko.KeynoteError("no slide titled %r" % want)
            out += hits
        elif part.isdigit() and 1 <= int(part) <= n:
            out.append(int(part))
        else:
            raise ko.KeynoteError("bad slide %r (1..%d or title:TEXT)" % (part, n))
    return out


def plan_slide_ops(n, skip, unskip, delete, order, moves):
    """-> ops for keynote_ops fill: K (skip by original number), D (delete, descending),
    M a b (move current slide a to position b). Numbers are original slide numbers."""
    ops = []
    for s in skip:
        ops += ["K", s, "true"]
    for s in unskip:
        ops += ["K", s, "false"]
    keep = [i for i in range(1, n + 1) if i not in set(delete)]
    want = list(keep)
    if order:
        if sorted(order) != keep:
            raise ko.KeynoteError("--order must list every remaining slide once: %s" % keep)
        want = list(order)
    for src, pos in moves:
        if src not in want:
            raise ko.KeynoteError("--move %d: slide is deleted" % src)
        if not 1 <= pos <= len(want):
            raise ko.KeynoteError("--move to %d: position out of 1..%d" % (pos, len(want)))
        want.remove(src)
        want.insert(pos - 1, src)
    for s in sorted(set(delete), reverse=True):
        ops += ["D", s]
    cur = list(keep)
    for k, target in enumerate(want):
        j = cur.index(target)
        if j != k:  # always j > k: the front is already in place
            ops += ["M", j + 1, k + 1]
            cur.insert(k, cur.pop(j))
    return ops, len(want)


def main(argv):
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("src")
    ap.add_argument("--out", required=True)
    ap.add_argument("--set", action="append", default=[], metavar="KEY=VALUE")
    ap.add_argument("--data", help="JSON object of KEY: VALUE")
    ap.add_argument("--token", default="{{%s}}", help="token format, %%s is the key")
    ap.add_argument("--skip", default="")
    ap.add_argument("--unskip", default="")
    ap.add_argument("--delete", default="")
    ap.add_argument("--order", default="")
    ap.add_argument("--move", action="append", default=[], metavar="N=POS")
    ap.add_argument("--export", action="append", default=[])
    ap.add_argument("--allow-leftover", action="store_true")
    ap.add_argument("--force", action="store_true")
    ko.add_export_args(ap)
    ns = ap.parse_args(argv)
    if "%s" not in ns.token:
        ap.error("--token must contain %s")

    try:
        values = {}
        if ns.data:
            with open(ns.data, encoding="utf-8-sig") as fh:
                values.update({str(k): "" if v is None else str(v) for k, v in json.load(fh).items()})
        for kv in ns.set:
            k, sep, v = kv.partition("=")
            if not sep:
                raise ko.KeynoteError("--set wants KEY=VALUE, got %r" % kv)
            values[k] = v
        ko.check_key_file(ns.src)
        if not ns.out.endswith(".key"):
            raise ko.KeynoteError("--out must end in .key")
        out = ko.real(ns.out)
        if out == ko.real(ns.src):
            raise ko.KeynoteError("--out must differ from SRC; the source is never edited")
        exports = [(ko.real(p), ko.format_of(p)) for p in ns.export]
        for path in [out] + [p for p, _ in exports]:
            if os.path.exists(path):
                if not ns.force:
                    raise ko.KeynoteError("exists (use --force): %s" % path)
                ko.remove_path(path)

        cache = {}

        def titles_of():
            if "t" not in cache:
                cache["t"] = slide_titles(ns.src)
            return cache["t"]

        slide_args = []
        wants_slides = ns.skip or ns.unskip or ns.delete or ns.order or ns.move
        final_n = None
        if wants_slides:
            n = len(titles_of())
            moves = []
            for m in ns.move:
                a, sep, b = m.partition("=")
                if not sep or not b.strip().isdigit():
                    raise ko.KeynoteError("--move wants N=POS, got %r" % m)
                moves.append((parse_spec(a, n, titles_of)[0], int(b)))
            order = parse_spec(ns.order, n, titles_of) if ns.order else []
            slide_args, final_n = plan_slide_ops(
                n, parse_spec(ns.skip, n, titles_of), parse_spec(ns.unskip, n, titles_of),
                parse_spec(ns.delete, n, titles_of), order, moves)

        os.makedirs(os.path.dirname(out), exist_ok=True)
        ko.copy_key(os.path.realpath(ns.src), out)
        args = [out]
        for k, v in values.items():
            args += ["T", ns.token % k, v]
        args += slide_args
        args += ko.export_opt_args(ns)
        for path, fmt in exports:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            args += ["X", path, fmt]
        args.append("S")
        prefix = ns.token.split("%s")[0]
        if prefix:
            args += ["L", prefix]
        res = ko.rows(ko.run_ops("fill", args, docs=[out]))
    except (ko.KeynoteError, OSError, ValueError) as e:
        print(json.dumps({"ok": False, "error": str(e)}, ensure_ascii=False))
        return 1

    counts = {r[1]: int(r[2]) for r in res if r[0] == "COUNT"}
    leftover = next((r[1] for r in res if r[0] == "LEFTOVER"), "").strip()
    slides = next((int(r[1]) for r in res if r[0] == "SLIDES"), None)
    exported = [r[1] for r in res if r[0] == "EXPORTED"]
    report = {
        "out": out,
        "counts": counts,
        "not_found": [k for k in values if counts.get(ns.token % k, 0) == 0],
        "leftover": leftover,
        "slides": slides,
        "exported": exported,
    }
    ok = (not leftover or ns.allow_leftover) and (final_n is None or slides == final_n) \
        and len(exported) == len(exports)
    report["ok"] = ok
    print(json.dumps(report, ensure_ascii=False))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
