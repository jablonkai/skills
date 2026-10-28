#!/usr/bin/env python3
"""Apply a list of edits to a copy of a .deckcraft or .pptx presentation, headless.

  dk_edit.py IN OUT EDITS [--pdf OUT.pdf [--include-hidden]] [--overwrite] [--expect-titles T1 T2 …]

IN is never written: OUT must be a different path (.deckcraft or .pptx). EDITS is a JSON
file or an inline JSON list. Slide numbers are 1-based, as people say them, and each edit
sees the deck as the edits before it left it ("delete 4, then move the last to 2" works
as read). "last" (or -1, -2 …) counts from the end.

  {"op": "title",    "slide": 1, "text": "Q3 2026 Update"}
  {"op": "subtitle", "slide": 1, "text": "Operations team"}
  {"op": "body",     "slide": 3, "text": "first bullet\\n\\tsub-bullet\\nsecond"}
  {"op": "replace",  "find": "2025", "with": "2026", "matchCase": true}   (whole deck)
  {"op": "delete",   "slide": 4}                    ("slide": [4, 6] deletes several)
  {"op": "move",     "slide": "last", "to": 2}
  {"op": "duplicate","slide": 2}
  {"op": "new",      "at": 3, "layout": "titleAndContent", "title": "…", "body": "…"}
  {"op": "notes",    "slide": 2, "text": "Presenter notes"}
  {"op": "picture",  "slide": 5, "path": "new.jpg", "nth": 1}   (replace a picture in place)
  {"op": "add-picture", "slide": 5, "path": "logo.png", "rect": [760, 440, 160, 60]}
  {"op": "layout",   "slide": 2, "layout": "twoContent"}
  {"op": "hide",     "slide": 6, "hidden": true}
  {"op": "theme",    "name": "Harbor"}
  {"op": "cmd",      "slide": 2, "id": "format.size", "params": {"size": 28}}   (any command)

Shape ids are resolved with slide.inspect inside the same session, never guessed. Prints
the titles before and after as JSON and exits 1 if --expect-titles doesn't match the
saved file or the input file changed. The PDF leaves hidden slides out unless
--include-hidden; the report lists them under `hidden` and `pdf_pages`.
"""
import argparse
import json
import os
import sys

from dklib import Session, ToolError, fit, image_size, info, refuse_existing, sha256

TITLE = ("title", "ctrTitle")


def resolve(n, count):
    """1-based (or "last"/negative) slide number → 0-based index."""
    if n == "last":
        n = -1
    n = int(n)
    i = count + n if n < 0 else n - 1
    if not 0 <= i < count:
        raise ValueError("slide %s is out of range: the deck has %d slides" % (n, count))
    return i


def placeholder(shapes, role):
    if role == "title":
        hits = [s for s in shapes if s.get("placeholder") in TITLE]
    elif role == "subtitle":
        hits = [s for s in shapes if s.get("placeholder") == "subTitle"]
    else:
        hits = [s for s in shapes if s.get("kind") == "placeholder"
                and s.get("placeholder") in ("body", "obj", "subTitle", None)]
    if not hits:
        raise ValueError("no %s placeholder on this slide (kinds: %s)" % (
            role, [s.get("placeholder") or s.get("kind") for s in shapes]))
    return hits[0]["id"]


def apply(sess, e, base):
    op = e["op"]
    count = len(sess.deck()["slides"])
    idx = resolve(e["slide"], count) if "slide" in e and not isinstance(e["slide"], list) else None
    if idx is not None:
        sess.cmd("slide.go", {"index": idx})
    if op in ("title", "subtitle", "body"):
        sid = placeholder(sess.slide(idx)["shapes"], op)
        sess.cmd("text.set", {"id": sid, "text": e["text"]})
    elif op == "replace":
        params = {"text": e["find"], "with": e["with"]}
        for k in ("matchCase", "wholeWords"):
            if k in e:
                params[k] = e[k]
        return sess.cmd("text.replace", params)
    elif op == "delete":
        nums = e["slide"] if isinstance(e["slide"], list) else [e["slide"]]
        ids = [sess.deck()["slides"][resolve(n, count)]["id"] for n in nums]
        sess.cmd("slide.delete", {"ids": ids})
    elif op == "move":
        sess.cmd("slide.move", {"from": idx, "to": resolve(e["to"], count)})
    elif op == "duplicate":
        sess.cmd("slide.duplicate", {"index": idx})
    elif op == "new":
        params = {k: e[k] for k in ("layout", "title", "body") if k in e}
        if "at" in e:
            params["at"] = min(int(e["at"]) - 1, count) if e["at"] != "end" else count
        else:
            params["at"] = count
        sess.cmd("slide.new", params)
    elif op == "notes":
        sess.cmd("slide.notes", {"index": idx, "text": e["text"]})
    elif op in ("picture", "add-picture"):
        path = os.path.realpath(os.path.join(base, e["path"]))
        if op == "picture":
            pics = [s for s in sess.slide(idx)["shapes"] if s.get("kind") == "picture"]
            nth = int(e.get("nth", 1))
            if len(pics) < nth:
                raise ValueError("slide %s has %d pictures, no picture %d" % (e["slide"], len(pics), nth))
            sess.cmd("picture.change", {"path": path, "ids": [pics[nth - 1]["id"]]})
        else:
            params = {"path": path}
            if "rect" in e:
                params["rect"] = fit(image_size(path), e["rect"])
            sess.cmd("insert.picture", params)
    elif op == "layout":
        sess.cmd("slide.layout", {"layout": e["layout"], "index": idx})
    elif op == "hide":
        sess.cmd("slide.hide", {"index": idx, "hidden": e.get("hidden", True)})
    elif op == "theme":
        themes = sess.themes()
        if e["name"] not in themes:
            raise ValueError("unknown theme %r; DeckCraft has: %s" % (e["name"], ", ".join(themes)))
        sess.cmd("design.theme", {"name": e["name"]})
    elif op == "cmd":
        return sess.cmd(e["id"], e.get("params", {}))
    else:
        raise ValueError("unknown op %r" % op)
    return None


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input")
    ap.add_argument("output")
    ap.add_argument("edits", help="JSON file or inline JSON list")
    ap.add_argument("--pdf")
    ap.add_argument("--include-hidden", action="store_true", help="put hidden slides in the PDF too")
    ap.add_argument("--overwrite", action="store_true")
    ap.add_argument("--expect-titles", nargs="+")
    a = ap.parse_args()

    src, out = os.path.realpath(a.input), os.path.realpath(a.output)
    if src == out:
        sys.exit("OUT must differ from IN: the original is never written")
    if os.path.isfile(a.edits):
        edits, base = json.load(open(a.edits, encoding="utf-8")), os.path.dirname(os.path.realpath(a.edits))
    else:
        edits, base = json.loads(a.edits), os.getcwd()
    refuse_existing([a.output, a.pdf], a.overwrite)
    before_hash = sha256(src)
    before = [s["title"] for s in info(src)["slides"]]

    pics = {os.path.dirname(os.path.realpath(os.path.join(base, e["path"])))
            for e in edits if e.get("op") in ("picture", "add-picture")}
    writes = {os.path.dirname(out)} | ({os.path.dirname(os.path.realpath(a.pdf))} if a.pdf else set())
    for d in writes:
        os.makedirs(d, exist_ok=True)
    sess = Session({os.path.dirname(src)} | pics, writes)
    results = []
    try:
        sess.open(src)
        for n, e in enumerate(edits, 1):
            try:
                results.append(apply(sess, e, base))
            except (ToolError, ValueError, KeyError) as err:
                sys.exit("edit %d %s failed, nothing saved: %s" % (n, json.dumps(e), err))
        sess.save_as(out)
        if a.pdf:
            sess.export(a.pdf, **({"includeHidden": True} if a.include_hidden else {}))
    finally:
        sess.close()

    saved = info(out)["slides"]
    after = [s["title"] for s in saved]
    hidden = [s["index"] + 1 for s in saved if s.get("hidden")]
    problems = []
    if sha256(src) != before_hash:
        problems.append("the input file changed")
    if a.expect_titles and after != a.expect_titles:
        problems.append("titles %r, expected %r" % (after, a.expect_titles))
    report = {"input": a.input, "output": a.output, "pdf": a.pdf, "before": before, "after": after,
              "hidden": hidden,
              "pdf_pages": (len(saved) if a.include_hidden else len(saved) - len(hidden)) if a.pdf else None,
              "answers": [r for r in results if r is not None], "input_unchanged": sha256(src) == before_hash,
              "problems": problems}
    print(json.dumps(report, indent=1, ensure_ascii=False))
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
