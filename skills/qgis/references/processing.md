# qgis_process reference (QGIS 4.2)

Run everything through `bash scripts/qgis.sh process …`. It sets the environment
(PROJ, GDAL, a skill-owned profile). Don't add `--skip-loading-plugins`: it also
unloads the core Processing plugin, which provides all 59 `gdal:*` algorithms.

## Contents
- [Commands](#commands)
- [Parameter values](#parameter-values)
- [Outputs](#outputs)
- [Key algorithms](#key-algorithms)
- [From PyQGIS](#from-pyqgis)

## Commands

```bash
$Q process list                       # every algorithm: id <TAB> name
$Q process help native:buffer         # parameters, types, accepted values, outputs
$Q process run native:buffer -- INPUT=a.gpkg DISTANCE=100 OUTPUT=b.gpkg
$Q process run native:buffer --json -- …          # JSON result (results, log, versions)
echo '{"inputs": {...}, "project_path": "p.qgz"}' | $Q process run native:buffer -
$Q process run model.model3 -- …                  # a Processing model file
$Q process run script.py -- …                     # a Processing script (QgsProcessingAlgorithm)
```

- With `--json` the output paths are in `results` (e.g. `{"OUTPUT": "/abs/b.gpkg"}`).
  Errors exit non-zero, and the reason is on stderr.
- `--PROJECT_PATH=p.qgz` makes the project's layers addressable by name and sets its
  CRS and ellipsoid. `--ELLIPSOID=EPSG:7030` sets the ellipsoid for area and length
  expressions.
- A list parameter is repeated: `-- LAYERS=a.gpx LAYERS=b.gpx`. In JSON it is an
  array. Two spellings work: `-- NAME=value …` after the separator, or `--NAME=value`
  with no separator. **Mixing them (`-- --LAYERS=…`) silently drops the values**, and
  the run fails with "mandatory parameters were not specified".

## Parameter values

| Type | Value form |
|---|---|
| vector/raster input | `path`, `path\|layername=tracks`, a project layer name with `--PROJECT_PATH` |
| CRS | `EPSG:23700`, `EPSG:3857`, a WKT or PROJ string |
| distance | a number **in the layer's CRS units** |
| enum | the index from `help` (e.g. `KERNEL=0` quartic) |
| field | the field name; several are `;`-separated |
| expression | a QGIS expression string, quoted for the shell: `EXPRESSION='"ele" > 300'` |
| extent | `xmin,xmax,ymin,ymax [EPSG:xxxx]` (note the order: both x first), or a layer path |
| data-defined | `field:NAME` or `expression:…` where `help` lists it |
| boolean | `true` / `false` |
| optional output | omit it, or `TEMPORARY_OUTPUT` for a temp file (the path is in results) |

## Outputs

- The output format follows the extension: `.gpkg`, `.geojson`, `.shp`, `.fgb`, `.csv`,
  `.kml` and `.gpx` for vectors; `.tif` for rasters.
- **`OUTPUT=x.gpkg` replaces the whole file.** To write a named layer into a new or
  existing GeoPackage and keep its other layers:
  `OUTPUT="ogr:dbname='x.gpkg' table=\"roads_eov\" (geom)"`.
- **Don't read and write the same GPKG in one run.** The output layer comes out with 0
  features. Write to a temporary file, then run `native:savefeatures` with
  `ACTION_ON_EXISTING_FILE=1` (create or overwrite the layer) into the target.
- GPKG adds an `fid` column. When a source attribute is named `fid` and isn't a unique
  integer, the write fails. Rename it first with `native:renametablefield`.
- GPX output takes only the GPX schema (`name`, `ele`, `time`, …). For other data write
  GPKG or GeoJSON.

## Key algorithms

| Id | Does | Main parameters |
|---|---|---|
| `native:reprojectlayer` | reproject a vector | INPUT, TARGET_CRS, OUTPUT |
| `gdal:warpreproject` | reproject a raster | INPUT, TARGET_CRS, RESAMPLING (0 nearest, 1 bilinear), TARGET_RESOLUTION, OUTPUT |
| `native:assignprojection` | fix a wrong CRS label (no transform) | INPUT, CRS, OUTPUT |
| `native:clip` | clip vectors by polygons (attributes kept) | INPUT, OVERLAY, OUTPUT |
| `native:extractbylocation` | keep whole features that intersect, are within … | INPUT, PREDICATE (0 intersect, 6 within), INTERSECT, OUTPUT |
| `native:extractbyexpression` | attribute filter | INPUT, EXPRESSION, OUTPUT |
| `gdal:cliprasterbymasklayer` | clip a raster by polygons | INPUT, MASK, CROP_TO_CUTLINE=true, OUTPUT |
| `native:buffer` | buffer | INPUT, DISTANCE, SEGMENTS=8, DISSOLVE=false, END_CAP_STYLE (0 round, 1 flat), OUTPUT |
| `native:dissolve` | merge geometries | INPUT, FIELD (optional), OUTPUT |
| `native:mergevectorlayers` | stack layers of one geometry type | LAYERS (repeat), CRS, OUTPUT; adds `layer`/`path` fields |
| `native:pointstopath` | ordered points → line | INPUT, ORDER_EXPRESSION, GROUP_EXPRESSION, OUTPUT |
| `native:explodelines` | a line → one feature per segment | INPUT, OUTPUT |
| `native:splitlinesbylength` | chop lines into pieces | INPUT, LENGTH (CRS units), OUTPUT |
| `native:pointsalonglines` | points every N units along lines | INPUT, DISTANCE, START_OFFSET, OUTPUT |
| `native:densifygeometriesgivenaninterval` | add vertices every N units | INPUT, INTERVAL, OUTPUT |
| `native:heatmapkerneldensityestimation` | KDE raster | INPUT (points), RADIUS, PIXEL_SIZE, WEIGHT_FIELD, KERNEL (0 quartic … 4 epanechnikov), OUTPUT_VALUE (0 raw, 1 scaled), OUTPUT |
| `native:fieldcalculator` | add or compute a field | INPUT, FIELD_NAME, FIELD_TYPE (0 decimal, 1 int, 2 string), FORMULA, OUTPUT |
| `native:joinattributesbylocation` | spatial join | INPUT, JOIN, PREDICATE, METHOD, OUTPUT |
| `native:countpointsinpolygon` | point counts per polygon | POLYGONS, POINTS, FIELD, OUTPUT |
| `native:savefeatures` | copy / convert / add a layer to a file | INPUT, OUTPUT, LAYER_NAME, ACTION_ON_EXISTING_FILE |
| `native:package` | many layers → one GPKG | LAYERS (repeat), OUTPUT, OVERWRITE |
| `gdal:contour` | contour lines from a DEM | INPUT, BAND, INTERVAL, FIELD_NAME, OUTPUT |
| `gdal:hillshade` | hillshade from a DEM | INPUT, Z_FACTOR, AZIMUTH, ALTITUDE, OUTPUT |
| `native:zonalstatisticsfb` | raster stats per polygon | INPUT, INPUT_RASTER, STATISTICS, OUTPUT |
| `native:printlayouttopdf` / `native:printlayouttoimage` | export a project's layout | LAYOUT (name), DPI, OUTPUT, with `--PROJECT_PATH` |
| `native:atlaslayouttopdf` / `…toimage` | export an atlas | LAYOUT, COVERAGE_LAYER, FILTER_EXPRESSION, OUTPUT |

Always confirm the parameter names with `help` for anything not in this table.
Parameters are occasionally renamed between minor versions.

## From PyQGIS

```python
from qgis_boot import start
start(processing=True)
import processing
res = processing.run("native:buffer", {"INPUT": layer_or_path, "DISTANCE": 100,
                                       "OUTPUT": "TEMPORARY_OUTPUT"})
buf = res["OUTPUT"]          # a QgsVectorLayer for TEMPORARY_OUTPUT, else the path
```

`processing.run` raises `QgsProcessingException` on failure. A layer object, memory
layers included, is a valid input. `TEMPORARY_OUTPUT` returns an in-memory
`QgsVectorLayer` for vector outputs.
