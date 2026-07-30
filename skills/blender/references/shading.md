# Shading — materials, shader nodes, world, lights, cameras

Verified on Blender 5.2.0 LTS.

## Principled BSDF

`use_nodes = True` gives you a `Principled BSDF` wired to `Material Output`. Address inputs
**by name** — the 4.0 rename is still in force and 5.x added more:

```python
m = bpy.data.materials.new("Metal")
m.use_nodes = True
bsdf = m.node_tree.nodes["Principled BSDF"]
bsdf.inputs["Base Color"].default_value = (0.8, 0.5, 0.2, 1.0)   # RGBA, linear
bsdf.inputs["Metallic"].default_value = 1.0
bsdf.inputs["Roughness"].default_value = 0.25
bsdf.inputs["Coat Weight"].default_value = 0.3
ob.data.materials.append(m)
```

Full input list in 5.2, in order:

```
Base Color, Metallic, Roughness, IOR, Alpha, Thin Wall, Normal, Weight,
Diffuse Roughness, Subsurface Weight, Subsurface Radius, Subsurface Scale,
Subsurface IOR, Subsurface Anisotropy, Specular IOR Level, Specular Tint,
Anisotropic, Anisotropic Rotation, Tangent, Transmission Weight, Coat Weight,
Coat Roughness, Coat IOR, Coat Tint, Coat Normal, Sheen Weight, Sheen Roughness,
Sheen Tint, Emission Color, Emission Strength, Thin Film Thickness, Thin Film IOR
```

There is no plain `Emission`, `Specular`, `Transmission` or `Clearcoat` input any more.

Emission and glass:

```python
bsdf.inputs["Emission Color"].default_value = (0.2, 0.6, 1.0, 1.0)
bsdf.inputs["Emission Strength"].default_value = 8.0

bsdf.inputs["Transmission Weight"].default_value = 1.0
bsdf.inputs["IOR"].default_value = 1.45
m.surface_render_method = "BLENDED"      # DITHERED (default) | BLENDED — EEVEE transparency
m.use_transparent_shadow = True
```

`blend_method` still exists but `surface_render_method` is the one EEVEE reads.
Other material flags: `use_backface_culling`, `displacement_method`.

## Building a node graph

```python
nt = m.node_tree
bsdf = nt.nodes["Principled BSDF"]
coord   = nt.nodes.new("ShaderNodeTexCoord")
mapping = nt.nodes.new("ShaderNodeMapping")
noise   = nt.nodes.new("ShaderNodeTexNoise")
ramp    = nt.nodes.new("ShaderNodeValToRGB")     # ColorRamp
bump    = nt.nodes.new("ShaderNodeBump")
for i, n in enumerate((coord, mapping, noise, ramp, bump)):
    n.location = (-1200 + i * 220, 200)          # keep the graph readable for the user

noise.inputs["Scale"].default_value = 6.0
noise.inputs["Detail"].default_value = 8.0
ramp.color_ramp.elements[0].position = 0.35
ramp.color_ramp.elements[0].color = (0.02, 0.03, 0.05, 1)
ramp.color_ramp.elements[1].position = 0.65

L = nt.links.new
L(coord.outputs["Object"], mapping.inputs["Vector"])
L(mapping.outputs["Vector"], noise.inputs["Vector"])
L(noise.outputs["Fac"], ramp.inputs["Fac"])
L(ramp.outputs["Color"], bsdf.inputs["Base Color"])
L(noise.outputs["Fac"], bump.inputs["Height"])
L(bump.outputs["Normal"], bsdf.inputs["Normal"])
```

Useful node idnames: `ShaderNodeBsdfPrincipled`, `ShaderNodeBsdfDiffuse`,
`ShaderNodeBsdfGlass`, `ShaderNodeBsdfTransparent`, `ShaderNodeEmission`,
`ShaderNodeMixShader`, `ShaderNodeAddShader`, `ShaderNodeOutputMaterial`,
`ShaderNodeTexImage`, `ShaderNodeTexNoise`, `ShaderNodeTexVoronoi`, `ShaderNodeTexWave`,
`ShaderNodeTexMusgrave`, `ShaderNodeTexGradient`, `ShaderNodeTexChecker`,
`ShaderNodeTexCoord`, `ShaderNodeUVMap`, `ShaderNodeMapping`, `ShaderNodeValToRGB`,
`ShaderNodeMix` (set `data_type`), `ShaderNodeMath`, `ShaderNodeVectorMath`,
`ShaderNodeBump`, `ShaderNodeNormalMap`, `ShaderNodeDisplacement`, `ShaderNodeAttribute`,
`ShaderNodeObjectInfo`, `ShaderNodeFresnel`, `ShaderNodeLayerWeight`, `ShaderNodeGroup`.

`ShaderNodeMix` uses numeric socket indices because the names repeat: inputs `[6]`/`[7]` are
the A/B colour sockets, output `[2]` is the colour result.

## Image textures

```python
img = bpy.data.images.new("Checker", 256, 256)
img.generated_type = "COLOR_GRID"          # BLANK | UV_GRID | COLOR_GRID
# or: img = bpy.data.images.load("/path/tex.png")

tex = nt.nodes.new("ShaderNodeTexImage")
tex.image = img
tex.interpolation = "Closest"              # Linear | Closest | Cubic | Smart
tex.extension = "REPEAT"                   # REPEAT | EXTEND | CLIP | MIRROR
uv = nt.nodes.new("ShaderNodeUVMap"); uv.uv_map = "UVMap"
nt.links.new(uv.outputs["UV"], tex.inputs["Vector"])
nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])

img.filepath_raw = "/path/out.png"
img.file_format = "PNG"
img.save()
```

For non-colour data (roughness, normal maps) set `img.colorspace_settings.name = "Non-Color"`.

## Shader node groups

```python
g = bpy.data.node_groups.new("TintGroup", "ShaderNodeTree")
g.interface.new_socket("Color",  in_out="INPUT",  socket_type="NodeSocketColor")
g.interface.new_socket("Result", in_out="OUTPUT", socket_type="NodeSocketColor")
gin  = g.nodes.new("NodeGroupInput")
gout = g.nodes.new("NodeGroupOutput")
mix  = g.nodes.new("ShaderNodeMix"); mix.data_type = "RGBA"
g.links.new(gin.outputs["Color"], mix.inputs[6])
g.links.new(mix.outputs[2], gout.inputs["Result"])

inst = other_material.node_tree.nodes.new("ShaderNodeGroup")
inst.node_tree = g
```

Socket types: `NodeSocketFloat`, `NodeSocketVector`, `NodeSocketColor`, `NodeSocketBool`,
`NodeSocketInt`, `NodeSocketString`, `NodeSocketShader`, `NodeSocketGeometry`,
`NodeSocketObject`, `NodeSocketMaterial`, `NodeSocketImage`, `NodeSocketCollection`.

## World

```python
w = bpy.data.worlds.new("Studio")
bpy.context.scene.world = w
w.use_nodes = True
nt = w.node_tree                    # default nodes: Background -> World Output
bg = nt.nodes["Background"]
bg.inputs["Strength"].default_value = 1.5
bg.inputs["Color"].default_value = (0.05, 0.05, 0.06, 1.0)
```

Procedural sky — **`NISHITA` is gone**, use the scattering models:

```python
sky = nt.nodes.new("ShaderNodeTexSky")
sky.sky_type = "MULTIPLE_SCATTERING"   # SINGLE_SCATTERING | MULTIPLE_SCATTERING
                                       # | PREETHAM | HOSEK_WILKIE
sky.sun_elevation = math.radians(25)
nt.links.new(sky.outputs["Color"], bg.inputs["Color"])
```

HDRI:

```python
env = nt.nodes.new("ShaderNodeTexEnvironment")
env.image = bpy.data.images.load("/path/studio.hdr")
nt.links.new(env.outputs["Color"], bg.inputs["Color"])
```

## Lights

```python
ld = bpy.data.lights.new("Key", type="AREA")   # POINT | SUN | SPOT | AREA
ld.energy = 400                                 # watts; SUN is irradiance (use ~3)
ld.color = (1.0, 0.95, 0.9)
ld.shape = "RECTANGLE"                          # AREA: SQUARE RECTANGLE DISK ELLIPSE
ld.size, ld.size_y = 2.0, 1.0
# SPOT: ld.spot_size = math.radians(45); ld.spot_blend = 0.2
# SUN:  ld.angle = math.radians(2)              # softness of the shadow
ob = bpy.data.objects.new("Key", ld); coll.objects.link(ob)
ob.location = (0, 0, 4)
```

## Cameras

```python
cd = bpy.data.cameras.new("Cam")
cd.lens = 50                          # mm; or cd.type = "ORTHO" + cd.ortho_scale
cd.sensor_width = 36
cd.dof.use_dof = True
cd.dof.focus_distance = 6.0
cd.dof.aperture_fstop = 2.8
# cd.dof.focus_object = subject       # auto-follow instead of a fixed distance
ob = bpy.data.objects.new("Cam", cd); coll.objects.link(ob)
ob.location = (6, -6, 4)
direction = Vector((0, 0, 0)) - ob.location
ob.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
bpy.context.scene.camera = ob
```

Or let a constraint keep it aimed as things move:

```python
c = ob.constraints.new("TRACK_TO")
c.target = subject
c.track_axis = "TRACK_NEGATIVE_Z"
c.up_axis = "UP_Y"
sync()
```
