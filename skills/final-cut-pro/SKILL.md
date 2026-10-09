---
name: final-cut-pro
description: 'Build and inspect Final Cut Pro timelines through FCPXML: generate a project from a clip list or CSV shot list (clips, gaps, B-roll, transitions, titles, lower thirds, markers, chapters, keywords) with exact rational-time math, validate it against the installed DTD, import it into FCP and confirm it via the read-only AppleScript model; add lower thirds or markers to an exported FCPXML; list clips with timeline and source in/out from .fcpxml/.fcpxmld. Use for any task or question that writes, reads or edits FCPXML, or converts FCPXML times, frames and timecode (drop frame too), e.g. "rough cut in Final Cut from these clips", "fcpxml from this shot list", "chapter markers in my FCP project", "lower thirds at these timecodes", "clips and in/out points in this fcpxml", "450 frames at 29.97 as FCPXML time", "bring my DaVinci Resolve timeline into Final Cut Pro", "vágd össze Final Cutban". Not for work inside DaVinci Resolve (davinci-resolve), Compressor or ffmpeg encodes, Motion templates, iMovie or Premiere XML.'
summary: "build and inspect Final Cut Pro timelines through FCPXML — rough cuts with gaps, connected clips, transitions, titles, markers and keywords, exact rational-time math, DTD validation, import with AppleScript read-back, FCPXML parsing and Resolve interchange"
category: video
risk: medium
tags:
    - final-cut-pro
    - fcpxml
    - video-editing
    - timecode
    - applescript
metadata:
  version: "1.0.0"
---

# Final Cut Pro via FCPXML

Final Cut Pro has **no editing API**. The skill writes FCPXML, checks it, and imports it
with `open`; FCP's AppleScript dictionary is **read-only** (libraries → events →
projects → sequence duration) and is used to confirm the import. Verified against
**Final Cut Pro 12.4** (bundle id `com.apple.FinalCut`, FCPXML 1.14) on macOS 27.

| Script | Does |
|---|---|
| `bash scripts/fcp.sh --check` | app, version, FCPXML versions, ffprobe/xmllint, Automation + Accessibility. Run first. |
| `python3 scripts/fcpxml-build.py SPEC.json --out X.fcpxml` | JSON spec (or `--shots CSV --media-dir DIR`) → validated FCPXML |
| `python3 scripts/fcpxml-verify.py X.fcpxml [--duration …]` | DTD, media, frame grid, handles, storyline, expectations, `--in-fcp` |
| `python3 scripts/fcp-import.py X.fcpxml [--library L]` | import, handle FCP's dialogs, confirm project + duration |
| `python3 scripts/fcpxml-edit.py IN --out OUT --titles/--markers …` | add lower thirds/markers to an existing FCPXML → new project |
| `python3 scripts/fcpxml-read.py IN [--json] [--all] [--expand]` | every clip: lane, timeline in/out, source in/out, media; titles; markers |
| `python3 scripts/fcptime.py rate/frames/time/tc/snap …` | exact time math; `--selftest` |
| `bash scripts/fcp.sh --projects` / `--templates [RE]` / `--dialogs` | what FCP has open; title/transition uids; what dialog is up |

Python is standard library only (system `python3` 3.9+); media probing needs
`ffprobe` (`brew install ffmpeg`). Every script prints JSON (read has a table mode)
and exits non-zero on failure — read the JSON, don't assume success.

## Workflow

1. `bash scripts/fcp.sh --check`. `automation: DENIED` → the user allows the terminal in
   System Settings ▸ Privacy & Security ▸ Automation ▸ Final Cut Pro. `accessibility:
   DENIED` → imports still work, but warning dialogs aren't read (ask the user to look).
2. **Build** from a spec, or **edit** an FCPXML the user exported
   (File ▸ Export XML… — FCP 12.4 writes a `.fcpxmld` bundle; exporting is a manual step).
3. `fcpxml-verify.py` with the expectations you know: `--duration` is a **length**
   (`512/25s`, `20.48` or `00:00:20:12`), not the end timecode; `--clips/--chapters/--titles`.
4. `fcp-import.py FILE --library ~/Movies/<Library>.fcpbundle`. It fails on any FCP
   import warning, a missing project or a duration mismatch. Ask before importing into
   a library the user works in; a separate library is the safe default.
5. Report what FCP shows (`fcp.sh --projects`), including any renamed project/event.

## The spec (fcpxml-build.py)

```json
{
  "project": "Rough cut", "event": "Race day", "library": "~/Movies/Race.fcpbundle",
  "media_dir": "footage", "format": {"rate": "25", "width": 1920, "height": 1080},
  "tc_start": "01:00:00:00", "drop_frame": false,
  "spine": [
    {"clip": "start.mov", "in": 2, "out": "00:00:09:12", "chapter": "Start",
     "keywords": ["start", "wide"], "markers": [{"at": 1.5, "name": "gun", "kind": "todo"}]},
    {"clip": "km10.mov", "in": "120f", "duration": 6, "transition": {"duration": 1}},
    {"gap": 2},
    {"title": {"text": "Finish", "duration": 3}}
  ],
  "connected": [{"clip": "drone.mov", "at": "01:00:04:00", "in": 3, "duration": 2.5}],
  "titles": [{"at": "01:00:01:00", "duration": 4, "text": ["Kovács Anna", "Race director"]}],
  "markers": [{"at": 12, "name": "Finish", "kind": "chapter"}]
}
```

- **Spine** items play back to back: `clip` (with `in`/`out` or `duration`; default the
  whole file), `gap`, or a standalone `title`. `transition` on an item is a cross
  dissolve *into* it, centred on the cut.
- **Source times** (`in`, `out`): seconds from the file's first frame, `"Nf"` frames,
  `"N/Ds"`, or the clip's **source timecode** as FCP shows it (embedded timecode when
  the file has one, else 00:00:00:00 at the first frame).
- **Timeline times** (`at`): timeline timecode (starting at `tc_start`) or seconds from
  the start. Per-item `markers[].at` is relative to that item's first frame.
- `connected` clips default to lane 1 (video) or −1 (audio-only); `audio: false` /
  `video: false` enable only one side. `titles` default to the lowest free lane above
  them; `template` is `lower-third` (default for 2+ lines), `basic`, any installed title
  name (`Formal`) or `Category/Name` when the name repeats (`Cinema/Bug`); `size`,
  `font`, `color` ("r g b a") are optional.
- Marker `kind`: `marker`, `chapter` (chapter marker), `todo` (to-do marker).
- `--library` adds the `library location` import option (no library chooser);
  media is referenced in place (`copy assets` 0) unless `--copy-media`.

Everything that isn't on a frame boundary is snapped and listed under `"adjusted"` in
the output — tell the user when something moved.

CSV shot list instead: header `clip,in,out,name,chapter,keywords,transition` (`duration`
instead of `out`; `gap` in a row with an empty clip):
`python3 scripts/fcpxml-build.py --shots shots.csv --media-dir footage --project "Rough cut" --library … --out cut.fcpxml`.

## Time rules FCP enforces

FCPXML times are rationals (`1001/30000s`); `fcptime.py` does all the math. Sequence
offsets start at `tcStart`. Every offset, duration **and clip start** must be a whole
number of *sequence* frames — even for a 29.97 clip in a 25p project, where the start
must sit on the 25p grid in absolute source time. An off-grid start doesn't fail the
import: FCP moves it and **splits off a one-frame clip at the end of the timeline**, so
the duration grows by a frame. `fcpxml-verify.py` catches this (`grid`).

```bash
python3 scripts/fcptime.py rate 29.97                       # 1001/30000s, DF-capable
python3 scripts/fcptime.py tc "00:59:58;28" --rate 29.97 --to-time
python3 scripts/fcptime.py frames 180180/30000s --rate 29.97   # 180
python3 scripts/fcptime.py snap 1.234 --rate 25              # 31/25s
```

## Editing an exported timeline

```bash
python3 scripts/fcpxml-edit.py "Race.fcpxmld" --project "Rough cut" --out lt.fcpxml \
  --titles lower-thirds.csv --marker "01:02:10:00|Aid station|chapter"
python3 scripts/fcp-import.py lt.fcpxml
```

Titles CSV: `at,duration,line1,line2,template` — `timecode`/`tc` for `at` and
`name`,`role` for the lines work too, so a list like `timecode,name,role` goes in as is. The output keeps only that project,
renames it `<name> edited` (or `--name`) and drops its uid, so FCP imports a new project
beside the original; the input file is never changed. Titles attach to the
primary-storyline item under `at`, above anything already connected there.

## Reading a timeline

`python3 scripts/fcpxml-read.py export.fcpxmld` prints, per project, each clip's lane,
timeline in/out (sequence timecode), source in/out (the media's timecode), duration and
file; then titles, markers (with kind) and keywords. `--json` for exact values
(`timeline_in` as FCPXML time, `*_s` seconds, `source_in_from_first_frame_s`),
`--all` adds gaps and transitions, `--expand` opens compound clips. Out points are
exclusive (in + duration). `~` after a timecode means the time falls between frames.

**From DaVinci Resolve:** export the timeline as FCPXML from Resolve (the
`davinci-resolve` skill can), then read or import it the same way; check it with
`fcpxml-verify.py` first (it names anything FCP would move or drop) and import with
`--library` if the file carries no library location. Not verified against a live
Resolve export.

## Pitfalls (details in references/gotchas.md)

- FCP drops a transition whose clips lack media handles (warning dialog) — the
  builder refuses those instead; shorten the transition or trim the clips.
- Missing media gives **no** warning, just an offline clip; build and verify check paths.
- Without a `library location` option FCP asks which library to import into;
  `fcp-import.py --library NAME` picks it from the list, otherwise the run stops.
- Importing a project whose name already exists in the same-named event is **silently
  discarded** (FCP merges a temporary `Event 2` and keeps the old project);
  `fcp-import.py` refuses that case — give the project a new name.
- Connected storylines count their children's offsets from 0; anything else drifts on
  every round trip. Export XML covers only what is selected in FCP's browser.

## Security and stop path

Nothing listens: the only app interactions are `open -b com.apple.FinalCut`, read-only
AppleScript `get`, and — during import — System Events reading FCP's own dialogs and
pressing their **buttons** (never keystrokes, so nothing can land in another app).
XML is built with ElementTree (no string splicing; titles with `<`, `&` or quotes are
safe) and parsed without fetching DTDs or entities. Media is referenced, never copied
or changed (unless `--copy-media`). Outputs are new files, replaced only with
`--force`; inputs are never rewritten. Every wait ends at `--timeout`/`FCP_TIMEOUT`
(120 s); the skill never quits FCP and never deletes libraries, events or projects —
cleaning a scratch library up is the user's call (close it in FCP, then delete it).

## References

- [references/fcpxml.md](references/fcpxml.md) — the element subset, attributes and order, effect uids, import options
- [references/time.md](references/time.md) — rational time, frame durations, timecode and drop frame
- [references/recipes.md](references/recipes.md) — raw FCPXML for what the scripts don't build
- [references/gotchas.md](references/gotchas.md) — every behaviour verified on FCP 12.4
