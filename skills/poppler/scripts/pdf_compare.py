#!/usr/bin/env python3
"""Compare two PDFs page by page: count, sizes and whitespace-normalised text.

  pdf_compare.py A.pdf B.pdf [--pages-a RANGE] [--pages-b RANGE] [--no-sizes] [--ignore-rotation]

Use it as the oracle after any page operation: e.g. a merge of a.pdf + b.pdf:1-3 should
equal `--pages-a 5-7` of the output against `--pages-b 1-3` of b.pdf. Rotation is
reported on its own ("rotation"); after a deliberate rotate pass --ignore-rotation.
Passwords for either side: --password-file/--password-env (tried on both).
Exit 0 identical, 1 different, 2 error.
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pdfcommon import (add_password_args, emit, norm, page_count, page_sizes, parse_range,  # noqa: E402
                       read_password, readable, text_pages)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("a")
    ap.add_argument("b")
    ap.add_argument("--pages-a")
    ap.add_argument("--pages-b")
    ap.add_argument("--no-sizes", action="store_true", help="ignore page size differences")
    ap.add_argument("--ignore-rotation", action="store_true", help="ignore /Rotate differences")
    add_password_args(ap)
    args = ap.parse_args()
    pw = read_password(args.password_file, args.password_env)

    with readable(args.a, pw) as pa, readable(args.b, pw) as pb:
        na, nb = page_count(pa), page_count(pb)
        sel_a = parse_range(args.pages_a, na) if args.pages_a else list(range(1, na + 1))
        sel_b = parse_range(args.pages_b, nb) if args.pages_b else list(range(1, nb + 1))
        sa, sb = page_sizes(pa), page_sizes(pb)
        ta, tb = text_pages(pa, sel_a, "plain"), text_pages(pb, sel_b, "plain")

    diffs = []
    if len(sel_a) != len(sel_b):
        diffs.append({"what": "page count", "a": len(sel_a), "b": len(sel_b)})
    for i, (p, q) in enumerate(zip(sel_a, sel_b)):
        if not args.no_sizes:
            wa, ha, _ = sa[p - 1]
            wb, hb, _ = sb[q - 1]
            if abs(wa - wb) > 0.5 or abs(ha - hb) > 0.5:
                diffs.append({"what": "size", "page_a": p, "page_b": q, "a": [wa, ha], "b": [wb, hb]})
        if not args.ignore_rotation and sa[p - 1][2] != sb[q - 1][2]:
            diffs.append({"what": "rotation", "page_a": p, "page_b": q, "a": sa[p - 1][2], "b": sb[q - 1][2]})
        if norm(ta[i]) != norm(tb[i]):
            diffs.append({"what": "text", "page_a": p, "page_b": q,
                          "a": norm(ta[i])[:120], "b": norm(tb[i])[:120]})
    emit({"identical": not diffs, "pages_compared": min(len(sel_a), len(sel_b)),
          "differences": diffs[:50], "a": args.a, "b": args.b})
    sys.exit(0 if not diffs else 1)


if __name__ == "__main__":
    main()
