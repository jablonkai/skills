#!/usr/bin/env python3
"""Check an FCPXML before (and after) importing it into Final Cut Pro.

  fcpxml-verify.py cut.fcpxml
  fcpxml-verify.py cut.fcpxml --duration 00:02:10:00 --chapters 5 --titles 3 --in-fcp

Always checked (each is something FCP silently drops, moves or re-times):
  dtd        valid against the installed FCP's DTD for the file's version
  media      every asset's file exists (offline clips otherwise)
  grid       offsets, durations and clip starts are whole sequence frames (FCP moves
             an off-grid start and splits off a one-frame clip at the end)
  spine      primary-storyline items are back to back (offset = previous offset + duration)
  handles    each transition has media under both halves (FCP drops it otherwise)
  storyline  connected storylines start their children at offset 0 (they drift otherwise)
  import     import-options: library location (else FCP asks which library)
Expectations (optional): --duration, --clips, --titles, --markers, --chapters,
--title-text (repeatable), --in-fcp (the project exists in running FCP with that duration).
Exit 0 only when every check passes; warnings don't fail.
"""
import argparse
import os
import sys
from fractions import Fraction

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fcptime import TC_RE, fmt_time, parse_time, parse_user_time, tc_to_time  # noqa: E402
from fcpxml_common import (FcpError, Resources, emit, list_projects, load, markers_of,  # noqa: E402
                           media_exists, projects, t, url_to_path, walk, xmllint)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("file")
    ap.add_argument("--project", help="check only this project")
    ap.add_argument("--duration", help="expected duration: seconds or HH:MM:SS:FF (length, not end tc)")
    ap.add_argument("--clips", type=int, help="expected number of clips (all lanes, titles excluded)")
    ap.add_argument("--titles", type=int)
    ap.add_argument("--markers", type=int, help="expected plain + to-do markers")
    ap.add_argument("--chapters", type=int)
    ap.add_argument("--title-text", action="append", default=[], help="a title must contain this")
    ap.add_argument("--in-fcp", action="store_true", help="compare with the project in running FCP")
    a = ap.parse_args()
    checks, warnings = [], []

    def check(name, ok, detail=None):
        checks.append({"check": name, "ok": bool(ok), **({"detail": detail} if detail else {})})

    try:
        root = load(a.file)
        version = root.get("version")
        ok, msgs = xmllint(a.file, version)
        check("dtd", ok, None if ok else msgs[:10])
        res = Resources(root)

        missing = []
        for asset in root.iter("asset"):
            for rep in asset.findall("media-rep"):
                src = rep.get("src", "")
                if src.startswith("file://") and not media_exists(src):
                    missing.append(url_to_path(src))
        check("media", not missing, missing[:20] or None)

        opts = {o.get("key"): o.get("value") for o in root.findall("import-options/option")}
        if "library location" not in opts:
            warnings.append("no 'library location' import option: FCP will ask which library to "
                            "import into (fcp-import.py --library answers it)")
        if opts.get("copy assets") == "1":
            warnings.append("copy assets=1: FCP copies every media file into the library")

        found = [(ev, pr) for ev, pr in projects(root) if pr.find("sequence") is not None
                 and (not a.project or pr.get("name") == a.project)]
        if not found:
            raise FcpError("no project to check" + (f" named {a.project!r}" if a.project else ""))
        tot = {"clips": 0, "titles": 0, "markers": 0, "chapters": 0}
        texts = []
        seqs = []
        for ev, pr in found:
            seq = pr.find("sequence")
            fd = res.frame_duration(seq.get("format"))
            if fd is None:
                check("format", False, f"{pr.get('name')}: sequence format has no frameDuration")
                continue
            tc_start = t(seq, "tcStart", "0s")
            spine = seq.find("spine")
            items = list(walk(spine, res, Fraction(0), tc_start))
            off_grid, gaps_in_spine, no_handles, drift = [], [], [], []
            for it in items:
                el = it["el"]
                name = el.get("name") or it["tag"]
                vals = [("offset", t(el, "offset")), ("duration", it["duration"])]
                if it["tag"] in ("asset-clip", "clip", "video", "audio", "mc-clip", "ref-clip",
                                 "sync-clip"):
                    vals.append(("start", it["start"]))
                for k, v in vals:
                    if (v / fd).denominator != 1:
                        off_grid.append(f"{name} {k}={fmt_time(v)} ({float(v / fd):.3f} frames)")
            # Primary storyline continuity and transitions.
            prim = [it for it in items if it["depth"] == 0]
            pos = tc_start
            clips_only = [it for it in prim if it["tag"] != "transition"]
            for it in clips_only:
                off = t(it["el"], "offset")
                if off != pos:
                    gaps_in_spine.append(f"{it['el'].get('name') or it['tag']} offset {fmt_time(off)}"
                                         f" but previous item ends at {fmt_time(pos)}")
                pos = off + it["duration"]
            for i, it in enumerate(prim):
                if it["tag"] != "transition":
                    continue
                half = it["duration"] / 2
                before = next((p for p in reversed(prim[:i]) if p["tag"] != "transition"), None)
                after = next((p for p in prim[i + 1:] if p["tag"] != "transition"), None)
                for side, clip, need in (("out", before, "after"), ("in", after, "before")):
                    if clip is None:
                        no_handles.append(f"transition at {fmt_time(it['tl_in'])} has no clip {need} it")
                        continue
                    asset = res.get(clip["el"].get("ref"))
                    if asset is None or asset.tag != "asset":
                        continue
                    a0 = t(asset, "start")
                    a1 = a0 + t(asset, "duration")
                    if side == "out" and clip["start"] + clip["duration"] + half > a1:
                        no_handles.append(f"{clip['el'].get('name')}: needs {fmt_time(half)} of media "
                                          f"after its out point for the transition")
                    if side == "in" and clip["start"] - half < a0:
                        no_handles.append(f"{clip['el'].get('name')}: needs {fmt_time(half)} of media "
                                          f"before its in point for the transition")
            for sl in spine.iter("spine"):
                if sl is spine:
                    continue
                kids = [k for k in sl if k.get("offset") is not None]
                if kids and t(kids[0], "offset") != 0:
                    drift.append(f"storyline {sl.get('name') or ''} starts its first child at "
                                 f"{kids[0].get('offset')}, not 0s")
            label = pr.get("name")
            check(f"grid [{label}]", not off_grid, off_grid[:20] or None)
            check(f"spine [{label}]", not gaps_in_spine, gaps_in_spine[:20] or None)
            check(f"handles [{label}]", not no_handles, no_handles or None)
            check(f"storyline [{label}]", not drift, drift or None)
            seq_dur = t(seq, "duration")
            if pos - tc_start != seq_dur:
                check(f"sequence duration [{label}]", False,
                      f"sequence says {fmt_time(seq_dur)}, spine adds up to {fmt_time(pos - tc_start)}")
            tot["clips"] += sum(1 for it in items if it["tag"] not in ("title", "gap", "transition"))
            tot["titles"] += sum(1 for it in items if it["tag"] == "title")
            texts += [" ".join("".join(x.itertext()) for x in it["el"].findall("text"))
                      for it in items if it["tag"] == "title"]
            for m in markers_of(spine, res, Fraction(0), tc_start):
                if m["tag"] == "chapter-marker":
                    tot["chapters"] += 1
                elif m["tag"] == "marker":
                    tot["markers"] += 1
            seqs.append((pr.get("name"), seq_dur, fd, seq.get("tcFormat") == "DF"))

        if a.duration:
            for name, dur, fd, drop in seqs:
                v = a.duration
                want = tc_to_time(v, fd, True if drop else None) if TC_RE.match(v) else \
                    parse_user_time(v, fd)
                check(f"duration [{name}]", dur == want, f"{fmt_time(dur)} vs expected {fmt_time(want)}"
                      if dur != want else None)
        for k in ("clips", "titles", "markers", "chapters"):
            want = getattr(a, k)
            if want is not None:
                check(k, tot[k] == want, f"{tot[k]} vs expected {want}" if tot[k] != want else None)
        for want in a.title_text:
            check(f"title text {want!r}", any(want in x for x in texts))
        if a.in_fcp:
            live = list_projects()
            for name, dur, fd, drop in seqs:
                hits = [p for p in live if p["project"] == name]
                if not hits:
                    check(f"in FCP [{name}]", False, "no open project with this name")
                    continue
                same = [p for p in hits if parse_time(p["duration"]) == dur]
                check(f"in FCP [{name}]", bool(same),
                      None if same else "durations in FCP: " + ", ".join(p["duration"] for p in hits)
                      + f" vs file {fmt_time(dur)}")
        ok = all(c["ok"] for c in checks)
        emit({"ok": ok, "file": a.file, "version": version, "counts": tot,
              "checks": checks, "warnings": warnings})
        return 0 if ok else 1
    except FcpError as e:
        emit({"ok": False, "error": str(e), "checks": checks})
        return 1


if __name__ == "__main__":
    sys.exit(main())
