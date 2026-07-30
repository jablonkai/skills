# Video Sequence Editor — strips, effects, transitions

Verified on Blender 5.2.0 LTS. `sequence_editor.sequences` was renamed to `.strips`, and
`new_effect()` changed signature — the old keyword names raise `TypeError`.

## Setup

```python
se = sc.sequence_editor_create()         # idempotent; returns the existing one
se.strips                                # top-level strips (StripsTopLevel)
se.strips_all                            # including strips nested in meta-strips
se.active_strip
```

A scene that has a sequence editor renders the **sequencer** instead of the 3D view whenever
`sc.render.use_sequencer` is True. If you are rendering 3D from the same scene:

```python
sc.render.use_sequencer = False
```

Otherwise an empty or partial sequencer silently produces an empty render.

## Signatures

```python
se.strips.new_effect(name, type, channel, frame_start, length=0,
                     input1=None, input2=None)
se.strips.new_image(name, filepath, channel, frame_start, fit_method='ORIGINAL')
se.strips.new_movie(name, filepath, channel, frame_start, fit_method='ORIGINAL')
se.strips.new_sound(name, filepath, channel, frame_start)
se.strips.new_scene(name, scene, channel, frame_start)
se.strips.new_meta(name, channel, frame_start)
```

Note `length=` (not `frame_end=`) and `input1=` / `input2=` (not `seq1=` / `seq2=`).

## Colour and text strips

```python
bg = se.strips.new_effect(name="BG", type="COLOR", channel=1,
                          frame_start=1, length=48)
bg.color = (0.05, 0.1, 0.2)

title = se.strips.new_effect(name="Title", type="TEXT", channel=2,
                             frame_start=1, length=48)
title.text = "HELLO"
title.font_size = 96
title.location = (0.5, 0.5)              # normalised screen space
title.anchor_x = "CENTER"                # LEFT | CENTER | RIGHT
title.anchor_y = "CENTER"                # TOP | CENTER | BOTTOM
title.use_shadow = True
title.use_box = False
title.color = (1, 1, 1, 1)
# title.font = bpy.data.fonts.load("/path/Inter.ttf")
```

Effect types: `ADD SUBTRACT ALPHA_OVER ALPHA_UNDER GAMMA_CROSS MULTIPLY OVER_DROP
WIPE GLOW TRANSFORM COLOR SPEED MULTICAM ADJUSTMENT GAUSSIAN_BLUR TEXT COLORMIX CROSS`.

## Media strips

```python
img = se.strips.new_image(name="Img", filepath="/abs/frame.png",
                          channel=3, frame_start=10, fit_method="FIT")
mov = se.strips.new_movie(name="Clip", filepath="/abs/clip.mp4",
                          channel=1, frame_start=1)
snd = se.strips.new_sound(name="Music", filepath="/abs/track.wav",
                          channel=5, frame_start=1)
```

`fit_method`: `SCALE_TO_FIT | SCALE_TO_FILL | FIT_TO_SCALE | ORIGINAL` (aliased as `FIT`).

An image strip covering several frames: extend `frame_final_duration` after creation, or
append more entries to `img.elements`.

## Transitions

Transitions take the two strips they blend as `input1` / `input2`:

```python
x = se.strips.new_effect(name="Cross", type="CROSS", channel=4,
                         frame_start=10, length=15,
                         input1=bg, input2=img)
x.input_1.name, x.input_2.name           # read back as input_1 / input_2
```

`GAMMA_CROSS` is the perceptually smoother cross-fade; `WIPE` exposes `transition_type`,
`direction`, `blur_width`.

## Timing, transform, blending

```python
s.frame_start                 # raw start
s.frame_final_start           # after handles
s.frame_final_duration
s.frame_offset_start          # trim in
s.frame_offset_end            # trim out
s.channel

s.transform.offset_x = 10
s.transform.offset_y = 0
s.transform.scale_x = 1.1
s.transform.scale_y = 1.1
s.transform.rotation = math.radians(3)
s.transform.origin = (0.5, 0.5)
s.crop.min_x = 0

s.blend_type = "ALPHA_OVER"   # REPLACE CROSS ALPHA_OVER ALPHA_UNDER ADD SUBTRACT
                              # MULTIPLY OVER_DROP GAMMA_CROSS COLOR_MIX
s.blend_alpha = 1.0
s.mute = False
s.lock = False
```

## Animating a strip

Strips are not IDs, so keyframes live on the **scene** with a path through the sequencer.
Use `strips_all` in the data path:

```python
fc = fcurve(sc, 'sequence_editor.strips_all["Title"].blend_alpha')
fc.keyframe_points.insert(1, 0.0)
fc.keyframe_points.insert(12, 1.0)
frame(6)
fc.evaluate(6)                # 0.432
```

The same pattern animates `transform.offset_x`, `transform.scale_x`, `color`, `font_size` —
anything with a data path under the strip.

## Meta-strips and modifiers

```python
meta = se.strips.new_meta(name="Act1", channel=6, frame_start=1)
# move strips into meta.strips to group them

mod = s.modifiers.new(name="CB", type="COLOR_BALANCE")
# BRIGHT_CONTRAST | COLOR_BALANCE | CURVES | HUE_CORRECT | MASK | TONEMAP | WHITE_BALANCE
```

## Rendering the sequence

```python
sc.render.use_sequencer = True
sc.frame_start, sc.frame_end = 1, 48
sc.render.image_settings.media_type = "VIDEO"
sc.render.image_settings.file_format = "FFMPEG"
sc.render.ffmpeg.format = "MPEG4"
sc.render.ffmpeg.codec = "H264"
sc.render.ffmpeg.audio_codec = "AAC"
sc.render.filepath = OUT + "/edit.mp4"
bpy.ops.render.render(animation=True)
```

Keep the edit in a **dedicated scene** so it does not hijack the 3D scene's renders: build
shots in one scene, add them to the VSE of another with `new_scene(...)`, and leave
`use_sequencer = False` on the 3D scene.
