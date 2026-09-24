# .drawio file format and styles

Use this when writing a `.drawio` file directly (no running draw.io, or a file that goes
into a repo), and for the style strings passed to `D.vertex` / `D.edge` in the live
mode — the style vocabulary is the same.

## Contents

- [File skeleton](#file-skeleton)
- [Cells](#cells)
- [Style strings](#style-strings)
- [Shapes](#shapes)
- [Palette](#palette)
- [Layout by hand](#layout-by-hand)
- [Checklist before handing a file over](#checklist-before-handing-a-file-over)

## File skeleton

```xml
<mxfile host="drawio">
  <diagram id="page-1" name="Overview">
    <mxGraphModel grid="1" gridSize="10" guides="1" connect="1" arrows="1" page="1"
                  pageWidth="1169" pageHeight="827" math="0" shadow="0">
      <root>
        <mxCell id="0"/>
        <mxCell id="1" parent="0"/>
        <!-- shapes and edges, parent="1" -->
      </root>
    </mxGraphModel>
  </diagram>
  <!-- more <diagram> elements = more pages -->
</mxfile>
```

- Cells `0` and `1` are mandatory: `0` is the root, `1` the default layer. Extra
  layers are more `<mxCell id="L2" value="Notes" parent="0"/>`.
- Write `<diagram>` content uncompressed (as above). draw.io also reads the compressed
  base64 form it sometimes saves; to get readable XML from such a file run
  `drawio-export.sh in.drawio out.drawio`.
- `.drawio.svg` / `.drawio.png` are images with the diagram embedded — produce them
  with `drawio-export.sh in.drawio out.svg -e` rather than by hand.

## Cells

```xml
<mxCell id="api" value="API gateway" style="rounded=1;whiteSpace=wrap;html=1;"
        vertex="1" parent="1">
  <mxGeometry x="200" y="80" width="120" height="60" as="geometry"/>
</mxCell>

<mxCell id="e1" value="HTTPS" style="edgeStyle=orthogonalEdgeStyle;html=1;endArrow=block;"
        edge="1" parent="1" source="web" target="api">
  <mxGeometry relative="1" as="geometry">
    <Array as="points"><mxPoint x="160" y="40"/></Array>   <!-- optional waypoints -->
  </mxGeometry>
</mxCell>
```

- Ids must be unique across the file; readable ids (`api`, `e-web-api`) make later
  edits easy.
- An edge needs `source`/`target` pointing at existing vertex ids, and a
  `<mxGeometry relative="1" as="geometry"/>` child.
- **Containers**: a vertex whose style starts with `swimlane;` (or has `container=1`).
  Children set `parent="<container id>"` and use coordinates **relative to the
  container**; `startSize=26` is the header height to leave free.
- **Custom data** (Edit Data…, tooltips, links): wrap the cell in a `UserObject`:

  ```xml
  <UserObject id="db" label="Postgres" owner="team-data" tooltip="primary" link="https://…">
    <mxCell style="shape=cylinder3;…" vertex="1" parent="1">
      <mxGeometry x="…" y="…" width="80" height="90" as="geometry"/>
    </mxCell>
  </UserObject>
  ```
- Labels with `html=1` are HTML inside an XML attribute, so they are escaped twice
  over: `value="a &amp;lt; b&lt;br&gt;line 2"` renders *a < b*, then a line break.
  (`&lt;br&gt;` becomes the tag `<br>`; `&amp;lt;` becomes the text `<`.)

## Style strings

`key=value;` pairs, optionally led by a shape name (`ellipse;`, `rhombus;`,
`swimlane;`). Always include `whiteSpace=wrap;html=1;` on labelled shapes.

| Purpose | Keys |
|---------|------|
| Fill / border | `fillColor`, `strokeColor`, `strokeWidth`, `dashed=1`, `rounded=1`, `arcSize`, `opacity`, `shadow=1`, `glass=0` |
| Text | `fontColor`, `fontSize`, `fontStyle` (bitmask: 1 bold, 2 italic, 4 underline), `fontFamily`, `align`, `verticalAlign`, `labelPosition`, `verticalLabelPosition`, `spacing` |
| Edge routing | `edgeStyle=orthogonalEdgeStyle` (default choice), `elbowEdgeStyle`, `entityRelationEdgeStyle` (ER), `none` for straight; `curved=1`, `rounded=1`, `jumpStyle=arc` |
| Edge ends | `endArrow`/`startArrow` = `block`, `classic`, `open`, `diamond`, `oval`, `none`, ER: `ERmandOne`, `ERmany`, `ERzeroToMany`, `ERoneToMany`; `endFill=0` hollow |
| Edge anchors | `exitX`, `exitY`, `entryX`, `entryY` (0–1 on the shape box) — pin where an edge leaves/enters |
| Behaviour | `movable=0`, `resizable=0`, `editable=0`, `deletable=0`, `locked=1`, `container=1`, `collapsible=0` |

## Shapes

| Diagram | Style start |
|---------|-------------|
| Process / box | `rounded=0;` · rounded `rounded=1;` |
| Decision | `rhombus;` |
| Start / end | `ellipse;` or `rounded=1;arcSize=50;` |
| Database | `shape=cylinder3;boundedLbl=1;size=12;` |
| Document, note | `shape=document;`, `shape=note;size=15;` |
| Actor | `shape=umlActor;verticalLabelPosition=bottom;verticalAlign=top;` |
| Cloud | `ellipse;shape=cloud;` |
| Text only | `text;html=1;align=left;verticalAlign=middle;` |
| Swimlane / group | `swimlane;startSize=26;` · horizontal pool `swimlane;horizontal=0;` |
| UML class | `swimlane;fontStyle=1;childLayout=stackLayout;horizontal=1;startSize=26;` with children `text;strokeColor=none;fillColor=none;align=left;spacingLeft=4;` |
| ER table | `shape=table;startSize=30;container=1;collapsible=1;childLayout=tableLayout;` (easiest: build one in the app, then copy its XML via `D.getXml()`) |
| Sequence lifeline | `shape=umlLifeline;perimeter=lifelinePerimeter;container=1;size=40;` |
| AWS | `shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.lambda;fillColor=#ED7100;strokeColor=#ffffff;verticalLabelPosition=bottom;verticalAlign=top;` — 60×60; the fill is the service category colour |
| Azure / GCP / Cisco | `image;…;image=img/lib/azure2/…svg` · `shape=mxgraph.gcp2.…` · `shape=mxgraph.cisco.…` |

For a stencil not listed: draw it once in the app (More Shapes ▸ enable the library),
select it, and read its style with `D.describe(cell).style` — don't guess stencil names.

## Palette

draw.io's own swatches read well together and in dark mode:

| Role | fillColor | strokeColor |
|------|-----------|-------------|
| Neutral | `#f5f5f5` | `#666666` |
| Blue (clients, entry) | `#dae8fc` | `#6c8ebf` |
| Green (services, success) | `#d5e8d4` | `#82b366` |
| Yellow (data, storage) | `#fff2cc` | `#d6b656` |
| Orange (external, queue) | `#ffe6cc` | `#d79b00` |
| Red (errors, risk) | `#f8cecc` | `#b85450` |
| Purple (security, auth) | `#e1d5e7` | `#9673a6` |

Use one colour per role and say what the colours mean (a legend box) when there are
more than two.

## Layout by hand

- Snap everything to the 10px grid; 120×60 boxes, 40–60px gaps, 160–200px between
  columns.
- Lay the main flow along one axis (left→right for architecture, top→bottom for
  processes); put side concerns (logging, auth) on the other.
- For anything beyond ~8 nodes, skip the arithmetic: write the cells at 0,0 and run
  `drawio-export.sh in.drawio out.drawio --layout horizontalFlow` (or an ELK JSON
  array) to get a laid-out copy.

## Checklist before handing a file over

1. Parses: `xmllint --noout file.drawio`.
2. Ids unique; every `parent`, `source`, `target` exists.
3. Renders: `drawio-export.sh file.drawio /tmp/check.png -b 10`, then look at the PNG —
   overlaps and edges crossing labels only show up visually.
