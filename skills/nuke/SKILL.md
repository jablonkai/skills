---
name: nuke
description: 'Build and render Nuke compositing scripts headless with Nuke Non-commercial (Foundry): author .nk comps as text (Read, Merge over, Grade, Transform, Roto, Text burn-ins, Write), fill plate-swap templates, set frame ranges, and render EXR/DPX/PNG/JPEG sequences or ProRes MOVs from the CLI, with each output checked frame by frame on disk. Knows the Non-commercial limits: 1920x1080 output cap, encrypted .nknc saves, the 10-node Python limit, and disabled h264. Use for "comp the foreground over this background plate in Nuke and render EXRs", "render this .nk", "batch render a folder of Nuke scripts", "make a Nuke slate / burn-in template", "swap the plate in this Nuke script", "why does my Nuke Write fail". Not for NLE timeline editing or grading (davinci-resolve, final-cut-pro), transcoding finished video (handbrake), motion-graphics animation (cavalry), 3D scenes and renders (blender), or plain image edits (gimp, krita, or ffmpeg).'
summary: "build and render Nuke comps headless with Nuke Non-commercial — .nk scripts authored as text, plate-swap templates, slates and burn-ins, Roto via Python hooks, EXR/DPX/PNG or ProRes renders with frame-count checks"
category: video
risk: low
tags:
    - nuke
    - compositing
    - vfx
    - exr
    - render
    - foundry
metadata:
  version: "1.0.0"
---

# Nuke (Non-commercial) via headless scripts

Nuke is driven by **one short-lived headless process per job**. There is no GUI, server
or bridge.

- Comps are written as **`.nk` text**, often filled from a template.
- [scripts/nk.py](scripts/nk.py) loads them with `nuke.scriptReadFile` inside
  `Nuke --nc -t`, renders each Write by name, and checks every expected frame on disk.

Verified against **Nuke 17.1v2 Non-commercial** (arm64, Python 3.11) on macOS 27.
Run `nk.py` with the system `python3`. It needs only the stdlib, plus `ffprobe` for the
output checks.

## Why the workflow looks like this

Non-commercial mode is headless-capable, but it imposes limits that break the obvious
approaches:

| Limit | Consequence for you |
|---|---|
| Must run with `--nc` (else exit 100, "No license") | `nk.py` adds it. Never call the Nuke binary without it. |
| Saves are **encrypted** `.nknc`; `-x` and `scriptOpen` refuse plain `.nk` | Keep the `.nk` **text** as the source of truth. Never "save" from Nuke over it. |
| Python gets only **10 Node objects** (`toNode`/`nodes.X()` then return `None`) | Don't build graphs node by node in Python. Write the `.nk` text and address nodes by name. |
| Writes may receive at most **1920×1080** | Scale bigger plates down before every Write. The templates do this. |
| **h264/mpeg4 disabled** | Use ProRes MOV (`mov64_codec apch`, the default) or image sequences. |

Details and symptoms: [references/gotchas.md](references/gotchas.md).

## Commands

```bash
NK=<this skill>/scripts/nk.py
python3 $NK find                       # Nuke binary + version, confirms --nc works
python3 $NK template --list            # bundled templates and their @@PLACEHOLDERS@@
python3 $NK template fg_over_bg -o comp.nk --plate FG=fg.1001.png --plate BG=bg.####.exr \
        --set OUT=renders/comp.####.exr --set GRADE_GAIN=0.8
python3 $NK check  comp.nk             # lint before rendering
python3 $NK render comp.nk [-F 1001-1048] [-X Write1,Write2] [--set Node.knob=value] [--py hook.py]
python3 $NK batch  shots/ -r           # every .nk/.nknc, one Nuke at a time, summary at the end
python3 $NK verify renders/comp.####.exr --frames 1001-1048 [--size 1920x1080]
```

- **Exit codes:**
  - 0: ok
  - 1: a Write failed or frames are missing
  - 2: usage or setup error
  - 3: licence error
- `--json` on `check`, `render`, `batch` and `verify` gives machine-readable output.
- `--licensed` must come **before** the subcommand (`nk.py --licensed render …`). It is
  only for commercially licensed installs.

What `render` does:

- Renders each enabled Write over the Root range, or over the Write's own `use_limit`
  range. `-F` overrides both.
- Creates output folders.
- Reports each Write's error by name, for example "h264 codecs are disabled…".
- Counts the frames on disk afterwards.
- Accepts encrypted `.nknc` too; their Writes are discovered inside Nuke.

## Workflow

1. **Inspect inputs.** Plate paths, frame ranges and sizes. `--plate` detects all three
   from `####`, `%04d` or any one frame of a sequence.
2. **Write the script.**
   - Start from a template when one fits:
     - `fg_over_bg`: FG premult over a graded BG, written as EXR.
     - `slate_burnin`: slate frame plus shot, version, date and frame burn-ins.
   - Otherwise hand-write `.nk` text. The wiring rules are short but unforgiving
     (input 0 is the *last pushed* node, and Merge2 input 0 is **B**). Read
     [references/nk-format.md](references/nk-format.md) before writing anything
     multi-input.
3. **`check`.** It catches:
   - unbalanced braces
   - missing plates
   - fonts that will render blank
   - disabled codecs
   - over-cap plates
4. **`render`**, then look at the result. Frame counts are verified automatically.
   - For correctness, sample pixels or make a contact sheet; see
     [references/recipes.md](references/recipes.md) §7.
   - To view an EXR, convert it to PNG first.
5. **Report** the script path, the output pattern, the frame count, the size and any NC
   compromise you made (downscaled plate, ProRes instead of h264).

## Writing `.nk` text — essentials

```tcl
Read { inputs 0  file "/p/fg.####.png"  first 1001  last 1048  origfirst 1001  origlast 1048  origset true  name FG }
Premult { name FG_Premult }
Read { inputs 0  file "/p/bg.####.exr"  first 1001  last 1048  origfirst 1001  origlast 1048  origset true  before hold  after hold  name BG }
Grade { white 0.8  gamma 1.1  name BG_Grade }
Merge2 { inputs 2  operation over  bbox B  name Comp }
Write { file "/r/comp.####.exr"  file_type exr  datatype "16 bit half"  create_directories true  name Write_EXR }
```

- Merge2 gets B = `BG_Grade` (pushed last) and A = `FG_Premult`. Premult is there
  because PNG alpha is straight.
- `#` comments only on their own line. A comment after a node's `}` breaks loading.
- Name every node you will address (`-X`, `--set`, hooks).
- **Text** nodes: always set `font "/System/Library/Fonts/Supplemental/Arial.ttf"`,
  `size`, `xjustify`, `yjustify` and `box`. The default font path is missing on macOS
  and the text silently renders blank.
  - Burn-in TCL: `\[frame]`, `\[format %04d \[frame]]`, `\[date %Y-%m-%d]`.
- **Expressions** go in braces per element: `size {{input.height*0.04}}`,
  `center {{input.width/2} {input.height/2}}`.
- **Roto** curves can't be written as text under NC. Add an empty `Roto` in the `.nk`
  and the shapes from `--py hook.py` (example in
  [references/python-api.md](references/python-api.md)).

## Templates

They live in [assets/templates/](assets/templates/) and use `@@KEY@@` /
`@@KEY:default@@` placeholders, which don't collide with Nuke's `{{expr}}`.

- `--plate KEY=PATH` fills `KEY`, `KEY_FIRST`, `KEY_LAST`, `KEY_SLATE` (first−1),
  `KEY_MID`, `KEY_W`, `KEY_H`, `KEY_FIT_W` and `KEY_FIT_H` (scaled to the 1080 cap).
- An unfilled placeholder is an error.
- A user-supplied template (any `.nk` with `@@…@@`) works the same way: pass its path
  instead of a bundled name.

## References

- [references/nk-format.md](references/nk-format.md): `.nk` syntax, stack wiring,
  Groups, expressions, and a table of common knobs.
- [references/recipes.md](references/recipes.md): comp, batch, slate, plate swap, Roto,
  over-cap plates, and pixel checks.
- [references/python-api.md](references/python-api.md): what Python can do under the
  10-node limit, plus load/save behaviour and hooks.
- [references/gotchas.md](references/gotchas.md): licence, NC limits, codecs, Text
  fonts, colour, and the security posture.
