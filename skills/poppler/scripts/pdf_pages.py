#!/usr/bin/env python3
"""Page operations with qpdf, each output checked (qpdf --check + page count).

  pdf_pages.py merge   OUT IN[:RANGE] IN[:RANGE] ...      # order as given
  pdf_pages.py select  IN OUT --pages RANGE                # keep, in range order
  pdf_pages.py select  IN OUT --every N [--start K]        # every N-th page from K
  pdf_pages.py remove  IN OUT --pages RANGE
  pdf_pages.py reorder IN OUT --order RANGE                # e.g. "3,1,2,4-z" or "z-1"
  pdf_pages.py rotate  IN OUT --angle +90 [--pages RANGE]  # +/- relative, bare = absolute
  pdf_pages.py split   IN OUTDIR [--size N] [--prefix NAME]

RANGE is qpdf syntax: 1,3,5-7  r1 (last)  z (last)  x (exclude)  :odd/:even.
Encrypted inputs: --password-file/--password-env (applies to every input).
Prints a JSON report; exit 0 on success, 2 on usage/tool errors, 4 on a bad password.
"""
import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pdfcommon import (add_password_args, check, compact, die, emit, page_count, parse_range,  # noqa: E402
                       qpdf, read_password)

RANGE_RE = re.compile(r"^(?:x?(?:r?\d+|z)(?:-(?:r?\d+|z))?,?)+(?::(?:odd|even))?$")


def split_spec(spec):
    """'file.pdf:1-3' -> ('file.pdf', '1-3'); a colon only counts when a range follows."""
    if ":" in spec:
        path, rng = spec.rsplit(":", 1)
        if rng in ("odd", "even"):
            path, rng2 = path.rsplit(":", 1) if ":" in path else (path, "1-z")
            return path, f"{rng2}:{rng}"
        if RANGE_RE.match(rng) and not os.path.exists(spec):
            return path, rng
    return spec, None


def guard(inp, out, in_place):
    if os.path.abspath(inp) == os.path.abspath(out) and not in_place:
        die("output would overwrite the input; choose another path or pass --in-place")


def finish(out, expected, password, extra=None):
    if not os.path.exists(out):
        die(f"qpdf wrote no output at {out}")
    # outputs are written unencrypted unless the input was encrypted (qpdf keeps it)
    got = page_count(out, password)
    res = {"output": out, "pages": got, "expected_pages": expected,
           "check": check(out, password)["status"]}
    if extra:
        res.update(extra)
    res["ok"] = got == expected and res["check"] != "errors"
    return res


def secret(password):
    return [f"--password={password}"] if password else None


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    m = sub.add_parser("merge")
    m.add_argument("out")
    m.add_argument("inputs", nargs="+", help="file.pdf or file.pdf:RANGE")
    m.add_argument("--fresh", action="store_true",
                   help="start from an empty PDF instead of the first input (drops its metadata/outline)")

    for name in ("select", "remove", "reorder", "rotate"):
        p = sub.add_parser(name)
        p.add_argument("inp")
        p.add_argument("out")
        p.add_argument("--in-place", action="store_true")
        if name in ("select", "remove", "rotate"):
            p.add_argument("--pages", required=name == "remove")
        if name == "select":
            p.add_argument("--every", type=int)
            p.add_argument("--start", type=int, default=1)
        if name == "reorder":
            p.add_argument("--order", required=True)
        if name == "rotate":
            p.add_argument("--angle", required=True, help="+90, -90, +180, or 0/90/180/270 absolute")

    s = sub.add_parser("split")
    s.add_argument("inp")
    s.add_argument("outdir")
    s.add_argument("--size", type=int, default=1, help="pages per output file")
    s.add_argument("--prefix", help="output name prefix (default: input stem)")

    for p in sub.choices.values():
        add_password_args(p)
    a = ap.parse_args()
    pw = read_password(a.password_file, a.password_env)

    if a.cmd == "merge":
        parts, expected = [], 0
        for spec in a.inputs:
            path, rng = split_spec(spec)
            if not os.path.exists(path):
                die(f"no such file: {path}")
            n = page_count(path, pw)
            pages = parse_range(rng, n) if rng else list(range(1, n + 1))
            expected += len(pages)
            parts.append((path, pages))
        if any(os.path.abspath(p) == os.path.abspath(a.out) for p, _ in parts):
            die("output would overwrite an input")
        args = ["--empty"] if a.fresh else ["@SECRET", parts[0][0]]
        args.append("--pages")
        for path, pages in parts:
            args += [path, "@SECRET", compact(pages)] if pw else [path, compact(pages)]
        args += ["--", a.out]
        proc = qpdf(args, secret(pw), fatal=True)  # one argfile fills every input's password slot
        report = finish(a.out, expected, pw, {"sources": [{"file": p, "pages": compact(pg)} for p, pg in parts]})

    elif a.cmd == "split":
        os.makedirs(a.outdir, exist_ok=True)
        n = page_count(a.inp, pw)
        stem = a.prefix or os.path.splitext(os.path.basename(a.inp))[0]
        proc = qpdf(["@SECRET", a.inp, f"--split-pages={a.size}",
                     os.path.join(a.outdir, f"{stem}-%d.pdf")], secret(pw), fatal=True)
        files = sorted(f for f in os.listdir(a.outdir) if f.startswith(stem + "-") and f.endswith(".pdf"))
        outs = [finish(os.path.join(a.outdir, f), page_count(os.path.join(a.outdir, f), pw), pw) for f in files]
        total = sum(o["pages"] for o in outs)
        report = {"outputs": outs, "files": len(outs), "pages_total": total, "input_pages": n,
                  "ok": total == n and all(o["ok"] for o in outs)}

    else:
        guard(a.inp, a.out, a.in_place)
        n = page_count(a.inp, pw)
        out = a.out + ".tmp.pdf" if a.in_place else a.out
        if a.cmd == "select":
            if a.every:
                if a.every < 1 or not 1 <= a.start <= n:
                    die("--every must be >= 1 and --start within the document")
                pages = list(range(a.start, n + 1, a.every))
            elif a.pages:
                pages = parse_range(a.pages, n)
            else:
                die("select needs --pages or --every")
            proc = qpdf(["@SECRET", a.inp, "--pages", ".", compact(pages), "--", out], secret(pw), fatal=True)
            extra = {"pages_kept": pages}
        elif a.cmd == "remove":
            drop = set(parse_range(a.pages, n))
            pages = [p for p in range(1, n + 1) if p not in drop]
            if not pages:
                die("that would remove every page")
            proc = qpdf(["@SECRET", a.inp, "--pages", ".", compact(pages), "--", out], secret(pw), fatal=True)
            extra = {"pages_removed": sorted(drop)}
        elif a.cmd == "reorder":
            pages = parse_range(a.order, n)
            missing = sorted(set(range(1, n + 1)) - set(pages))
            proc = qpdf(["@SECRET", a.inp, "--pages", ".", compact(pages), "--", out], secret(pw), fatal=True)
            extra = {"order": pages, "pages_dropped": missing}
        else:  # rotate
            if not re.fullmatch(r"[+-]?(0|90|180|270)", a.angle):
                die("--angle must be a multiple of 90, e.g. +90, -90, 180")
            pages = list(range(1, n + 1))
            target = parse_range(a.pages, n) if a.pages else pages
            proc = qpdf(["@SECRET", a.inp, f"--rotate={a.angle}:{compact(sorted(set(target)))}", out], secret(pw), fatal=True)
            extra = {"rotated_pages": sorted(set(target)), "angle": a.angle}
        report = finish(out, len(pages), pw, extra)
        if a.in_place and report["ok"]:
            os.replace(out, a.inp)
            report["output"] = a.inp

    if proc.returncode == 3:
        report["qpdf_warnings"] = proc.stderr.strip().splitlines()[:10]
    emit(report)
    sys.exit(0 if report["ok"] else 1)


if __name__ == "__main__":
    main()
