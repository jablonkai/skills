# Rendering — engines, passes, compositor, output

Verified on Blender 5.2.0 LTS.

## Engines

```python
sc.render.engine = "BLENDER_EEVEE"      # NOT "BLENDER_EEVEE_NEXT" (that was 4.2–4.5)
sc.render.engine = "CYCLES"
sc.render.engine = "BLENDER_WORKBENCH"
```

**Do not gate on the enum.** Cycles is an add-on, so introspection reports only
`['BLENDER_EEVEE']` while the assignment above works fine. Assign and catch.

### EEVEE

```python
ee = sc.eevee
ee.taa_render_samples = 32        # final samples
ee.taa_samples = 8                # viewport
ee.use_shadows = True
ee.use_raytracing = False         # screen-space GI/reflections/refraction
ee.use_volumetric_shadows = True
ee.shadow_ray_count = 1
```

`use_bloom` and `use_gtao` are gone — bloom is a compositor Glare node now, and ambient
occlusion is part of ray-tracing.

### Cycles

```python
sc.render.engine = "CYCLES"
cy = sc.cycles
cy.samples = 128
cy.use_adaptive_sampling = True
cy.adaptive_threshold = 0.01
cy.use_denoising = True
cy.denoiser = "OPENIMAGEDENOISE"
cy.max_bounces = 6
cy.device = "GPU"                 # 'CPU' | 'GPU'

prefs = bpy.context.preferences.addons["cycles"].preferences
prefs.compute_device_type         # 'METAL' on this machine
[(d.name, d.type) for d in prefs.devices]
for d in prefs.devices:
    d.use = True                  # GPU rendering needs devices enabled here too
```

### Workbench

```python
sc.render.engine = "BLENDER_WORKBENCH"
sc.display.shading.light = "STUDIO"      # FLAT | STUDIO | MATCAP
sc.display.shading.color_type = "OBJECT" # MATERIAL | OBJECT | RANDOM | SINGLE | TEXTURE
```

## Colour management

```python
vs = sc.view_settings
vs.view_transform = "AgX"         # AgX | Filmic | Standard | Khronos PBR Neutral | Raw
vs.look = "AgX - Medium High Contrast"
vs.exposure = 0.2
vs.gamma = 1.0
sc.sequencer_colorspace_settings.name = "sRGB"
```

These enums are OCIO-driven and also read back as `['NONE']` — assign, don't introspect.

## View layers and passes

```python
vl = sc.view_layers[0]
vl.use_pass_combined = True
vl.use_pass_z = True
vl.use_pass_normal = True
vl.use_pass_mist = True
vl.use_pass_object_index = True
vl.use_pass_cryptomatte_object = True
vl.pass_cryptomatte_depth = 6
# Cycles-only: vl.cycles.use_pass_shadow_catcher, denoising_store_passes
```

Multiple view layers render separately and cost accordingly:

```python
extra = sc.view_layers.new("Background")
extra.use = True
coll_layer = extra.layer_collection.children["Foreground"]
coll_layer.exclude = True          # per-view-layer collection visibility
```

Saving passes needs a multi-layer format:

```python
sc.render.image_settings.media_type = "MULTI_LAYER_IMAGE"
sc.render.image_settings.file_format = "OPEN_EXR_MULTILAYER"
```

## Compositor — a node group in 5.x

`scene.node_tree` **does not exist**. The compositor is a real node group with
`NodeGroupInput` / `NodeGroupOutput`, and `CompositorNodeComposite` is gone:

```python
g = bpy.data.node_groups.new("Comp", "CompositorNodeTree")
sc.compositing_node_group = g
sc.use_nodes = True
sc.render.use_compositing = True

g.interface.new_socket("Image", in_out="INPUT",  socket_type="NodeSocketColor")
g.interface.new_socket("Image", in_out="OUTPUT", socket_type="NodeSocketColor")
ni    = g.nodes.new("NodeGroupInput")
no    = g.nodes.new("NodeGroupOutput")
glare = g.nodes.new("CompositorNodeGlare")
g.links.new(ni.outputs[0], glare.inputs["Image"])
g.links.new(glare.outputs["Image"], no.inputs[0])
```

**An unterminated group silently swallows the render** — `bpy.ops.render.render()` returns
`{'FINISHED'}` and writes nothing. Either finish the graph or set
`sc.render.use_compositing = False`.

Compositor node **settings became input sockets** in 5.x. `glare.glare_type` raises
`AttributeError`; use:

```python
glare.inputs["Type"].default_value        # also: Quality, Threshold, Smoothness, Clamp,
                                          # Maximum, Strength, Saturation, Tint, Size,
                                          # Streaks, Streaks Angle, Iterations, Fade,
                                          # Color Modulation, Diagonal, Sun Position, Jitter
glare.outputs                             # ['Image', 'Glare', 'Highlights']
```

92 `CompositorNode*` types exist. Common ones: `RLayers`, `Image`, `Viewer`, `OutputFile`,
`Blur`, `Denoise`, `Glare`, `AlphaOver`, `SetAlpha`, `ColorBalance`, `Levels`, `Tonemap`,
`LensDistortion`, `Crop`, `Scale`, `Translate`, `MovieDistortion`, `BlankImage`,
`ImageCoordinates`, `ImageInfo`, `StringToImage`, `BokehImage`.

`CompositorNodeRLayers` feeds render passes in; `CompositorNodeOutputFile` writes extra
files alongside the main output.

## Output settings

```python
r = sc.render
r.resolution_x, r.resolution_y = 1920, 1080
r.resolution_percentage = 100
r.fps = 24
r.film_transparent = True                 # alpha background
r.filepath = "/abs/path/out.png"

r.image_settings.media_type = "IMAGE"     # IMAGE | MULTI_LAYER_IMAGE | VIDEO
r.image_settings.file_format = "PNG"
r.image_settings.color_mode = "RGBA"      # BW | RGB | RGBA
r.image_settings.color_depth = "16"       # '8' | '16' (| '32' for EXR)
r.image_settings.compression = 15
```

Image formats: `AVIF JPEG OPEN_EXR PNG WEBP BMP CINEON DPX IRIS JPEG2000 HDR TARGA
TARGA_RAW TIFF OPEN_EXR_MULTILAYER FFMPEG`.

### Video

`FFMPEG` is rejected unless you switch the media type first:

```python
r.image_settings.media_type = "VIDEO"
r.image_settings.file_format = "FFMPEG"
r.ffmpeg.format = "MPEG4"                 # MPEG4 | QUICKTIME | MKV | WEBM | AVI …
r.ffmpeg.codec = "H264"                   # H264 | HEVC | VP9 | AV1 | PRORES | FFV1 …
r.ffmpeg.constant_rate_factor = "HIGH"    # LOSSLESS PERC_LOSSLESS HIGH MEDIUM LOW …
r.ffmpeg.ffmpeg_preset = "GOOD"
r.ffmpeg.audio_codec = "AAC"
```

## Rendering

```python
render(OUT + "/hero.png", engine="CYCLES", samples=128, width=1920, height=1080)
```

The bridge's `render()` saves and restores every setting it touches, sets the frame, moves
the file from `frame_path()` to exactly the path you asked for, and raises a diagnostic
`RuntimeError` if nothing was written.

Raw form:

```python
sc.render.filepath = "/abs/path/still.png"
bpy.ops.render.render(write_still=True)
os.path.exists(bpy.path.abspath(sc.render.frame_path()))   # ALWAYS verify
```

Animation:

```python
sc.frame_start, sc.frame_end = 1, 48
sc.render.filepath = "/abs/dir/frame_"     # PNG sequence -> frame_0001.png …
bpy.ops.render.render(animation=True)
```

This blocks the main thread for the whole range. Raise `BLENDER_SEND_TIMEOUT`, keep the
range short while iterating, and warn the user their UI will be frozen.

`bpy.data.images["Render Result"]` reports `size == (0, 0)` and `has_data == False` even
after a good render, and `save_render()` on it can fail — check the file on disk instead.

## Why a render produced nothing

In order of likelihood:

1. `use_compositing = True` with a compositor group that has no `NodeGroupOutput`.
2. `use_sequencer = True` with a sequence editor present — the VSE output replaces the 3D
   render. Set `sc.render.use_sequencer = False`.
3. `sc.camera is None`.
4. Everything hidden via `hide_render` or an excluded layer collection.
