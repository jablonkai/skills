---
name: video-review-notes
description: "Read and act on the review notes the user leaves on rendered cuts with their Video Review app (the desktop app that writes `VIDEO.comments.json` next to each render). Use this whenever the user says they watched a cut and left notes or comments, asks what their notes say, wants notes fixed in DaVinci Resolve, mentions a `.comments.json` file, or refers to notes, comments or marks they put on a video, in any language (the user often writes in Hungarian), even if they don't name the app or the file. Also use it before editing a reel that has a comments file next to its render, so open notes are not missed. Not for adding Resolve markers or general editing with no review notes (davinci-resolve)."
summary: "read and act on timecoded, scene and on-frame review notes left in the Video Review app — list open notes, extract the marked frames with the box or point drawn on, map them to Resolve timeline timecode, and mark them done atomically"
category: video
compatibility: "Built for the Video Review app 0.1.0 (github.com/jablonkai/video-review) with mpv and ffmpeg; Resolve steps use DaVinci Resolve Studio 21.1.0."
risk: low
tags:
  - video-review
  - review-notes
  - davinci-resolve
  - ffmpeg
allowed-tools: Bash, Read
argument-hint: "[render folder or video file]"
metadata:
  version: "1.0.4"
  author: "Tamás Jablonkai"
---

# Video review notes

The user reviews finished renders in their own Video Review app and leaves notes that are
tied to time (a single frame, a range, or whole scenes) and optionally to a place on the
picture (a point or a box). The app saves them next to the video. Your job is to turn
each note into a concrete, located request: *which frame(s), which part of the picture,
which clip on which Resolve timeline, and what the user wants changed*.

The app is open source: <https://github.com/jablonkai/video-review> (Rust/egui desktop app
for macOS, built on libmpv and ffmpeg; `brew install mpv ffmpeg`, then
`cargo run --release -- <folder-or-videos...>` or install the `.dmg` from
`tools/make-dmg.sh`). Check its README and `src/model.rs` there if the file format seems
to have changed. The app can also export notes itself as EDL (Resolve markers), FCPXML or
Markdown; point the user to that when they only want markers, not fixes.

Notes are often terse, half-typed, or in Hungarian. A note is only as clear as the frame it
points at, so always look at the frame before deciding what a note means.

## Where the notes are

- `<video>.comments.json` next to each render (usually the project's render folder).
- `<video>.scenes.json` next to it holds the scene cuts (seconds) the app detected.
  It is only valid for the file it was made from (size and mtime); after a re-render,
  `list` shows no scene number until the app has opened the video and detected again.
- The app re-reads the file every 4 seconds, so a change you make shows up in the
  app without a restart.

## File format

```json
{
  "video": "reel.mp4",
  "fps": 29.97,
  "comments": [
    {"text": "...", "t_in": 62.622, "t_out": 76.074,
     "area": {"x": 0.40, "y": 0.48, "w": 0.11, "h": 0.14},
     "scenes": null, "frame_in": 1876, "frame_out": 2279,
     "done": false, "id": "91d05bc5", "created": "2026-10-16T00:06:24"}
  ]
}
```

How to read each field:

| Field | Meaning |
|---|---|
| `t_in`, `t_out: null` | A **moment**: exactly one frame, `frame_in`. The note is about that single frame (a flash frame, a bad transition frame, a still to check). |
| `t_in`, `t_out` | A **range**: frames `frame_in` up to but not including `frame_out`. |
| `scenes: [a, b]` | The range was picked as whole scenes `a..b` (1-based, from `scenes.json`). The note is about those shots as units, e.g. a shot to swap, trim, or regrade. |
| `area: null` | The whole picture. |
| `area` with `w = h = 0` | A **point** at `x, y` (fractions of picture width/height from the top-left). Something specific there: a face, a logo, a bib number, an artifact. |
| `area` with `w, h` | A **box**: the region `x..x+w`, `y..y+h`. |
| `done` | The user (or you) already handled it. Skip unless asked. |
| `frame_in/out` | Frame numbers at the file's `fps`, counted from 0. They are derived from `t_in/t_out` with `floor(t * fps + 0.001)`; use them rather than seconds when you talk to Resolve. |

The app numbers notes 1, 2, 3… in time order **including done ones**. Use the same numbers
when you talk to the user ("#2"), because that is what they see in the app.

## Workflow

1. **List the open notes.**
   ```bash
   S=scripts   # relative to this skill's directory
   python3 $S/notes.py list "<render folder>"
   ```
   This prints every open note with its number, kind, timecode, frames, scene and area.
   Add `--all` to include done notes and `--json` for machine-readable output.

2. **Look at every note's frame before you interpret it.**
   ```bash
   python3 $S/notes.py frames "<video>" --out <scratch dir>
   ```
   This writes JPEGs of the exact frame or frames, with the note's box or point drawn in
   yellow. A moment gives you one frame; a range gives you the first, middle and last frame.
   When the user asks about one note or a few, add `--id <id>` (repeatable; ids come from
   `list`) so you only extract those instead of every open note.
   Read the images. The text alone ("not good here", "fffff") rarely says what is wrong, and
   the picture usually does: a soft shot, a jump cut, a face cut off by a title, a bad
   colour match.

3. **Locate it in Resolve** when a fix is needed (see below).

4. **Report back in the user's language** (usually Hungarian), one line per note:
   number, where it is, what you think it asks for, and what you will do or did.
   For example: "#2 (01:02:16–01:15:29, a box on the runner's legs): the shot jitters
   here; I'll stabilise it."

5. **After fixing**, mark the note done:
   ```bash
   python3 $S/notes.py done "<video>" <id>
   ```
   This changes only that note's `done` field, writes the file atomically, and keeps
   the format the app writes. The app then shows the note as done. Don't mark a note
   done that you only interpreted and didn't fix.

## Mapping to the Resolve timeline

Renders are usually made from a whole timeline, so render frame 0 is the timeline's first
frame. Get the timeline's start timecode and frame rate from Resolve (the
`davinci-resolve` MCP: timeline settings and start timecode). Then:

```bash
python3 $S/notes.py list "<video>" \
  --timeline-fps 24 --timeline-start 01:00:00:00
```

This adds `timeline: HH:MM:SS:FF` to each note. Then find the clip that covers that
timeline frame: list the timeline items and pick the one whose start ≤ frame < end, on the
top video track that has content there.

Watch out for these:
- **The render and timeline rates can differ** (e.g. a 29.97 fps render of a 24 fps
  timeline), so a frame number is not the same on both. The script converts with
  `round(frame × timeline_fps / render_fps)`. Say so when the rates differ, because the
  match is then only accurate to about a frame.
- **Partial renders.** If the render used In/Out marks instead of the whole timeline,
  ask for (or find) the In point and use it as `--timeline-start`.
- **Drop-frame.** The script prints non-drop-frame timecode, which is what Resolve shows
  for 29.97 unless the project uses drop-frame.

## When a note is unclear

Some notes are keyboard tests or placeholders ("fffff", "dfdfd"), and some break off
mid-word. If the frame doesn't make the intent obvious, ask, and show what
you can see: "#1 at 00:00:25:10 only says 'fffff' and a cut-off word. The frame is a runner passing the
tent. Is that a test, or is something wrong with this shot?" A guessed fix is worse than
a question, because it changes the cut in a way the user didn't ask for.

## Rules that protect the user's notes

- Never delete or rewrite a note's `text`, and never remove notes. They are the user's
  record. The only field you change is `done`.
- Change `done` only through `notes.py done`. It writes atomically (a temp file, then a
  rename), as the app does, so the app never reads a half-written file.
- Don't add new notes on the user's behalf unless asked. If you have findings of your
  own, report them in chat.
