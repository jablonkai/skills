#!/usr/bin/env python3
"""Redact phrases or patterns in a PDF for good, then prove it.

  pf_redact.py IN.pdf --out OUT.pdf (--find PHRASE… | --pattern NAME… | --page N…)
               [--case-sensitive] [--whole-words] [--overlay TEXT] [--fill COLOR]
               [--sanitize] [--fix-faux] [--overwrite]

Steps: audit the input (faux redactions that are already there are reported, and
with --fix-faux also truly redacted by each box's rectangle),
mark every match on every page, apply the marks, optionally remove hidden
information (--sanitize: metadata, attachments, scripts…), save to OUT, then read
OUT back. It passes only when each phrase is gone from the page text and from the
title/subject/keywords/bookmarks, and `audit` finds nothing. Prints JSON; exit 1
on a failed proof.

--pattern takes PdfCraft's Search & Redact patterns: phone, email, credit-card,
ssn, date. --page redacts whole pages.
"""

import argparse
import json
import os
import subprocess
import sys

import pflib

HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input")
    ap.add_argument("--out", required=True)
    ap.add_argument("--find", nargs="+", default=[], metavar="PHRASE")
    ap.add_argument("--pattern", nargs="+", default=[],
                    choices=["phone", "email", "credit-card", "ssn", "date"])
    ap.add_argument("--page", nargs="+", type=int, default=[], help="redact these whole pages")
    ap.add_argument("--case-sensitive", action="store_true")
    ap.add_argument("--whole-words", action="store_true")
    ap.add_argument("--overlay", help="text shown on each box")
    ap.add_argument("--fill", help="box colour, e.g. #000000 (default black)")
    ap.add_argument("--sanitize", action="store_true", help="also remove hidden information")
    ap.add_argument("--fix-faux", action="store_true",
                    help="also truly redact what the input's faux redactions (boxes over live "
                         "text) hide, by each box's rectangle")
    ap.add_argument("--overwrite", action="store_true", help="allow replacing an existing OUT")
    a = ap.parse_args()

    src, out = os.path.abspath(a.input), os.path.abspath(a.out)
    if not (a.find or a.pattern or a.page or a.fix_faux):
        ap.error("give --find, --pattern, --page or --fix-faux")
    if not os.path.exists(src):
        pflib.die(f"{a.input}: no such file")
    if src == out:
        pflib.die("--out must differ from the input: keep the original until the result is proven")
    if os.path.exists(out) and not a.overwrite:
        pflib.die(f"{a.out} exists (pass --overwrite to replace it)")

    before, _ = pflib.audit(src)

    common = {}
    if a.overlay:
        common["overlay"] = a.overlay
    if a.fill:
        common["fill"] = a.fill
    steps = [{"tool": "doc_open", "args": {"path": src}}]
    marks = []
    if a.find:
        # `words` reports matched_words per phrase and, unlike `find`, does not fail
        # the whole script when one phrase has no match.
        args = {"doc": 1, "words": a.find, **common}
        if a.case_sensitive:
            args["case_sensitive"] = True
        if a.whole_words:
            args["whole_words"] = True
        steps.append({"tool": "redact_mark", "args": args})
        marks.append("words")
    for name in a.pattern:
        steps.append({"tool": "redact_mark", "args": {"doc": 1, "pattern": name, **common}})
        marks.append(f"pattern {name}")
    if a.page:
        steps.append({"tool": "redact_mark",
                      "args": {"doc": 1, "whole_pages": True, "pages": a.page, **common}})
        marks.append(f"pages {a.page}")
    if a.fix_faux:
        # covered_text is the whole line the box touches, so redacting that string
        # would take out visible words too; the box's rect removes only what it hides.
        for f in before.get("findings", []):
            if f.get("kind") == "covered-text" and f.get("rect"):
                steps.append({"tool": "redact_mark",
                              "args": {"doc": 1, "page": f["page"], "rect": f["rect"], **common}})
                marks.append(f"faux box p{f['page']}")
    steps.append({"tool": "redact_apply", "args": {"doc": 1}})
    if a.sanitize:
        steps.append({"tool": "doc_remove_hidden", "args": {"doc": 1}})
    steps.append({"tool": "doc_save", "args": {"doc": 1, "path": out}})

    report = pflib.run_steps(steps)
    failed = pflib.step_failures(report)
    result = {"input": src, "output": out, "ok": False,
              "input_faux_redactions": [
                  {"page": f.get("page"), "kind": f.get("kind"), "covered_text": f.get("covered_text")}
                  for f in before.get("findings", [])]}
    if failed:
        result["error"] = failed[0].get("error", "a step was skipped")
        print(json.dumps(result, indent=2))
        sys.exit(1)

    mark_steps = [s for s in report["steps"] if s["tool"] == "redact_mark"]
    result["marks"] = {}
    for m, s in zip(marks, mark_steps):
        r = pflib.first(s["result"])
        if m == "words":
            for w in r.get("matched_words", []):
                result["marks"][f"find {w['word']!r}"] = w.get("marked")
        else:
            result["marks"][m] = r.get("marked")
    result["applied"] = next(pflib.first(s["result"]).get("applied")
                             for s in report["steps"] if s["tool"] == "redact_apply")
    zero = [m for m, n in result["marks"].items() if not n]

    verify = [sys.executable, os.path.join(HERE, "pf_verify.py"), out, "--audit-clean"]
    # Case-sensitive redaction leaves other casings on purpose, so only an exact
    # check applies; pf_verify's text checks ignore case.
    if not a.case_sensitive:
        for phrase in a.find:
            verify += ["--absent", phrase]
    p = subprocess.run(verify, capture_output=True, text=True)
    proof = json.loads(p.stdout)
    result["proof"] = proof["files"][out]
    if a.case_sensitive and a.find:
        texts = pflib.page_texts(out)
        left = {ph: [i for i, t in enumerate(texts, 1) if ph in t] for ph in a.find}
        left = {k: v for k, v in left.items() if v}
        result["proof"].append({"check": "absent (case-sensitive)", "ok": not left,
                                "detail": "absent" if not left else f"still on pages {left}"})
    result["ok"] = all(c["ok"] for c in result["proof"])
    # pf_verify reports "pages [] ['title', …]" when only metadata/bookmarks still match.
    if any(not c["ok"] and c["detail"].startswith("pages [] ") for c in result["proof"]):
        result["hint"] = ("the page text is clean but metadata or bookmarks still hold a phrase: "
                          "re-run with --sanitize, or fix that entry (doc_set_info / bookmark_rename)")
    if zero:
        result["warning"] = f"no matches for: {', '.join(zero)} — check the spelling or the text layer (OCR scans first)"
    print(json.dumps(result, indent=2))
    sys.exit(0 if result["ok"] else 1)


if __name__ == "__main__":
    main()
