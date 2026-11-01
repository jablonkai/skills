---
name: filmcraft
description: 'Automate FilmCraft, the Premiere-style non-linear video editor, headless with filmcraft-cli: create projects and sequences from imported media, assemble rough cuts on V1 with B-roll on upper tracks, add titles and transitions, add markers from a list of timecodes, set in/out ranges, export with built-in or user presets (H.264, ProRes, DNxHR, MXF, image sequences, audio) at full or reduced scale, and inspect a .fcproj, all verified by an inspect read-back and ffprobe. Use when the user mentions FilmCraft, filmcraft-cli or a .fcproj file, or wants an edit or export done with FilmCraft: "assemble a rough cut from these clips in FilmCraft", "add markers from this timecode list to my .fcproj", "export the sequence as ProRes and a half-res H.264 preview", "what is on the timeline of this project". Not for DaVinci Resolve (davinci-resolve), Final Cut Pro or FCPXML (final-cut-pro), plain file-to-file transcodes with no FilmCraft project (handbrake, compressor), or Apple Motion templates (apple-motion).'
summary: "automate FilmCraft headless with filmcraft-cli — projects and sequences from imported media, rough cuts with B-roll, titles and transitions, markers from timecode lists, in/out ranges, preset or format exports (H.264, ProRes, DNxHR, image sequences) at full or reduced scale, inspect and ffprobe read-back verified"
category: video
compatibility: "Built for FilmCraft 0.16.0 and filmcraft-cli 0.16.0 on macOS; ffprobe (FFmpeg) for export checks. Pre-1.0, so command ids may change."
risk: medium
tags: [filmcraft, video-editing, nle, premiere, timeline, export, prores, headless]
license: GPL-3.0-only
metadata:
  version: "1.1.4"
  author: "Tamás Jablonkai"
---

# FilmCraft via filmcraft-cli

FilmCraft is a Premiere-style video editor. Every menu item, shortcut and timeline gesture
is a command in one engine registry (716 in 0.16.0). `filmcraft-cli` runs those commands
headless against a `.fcproj` and exports through the same render engine as the app. This
skill drives that route and checks every result by reading the project and the exports
back. Verified against **FilmCraft 0.16.0 / filmcraft-cli 0.16.0** on macOS. The software
is pre-1.0, so when a pinned command id or param fails, look it up instead of guessing.

```sh
command -v filmcraft-cli || ls ~/.local/bin/filmcraft-cli
filmcraft-cli --version
```

## Pick the route

| Task | Route |
|---|---|
| What's in this project / on this timeline? | `scripts/fc_verify.py show P.fcproj`, or `filmcraft-cli --project P inspect` |
| Build or edit (import, sequence, cuts, titles, transitions, markers, in/out) | `scripts/fc_run.py` with a step list, one session, saved to a new `.fcproj` |
| Markers from a list of timecodes | `scripts/fc_markers.py P list.csv > m.jsonl`, then `fc_run.py` |
| Export (one or several presets, scaled, ranges) | `scripts/fc_export.py P.fcproj --range entire OUT=PRESET[@SCALE]…` |
| Check the result | `fc_verify.py seq P spec.json` and the ffprobe lines `fc_export.py` prints |
| Is there a command for X? What are its params? | `filmcraft-cli commands <word>`, `filmcraft-cli describe <id>` |
| Which presets exist? | `filmcraft-cli export --list-presets [query]` |

The live app (`--bridge 127.0.0.1:PORT` to an app started with `filmcraft --control PORT`,
or `mcp --bridge`) is for when the user wants to watch the edit in the open app. This skill
works headless and doesn't start that channel. If the user runs it, it is theirs to stop,
and a project open in the app should be saved to a new file headless instead of edited
under it ([gotchas](references/gotchas.md#live-app-and-bridge)).

## Scripts

Python 3.9+, standard library only. Call them as `python3 $S/<script>` with
`S=<this skill>/scripts`. Each prints what it did and exits 1 when something failed.

- **`fc_run.py [--project IN.fcproj] --out OUT.fcproj [--overwrite] [--keep-going] STEPS`**
  runs `{"id","params","as"?}` steps (`.jsonl`, a `.json` list, or `-`) in **one engine
  session** and then saves with `file.saveAs`. A step with `"as": "cut"` keeps its result,
  and later params can say `"$cut.placed[1][0]"`. That is how a transition or title edit
  gets the clip id it needs. The script refuses to overwrite an existing `--out`. It saves
  nothing when a step fails, and at the end prints the saved sequence: tracks, clips in
  frames, transitions, markers and in/out.
- **`fc_markers.py P.fcproj LIST [--color Green] [--sequence-start 01:00:00:00]`** reads
  CSV or text with `HH:MM:SS:FF`, `;FF` drop-frame, `123f` or seconds, plus name, comment,
  colour and duration. It prints `markers.add` steps with exact frame-aligned ticks at the
  sequence's rate, maps everyday colour names to FilmCraft labels, and exits 1 if a time
  falls outside the sequence.
- **`fc_export.py P.fcproj [--sequence ID|NAME] [--range entire|inOut|S-E] [--overwrite] JOB…`**
  takes jobs of the form `out.mp4="YouTube 1080p Full HD"`, `"…@0.5"` or `out.mov=fmt:prores`
  and runs them all in one process. The range is always passed explicitly. The script
  refuses empty sequences, existing outputs and offline media, and ffprobes every output
  (codec, size, frame count against the range).
- **`fc_verify.py`** has three modes. `show P` prints a summary. `seq P spec.json` asserts
  the name, fps, size, duration, per-track clip order/start/frames, transitions, markers
  and in/out. `media FILE --codec --size --frames|--seconds` checks an exported file.

## Workflow

1. **Inspect first.** Run `fc_verify.py show P.fcproj`, and for the project tree
   `filmcraft-cli --project P inspect project`. For new media, run
   `filmcraft-cli probe clip.mov` to get its length, frame rate and size before you plan
   the cut.
2. **Look up anything you haven't used.** Run `filmcraft-cli commands marker` and
   `filmcraft-cli describe markers.add`. The param string is the contract: an unknown
   param or label fails the step. The ids most jobs need are in
   [commands.md](references/commands.md).
3. **Write the whole edit as one step list** and run it with `fc_run.py`, saving to a new
   `.fcproj`. Start with `file.newProject` (or `--project`), then `file.import`
   (`"as":"imp"`), `file.newSequence` with the delivery size and fps, `timeline.place
   items=$imp.items` for the cut, then titles, transitions and markers. Recipes are in
   [recipes.md](references/recipes.md).
4. **Read back.** Check the summary `fc_run.py` printed, or run `fc_verify.py seq` with a
   spec of what the user asked for: clip order, starts and lengths in frames, the
   transition at the right cut, the title on the right track, every marker at its frame.
   To see a frame, run `filmcraft-cli --project P render --seconds 1 --out f.png --scale 0.25`
   and look at the image.
5. **Export last** with `fc_export.py`, naming the range: `--range entire` unless the user
   asked for in/out or a span. Several deliverables go in one call. Exports render in real
   time or slower on a busy machine, so give the export its own command with a long
   timeout (10 minutes) instead of chaining it after the edit or polling a background job.
6. **Report** the project path, the timeline as the read-back showed it, each output with
   its codec, size and duration from ffprobe, and anything you could not verify.

## The traps that cost the most (details in [gotchas.md](references/gotchas.md))

- **`run` and `exec` without `--save`/`--save-as` keep nothing** and still exit 0. A
  failing line aborts the run and nothing is saved, including the lines before it. Use
  `fc_run.py`.
- **The default export range is in/out whenever in/out points are set**, with presets and
  `--format` alike. A 12 s timeline with in/out marked exports 8 s. Always pass `--range`.
- **The out point is inclusive.** In at 1 s and out at 9 s exports 201 frames at 25 fps,
  not 200.
- **A fixed-size preset ignores `--scale`.** `YouTube 1080p Full HD` with `--scale 0.5`
  still writes 1920×1080. Pass `width`/`height` (`fc_export.py` does this for `@0.5`) or
  use a Match Source preset or `--format`.
- **An empty sequence exports a 1-frame file with exit 0**, for example when the wrong
  sequence is active. The **last `file.newSequence` becomes the active sequence**, and
  `export` always takes the active one. `fc_export.py` refuses empty sequences and takes
  `--sequence`.
- **Export overwrites existing files and creates folders silently.** `fc_export.py`
  refuses to overwrite unless you pass `--overwrite`.
- **Commands need ids from earlier results** (`timeline.place` → clip ids for transitions
  and trims; `graphics.newText` → the title clip). A wrong id gives misleading errors such
  as `no edit point at the playhead`. Pass ids with `"as"` and `$refs`.
- **`markers.add` without a time drops the marker at the playhead (0)** and still
  succeeds. Its documented param is `time` in ticks (254016000000 per second).
  `fc_markers.py` converts timecodes for you.
- **Marker colours are FilmCraft label names** (Rose, Mango, Yellow, Green, Blue, …).
  Unknown names fail the step; since 0.16.0 `Red` and `Orange` alias Rose and Mango.
- **`graphics.newText` takes the lowest video track free over its span**, which is V3 when
  B-roll sits on V2. Its `track` param is a **0-based index** (1 = V2). A name such as
  `"V2"`, or an index past the last track, is silently ignored. It is point text starting at the frame centre: centre it with
  `graphics.align` (`hcenter`, then `vcenter`), or set `track` and `position` explicitly.
- **Offline media renders as placeholder frames.** `export` exits 1 and lists it in
  `offlineMedia`. Fix the paths instead of passing `--allow-offline`, unless the user
  accepts placeholders.

## References

- [references/cli.md](references/cli.md): subcommands, options, the `run` JSONL format,
  time units, exit codes, `probe`, `render`, `mcp`.
- [references/commands.md](references/commands.md): pinned command ids by task, with
  params, and how to look up the rest.
- [references/recipes.md](references/recipes.md): rough cut with title and dissolve,
  B-roll, markers and in/out ProRes, multi-preset delivery, image sequences, trims.
- [references/gotchas.md](references/gotchas.md): everything that fails silently, and the
  notes on the live app and bridge.
