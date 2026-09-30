#!/usr/bin/env python3
"""Add titles (lower thirds) and markers to an existing FCPXML — typically one exported
from FCP — and write a NEW file that imports as a new project. The input is never
modified.

  fcpxml-edit.py in.fcpxmld --out out.fcpxml --titles lt.csv [--project "Rough cut"]
  fcpxml-edit.py in.fcpxml --out out.fcpxml \
      --title "01:00:12:00|4|Kovács Anna|Race director" \
      --marker "01:00:30:00|Chapter 2|chapter" --marker "95.5|fix audio|todo"

Titles CSV columns (header row, case-insensitive): at (or timecode/tc/time/start),
duration (default --duration, 4 s), the text as line1 [, line2 …], or text (lines separated by
' | '), or name/title then role/subtitle; template (lower-third | basic | any installed
title name, default lower-third for 2+ lines), lane (default: above everything
connected there). Markers CSV: at (or timecode …), name, kind (marker | chapter | todo), note.

'at' is timeline timecode (HH:MM:SS:FF, as FCP's timeline shows it, from the
sequence's tcStart) or seconds from the start of the timeline. Each title/marker is
attached to the primary-storyline item under that point, at the exact frame.

The output project gets a new name (default "<name> edited", --name to set) and loses
its uid, so FCP imports it next to the original instead of merging into it.
"""
import argparse
import csv
import os
import sys
import xml.etree.ElementTree as ET
from fractions import Fraction

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fcptime import TC_RE, TimeError, fmt_time, parse_user_time, snap, tc_to_time  # noqa: E402
from fcpxml_common import (TITLE_TEMPLATES, FcpError, Resources, emit,  # noqa: E402
                           find_template, insert_child, load, projects, save, t, walk, xmllint)

def template(name):
    if name in TITLE_TEMPLATES:
        return TITLE_TEMPLATES[name]
    return find_template(name, "title")


class Editor:
    def __init__(self, root, project, seq):
        self.root, self.project, self.seq = root, project, seq
        self.res = Resources(root)
        self.fd = self.res.frame_duration(seq.get("format"))
        if self.fd is None:
            raise FcpError("the sequence's format has no frameDuration")
        self.drop = seq.get("tcFormat") == "DF"
        self.tc_start = t(seq, "tcStart", "0s")
        self.total = t(seq, "duration", "0s")
        self.spine = seq.find("spine")
        self.primary = [it for it in walk(self.spine, self.res, Fraction(0), self.tc_start)
                        if it["depth"] == 0 and it["tag"] != "transition"]
        self.ts_n = 0
        self.added = []

    def at(self, value, what):
        v = str(value).strip()
        if TC_RE.match(v):
            tl = tc_to_time(v, self.fd, True if self.drop else None) - self.tc_start
        else:
            tl = parse_user_time(v, self.fd)
        s = snap(tl, self.fd)
        if s != tl:
            self.added.append({"adjusted": what, "requested": fmt_time(tl), "used": fmt_time(s)})
        if s < 0 or s >= self.total:
            raise FcpError(f"{what}: {v} is outside the timeline (0 – {float(self.total):.3f} s "
                           f"from {self.seq.get('tcStart', '0s')})")
        return s

    def owner(self, tl):
        for it in self.primary:
            if it["tl_in"] <= tl < it["tl_out"]:
                return it
        raise FcpError(f"no primary-storyline item at {fmt_time(tl)}")

    def lane_above(self, owner, tl, d):
        """First lane above every connected item overlapping [tl, tl+d) on this owner."""
        top = 0
        for it in walk(owner["el"], self.res, owner["tl_in"], owner["start"]):
            if it["lane"] > 0 and it["tl_in"] < tl + d and it["tl_out"] > tl:
                top = max(top, it["lane"])
        return top + 1

    def new_ts_id(self):
        used = {e.get("id") for e in self.root.iter() if e.get("id")}
        while True:
            self.ts_n += 1
            if f"ts{self.ts_n}" not in used:
                return f"ts{self.ts_n}"

    def add_title(self, at, dur, lines, tmpl=None, lane=None, font="Helvetica Neue", sizes=None):
        what = f"title {' | '.join(lines)!r}"
        tl = self.at(at, what)
        d = snap(parse_user_time(dur, self.fd), self.fd)
        if d <= 0:
            raise FcpError(f"{what}: duration under one frame")
        name, uid = template(tmpl or ("lower-third" if len(lines) > 1 else "basic"))
        ref = self.res.effect(uid, name)
        own = self.owner(tl)
        ln = int(lane) if lane else self.lane_above(own, tl, d)
        el = ET.Element("title", {"ref": ref, "lane": str(ln),
                                  "offset": fmt_time(own["start"] + (tl - own["tl_in"])),
                                  "name": " – ".join(lines)[:60], "start": "3600s",
                                  "duration": fmt_time(d)})
        ids = []
        for line in lines:
            tsid = self.new_ts_id()
            ids.append(tsid)
            tx = ET.SubElement(el, "text")
            ET.SubElement(tx, "text-style", {"ref": tsid}).text = line
        for k, tsid in enumerate(ids):
            size = (sizes[k] if sizes and k < len(sizes) else
                    ("50" if k == 0 else "36") if len(lines) > 1 else "63")
            sd = ET.SubElement(el, "text-style-def", {"id": tsid})
            ET.SubElement(sd, "text-style", {"font": font, "fontSize": str(size),
                                             "fontColor": "1 1 1 1"})
        insert_child(own["el"], el)
        self.added.append({"title": lines, "at": fmt_time(tl), "lane": ln,
                           "on": own["el"].get("name"), "duration": fmt_time(d)})
        if tl + d > self.total:
            self.added.append({"warning": f"{what} runs past the end of the timeline"})

    def add_marker(self, at, name, kind="marker", note=None):
        what = f"marker {name!r}"
        tl = self.at(at, what)
        own = self.owner(tl)
        attrs = {"start": fmt_time(own["start"] + (tl - own["tl_in"])),
                 "duration": fmt_time(self.fd), "value": name}
        if kind == "chapter":
            tag = "chapter-marker"
            attrs["posterOffset"] = "0s"
        elif kind in ("marker", "todo"):
            tag = "marker"
            if kind == "todo":
                attrs["completed"] = "0"
        else:
            raise FcpError(f"{what}: kind must be marker, chapter or todo")
        if note:
            attrs["note"] = note
        insert_child(own["el"], ET.Element(tag, attrs))
        self.added.append({"marker": name, "kind": kind, "at": fmt_time(tl),
                           "on": own["el"].get("name")})


AT_COLS = ("at", "timecode", "tc", "time", "start")
LINE_COLS = ("name", "title", "role", "subtitle")   # in display order


def first(row, keys):
    for k in keys:
        if row.get(k):
            return row[k]
    return None


def read_csv(path):
    with open(path, newline="", encoding="utf-8-sig") as f:
        return [{(k or "").strip().lower(): (v or "").strip() for k, v in r.items()}
                for r in csv.DictReader(f)]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("file", help="input .fcpxml or .fcpxmld (not modified)")
    ap.add_argument("--out", required=True)
    ap.add_argument("--project", help="project to edit when the file has several")
    ap.add_argument("--name", help="name of the output project (default '<name> edited')")
    ap.add_argument("--keep-name", action="store_true", help="keep the project name and uid")
    ap.add_argument("--titles", help="titles CSV")
    ap.add_argument("--markers", help="markers CSV")
    ap.add_argument("--title", action="append", default=[], metavar="AT|DUR|LINE1[|LINE2…]")
    ap.add_argument("--marker", action="append", default=[], metavar="AT|NAME[|KIND[|NOTE]]")
    ap.add_argument("--template", help="title template for every title without one")
    ap.add_argument("--duration", default="4", help="title length when a row gives none (default 4 s)")
    ap.add_argument("--library", help="add a 'library location' import option (.fcpbundle)")
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    try:
        if os.path.abspath(a.out) == os.path.abspath(a.file):
            raise FcpError("--out must differ from the input; the input is never modified")
        root = load(a.file)
        cands = [(ev, pr) for ev, pr in projects(root)
                 if pr.find("sequence") is not None and (not a.project or pr.get("name") == a.project)]
        if not cands:
            raise FcpError("no matching project in the file")
        if len(cands) > 1:
            raise FcpError("several projects: pass --project (" +
                           ", ".join(repr(p.get("name")) for _, p in cands) + ")")
        ev, pr = cands[0]
        # Keep only the project we edit: other projects would be re-imported as copies.
        for e2 in root.iter("event"):
            for p2 in list(e2.findall("project")):
                if p2 is not pr:
                    e2.remove(p2)
        ed = Editor(root, pr, pr.find("sequence"))
        for r in (read_csv(a.titles) if a.titles else []):
            at = first(r, AT_COLS)
            lines = [r[k] for k in sorted(k for k in r if k.startswith("line") and r[k])] or \
                    [x.strip() for x in r.get("text", "").split("|") if x.strip()] or \
                    [r[k] for k in LINE_COLS if r.get(k)]
            if not at or not lines:
                raise FcpError(f"titles CSV row needs a time ({'/'.join(AT_COLS)}) and text "
                               f"(line1, line2 … | text | {'/'.join(LINE_COLS)}): {r}")
            ed.add_title(at, r.get("duration") or a.duration, lines, r.get("template") or a.template,
                         r.get("lane") or None)
        for spec in a.title:
            parts = spec.split("|")
            if len(parts) < 3:
                raise FcpError(f"--title {spec!r}: use AT|DURATION|LINE1[|LINE2]")
            ed.add_title(parts[0], parts[1] or a.duration, parts[2:], a.template)
        for r in (read_csv(a.markers) if a.markers else []):
            at, name = first(r, AT_COLS), first(r, ("name", "marker", "title", "value"))
            if not at or not name:
                raise FcpError(f"markers CSV row needs a time ({'/'.join(AT_COLS)}) and a name: {r}")
            ed.add_marker(at, name, r.get("kind") or r.get("type") or "marker", r.get("note") or None)
        for spec in a.marker:
            parts = spec.split("|")
            ed.add_marker(parts[0], parts[1], parts[2] if len(parts) > 2 and parts[2] else "marker",
                          parts[3] if len(parts) > 3 else None)
        if not a.keep_name:
            pr.set("name", a.name or f"{pr.get('name')} edited")
            for k in ("uid", "modDate"):
                pr.attrib.pop(k, None)
        # Import options: reference media in place and show warnings.
        opts = root.find("import-options")
        if opts is None:
            opts = ET.Element("import-options")
            root.insert(0, opts)
        have = {o.get("key") for o in opts}
        lib = a.library
        if not lib:
            le = root.find("library")
            if le is not None and le.get("location"):
                lib = le.get("location")
        if lib and "library location" not in have:
            if not lib.startswith("file://"):
                import urllib.parse
                lib = "file://" + urllib.parse.quote(os.path.abspath(os.path.expanduser(lib))) + "/"
            ET.SubElement(opts, "option", {"key": "library location", "value": lib})
        if "copy assets" not in have:
            ET.SubElement(opts, "option", {"key": "copy assets", "value": "0"})
        if "suppress warnings" not in have:
            ET.SubElement(opts, "option", {"key": "suppress warnings", "value": "0"})
        path = save(root, a.out, a.force)
        ok, msgs = xmllint(path, root.get("version"))
        emit({"ok": ok, "file": path, "project": pr.get("name"), "event": ev,
              "added": ed.added, "dtd_valid": ok, **({"dtd_errors": msgs[:20]} if not ok else {})})
        return 0 if ok else 1
    except (FcpError, TimeError, KeyError, OSError) as e:
        emit({"ok": False, "error": str(e) if not isinstance(e, KeyError) else f"missing column {e}"})
        return 1


if __name__ == "__main__":
    sys.exit(main())
