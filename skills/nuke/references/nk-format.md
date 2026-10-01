# .nk script format

A `.nk` file is a TCL script that Nuke evaluates top to bottom. Hand-authored text
loads under Non-commercial through `nuke.scriptReadFile` (which `nk.py render` uses).
Everything below was verified on Nuke 17.1v2.

## Layout

```tcl
#! nuke
version 17.1 v2
Root {
 inputs 0
 first_frame 1001
 last_frame 1048
 format "1920 1080 0 0 1920 1080 1 comp_format"
}
Read {
 inputs 0
 file "/plates/sh010/bg.####.exr"
 first 1001
 last 1048
 origfirst 1001
 origlast 1048
 origset true
 before hold
 after hold
 name BG
}
Grade {
 white 0.8
 name BG_Grade
}
Write {
 file "/renders/sh010/comp.####.exr"
 file_type exr
 create_directories true
 name Write_EXR
}
```

- Each node is `Class {` followed by one `knob value` pair per line, then `}`. Values are
  TCL words: `bare`, `"quoted"` (with `\n`, `\"` and `\[` escapes), or `{braced list}`.
- `name` is optional. Nuke assigns `Grade1`, `Grade2`, …, but always name the nodes
  you will address from `--set`, `-X` or a hook.
- `#` lines are comments, but only as whole lines. A trailing `# …` after a node's `}`
  makes the load fail; `nk.py check` flags it. `version` is optional.
- Omitted knobs keep their defaults. Write only what you change.

## Wiring: the node stack

There are no explicit edges. Nuke keeps a stack of node outputs:

- A node with `inputs 0` (Read, Constant, ColorWheel, Roto, CheckerBoard2…) pushes a new output.
- A node without an `inputs` line takes 1 input: it pops the top of the stack, then pushes itself.
- `inputs N` pops N outputs. **The last-pushed output becomes input 0**, the one before
  it input 1, and so on.
- `set N_bg [stack 0]` names the current top of the stack. `push $N_bg` pushes it again,
  which is how one output feeds several nodes. `push 0` pushes an empty input.

**Merge2** has input 0 = **B** (background) and input 1 = **A** (foreground). To put A
over B, build the A branch first and the B branch last:

```tcl
Read { inputs 0  file "/fg.####.png"  name FG }
Premult { name FG_Premult }
Read { inputs 0  file "/bg.####.exr"  name BG }
Grade { white 0.6  name BG_Grade }
Merge2 { inputs 2  operation over  name Comp }
```

How the stack evolves:

1. After `Premult`, the stack holds `FG_Premult`.
2. After `Grade`, it holds `FG_Premult, BG_Grade`.
3. `Merge2` takes B = `BG_Grade` and A = `FG_Premult`.

One-line `{ … }` bodies like these parse fine, but multi-line bodies are easier to diff.

**Masks:** `inputs 1+1` means 1 main input plus a mask input. Push the mask first, then the
source:

```tcl
Roto { inputs 0  output alpha  name Matte }
Constant { inputs 0  color {0.18 0.18 0.18 1}  name Src }
Grade { inputs 1+1  white 4  maskChannelMask rgba.alpha  name MaskedGrade }
```

**Switch / Dissolve:** input 0 is again the last pushed. `which {{frame<1001}}` evaluates
to 1 on frames before 1001, which selects the *earlier-pushed* branch.

**Groups:** `Group { name G }` … nodes … `Output { }` … `end_group`. Nodes inside are
addressed as `G.Write1` (by `nk.py -X`, `--set` and `nuke.toNode`).

## Expressions and TCL

- To give a knob an expression, wrap each element in braces: `size {{input.height*0.04}}`
  (scalar), `center {{input.width/2} {input.height/2}}` (XY), `which {{frame<1001}}`.
- Use TCL in strings, escaped as `\[ … ]` inside a quoted `message`:
  - `\[frame]`
  - `\[format %04d \[frame]]`
  - `\[date %Y-%m-%d]`
  - `\[value root.name]`
  - `\[expr 1048-1001+1]`
- Write file names take `####` or `%04d` for the frame number.
- `[file dirname [value root.name]]` works in paths because `nk.py` sets `root.name` to the
  script path after loading.

## Knobs used most

| Node | Knobs |
|---|---|
| Root | `first_frame`, `last_frame`, `format "W H 0 0 W H 1 name"`, `fps` |
| Read | `file`, `first`/`last`, `origfirst`/`origlast`, `origset true`, `before`/`after` (`hold`, `loop`, `bounce`, `black`), `colorspace`, `premultiplied`, `raw` |
| Write | `file`, `file_type` (`exr`, `dpx`, `tiff`, `png`, `jpeg`, `mov`), `channels rgba`, `create_directories true`, `use_limit true` + `first`/`last`, `colorspace` |
| Write exr | `datatype "16 bit half"`/`"32 bit float"`, `compression "Zip (1 scanline)"`/`"PIZ Wavelet (32 scanlines)"`/`none` |
| Write mov | `mov64_codec` (`appr` ProRes 422 Proxy, `apch` 422 HQ, `ap4h` 4444, `mjpeg`, `rle`, `v210`; h264/mpeg4 are disabled in NC), `mov64_fps` |
| Grade | `blackpoint`, `whitepoint`, `black` (lift), `white` (gain), `multiply`, `add` (offset), `gamma`, `mix`, `maskChannelMask` |
| ColorCorrect | `saturation`, `contrast`, `gamma`, `gain`, `offset` |
| Merge2 | `operation` (`over`, `plus`, `screen`, `multiply`, `stencil`, `mask`, `under`, `max`, `min`, `difference`), `bbox` (`union`, `B`, `A`, `intersection`), `mix` |
| Transform | `translate {x y}`, `rotate`, `scale`, `center {x y}`, `filter` |
| Reformat | `type` (`"to format"`, `"to box"`, `scale`), `format "…"`, `box_width`/`box_height`/`box_fixed true`, `scale`, `resize` (`fit`, `fill`, `width`, `height`, `none`) |
| Crop | `box {x y r t}`, `reformat true`, `crop false` |
| Text | `message`, `font` (a file path — always set it), `size`, `xjustify`/`yjustify`, `box {x y r t}`, `color`, `leading` |
| Rectangle | `area {x y r t}`, `color {r g b a}`, `opacity`, `softness` |
| Constant | `color {r g b a}`, `format` |
| FrameHold | `first_frame` |
| TimeOffset | `time_offset` |
| Retime | `input.first`/`input.last`/`output.first`/`output.last`, `speed` |
| Blur | `size`, `channels` |
| Premult / Unpremult | — |

Coordinates are pixels with the origin at the **bottom-left** (y goes up).
