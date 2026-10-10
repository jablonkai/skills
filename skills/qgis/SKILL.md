---
name: qgis
description: 'Automate QGIS 4 headless on macOS with PyQGIS and qgis_process: load GPX, GeoJSON, GeoPackage, Shapefile and GeoTIFF data, reproject (WGS 84, UTM, EOV/EPSG:23700, Web Mercator), run Processing algorithms (buffer, clip, merge, dissolve, kernel-density heatmaps), style layers (e.g. elevation-coloured route segments) and export print layouts to PDF/PNG with legend, scale bar and north arrow, inspecting any GIS file (layers, feature counts, CRS, extent). Use whenever a task needs real GIS processing or a cartographic map: "render this GPX route as a PDF map coloured by elevation", "heatmap from all my GPX runs", "clip this layer to the county and save it as GeoPackage in EOV", "export the print layout from my .qgz", "which CRS and how many features are in this gpkg", "qgis_process", Hungarian "készíts térképet a GPX-ből". Not for GPX stats without a map (plain Python), DUV race data (duv), hand-drawn poster maps (inkscape), 3D terrain (blender), web maps (Leaflet) or diagrams (drawio).'
summary: "automate QGIS 4 headless with PyQGIS and qgis_process — GPX/GeoJSON/GeoPackage/raster loading, reprojection, Processing algorithms (buffer, clip, heatmap), graduated styling, and print-layout PDF/PNG map export with verified feature counts and CRS"
category: gis
risk: low
tags:
  - qgis
  - pyqgis
  - qgis-process
  - gis
  - gpx
  - geopackage
  - maps
  - heatmap
metadata:
  version: "1.0.0"
---

# QGIS Automation

Every call is **one short headless process** on the QGIS app bundle's own tools: PyQGIS
scripts run on the bundled Python, and Processing algorithms run through `qgis_process`.
Nothing listens on a port, the GUI doesn't need to be open, and the user's QGIS profile
and plugins are never loaded. The runs use a skill-owned profile in
`~/Library/Caches/qgis-skill/`. Verified against **QGIS 4.2.3** (Qt 6.11, GDAL 3.13,
PROJ 9.8) on macOS 27.

Always go through `scripts/qgis.sh`. Outside the GUI the bundle is not
self-configuring: a bare `qgis_process` can't find `proj.db`, so **every EPSG lookup
fails silently**, and the bundled `python3.12` dies on `No module named 'encodings'`
unless `PYTHONHOME` points at `Contents/Frameworks`.
The wrapper sets the environment, kills runs after `QGIS_TIMEOUT` seconds (default 300)
and filters the harmless stderr noise.

- [references/processing.md](references/processing.md): `qgis_process` syntax,
  parameter value forms, GeoPackage outputs, and the key algorithms with their
  parameters. Read it before any Processing run not shown below.
- [references/pyqgis-api.md](references/pyqgis-api.md): loading URIs, CRS transforms,
  renderers, layout items, exporters and writers in 4.x. Read it before writing a
  custom PyQGIS script.
- [references/recipes.md](references/recipes.md): worked flows, including a race
  course map with a basemap, clip + reproject + GPKG, buffers along a course, merging
  GPX files, atlas pages, and handing a result to the GUI.
- [references/gotchas.md](references/gotchas.md): **read it when an output is empty,
  a map is blank, or a CRS looks wrong.** It also covers the security posture.

## 1. Check first

```bash
Q="bash scripts/qgis.sh"     # paths are relative to this skill's directory
$Q check                     # app, version, proj.db, PyQGIS
```

If it says QGIS is not found, ask before installing (`brew install --cask qgis`), or
set `QGIS_APP=/path/to/QGIS.app` for a copy outside `/Applications`.

## 2. Pick the tool

| Task | Use |
|---|---|
| Route / course map coloured by elevation → PDF/PNG | `gpx_route_map.py` (§3) |
| Heatmap from many GPX files | `gpx_heatmap.py` (§4) |
| Clip, buffer, reproject, merge, dissolve … → file | `qgis_process run` (§5) |
| Layouts already designed in a `.qgz` → PDF/PNG, atlas | `layout_export.py` (§6) |
| What's in a file: layers, counts, CRS, extent, raster stats | `qgis_inspect.py` (§7) |
| Anything else (custom styling, labels, several maps) | your own PyQGIS script (§8) |

Each script prints JSON on stdout. The exit codes are **2** usage, **3** missing or
unreadable input, **4** verification failed, **5** QGIS or processing error. Run any
script with `--help` for the full option list.

## 3. Route map coloured by elevation

```bash
$Q python scripts/gpx_route_map.py course.gpx -o course.pdf -o course.png \
   --title "Buda Hills 25K" [--classes 7 --mode jenks --ramp Spectral] \
   [--basemap osm] [--project course.qgz] [--save-segments segs.gpkg]
```

- The track becomes one segment per pair of consecutive points, each carrying the mean
  elevation of its ends. A graduated renderer colours them with Spectral inverted, so
  low is blue and high is red. A dark casing keeps pale classes readable, and the start
  and finish get markers.
- The map is drawn in the **local UTM zone**, so the scale bar shows true kilometres.
  The subtitle gives distance, ascent/descent and the elevation range, all computed on
  the ellipsoid. Labelled distance markers are placed every 1/5/10/25 km depending on
  length (`--km-every 2`, or `0` for none). The page orientation follows the route's
  shape.
- Elevation comes from `ele`, or from the Z value when `ele` is empty. With no
  elevation at all the script exits 3. Say so rather than drawing a single-colour line.
- `--basemap osm` needs network access and adds the required attribution.
  `--project` saves an editable `.qgz` plus a `_data.gpkg` beside it, because memory
  layers don't survive in a project.
- **Report** the `stats` and `classes` from the JSON, and look at the PNG before
  saying the map is done.

## 4. Heatmap from many GPX files

```bash
$Q python scripts/gpx_heatmap.py runs/ -o heatmap.tif --png heatmap.png [--pdf heatmap.pdf] \
   --title "2026 training" [--radius 150 --pixel 10 --spacing 10 --raw-points --crs EPSG:23700]
```

- Tracks are **resampled every `--spacing` m** before the kernel density is computed.
  A watch that logs every second would otherwise count 10× a 10 s logger, and pauses
  would become hot spots. Use `--raw-points` only when visits or dwell time is the
  point.
- The density is computed in a metric CRS (UTM by default). `RADIUS` and `PIXEL_SIZE`
  are in **layer units**, so in EPSG:4326 they would be degrees and give a single blob.
  The script refuses a geographic `--crs`.
- The GeoTIFF holds raw density, and the styled map draws zero as transparent. The JSON
  reports `peak` (the densest cell in WGS 84) and `points_per_file`, so check that
  every file contributed.

## 5. Processing algorithms (`qgis_process`)

```bash
$Q process help native:clip                      # parameters, value forms, defaults
$Q process run native:clip -- INPUT=places.geojson OVERLAY=area.geojson OUTPUT=/tmp/c.gpkg
$Q process run native:reprojectlayer -- INPUT=/tmp/c.gpkg TARGET_CRS=EPSG:23700 \
   OUTPUT="ogr:dbname='clipped.gpkg' table=\"places_eov\" (geom)"
echo '{"inputs": {"INPUT": "a.gpx|layername=tracks", "DISTANCE": 500, "OUTPUT": "b.gpkg"}}' \
   | $Q process run native:buffer -        # JSON in, JSON out
```

- Find algorithms with `$Q process list | grep -i <word>`. `native:` algorithms are
  fastest. The `gdal:` ones shell out to GDAL.
- **Distances are in the layer's CRS units.** Reproject to a metric CRS before you
  buffer or measure. A 500 m buffer on EPSG:4326 data with `DISTANCE=500` means 500
  degrees.
- Multi-layer inputs need `path|layername=x`. GPX has `tracks`, `track_points`,
  `routes`, `route_points` and `waypoints`.
- **GeoPackage outputs:** `OUTPUT=file.gpkg` **replaces the whole file**, including
  other layers. To add a layer use `OUTPUT="ogr:dbname='file.gpkg' table=\"name\"
  (geom)"`. Never write into the GPKG you are reading from, because the result comes
  out empty. Chain through a temporary file instead.
- Add `--json` (e.g. `run native:clip --json -- …`) for machine-readable results. The output paths are in
  `results`.

## 6. Export layouts from an existing project

```bash
$Q python scripts/layout_export.py project.qgz --list
$Q python scripts/layout_export.py project.qgz -o map.pdf --layout "A3 overview" --dpi 300
$Q python scripts/layout_export.py project.qgz --out-dir out --format png
$Q python scripts/layout_export.py project.qgz --layout Stages --atlas --out-dir pages --format pdf
```

The script refuses to export when layers have broken paths (exit 4 lists them),
because a missing source renders as an empty map with no error. Fix the paths, or pass
`--allow-missing` when that is really intended.

## 7. Verify every output

```bash
$Q python scripts/qgis_inspect.py out.gpkg --expect-crs EPSG:23700 --expect-count 96 --expect-layers 1
$Q python scripts/qgis_inspect.py heatmap.tif --stats
```

- A file that merely exists is not done. Check the feature counts against the input
  and the expectation, check the CRS authid, and check that the extent is plausible
  (`extent_wgs84` should be where the data is).
- For maps, open the PNG with the image viewer tool and look. Check that the line or
  heat is visible and that the legend, scale bar and title are present.
- Report what you checked in your answer, not just the paths.

## 8. Custom PyQGIS scripts

Write the script to a scratch file and run it with `$Q python script.py`. Start it
with:

```python
import os, sys
sys.path.insert(0, "<this skill>/scripts")      # qgis.sh also puts scripts/ on PYTHONPATH
from qgis_boot import start, emit, fail, load_vector, utm_crs, map_layout, export_layout
start(processing=True)                           # headless QgsApplication (+ Processing)
import processing                                # processing.run("native:buffer", {...})
```

- `load_vector("f.gpx", prefer=["track_points"])` picks a GPX sublayer. `utm_crs(lon,
  lat)` gives a metric CRS. `map_layout(project, layers, extent, title=…,
  legend_layers=[…], crs=…)` builds a title, map, legend, scale bar and north arrow.
  `export_layout(layout, ["a.pdf", "a.png"], dpi)` writes the files.
- `emit(dict)` prints JSON and exits, skipping a Qt teardown crash. Call it last.
- Use the 4.x API from [references/pyqgis-api.md](references/pyqgis-api.md). Old
  snippets from the web often use QGIS 2 names that no longer exist
  (`QgsMapLayerRegistry`, `QgsComposition`, `iface` in a standalone script).

## Handing work to the GUI

`$Q open result.qgz` opens a project in the user's QGIS for manual tweaks. Use it only
when the user asks to see or edit it. A saved project must reference files
(`--project` does this), not memory layers.
