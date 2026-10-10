# Recipes

`Q="bash scripts/qgis.sh"`, run from the skill directory. Every recipe ends with a
`qgis_inspect.py` check. Run it, and report the counts and CRS.

## Contents
- [Race course map with km markers and a basemap](#race-course-map-with-km-markers-and-a-basemap)
- [Clip, reproject, GeoPackage](#clip-reproject-geopackage)
- [Corridor around a course](#corridor-around-a-course)
- [Merge many GPX files into one layer](#merge-many-gpx-files-into-one-layer)
- [Heatmap variants](#heatmap-variants)
- [Raster: hillshade and contours from a DEM](#raster-hillshade-and-contours-from-a-dem)
- [Atlas: one page per stage](#atlas-one-page-per-stage)
- [Reuse a style or template from the GUI](#reuse-a-style-or-template-from-the-gui)
- [Hand the result to the GUI](#hand-the-result-to-the-gui)

## Race course map with km markers and a basemap

The quick version is one command:

```bash
$Q python scripts/gpx_route_map.py course.gpx -o course.pdf --basemap osm --title "UB 100"
```

For km markers, build them first, then draw them in a custom script:

```bash
$Q process run native:reprojectlayer -- INPUT="course.gpx|layername=tracks" TARGET_CRS=EPSG:32634 OUTPUT=/tmp/course_utm.gpkg
$Q process run native:pointsalonglines -- INPUT=/tmp/course_utm.gpkg DISTANCE=1000 OUTPUT=/tmp/km.gpkg
```

`pointsalonglines` adds a `distance` field in metres, and point 0 is the start. Label
the points with `round("distance"/1000)` (see pyqgis-api.md › Labels). Then add them to
the layers passed to `map_layout`. Pick the UTM zone with `utm_crs(lon, lat)`; EPSG:32634
covers 18–24° E, which includes Budapest.

## Clip, reproject, GeoPackage

```bash
$Q process run native:clip -- INPUT=places.geojson OVERLAY=area.geojson OUTPUT=/tmp/clip.gpkg
$Q process run native:reprojectlayer -- INPUT=/tmp/clip.gpkg TARGET_CRS=EPSG:23700 \
   OUTPUT="ogr:dbname='clipped.gpkg' table=\"places\" (geom)"
$Q python scripts/qgis_inspect.py clipped.gpkg --expect-crs EPSG:23700 --expect-layers 1
```

- The order barely matters for points. For polygons and lines, clipping first in the
  source CRS keeps the clip boundary exact.
- When the two inputs have different CRSs, `native:clip` reprojects the overlay on the
  fly. The output takes the INPUT's CRS.
- Use `native:extractbylocation` (PREDICATE=0 intersects, 6 within) to keep **whole**
  features instead of cutting them.
- The table-syntax output writes a layer with a meaningful name instead of the file
  name. A plain `OUTPUT=clipped.gpkg` would name it `clipped`.

## Corridor around a course

```bash
$Q process run native:reprojectlayer -- INPUT="course.gpx|layername=tracks" TARGET_CRS=EPSG:32634 OUTPUT=/tmp/c.gpkg
$Q process run native:buffer -- INPUT=/tmp/c.gpkg DISTANCE=250 DISSOLVE=true OUTPUT=corridor.gpkg
$Q process run native:extractbylocation -- INPUT=pois.gpkg PREDICATE=0 INTERSECT=corridor.gpkg OUTPUT=pois_near.gpkg
```

Buffer only in a metric CRS. `DISTANCE=250` on EPSG:4326 data means 250 degrees.

## Merge many GPX files into one layer

```bash
args=(); for f in runs/*.gpx; do args+=("LAYERS=$f|layername=tracks"); done
$Q process run native:mergevectorlayers -- "${args[@]}" CRS=EPSG:4326 OUTPUT=all_runs.gpkg
```

The merged layer gets `layer` and `path` fields naming each source. `tracks` gives one
line per file. Use `track_points` for the raw points, which keep the `ele` and `time`
fields.

## Heatmap variants

```bash
$Q python scripts/gpx_heatmap.py runs/ -o h.tif --png h.png                     # defaults
$Q python scripts/gpx_heatmap.py runs/ -o h.tif --png h.png --radius 60 --pixel 5   # city streets
$Q python scripts/gpx_heatmap.py runs/ -o h.tif --pdf h.pdf --basemap osm --crs EPSG:23700
$Q python scripts/gpx_heatmap.py waypoints.gpx -o h.tif --raw-points            # point data as-is
```

- Choose the radius from the question. Use 50–100 m to tell parallel streets apart and
  300 m+ for "which areas do I run in". The default pixel gives about 1500 cells across
  the extent.
- Tracks that are far apart, like two cities, make a huge mostly empty raster. Split
  them by area and make one heatmap per area.

## Raster: hillshade and contours from a DEM

```bash
$Q process run gdal:warpreproject -- INPUT=dem.tif TARGET_CRS=EPSG:23700 RESAMPLING=1 OUTPUT=/tmp/dem_eov.tif
$Q process run gdal:hillshade -- INPUT=/tmp/dem_eov.tif BAND=1 Z_FACTOR=1 OUTPUT=hillshade.tif
$Q process run gdal:contour -- INPUT=/tmp/dem_eov.tif BAND=1 INTERVAL=20 FIELD_NAME=ELEV OUTPUT=contours.gpkg
$Q python scripts/qgis_inspect.py hillshade.tif --stats
```

Resample a continuous DEM with RESAMPLING=1 (bilinear) and categorical rasters with 0
(nearest). On a DEM in degrees, hillshade needs `SCALE=111120`, so reproject first.

## Atlas: one page per stage

Build the layout in a script (`map_layout`), then set
`lay.atlas().setCoverageLayer(stages)`, `setEnabled(True)`, `map.setAtlasDriven(True)`
and `project.write("stages.qgz")`. Then export:

```bash
$Q python scripts/layout_export.py stages.qgz --layout Stages --atlas --out-dir pages --format pdf
$Q python scripts/layout_export.py stages.qgz --layout Stages --atlas --single-pdf -o stages.pdf
```

The stages layer must be saved to a file, not a memory layer, so the atlas survives in
the project.

## Reuse a style or template from the GUI

- When the user has a `.qml` style, call `layer.loadNamedStyle("style.qml")` before
  adding the layer.
- When they have a `.qpt` layout template, load it (pyqgis-api.md › Print layouts),
  then set the text of items by their id.
- When they have a `.qgz`, use `layout_export.py`, and for different data swap the
  source with `layer.setDataSource(newpath, name, "ogr")`.

## Hand the result to the GUI

`$Q open result.qgz` opens it in the user's QGIS. Only projects that reference files
reopen correctly. `gpx_route_map.py --project` writes the sidecar `_data.gpkg` for
that reason.
