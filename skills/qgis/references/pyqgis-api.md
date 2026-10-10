# PyQGIS 4.x reference for headless scripts

QGIS 4 is built on Qt 6 and PyQt6. The scoped enums (`Qgis.GeometryType.Line`,
`QgsLayoutExporter.ExportResult.Success`) are the 4.x spelling. In 4.2 most 3.x
spellings (`QgsWkbTypes.LineGeometry`, `QgsUnitTypes.DistanceKilometers`,
`QgsLayoutExporter.Success`) still work, so both appear in older code. `QgsField`
accepts both `QVariant.Int` and `QMetaType.Type.Int`.

## Contents
- [Bootstrap](#bootstrap)
- [Loading data](#loading-data)
- [CRS and transforms](#crs-and-transforms)
- [Features and memory layers](#features-and-memory-layers)
- [Writing files](#writing-files)
- [Styling](#styling)
- [Labels](#labels)
- [Print layouts](#print-layouts)
- [Projects](#projects)

## Bootstrap

```python
import sys; sys.path.insert(0, "<skill>/scripts")
from qgis_boot import start, emit
start(processing=True)            # QgsApplication([], False) + initQgis (+ Processing)
...
emit({"ok": True, ...})           # prints JSON, then os._exit — skips a teardown crash
```

Run it with `bash scripts/qgis.sh python script.py`. `iface` doesn't exist headless,
so canvas and GUI calls (`iface.mapCanvas()`, `iface.activeLayer()`) can't be used.
Work with layers, the project and layouts instead.

## Loading data

```python
from qgis.core import QgsVectorLayer, QgsRasterLayer, QgsProviderRegistry
QgsVectorLayer("/d/a.gpkg|layername=roads", "roads", "ogr")
QgsVectorLayer("/d/run.gpx|layername=track_points", "pts", "ogr")   # tracks, routes, route_points, waypoints
QgsVectorLayer("/d/a.geojson", "a", "ogr")
QgsVectorLayer("/d/a.csv?type=csv&xField=lon&yField=lat&crs=EPSG:4326", "csv", "delimitedtext")
QgsRasterLayer("/d/dem.tif", "dem")
QgsRasterLayer("type=xyz&url=https://tile.openstreetmap.org/{z}/{x}/{y}.png&zmax=19&zmin=0", "OSM", "wms")
[(s.name(), s.uri()) for s in QgsProviderRegistry.instance().querySublayers("/d/a.gpkg")]
```

Always check `layer.isValid()`. An invalid layer has 0 features and an empty extent,
and it raises no error. GPX `track_points` fields are `track_fid`, `track_seg_id`,
`track_seg_point_id`, `ele`, `time` …, and the geometry is PointZ, with elevation in
both Z and `ele`.

## CRS and transforms

```python
from qgis.core import QgsCoordinateReferenceSystem as CRS, QgsCoordinateTransform, QgsProject
eov = CRS("EPSG:23700"); assert eov.isValid()
xf = QgsCoordinateTransform(layer.crs(), eov, QgsProject.instance())
g = QgsGeometry(f.geometry()); g.transform(xf)           # in place
bbox = xf.transformBoundingBox(layer.extent())
```

- Metric CRSs: the local UTM zone (`utm_crs(lon, lat)` in qgis_boot), EOV `EPSG:23700`
  for Hungary, Web Mercator `EPSG:3857` (only for tiles; it distorts distances by
  1/cos(lat), about ×1.5 at 47° N).
- Ellipsoidal lengths and areas: `QgsDistanceArea()` with `setSourceCrs(crs,
  ctx)` and `setEllipsoid("EPSG:7030")`, then `measureLine(p1, p2)` or
  `measureLength(geom)` in metres.

## Features and memory layers

```python
lyr = QgsVectorLayer("LineString?crs=EPSG:4326&field=ele:double&field=name:string", "seg", "memory")
f = QgsFeature(lyr.fields())
f.setGeometry(QgsGeometry.fromPolylineXY([QgsPointXY(x1, y1), QgsPointXY(x2, y2)]))
f.setAttributes([312.5, "a"])
lyr.dataProvider().addFeatures([f]); lyr.updateExtents()
for f in lyr.getFeatures(QgsFeatureRequest().setFilterExpression('"ele" > 300')): ...
```

Memory layers are lost when a project is saved. Write them to a GPKG first.
`geom.interpolate(d)`, `geom.length()` and `geom.area()` work in CRS units.

## Writing files

```python
from qgis.core import QgsVectorFileWriter
o = QgsVectorFileWriter.SaveVectorOptions()
o.driverName = "GPKG"; o.layerName = "roads_eov"
o.ct = QgsCoordinateTransform(lyr.crs(), CRS("EPSG:23700"), QgsProject.instance())  # optional reprojection
o.actionOnExistingFile = QgsVectorFileWriter.CreateOrOverwriteLayer                 # keep other layers
err, msg, path, layer = QgsVectorFileWriter.writeAsVectorFormatV3(lyr, "out.gpkg", QgsProject.instance().transformContext(), o)
assert err == QgsVectorFileWriter.NoError, msg
```

Without `actionOnExistingFile` the default is `CreateOrOverwriteFile`, which deletes
every other layer in the GPKG. The output CRS is the source's unless `o.ct` is set.

## Styling

```python
from qgis.core import (QgsGraduatedSymbolRenderer, QgsClassificationJenks, QgsStyle, QgsLineSymbol,
    QgsCategorizedSymbolRenderer, QgsRendererCategory, QgsSymbol, QgsSingleSymbolRenderer)
r = QgsGraduatedSymbolRenderer("ele")
r.setSourceSymbol(QgsLineSymbol.createSimple({"line_width": "1.2"}))
ramp = QgsStyle.defaultStyle().colorRamp("Spectral"); ramp.invert(); r.setSourceColorRamp(ramp)
r.setClassificationMethod(QgsClassificationJenks())     # EqualInterval, Quantile, PrettyBreaks
r.updateClasses(lyr, 7); lyr.setRenderer(r)

cats = [QgsRendererCategory(v, QgsSymbol.defaultSymbol(lyr.geometryType()), str(v)) for v in lyr.uniqueValues(lyr.fields().indexOf("type"))]
lyr.setRenderer(QgsCategorizedSymbolRenderer("type", cats))
```

- The default style has 35 ramps, including `Spectral`, `Viridis`, `Magma`, `Inferno`,
  `Turbo`, `RdYlGn` and `Blues`.
- **Data-defined colour** without classes uses a symbol layer property:
  `sym.symbolLayer(0).setDataDefinedProperty(QgsSymbolLayer.Property.StrokeColor,
  QgsProperty.fromExpression("ramp_color('Spectral', scale_linear(\"ele\",100,500,1,0))"))`.
- **Raster pseudocolor:** `QgsColorRampShader(min, max)` with
  `setColorRampItemList([...ColorRampItem(value, QColor, label)])`, inside a
  `QgsRasterShader`, inside a `QgsSingleBandPseudoColorRenderer(provider, 1, shader)`.
  A first item with alpha 0 at 0 makes zero transparent.
- Saving and loading styles: `lyr.saveNamedStyle("a.qml")`, `lyr.loadNamedStyle("a.qml")`.
  This is the way to reuse a style the user designed in the GUI.

## Labels

```python
from qgis.core import QgsPalLayerSettings, QgsTextFormat, QgsVectorLayerSimpleLabeling
s = QgsPalLayerSettings(); s.fieldName = "name"; s.enabled = True
fmt = QgsTextFormat(); fmt.setSize(9); s.setFormat(fmt)
s.placement = Qgis.LabelPlacement.Line        # for lines; AroundPoint / OverPoint for points
lyr.setLabeling(QgsVectorLayerSimpleLabeling(s)); lyr.setLabelsEnabled(True)
```

For km markers along a course, run `native:pointsalonglines` with DISTANCE=1000 in a
metric CRS, then label with `round("distance"/1000)`.

## Print layouts

```python
from qgis.core import (QgsPrintLayout, QgsLayoutItemMap, QgsLayoutItemLabel, QgsLayoutItemLegend,
    QgsLayoutItemScaleBar, QgsLayoutItemPicture, QgsLayoutPoint, QgsLayoutSize, QgsLayoutExporter)
lay = QgsPrintLayout(QgsProject.instance()); lay.initializeDefaults()     # one A4 landscape page
lay.pageCollection().page(0).setPageSize(QgsLayoutSize(210, 297))         # mm; portrait A4
m = QgsLayoutItemMap(lay); m.attemptMove(QgsLayoutPoint(10, 20)); m.attemptResize(QgsLayoutSize(190, 250))
m.setCrs(crs); m.setLayers([top, ..., bottom]); lay.addLayoutItem(m); m.zoomToExtent(extent_in_map_crs)
m.setScale(25000)                                                          # fixed scale instead
```

- Item order: `setLayers` takes the top layer first. Call `zoomToExtent` **after**
  `addLayoutItem` and `attemptResize`, or the aspect ratio is wrong.
- **Scale bar:** `setLinkedMap(m)`, `setStyle("Single Box")`,
  `setUnits(QgsUnitTypes.DistanceKilometers)`, `setUnitLabel("km")`,
  `applyDefaultSize(...)`. In a geographic map CRS the bar is meaningless, so use a
  projected map CRS.
- **North arrow:** a `QgsLayoutItemPicture` with
  `setPicturePath(QgsApplication.pkgDataPath() + "/svg/arrows/NorthArrow_02.svg")` and
  `setLinkedMap(m)`.
- **Legend:** `setLinkedMap(m)`; `setSyncMode(Qgis.LegendSyncMode.Manual)` (4.0+;
  `setAutoUpdateModel(False)` in 3.x); then `model().rootGroup()` with
  `removeAllChildren()` / `addLayer(lyr)`. Hide a layer's name with
  `QgsLegendRenderer.setNodeLegendStyle(node, QgsLegendStyle.Hidden)`.
- **Export:** set `QgsLayoutExporter(lay)` with `exportToPdf(path,
  PdfExportSettings())`, `exportToImage(path, ImageExportSettings())` or
  `exportToSvg`. Set `settings.dpi`. Use `forceVectorOutput=True` for vector PDFs and
  `generateWorldFile=False` for PNGs (it avoids GDAL's `ERROR 6`). The result `0`
  means success, and `exporter.errorMessage()` gives the reason otherwise.
- **Atlas:** `lay.atlas().setCoverageLayer(lyr)`, `setEnabled(True)`, and
  `m.setAtlasDriven(True)`. Then the static
  `QgsLayoutExporter.exportToPdf(lay.atlas(), path, settings)` makes one multi-page
  file, and `exportToPdfs(...)` makes one file per feature.
- **Templates:** load a `.qpt` with `QgsReadWriteContext()`,
  `doc = QDomDocument(); doc.setContent(open(p).read())`, then
  `lay.loadFromTemplate(doc, ctx)`. Then find items by id:
  `lay.itemById("title").setText(...)`.

## Projects

```python
p = QgsProject.instance(); p.read("in.qgz")
p.mapLayersByName("roads")[0]; p.layoutManager().layoutByName("A3")
p.setCrs(CRS("EPSG:23700")); p.addMapLayers([a, b]); p.layoutManager().addLayout(lay)
p.write("out.qgz")
```

`p.read` returns False on a missing file but True even when layer sources are broken.
Check every `lyr.isValid()` afterwards, as `layout_export.py` does.
