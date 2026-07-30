# Geometry Nodes — building trees from script

Verified on Blender 5.2.0 LTS. The important 5.x change is how the **modifier exposes its
inputs** — see "Driving the modifier" below; the 4.x idiom raises `TypeError`.

## A complete scatter tree

```python
g = bpy.data.node_groups.new("Scatter", "GeometryNodeTree")
g.interface.new_socket("Geometry", in_out="INPUT",  socket_type="NodeSocketGeometry")
g.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
dens = g.interface.new_socket("Density", in_out="INPUT", socket_type="NodeSocketFloat")
dens.default_value = 40.0

gin  = g.nodes.new("NodeGroupInput");  gin.location  = (-600, 0)
gout = g.nodes.new("NodeGroupOutput"); gout.location = (600, 0)
dist = g.nodes.new("GeometryNodeDistributePointsOnFaces"); dist.location = (-300, 0)
inst = g.nodes.new("GeometryNodeInstanceOnPoints");        inst.location = (0, 0)
ico  = g.nodes.new("GeometryNodeMeshIcoSphere");           ico.location  = (-300, -300)
ico.inputs["Radius"].default_value = 0.08
join = g.nodes.new("GeometryNodeJoinGeometry");            join.location = (300, 0)
real = g.nodes.new("GeometryNodeRealizeInstances");        real.location = (450, 0)

L = g.links.new
L(gin.outputs["Geometry"], dist.inputs["Mesh"])
L(gin.outputs["Density"],  dist.inputs["Density"])
L(dist.outputs["Points"],  inst.inputs["Points"])
L(ico.outputs["Mesh"],     inst.inputs["Instance"])
L(inst.outputs["Instances"], join.inputs["Geometry"])
L(gin.outputs["Geometry"],   join.inputs["Geometry"])   # join takes multiple links
L(join.outputs["Geometry"],  real.inputs["Geometry"])
L(real.outputs["Geometry"],  gout.inputs["Geometry"])

mod = ob.modifiers.new("GN", "NODES")
mod.node_group = g
```

Without the **Realize Instances** node this reports 8 vertices (the base cube only) —
`to_mesh()` never sees instances. With it: 43208. If you only need a count, walk the
depsgraph instead of realizing:

```python
dg = bpy.context.evaluated_depsgraph_get()
sum(1 for i in dg.object_instances if i.is_instance)     # 3600
```

## Driving the modifier from Python

The interface assigns each socket a stable identifier (`Socket_0`, `Socket_1`, …) — the
*name* is only a label, so look the identifier up:

```python
[(it.name, it.identifier, it.in_out) for it in g.interface.items_tree
 if it.item_type == "SOCKET"]
# [('Geometry', 'Socket_1', 'OUTPUT'), ('Geometry', 'Socket_0', 'INPUT'),
#  ('Density',  'Socket_2', 'INPUT')]
```

Then set the value — **Blender 5.x path**:

```python
mod.properties.inputs["Socket_2"]["value"] = 120.0
ob.update_tag()
```

`mod["Socket_2"] = 120.0` (the Blender 4.x idiom every tutorial shows) raises
`TypeError: id properties not supported for this type`.

Each entry is an `IDPropertyGroup`; `to_dict()` shows what it holds:

```python
mod.properties.inputs["Socket_2"].to_dict()
# {'value': 40.0, 'type': 1, 'attribute_name': ''}
```

Set `attribute_name` (and the appropriate `type`) to drive the socket from a mesh attribute
instead of a constant.

## Fields — position, normal, and per-element math

Fields are ordinary links; a node that outputs a field feeds a socket that accepts one.

```python
g = bpy.data.node_groups.new("Displace", "GeometryNodeTree")
g.interface.new_socket("Geometry", in_out="INPUT",  socket_type="NodeSocketGeometry")
g.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
gin    = g.nodes.new("NodeGroupInput")
gout   = g.nodes.new("NodeGroupOutput")
setpos = g.nodes.new("GeometryNodeSetPosition")
noise  = g.nodes.new("ShaderNodeTexNoise")          # shader texture nodes work here
pos    = g.nodes.new("GeometryNodeInputPosition")
normal = g.nodes.new("GeometryNodeInputNormal")
scale  = g.nodes.new("ShaderNodeVectorMath"); scale.operation = "SCALE"

L = g.links.new
L(gin.outputs["Geometry"], setpos.inputs["Geometry"])
L(pos.outputs["Position"], noise.inputs["Vector"])
L(normal.outputs["Normal"], scale.inputs[0])
L(noise.outputs["Fac"], scale.inputs["Scale"])
L(scale.outputs["Vector"], setpos.inputs["Offset"])
L(setpos.outputs["Geometry"], gout.inputs["Geometry"])
```

Stack a `SUBSURF` modifier *before* the `NODES` one to give the displacement something to
push around (386 verts at `levels = 3`).

## Zones

Simulation and repeat zones are node pairs that must be explicitly linked:

```python
sim_in  = g.nodes.new("GeometryNodeSimulationInput")
sim_out = g.nodes.new("GeometryNodeSimulationOutput")
sim_in.pair_with_output(sim_out)          # required — creates the zone

rep_in  = g.nodes.new("GeometryNodeRepeatInput")
rep_out = g.nodes.new("GeometryNodeRepeatOutput")
rep_in.pair_with_output(rep_out)
```

Add state items on the *output* node (`sim_out.state_items.new(type, name)`,
`rep_out.repeat_items.new(...)`); the matching sockets appear on both ends.

## Node families

Prefix is `GeometryNode…` unless noted.

- **Input geometry**: `MeshCube`, `MeshGrid`, `MeshCircle`, `MeshCylinder`, `MeshCone`,
  `MeshIcoSphere`, `MeshUVSphere`, `MeshLine`, `CurvePrimitiveCircle`,
  `CurvePrimitiveBezierSegment`, `CurvePrimitiveLine`, `CurvePrimitiveQuadrilateral`,
  `Points`, `ObjectInfo`, `CollectionInfo`, `IsViewport`.
- **Read fields**: `InputPosition`, `InputNormal`, `InputIndex`, `InputID`,
  `InputRadius`, `InputNamedAttribute`, `InputSceneTime`.
- **Write**: `SetPosition`, `SetShadeSmooth`, `SetMaterial`, `SetCurveRadius`,
  `SetCurveTilt`, `StoreNamedAttribute`.
- **Instancing**: `InstanceOnPoints`, `RealizeInstances`, `RotateInstances`,
  `ScaleInstances`, `TranslateInstances`, `InstancesToPoints`.
- **Distribution / sampling**: `DistributePointsOnFaces`, `DistributePointsInVolume`,
  `SampleNearest`, `SampleIndex`, `SampleCurve`, `RaycastGeometry`.
- **Topology**: `JoinGeometry`, `SeparateGeometry`, `DeleteGeometry`, `DualMesh`,
  `SubdivideMesh`, `SubdivisionSurface`, `ExtrudeMesh`, `MergeByDistance`,
  `Triangulate`, `MeshBoolean`, `ConvexHull`, `Transform`.
- **Curves**: `CurveToMesh`, `CurveToPoints`, `MeshToCurve`, `FillCurve`, `FilletCurve`,
  `ResampleCurve`, `TrimCurve`, `CurveLength`.
- **Utility (shared with shaders)**: `ShaderNodeMath`, `ShaderNodeVectorMath`,
  `ShaderNodeMapRange`, `ShaderNodeMix`, `ShaderNodeValToRGB`, `ShaderNodeTexNoise`,
  `ShaderNodeTexVoronoi`, `FunctionNodeRandomValue`, `FunctionNodeCompare`,
  `FunctionNodeBooleanMath`, `FunctionNodeAlignRotationToVector`.

When unsure of an idname or a socket name, ask the live session rather than guessing:

```python
n = g.nodes.new("GeometryNodeDistributePointsOnFaces")
print([s.name for s in n.inputs], [s.name for s in n.outputs])
print([t for t in dir(bpy.types) if t.startswith("GeometryNode")])
```

## Reusing a tree

A node group is a data-block: assign the same `g` to a `NODES` modifier on many objects and
give each one different `properties.inputs[...]` values. Instance it inside another tree with
a `GeometryNodeGroup` node whose `node_tree` you set.
