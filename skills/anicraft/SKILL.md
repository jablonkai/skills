---
name: anicraft
description: 'Automate AniCraft (Flash/Animate-style 2D vector animation) headless with anicraft-cli: build .anicraft documents from a step spec (symbols, layers, classic, motion and shape tweens with easing and hints, motion paths, bone rigs with limits and poses, a camera, sounds, frame actions and ActionScript checked by script.check and test_movie); edit .anicraft files (swap text and bitmaps, add tweens); export MP4/WebM, GIF, PNG sequence, sprite sheet with JSON map, Lottie, HTML and SVG, with read-back and rendered frames. Use when the user mentions AniCraft, anicraft-cli or a .anicraft file, or wants Flash/Animate-style tweened or rigged vector animation: "animate a bouncing ball in AniCraft", "rig this arm with bones and make it wave", "add a stop() action and test the movie", "export this .anicraft as Lottie and a sprite sheet". Not for Cavalry (cavalry), After Effects-style comps (effectcraft), painted animation (rebelle), Godot scenes (godot), or turning existing video or images into GIFs (ffmpeg, imagemagick).'
summary: "automate AniCraft headless with anicraft-cli — tweened and rigged vector animation from a step spec with symbols, motion paths, easing, shape hints, bone rigs and a camera, frame actions checked by script.check and test_movie, MP4/GIF/PNG-sequence/sprite-sheet/Lottie/HTML export, info and render read-back verified"
category: motion-design
compatibility: "Built for AniCraft 0.2.0 (6dbf120) and anicraft-cli 0.2.0 on macOS, Python 3.9+, FFmpeg 7+ (ffmpeg for video export, ffprobe for checks); pre-1.0, so command ids may change."
risk: low
tags: [anicraft, animate, flash, 2d-animation, tween, bones, lottie, sprite-sheet, headless]
license: GPL-3.0-only
metadata:
  version: "1.0.0"
  author: "Tamás Jablonkai"
---

# AniCraft via anicraft-cli

AniCraft is a Flash/Animate-style vector animation app: a document (`.anicraft`, JSON)
holds scenes, each scene a timeline of layers, each layer keyframes with elements
(shapes, text, symbol instances, bitmaps). Every menu item is a command in one engine
registry (225 in 0.2.0); the same commands run in the app, from `anicraft-cli exec`/`run`,
and in a stateful `serve` session. This skill drives them **headless** — no window opens —
and checks every result by reading the document, the exports or rendered frames back.
Verified against **AniCraft 0.2.0** and **anicraft-cli 0.2.0** on macOS; pre-1.0, so when a
pinned id fails, look it up rather than guess.

```sh
command -v anicraft-cli || ls ~/.local/bin/anicraft-cli
anicraft-cli --version        # 0.2.0
```

## Pick the route

| Task | Route |
|---|---|
| New animation, or several edits to a file | `scripts/ac_build.py spec.json` — steps run in one `serve` session |
| One read-only query or one edit | `anicraft-cli exec F CMD '{json}' [--save out.anicraft]` |
| What a file holds (layers, keyframes, tweens, texts, bones, actions) | `scripts/ac_inspect.py F [--at 1 15 30]` |
| Find a command and its params | `scripts/ac_commands.py WORD…` / `--prefix motion.` / `--id camera.set` |
| Look at a frame | `anicraft-cli render F --out f.png --frame N [--scale S]` (1-based) |
| Frames / quick GIF | `anicraft-cli render-seq F --out-dir D --from A --to B`, `anicraft-cli gif F --out a.gif` |
| Deliverables (MP4/WebM, GIF, PNG seq, sprite sheet, Lottie, HTML, SVG, WAV) | `file.export_*` steps in the spec ([export.md](references/export.md)) |
| Check document or exports | `scripts/ac_verify.py doc|media|edges|sheet|lottie|html|seq|differ` |

`run F script.json` also exists, but its steps can't use ids returned by earlier steps
(bone, instance, layer ids) — prefer `ac_build.py`.

## Scripts

`S=<this skill>/scripts`; call as `python3 $S/<script>`. Python 3.9+, standard library
only, each with a full `--help`.

- **`ac_build.py SPEC.json [--overwrite] [--dry-run]`** — (`--overwrite` also replaces existing export files) `{"new": {width,height,fps,background}}`
  or `{"source": "in.anicraft"}`, `"out"`, `"steps"`, optional `"renders"`. Each step is
  `{"cmd", "params", "as", "on"}`: `"$name.key"` uses an earlier result, `"$layer:Name"` a
  layer id, `"on": {"layer", "frame"}` activates a layer and moves the playhead first.
  **Frames in the spec are 1-based** (converted for the engine). Stops at the first error
  and saves nothing; creates export folders; prints layers with 1-based keyframe ranges.
- **`ac_inspect.py F [--at N…]`** — stage, layers, keyframes (tween kind, motion keys,
  hints, poses, actions, scripts), elements (text content, symbol, bitmap names), library;
  with `--at`, camera, bone angles and motion positions at those frames.
- **`ac_verify.py`** prints JSON and exits 1 on a failed check, e.g.
  `doc F --size 1080x1080 --fps 30 --frames 30 --symbol Ball:graphic --motion-path Ball --motion-key Ball:scale_y@16=70 --camera 30:zoom=130 --bones 3 --limited 2 --poses Armature_1:3 --shape-tween Morph --hints Morph:2 --text Goodbye --bitmap new.png --action 24:stop --scripts-run --test-movie-ends 24`;
  `media out.mp4 --frames 30 --size 1080x1080 --fps 30`; `edges F --frames 1 15 30`; `sheet s.json --frames 60`;
  `lottie a.json --frames 24`; `html a.html`; `seq DIR --frames 60`; `differ a.png b.png`.
- **`ac_commands.py`** — filtered registry lookup. Never dump `anicraft-cli commands` (1800 lines).

## Workflow

1. **Inspect first**: `ac_inspect.py F` on any supplied file; look up every command you
   haven't used this session with `ac_commands.py` — params change between versions.
2. **Never write over the input.** `ac_build.py` refuses `out == source`; with `exec`,
   always `--save` to a new name.
3. **Build with a spec** — recipes in [recipes.md](references/recipes.md) (bouncing ball,
   camera move, bone rig, shape tween with hints, edit text/bitmap, stop action).
4. **Read back** with `ac_verify.py doc` and the per-export checks.
5. **Look at it**: render the telling frames (start, impact/extreme, end) and view **each**
   of them — a shape on the wrong keyframe, a rig bending the wrong way, the camera
   cropping an object at the end of a zoom only show up there. `ac_verify.py edges F
   --frames 1 15 30 [--color #rrggbb]` flags anything cut off by the frame edge.
6. **Report** outputs, the checks that passed, and anything you could not verify. Pass
   on every export's `notes`/`report` — e.g. Lottie in 0.2.0 leaves bitmap fills out, so
   a swapped logo is missing there even though the HTML and the document have it.

## The traps that cost the most (details in [gotchas.md](references/gotchas.md))

- **Two frame bases.** CLI flags (`render --frame`, `--from/--to`) and the timeline are
  1-based; command params (`frame`, export `from`/`to`), `info` and the file are 0-based:
  `exec … timeline.insert_keyframe '{"frame":10}'` makes a key at timeline frame 11.
  `ac_build.py` specs and `ac_verify.py`/`ac_inspect.py` output are 1-based throughout.
- **Drawing goes to the active layer at the playhead.** `draw.*`, `text.create`,
  `file.import`, `library.place` take no frame; `insert_blank_keyframe` does not move the
  playhead. Use `"on": {"layer": …, "frame": …}` on every drawing step.
- **The active layer moves.** `camera.add`, `layer.new`, `file.import`, `bone.add` make
  their layer active; commands without `layer` then hit that one. Pass `layer` explicitly.
- **Actions and scripts attach to the keyframe that *contains* the frame.** `stop` on the
  last frame needs `timeline.insert_keyframe` there first, or it lands on frame 1 and the
  movie stops immediately. `ac_verify.py doc --test-movie-ends N` catches it.
- **Motion tweens ease with `motion.set_ease`**; `timeline.set_easing` is for classic and
  shape tweens and fails on a motion tween ("this span has no tween").
- **Camera moves need keyframes on the camera layer**: `insert_keyframe` →
  `camera.set {frame}` → `timeline.create_tween` on the camera layer. Without the key,
  `camera.set` changes the whole span.
- **Colours are `#rrggbb` only**; overwriting a file needs `"confirm": true`; exports don't
  create folders (`ac_build.py` does); sprite sheets are capped at 16.7 Mpx — pass `scale`.
- **Ids are integers.** `bone.*` takes the bone id `bone.add` returned, not its name.

## References

- [references/cli.md](references/cli.md) — subcommands, `serve`/`mcp`, frame bases, plug-ins.
- [references/commands.md](references/commands.md) — pinned 0.2.0 ids by task, with key params.
- [references/recipes.md](references/recipes.md) — spec recipes for each workflow.
- [references/export.md](references/export.md) — export commands, outputs, and how to check them.
- [references/gotchas.md](references/gotchas.md) — silent failures and surprises.
- [references/security.md](references/security.md) — what runs, file access, why no live bridge.
