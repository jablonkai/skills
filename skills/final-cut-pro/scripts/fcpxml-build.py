#!/usr/bin/env python3
"""Build an FCPXML project from a JSON spec or a CSV shot list, then DTD-validate it.

  fcpxml-build.py spec.json --out cut.fcpxml [--library ~/Movies/X.fcpbundle] [--force]
  fcpxml-build.py --shots shots.csv --media-dir ./footage --project "Rough cut" \
      --rate 25 --out cut.fcpxml

Every media file is probed with ffprobe (duration, rate, size, audio, embedded
timecode), every time is exact rational math, and every value is placed on a frame
boundary of the sequence (clip starts too, in absolute asset time — FCP conforms them).
Anything snapped is reported under "adjusted". Missing media, a clip running past the
end of its media, and a transition without media handles are errors, because FCP
would import those as offline clips or drop them. See SKILL.md for the spec format.
"""
import argparse
import csv
import json
import os
import subprocess
import sys
import xml.etree.ElementTree as ET
from fractions import Fraction

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fcptime import (RATE_NAME, FD_TEXT, TimeError, fmt_time, frame_duration,  # noqa: E402
                     parse_user_time, snap, tc_to_time, time_to_tc, TC_RE)
from fcpxml_common import (TITLE_TEMPLATES, TRANSITIONS, FcpError, emit,  # noqa: E402
                           find_template, latest_version, media_url, save, xmllint)

class BuildError(Exception):
    pass


# ---------------------------------------------------------------- media

def ffprobe(path):
    try:
        r = subprocess.run(["ffprobe", "-v", "error", "-show_streams", "-show_format",
                            "-of", "json", path], capture_output=True, text=True, timeout=60)
    except FileNotFoundError:
        raise BuildError("ffprobe not found: brew install ffmpeg")
    if r.returncode != 0:
        raise BuildError(f"ffprobe cannot read {path}: {r.stderr.strip()}")
    return json.loads(r.stdout)


class Media:
    def __init__(self, path):
        self.path = os.path.abspath(os.path.expanduser(path))
        self.url = media_url(self.path)
        info = ffprobe(self.path)
        streams = info.get("streams", [])
        v = next((s for s in streams if s.get("codec_type") == "video"
                  and not s.get("disposition", {}).get("attached_pic")), None)
        a = next((s for s in streams if s.get("codec_type") == "audio"), None)
        if v is None and a is None:
            raise BuildError(f"{path}: no audio or video stream")
        self.has_video, self.has_audio = v is not None, a is not None
        fmt = info.get("format", {})
        if v is not None:
            rate = v.get("r_frame_rate") or v.get("avg_frame_rate") or "0/1"
            if rate in ("0/0", "0/1") or (v.get("nb_frames") in (None, "1") and
                                           not v.get("duration") and not fmt.get("duration")):
                raise BuildError(f"{path}: still image or unknown frame rate; stills are not "
                                 "supported by the builder (make a clip with ffmpeg -loop 1)")
            self.fd = frame_duration(rate)
            self.width, self.height = int(v["width"]), int(v["height"])
            nb = v.get("nb_frames")
            if nb and nb.isdigit() and int(nb) > 1:
                self.duration = int(nb) * self.fd
            else:
                d = Fraction(v.get("duration") or fmt.get("duration") or "0")
                self.duration = snap(d, self.fd, "floor")
        else:
            self.fd = None
            self.width = self.height = None
            sr = int(a.get("sample_rate", "48000"))
            d = Fraction(a.get("duration") or fmt.get("duration") or "0")
            self.duration = Fraction(round(d * sr), sr)
        if self.duration <= 0:
            raise BuildError(f"{path}: zero duration")
        self.channels = int(a.get("channels", 2)) if a else 0
        self.sample_rate = int(a.get("sample_rate", 48000)) if a else 0
        tc = None
        for src in [v or {}, fmt] + [s for s in streams if s.get("codec_type") == "data"]:
            tc = (src.get("tags") or {}).get("timecode") or tc
        self.tc = tc
        self.start = Fraction(0)
        if tc and self.fd and TC_RE.match(tc):
            self.start = tc_to_time(tc, self.fd)
        self.name = os.path.splitext(os.path.basename(self.path))[0]
        self.asset_id = None

    @property
    def end(self):
        return self.start + self.duration


# ---------------------------------------------------------------- builder

class Builder:
    def __init__(self, spec, args):
        self.spec = spec
        self.args = args
        self.adjusted = []
        self.warnings = []
        self.media = {}
        self.formats = {}
        self.effects = {}
        self.ids = 0
        self.ts = 0
        self.root = ET.Element("fcpxml", {"version": args.version})
        self.opts = ET.SubElement(self.root, "import-options")
        self.res = ET.SubElement(self.root, "resources")
        self.base = spec.get("media_dir") or args.media_dir or "."
        f = spec.get("format") or {}
        self.rate_given = f.get("rate") or args.rate
        self.seq_fd = frame_duration(self.rate_given) if self.rate_given else None
        self.size = (f.get("width"), f.get("height"))
        self.drop = bool(spec.get("drop_frame", False))

    def nid(self):
        self.ids += 1
        return f"r{self.ids}"

    def note(self, what, before, after, grid):
        if before != after:
            self.adjusted.append({"what": what, "requested": fmt_time(before),
                                  "used": fmt_time(after, grid), "grid": FD_TEXT.get(grid, fmt_time(grid))})

    # -- resources
    def format_id(self, fd, w, h):
        key = (fd, w, h)
        if key not in self.formats:
            attrs = {"id": self.nid(), "frameDuration": FD_TEXT.get(fd, fmt_time(fd)),
                     "width": str(w), "height": str(h)}
            suffix = RATE_NAME.get(fd)
            name = {(1920, 1080): "1080p", (1280, 720): "720p"}.get((w, h))
            if suffix and name:
                attrs["name"] = f"FFVideoFormat{name}{suffix}"
            elif suffix and (w, h) in ((3840, 2160), (4096, 2160), (1080, 1920), (1080, 1080)):
                attrs["name"] = f"FFVideoFormat{w}x{h}p{suffix}"
            el = ET.Element("format", attrs)
            self.res.insert(len(self.formats), el)
            self.formats[key] = attrs["id"]
        return self.formats[key]

    def get_media(self, path):
        p = path if os.path.isabs(os.path.expanduser(path)) else os.path.join(self.base, path)
        p = os.path.abspath(os.path.expanduser(p))
        if p not in self.media:
            try:
                m = Media(p)
            except FcpError as e:
                raise BuildError(str(e))
            attrs = {"id": self.nid(), "name": m.name, "start": fmt_time(m.start, m.fd),
                     "duration": fmt_time(m.duration, m.fd),
                     "hasVideo": "1" if m.has_video else "0",
                     "hasAudio": "1" if m.has_audio else "0"}
            if m.has_video:
                attrs["format"] = self.format_id(m.fd, m.width, m.height)
                attrs["videoSources"] = "1"
            if m.has_audio:
                attrs.update(audioSources="1", audioChannels=str(m.channels),
                             audioRate=str(m.sample_rate))
            a = ET.SubElement(self.res, "asset", attrs)
            ET.SubElement(a, "media-rep", {"kind": "original-media", "src": m.url})
            m.asset_id = attrs["id"]
            self.media[p] = m
        return self.media[p]

    def effect(self, key, table, what):
        if isinstance(key, dict):
            name, uid = key.get("name") or "Custom", key["uid"]
        elif key in table:
            name, uid = table[key]
        else:
            name, uid = find_template(key, what)
        if uid not in self.effects:
            self.effects[uid] = self.nid()
            ET.SubElement(self.res, "effect", {"id": self.effects[uid], "name": name, "uid": uid})
        return self.effects[uid]

    # -- times
    def src_time(self, value, m):
        """Source in/out: seconds from the first frame, 'Nf', or the clip's own
        source timecode (as FCP shows it; 00:00:00:00 at the first frame without one)."""
        fd = m.fd or self.seq_fd
        if isinstance(value, str) and TC_RE.match(value):
            return tc_to_time(value, fd)
        return m.start + parse_user_time(value, fd)

    def tl_time(self, value):
        """Timeline position: seconds from the start, or timeline timecode (tc_start-based)."""
        if isinstance(value, str) and TC_RE.match(value):
            return tc_to_time(value, self.seq_fd, True if self.drop else None) - self.tc_start
        return parse_user_time(value, self.seq_fd)

    def dur(self, value):
        return parse_user_time(value, self.seq_fd)

    # -- build
    def build(self):
        spec = self.spec
        spine_spec = spec.get("spine") or []
        if not spine_spec:
            raise BuildError("spec has no spine items")
        # Sequence format: given rate, else the first video clip's.
        first_video = None
        for it in spine_spec:
            if "clip" in it:
                m = self.get_media(it["clip"])
                if m.has_video:
                    first_video = m
                    break
        if self.seq_fd is None:
            if first_video is None:
                raise BuildError("no video clip on the spine: give format.rate")
            self.seq_fd = first_video.fd
        w = self.size[0] or (first_video.width if first_video else 1920)
        h = self.size[1] or (first_video.height if first_video else 1080)
        seq_fmt = self.format_id(self.seq_fd, int(w), int(h))
        if self.drop and self.seq_fd not in (Fraction(1001, 30000), Fraction(1001, 60000)):
            raise BuildError("drop_frame needs a 29.97 or 59.94 sequence")
        self.tc_start = Fraction(0)
        if spec.get("tc_start"):
            self.tc_start = tc_to_time(spec["tc_start"], self.seq_fd, True if self.drop else None)

        # Import options: never copy media unless asked, always show warnings.
        lib = self.args.library or spec.get("library")
        if lib:
            lp = os.path.abspath(os.path.expanduser(lib))
            if not lp.endswith(".fcpbundle"):
                raise BuildError("--library must be a .fcpbundle path")
            ET.SubElement(self.opts, "option", {"key": "library location",
                                                "value": "file://" + _quote(lp) + "/"})
        ET.SubElement(self.opts, "option", {"key": "copy assets",
                                            "value": "1" if self.args.copy_media else "0"})
        ET.SubElement(self.opts, "option", {"key": "suppress warnings", "value": "0"})

        library = ET.SubElement(self.root, "library")
        event = ET.SubElement(library, "event", {"name": spec.get("event") or self.args.event
                                                 or "FCP Skill"})
        project = ET.SubElement(event, "project", {"name": spec.get("project") or
                                                   self.args.project or "Untitled"})
        seq = ET.SubElement(project, "sequence", {
            "format": seq_fmt, "duration": "0s", "tcStart": fmt_time(self.tc_start, self.seq_fd),
            "tcFormat": "DF" if self.drop else "NDF", "audioLayout": "stereo",
            "audioRate": "48k"})
        spine = ET.SubElement(seq, "spine")

        pos = Fraction(0)          # timeline position (0 = sequence start)
        self.items = []            # (el, tl_in, tl_out, local_start, media|None)
        prev = None
        for i, it in enumerate(spine_spec):
            label = it.get("name") or it.get("clip") or f"item {i + 1}"
            if "clip" in it:
                el, m, start, d = self.clip_el(it, f"spine[{i}] {label}")
            elif "gap" in it:
                d = self.snap_dur(self.dur(it["gap"]), f"spine[{i}] gap")
                start = Fraction(3600)
                el = ET.Element("gap", {"name": it.get("name", "Gap"), "start": "3600s",
                                        "duration": fmt_time(d, self.seq_fd)})
                m = None
            elif "title" in it:
                t_ = it["title"] if isinstance(it["title"], dict) else {"text": it["title"]}
                d = self.snap_dur(self.dur(t_.get("duration", it.get("duration", 5))),
                                  f"spine[{i}] title")
                el = self.title_el(t_, d, None)
                start, m = Fraction(3600), None
            else:
                raise BuildError(f"spine[{i}]: needs clip, gap or title")
            tr = it.get("transition")
            if tr:
                if prev is None:
                    raise BuildError(f"spine[{i}]: a transition needs an item before it")
                self.transition(spine, tr, prev, (el, m, start, d), pos, f"spine[{i}]")
            el.set("offset", fmt_time(self.tc_start + pos, self.seq_fd))
            spine.append(el)
            self.items.append((el, pos, pos + d, start, m))
            self.item_markers(el, it, start, d, m)
            prev = (el, m, start, d)
            pos += d
        seq.set("duration", fmt_time(pos, self.seq_fd))
        self.total = pos

        for j, c in enumerate(spec.get("connected") or []):
            self.connected(c, f"connected[{j}]")
        for j, t_ in enumerate(spec.get("titles") or []):
            self.timeline_title(t_, f"titles[{j}]")
        for j, mk in enumerate(spec.get("markers") or []):
            self.timeline_marker(mk, f"markers[{j}]")
        # Formats first, then assets and effects (FCP's own order; any order validates).
        return self.root

    def snap_dur(self, d, what):
        s = snap(d, self.seq_fd)
        if s <= 0:
            raise BuildError(f"{what}: duration {fmt_time(d)} is under one frame")
        self.note(f"{what} duration", d, s, self.seq_fd)
        return s

    def clip_el(self, it, what):
        m = self.get_media(it["clip"])
        start = self.src_time(it.get("in", 0), m)
        # FCP conforms every clip start to the *sequence* frame grid in absolute asset
        # time; an off-grid start (e.g. a 29.97 clip in 25p) makes it split off a bogus
        # one-frame clip at the end of the timeline on import.
        s2 = snap(start, self.seq_fd, "ceil")
        self.note(f"{what} in", start, s2, self.seq_fd)
        start = s2
        if "out" in it:
            d = self.src_time(it["out"], m) - start
        elif "duration" in it:
            d = self.dur(it["duration"])
        else:
            d = m.end - start
        d = self.snap_dur(d, what)
        if start < m.start or start + d > m.end:
            raise BuildError(f"{what}: {fmt_time(start - m.start)}–{fmt_time(start - m.start + d)} "
                             f"is outside the media (0–{fmt_time(m.duration)} s from its first frame)")
        attrs = {"ref": m.asset_id, "name": it.get("name") or m.name,
                 "start": fmt_time(start, self.seq_fd), "duration": fmt_time(d, self.seq_fd),
                 "tcFormat": "DF" if self.drop else "NDF"}
        if it.get("audio") is False and m.has_video:
            attrs["srcEnable"] = "video"
        if it.get("video") is False and m.has_audio:
            attrs["srcEnable"] = "audio"
        if it.get("enabled") is False:
            attrs["enabled"] = "0"
        return ET.Element("asset-clip", attrs), m, start, d

    def transition(self, spine, tr, prev, cur, cut, what):
        tr = tr if isinstance(tr, dict) else {"duration": tr}
        d = self.dur(tr.get("duration", 1))
        n = round(d / self.seq_fd)
        n += n % 2   # centered on the cut: half must be whole frames
        d2 = max(2, n) * self.seq_fd
        self.note(f"{what} transition duration (even frames, centered)", d, d2, self.seq_fd)
        half = d2 / 2
        pel, pm, pstart, pd = prev
        cel, cm, cstart, cd = cur
        if pd < half or cd < half:
            raise BuildError(f"{what}: transition of {fmt_time(d2)} is longer than half an "
                             f"adjacent item")
        if pm is not None and pstart + pd + half > pm.end:
            raise BuildError(f"{what}: the previous clip needs {fmt_time(half)} of media after "
                             f"its out point for the transition (has {fmt_time(pm.end - pstart - pd)}); "
                             "move its out point earlier or shorten the transition")
        if cm is not None and cstart - half < cm.start:
            raise BuildError(f"{what}: this clip needs {fmt_time(half)} of media before its in "
                             f"point for the transition (has {fmt_time(cstart - cm.start)}); "
                             "move its in point later or shorten the transition")
        name, uid = TRANSITIONS.get(tr.get("type", "cross-dissolve"), (None, None))
        if uid is None:
            raise BuildError(f"{what}: unknown transition {tr.get('type')!r} "
                             f"(have {', '.join(TRANSITIONS)})")
        ref = self.effect(tr.get("type", "cross-dissolve"), TRANSITIONS, "transition")
        t_el = ET.SubElement(spine, "transition", {
            "name": name, "offset": fmt_time(self.tc_start + cut - half, self.seq_fd),
            "duration": fmt_time(d2, self.seq_fd)})
        ET.SubElement(t_el, "filter-video", {"ref": ref, "name": name})

    def marker_el(self, kind, name, local, note=None):
        attrs = {"start": fmt_time(local), "duration": fmt_time(self.seq_fd), "value": name}
        if kind == "chapter":
            attrs["posterOffset"] = "0s"
            tag = "chapter-marker"
        else:
            tag = "marker"
            if kind == "todo":
                attrs["completed"] = "0"
            elif kind != "marker":
                raise BuildError(f"marker kind {kind!r}: use marker, chapter or todo")
        if note:
            attrs["note"] = note
        return ET.Element(tag, attrs)

    def item_markers(self, el, it, start, d, m):
        """Per-item chapter/markers/keywords. Marker 'at' is relative to the item's first frame."""
        pending = []
        if it.get("chapter"):
            pending.append(self.marker_el("chapter", it["chapter"], start))
        for mk in it.get("markers") or []:
            rel = self.dur(mk.get("at", 0))
            if not 0 <= rel < d:
                raise BuildError(f"marker {mk.get('name')!r} at {fmt_time(rel)} is outside its "
                                 f"item ({fmt_time(d)} long)")
            local = start + snap(rel, self.seq_fd)
            pending.append(self.marker_el(mk.get("kind", "marker"), mk["name"], local,
                                          mk.get("note")))
        kws = it.get("keywords")
        if kws:
            kws = [k.strip() for k in (kws.split(",") if isinstance(kws, str) else kws) if k.strip()]
            pending.append(ET.Element("keyword", {"start": fmt_time(start), "duration":
                                                  fmt_time(d, self.seq_fd),
                                                  "value": ", ".join(kws)}))
        for p in pending:
            el.append(p)

    def owner_at(self, tl, what):
        if tl < 0 or tl > self.total:
            raise BuildError(f"{what}: {fmt_time(tl)} is outside the timeline "
                             f"(0–{fmt_time(self.total)})")
        for el, a, b, start, m in self.items:
            if a <= tl < b:
                return el, a, start
        el, a, b, start, m = self.items[-1]
        return el, a, start

    def connected(self, c, what):
        at = self.tl_time(c.get("at", 0))
        at2 = snap(at, self.seq_fd)
        self.note(f"{what} at", at, at2, self.seq_fd)
        el, m, start, d = self.clip_el(c, what)
        owner, tl_in, ostart = self.owner_at(at2, what)
        lane = int(c.get("lane", 1 if m.has_video else -1))
        if lane == 0:
            raise BuildError(f"{what}: lane 0 is the primary storyline; use a spine item")
        el.set("lane", str(lane))
        el.set("offset", fmt_time(ostart + (at2 - tl_in)))
        _insert_anchor(owner, el)
        self.items_lane_max = max(getattr(self, "items_lane_max", 0), lane)

    def title_el(self, t_, d, lane):
        text = t_.get("text", "")
        lines = text if isinstance(text, list) else str(text).split("\n")
        ref = self.effect(t_.get("template", "lower-third" if len(lines) > 1 else "basic"),
                          TITLE_TEMPLATES, "title")
        attrs = {"ref": ref, "name": t_.get("name") or " – ".join(lines)[:60]}
        if lane is not None:
            attrs["lane"] = str(lane)
        attrs.update({"offset": "0s", "start": "3600s", "duration": fmt_time(d, self.seq_fd)})
        el = ET.Element("title", attrs)
        style = {"font": t_.get("font", "Helvetica Neue"), "fontColor": t_.get("color", "1 1 1 1")}
        sizes = t_.get("size")
        ids = []
        for k, line in enumerate(lines):
            self.ts += 1
            tsid = f"ts{self.ts}"
            ids.append(tsid)
            tx = ET.SubElement(el, "text")
            ET.SubElement(tx, "text-style", {"ref": tsid}).text = line
        for k, tsid in enumerate(ids):
            sz = sizes[k] if isinstance(sizes, list) and k < len(sizes) else sizes
            s = dict(style)
            if sz:
                s["fontSize"] = str(sz)
            elif len(lines) > 1:
                s["fontSize"] = "50" if k == 0 else "36"
            else:
                s["fontSize"] = "63"
            d_el = ET.SubElement(el, "text-style-def", {"id": tsid})
            ET.SubElement(d_el, "text-style", s)
        return el

    def timeline_title(self, t_, what):
        at = self.tl_time(t_["at"])
        at2 = snap(at, self.seq_fd)
        self.note(f"{what} at", at, at2, self.seq_fd)
        d = self.snap_dur(self.dur(t_.get("duration", 4)), what)
        lane = int(t_.get("lane", getattr(self, "items_lane_max", 0) + 1))
        el = self.title_el(t_, d, lane)
        owner, tl_in, ostart = self.owner_at(at2, what)
        el.set("offset", fmt_time(ostart + (at2 - tl_in)))
        _insert_anchor(owner, el)
        if at2 + d > self.total:
            self.warnings.append(f"{what} runs past the end of the timeline")

    def timeline_marker(self, mk, what):
        at = self.tl_time(mk["at"])
        at2 = snap(at, self.seq_fd)
        self.note(f"{what} at", at, at2, self.seq_fd)
        owner, tl_in, ostart = self.owner_at(at2, what)
        owner.append(self.marker_el(mk.get("kind", "marker"), mk["name"],
                                    ostart + (at2 - tl_in), mk.get("note")))


def _quote(p):
    import urllib.parse
    return urllib.parse.quote(p)


def _insert_anchor(owner, el):
    """Anchored items go before the owner's markers and keywords (DTD order)."""
    for i, c in enumerate(list(owner)):
        if c.tag in ("marker", "chapter-marker", "keyword", "rating", "analysis-marker",
                     "filter-video", "filter-audio", "metadata", "audio-channel-source"):
            owner.insert(i, el)
            return
    owner.append(el)


# ---------------------------------------------------------------- CSV shot list

def spec_from_csv(path, args):
    """Columns (header row, case-insensitive): clip, in, out | duration, name, chapter,
    marker, keywords (';' or ','), transition (duration into this shot)."""
    spine = []
    with open(path, newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        raise BuildError(f"{path}: no rows")
    for n, row in enumerate(rows, 2):
        r = {(k or "").strip().lower(): (v or "").strip() for k, v in row.items()}
        if not r.get("clip"):
            if r.get("gap"):
                spine.append({"gap": r["gap"]})
                continue
            raise BuildError(f"{path}:{n}: empty clip column")
        it = {"clip": r["clip"]}
        for k in ("in", "out", "duration", "name", "chapter", "transition"):
            if r.get(k):
                it[k] = r[k]
        if r.get("keywords"):
            it["keywords"] = [k for k in r["keywords"].replace(";", ",").split(",") if k.strip()]
        if r.get("marker"):
            it["markers"] = [{"at": 0, "name": r["marker"]}]
        spine.append(it)
    return {"spine": spine}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("spec", nargs="?", help="JSON spec file ('-' for stdin)")
    ap.add_argument("--shots", help="CSV shot list instead of a spec")
    ap.add_argument("--media-dir", help="base folder for relative clip paths (default: cwd)")
    ap.add_argument("--project", help="project name (overrides spec)")
    ap.add_argument("--event", help="event name (default 'FCP Skill')")
    ap.add_argument("--rate", help="sequence rate (default: first video clip's)")
    ap.add_argument("--library", help="import into this .fcpbundle (skips FCP's library chooser)")
    ap.add_argument("--copy-media", action="store_true", help="let FCP copy media into the library")
    ap.add_argument("--version", help="FCPXML version (default: newest the installed FCP reads)")
    ap.add_argument("--out", required=True, help=".fcpxml (or .fcpxmld) to write")
    ap.add_argument("--force", action="store_true", help="replace --out if it exists")
    ap.add_argument("--no-validate", action="store_true", help="skip the DTD check")
    a = ap.parse_args()
    try:
        if a.shots:
            spec = spec_from_csv(a.shots, a)
        elif a.spec:
            spec = json.load(sys.stdin if a.spec == "-" else open(a.spec, encoding="utf-8"))
        else:
            ap.error("give a JSON spec or --shots CSV")
        for k in ("project", "event"):
            if getattr(a, k):
                spec[k] = getattr(a, k)
        a.version = a.version or spec.get("version") or latest_version()
        b = Builder(spec, a)
        root = b.build()
        path = save(root, a.out, a.force)
        result = {"ok": True, "file": path, "version": a.version,
                  "project": spec.get("project") or "Untitled",
                  "duration": fmt_time(b.total, b.seq_fd),
                  "timecode_out": time_to_tc(b.total, b.seq_fd, b.drop, b.tc_start),
                  "frame_duration": FD_TEXT.get(b.seq_fd), "clips": len(root.findall(".//asset-clip")),
                  "titles": len(root.findall(".//title")),
                  "markers": len(root.findall(".//marker")),
                  "chapters": len(root.findall(".//chapter-marker")),
                  "transitions": len(root.findall(".//transition")),
                  "media": len(b.media), "adjusted": b.adjusted, "warnings": b.warnings}
        if not a.no_validate:
            ok, msgs = xmllint(path, a.version)
            result["dtd_valid"] = ok
            if not ok:
                result.update(ok=False, dtd_errors=msgs[:20])
        emit(result)
        return 0 if result["ok"] else 1
    except (BuildError, FcpError, TimeError, KeyError, ValueError, OSError) as e:
        msg = str(e) if not isinstance(e, KeyError) else f"missing field {e}"
        emit({"ok": False, "error": msg})
        return 1


if __name__ == "__main__":
    sys.exit(main())
