# Gotchas (QGIS 4.2.3, macOS)

## Environment
- **Bare `qgis_process` gives `Cannot find proj.db`.** Its EPSG registry is then empty
  and CRS lookups fail silently. **The bundled python3.12 dies with `No module named
  'encodings'`** unless `PYTHONHOME=Contents/Frameworks` (what the bundle's own
  `MacOS/python` wrapper sets). `qgis.sh` sets `PROJ_DATA`, `GDAL_DATA`, `PYTHONHOME`,
  `PYTHONPATH`, `QGIS_PREFIX_PATH` and `QT_QPA_PLATFORM=offscreen`. For a shell of your own, run
  `eval "$(bash scripts/qgis.sh env)"`, which also exports `$QGIS_PYTHON` and
  `$QGIS_PROCESS`.
- **`QGIS_PREFIX_PATH` must be the `.app`, not `Contents/MacOS`.** With the wrong value
  `pkgDataPath()` points nowhere, so north arrows, SVG markers and the default style
  ramps go missing without an error.
- **`--skip-loading-plugins` unloads the core Processing plugin** and with it all 59
  `gdal:*` algorithms. The skill uses a skill-owned profile instead
  (`QGIS_CUSTOM_CONFIG_PATH`), which keeps user plugins out without losing GDAL.
- **The system Python can't import `qgis`.** Only the bundled interpreter matches the
  compiled bindings. Don't `pip install` into the app bundle: it modifies a signed
  app, and updates replace it anyway. Use what the bundle ships (numpy and GDAL's
  `osgeo` are included).
- **Harmless noise that the wrapper filters:** `qt.qpa.fonts … missing font family`, `ERROR 6: PNG driver does not
  support update access` (from the world-file write; the PNG itself is fine). Set
  `QGIS_VERBOSE=1` to see everything.
- Each process takes about 2–3 s to start. Batch work into one script rather than
  calling `qgis_process` 50 times.

## Units and CRS
- **Distances follow the layer's CRS units.** Buffer, heatmap radius and pixel size,
  `splitlinesbylength` and `pointsalonglines` all read degrees on EPSG:4326 data.
  GPX and GeoJSON are always EPSG:4326, so reproject to UTM or EOV (EPSG:23700) first.
- **A scale bar on a geographic map is wrong.** Set the map item's CRS to a projected
  CRS.
- **EPSG:3857 distorts distances.** It's about ×1.47 at 47° N. Use it for web tiles,
  never for measuring.
- **A wrong CRS label is not a transform.** When coordinates look like metres but the
  file says EPSG:4326, fix the label with `native:assignprojection`. Reprojecting would
  move everything to nonsense.
- An extent string is `xmin,xmax,ymin,ymax`, with both x values first, not the
  bbox order.

## Data
- **GPX is multi-layer:** `tracks`, `track_points`, `routes`, `route_points` and
  `waypoints`. Opening the bare path takes the first sublayer, which is `waypoints` and
  often empty. Use `|layername=track_points` (`load_vector(..., prefer=[...])` does it).
- GPX elevation sits in both `ele` and the geometry's Z. Some exports (Strava routes,
  hand-drawn courses) have neither. Say so instead of colouring by nothing.
- GPX `time` loads as a datetime field. Sort track points by `track_fid`,
  `track_seg_id` and `track_seg_point_id`, not by feature id, when you rebuild lines.
- **Invalid layers don't raise.** `QgsVectorLayer("missing.gpkg", …)` is just
  `isValid() == False`, with 0 features and an empty extent. Always check it.
- Projects with broken paths still load (`read()` is True) and export empty maps.
  `layout_export.py` refuses them unless `--allow-missing` is passed.

## Outputs
- **`OUTPUT=x.gpkg` deletes every other layer in `x.gpkg`.** Use the table syntax
  `OUTPUT="ogr:dbname='x.gpkg' table=\"name\" (geom)"`. In PyQGIS use
  `actionOnExistingFile = CreateOrOverwriteLayer`.
- **Reading and writing the same GPKG in one run gives an empty layer.** Go through a
  temporary file.
- **Memory layers aren't saved in a `.qgz`.** Persist them to a GPKG first and repoint
  them with `setDataSource`.
- Shapefile truncates field names to 10 characters and needs sidecar files. Prefer GPKG
  unless the user asks for SHP.
- `QgsLayoutExporter` returns `0` on success. Always compare against `Success`,
  because a failed export can still leave a 0-byte file behind.

## Rendering
- **Locale:** scale bars and legends follow `QLocale`. On a Hungarian system they show
  "2,5 km". `qgis_boot.start()` defaults to en_US; set `QGIS_LOCALE=hu_HU` for
  Hungarian output.
- Fonts: the default "Open Sans"/"Sans Serif" are not on macOS. `qgis_boot` uses
  Helvetica. Name an installed font explicitly in custom layouts.
- After `addLayoutItem`, call `map.zoomToExtent()` **after** setting the size, or the
  extent keeps the default aspect ratio.
- Raster legends show a "Band 1 (Gray)" caption. `map_layout` hides that node.
- OSM tiles need network and the attribution "© OpenStreetMap contributors". Respect the
  tile usage policy: one map export is fine, bulk tile scraping isn't.
- `exitQgis()` can crash during Qt teardown after an export. `emit()` uses `os._exit`
  after flushing the JSON.

## Security posture (#17, #22, #32, #35)
- **No listener.** The skill never opens a port, socket or pipe. Each call is a
  child process that exits, so cross-origin requests (#17) and token auth (#32) don't
  apply.
- **Scope (#22).** Scripts read only the paths they are given and write only to their
  output paths and a temp dir (the heatmap's intermediate GPKG). The headless runs use
  `~/Library/Caches/qgis-skill/profile`, never the user's QGIS profile, so the user's
  plugins and their Python startup code are not executed. The only network access is
  `--basemap osm` (tile fetches) and anything a custom script does on purpose.
- **Python in projects.** `.qgz` files can embed Python macros and expression
  functions. The skill never enables macros and its profile has no trust settings.
  Still, don't open an untrusted project in the user's GUI (`qgis.sh open`) on their
  behalf, because their profile may allow macros.
- **Stop path (#35).** Every call is killed after `QGIS_TIMEOUT` seconds (default 300,
  exit 124). There is no daemon to stop. `pkill -f qgis_process` clears anything left
  over from a killed shell.
