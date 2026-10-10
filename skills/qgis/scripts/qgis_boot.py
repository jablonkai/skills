"""Shared helpers for the skill's PyQGIS scripts (QGIS 4.x, also 3.34+).

Run scripts through `qgis.sh python`, which sets the environment the bundled
interpreter needs. Import this module first: it starts a headless QgsApplication.

    from qgis_boot import start, emit, fail, load_vector, utm_crs, map_layout, export_layout
    start()
"""

import glob
import json
import math
import os
import sys

from qgis.core import (
    Qgis,
    QgsApplication,
    QgsCoordinateReferenceSystem,
    QgsCoordinateTransform,
    QgsLayoutExporter,
    QgsLayoutItemLabel,
    QgsLayoutItemLegend,
    QgsLayoutItemMap,
    QgsLayoutItemPicture,
    QgsLayoutItemScaleBar,
    QgsLayoutPoint,
    QgsLayoutSize,
    QgsLegendRenderer,
    QgsLegendStyle,
    QgsMapLayerLegendUtils,
    QgsPrintLayout,
    QgsProject,
    QgsProviderRegistry,
    QgsRasterLayer,
    QgsRectangle,
    QgsTextFormat,
    QgsUnitTypes,
    QgsVectorLayer,
)

_app = None
_processing = False

# Exit codes shared by every script.
# 2 usage, 3 missing or unreadable input, 4 verification failed, 5 QGIS/processing error.
EXIT_OK, EXIT_USAGE, EXIT_INPUT, EXIT_VERIFY, EXIT_QGIS = 0, 2, 3, 4, 5


def start(processing=False):
    """Start a headless QGIS once; with processing=True also load Processing."""
    global _app, _processing
    if _app is None:
        _app = QgsApplication([], False)
        _app.initQgis()
        # Scale bars and legends follow the system locale (e.g. "2,5 km" on a Hungarian
        # Mac); QGIS_LOCALE=hu_HU (or any) overrides the English default.
        from qgis.PyQt.QtCore import QLocale

        QLocale.setDefault(QLocale(os.environ.get("QGIS_LOCALE", "en_US")))
    if processing and not _processing:
        from processing.core.Processing import Processing

        Processing.initialize()
        _processing = True
    return _app


def emit(obj, code=EXIT_OK):
    """Print the JSON result on stdout and exit with `code`."""
    sys.stdout.write(json.dumps(obj, indent=2, ensure_ascii=False, default=str) + "\n")
    sys.stdout.flush()
    # exitQgis() can crash in Qt teardown after a layout export on some builds and turn
    # a success into a non-zero status; the result is already written, so skip it.
    os._exit(code)


def fail(message, code=EXIT_QGIS, **extra):
    sys.stderr.write(f"error: {message}\n")
    emit({"ok": False, "error": message, **extra}, code)


def sublayers(path):
    """[(name, uri)] for a multi-layer file (GPX, GeoPackage, ...)."""
    return [(s.name(), s.uri()) for s in QgsProviderRegistry.instance().querySublayers(path)]


def load_vector(source, name=None, prefer=None):
    """Load a vector layer from `path` or `path|layername=x`.

    For a multi-layer file without a layername, the first non-empty sublayer named
    in `prefer` (e.g. ["track_points", "route_points"]) wins, else the first one.
    """
    path = source.split("|", 1)[0]
    if not os.path.exists(path):
        fail(f"no such file: {path}", EXIT_INPUT)
    uri = source
    if "|" not in source:
        subs = sublayers(path)
        if len(subs) > 1:
            by_name = dict(subs)
            uri = subs[0][1]
            for want in prefer or []:
                if want in by_name:
                    probe = QgsVectorLayer(by_name[want], want, "ogr")
                    if probe.isValid() and probe.featureCount() > 0:
                        uri = by_name[want]
                        break
    layer = QgsVectorLayer(uri, name or os.path.splitext(os.path.basename(path))[0], "ogr")
    if not layer.isValid():
        fail(f"not a readable vector layer: {source}", EXIT_INPUT)
    return layer


def band_stats(provider, band=1):
    """Full band statistics. QGIS 4.2's binding flags every call as deprecated, even
    with the enum it asks for, so the warning is silenced here."""
    import warnings

    flag = Qgis.RasterBandStatistic.All if hasattr(Qgis, "RasterBandStatistic") else 127
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        return provider.bandStatistics(band, flag)


def load_raster(path, name=None):
    layer = QgsRasterLayer(path, name or os.path.splitext(os.path.basename(path))[0])
    if not layer.isValid():
        fail(f"not a readable raster: {path}", EXIT_INPUT)
    return layer


def utm_crs(lon, lat):
    """WGS 84 / UTM zone for a point: a metric CRS for distances, buffers, heatmaps."""
    zone = int(math.floor((lon + 180) / 6)) + 1
    return QgsCoordinateReferenceSystem(f"EPSG:{(32600 if lat >= 0 else 32700) + zone}")


def crs_or_fail(spec):
    crs = QgsCoordinateReferenceSystem(spec)
    if not crs.isValid():
        fail(f"unknown CRS {spec!r} (use an authority id like EPSG:23700)", EXIT_USAGE)
    return crs


def transform_extent(extent, src_crs, dst_crs):
    if src_crs == dst_crs:
        return QgsRectangle(extent)
    return QgsCoordinateTransform(src_crs, dst_crs, QgsProject.instance()).transformBoundingBox(extent)


def north_arrow_svg():
    found = sorted(glob.glob(os.path.join(QgsApplication.pkgDataPath(), "svg", "arrows", "NorthArrow_0*.svg")))
    return found[1] if len(found) > 1 else (found[0] if found else None)


def _text(size, bold=False):
    fmt = QgsTextFormat()
    font = fmt.font()
    font.setFamily("Helvetica")
    font.setBold(bold)
    fmt.setFont(font)
    fmt.setSize(size)
    return fmt


def map_layout(project, layers, extent, title="", subtitle="", legend_layers=None,
               legend_title="", page="A4", orientation="auto", margin=0.08, crs=None):
    """A one-map print layout: title, subtitle, map, legend, scale bar, north arrow.

    `extent` is in `crs` (default: the project CRS). Returns (layout, map_item).
    """
    sizes = {"A4": (297, 210), "A3": (420, 297), "A5": (210, 148), "LETTER": (279.4, 215.9)}
    long_mm, short_mm = sizes.get(page.upper(), sizes["A4"])
    if orientation == "auto":
        orientation = "landscape" if extent.width() >= extent.height() else "portrait"
    w, h = (long_mm, short_mm) if orientation == "landscape" else (short_mm, long_mm)

    layout = QgsPrintLayout(project)
    layout.initializeDefaults()
    layout.setName(title or "Map")
    pc = layout.pageCollection()
    pc.page(0).setPageSize(QgsLayoutSize(w, h))

    m = 10.0
    top = m
    if title:
        lbl = QgsLayoutItemLabel(layout)
        lbl.setText(title)
        lbl.setTextFormat(_text(20, bold=True))
        lbl.attemptMove(QgsLayoutPoint(m, top))
        lbl.attemptResize(QgsLayoutSize(w - 2 * m, 10))
        layout.addLayoutItem(lbl)
        top += 11
    if subtitle:
        sub = QgsLayoutItemLabel(layout)
        sub.setText(subtitle)
        sub.setTextFormat(_text(10))
        sub.attemptMove(QgsLayoutPoint(m, top))
        sub.attemptResize(QgsLayoutSize(w - 2 * m, 6))
        layout.addLayoutItem(sub)
        top += 7

    map_h = h - top - m - 12  # room for the scale bar below the map
    mp = QgsLayoutItemMap(layout)
    mp.attemptMove(QgsLayoutPoint(m, top))
    mp.attemptResize(QgsLayoutSize(w - 2 * m, map_h))
    if crs is not None:
        mp.setCrs(crs)
    ext = QgsRectangle(extent)
    ext.scale(1 + margin * 2)
    mp.setLayers(layers)
    mp.setFrameEnabled(True)
    layout.addLayoutItem(mp)
    mp.zoomToExtent(ext)

    sb = QgsLayoutItemScaleBar(layout)
    sb.setLinkedMap(mp)
    sb.setStyle("Single Box")
    sb.setUnits(QgsUnitTypes.DistanceKilometers)
    sb.setUnitLabel("km")
    sb.setNumberOfSegments(4)
    sb.setNumberOfSegmentsLeft(0)
    sb.applyDefaultSize(QgsUnitTypes.DistanceKilometers)
    sb.setTextFormat(_text(8))
    sb.attemptMove(QgsLayoutPoint(m, top + map_h + 2))
    layout.addLayoutItem(sb)

    svg = north_arrow_svg()
    if svg:
        na = QgsLayoutItemPicture(layout)
        na.setPicturePath(svg)
        na.attemptResize(QgsLayoutSize(12, 18))
        na.attemptMove(QgsLayoutPoint(w - m - 16, top + 4))
        na.setLinkedMap(mp)
        layout.addLayoutItem(na)

    if legend_layers:
        lg = QgsLayoutItemLegend(layout)
        lg.setLinkedMap(mp)
        if hasattr(lg, "setSyncMode"):  # 4.0+
            lg.setSyncMode(Qgis.LegendSyncMode.Manual)
        else:
            lg.setAutoUpdateModel(False)
        root = lg.model().rootGroup()
        root.removeAllChildren()
        for lyr in legend_layers:
            node = root.addLayer(lyr)
            if legend_title and len(legend_layers) == 1:
                # The legend title already names the layer; don't print it twice.
                QgsLegendRenderer.setNodeLegendStyle(node, QgsLegendStyle.Hidden)
            if isinstance(lyr, QgsRasterLayer):
                # A raster's first legend node is the "Band 1 (Gray)" caption; keep
                # only the colour ramp below it.
                n = len(lg.model().layerLegendNodes(node, True))
                if n > 1:
                    QgsMapLayerLegendUtils.setLegendNodeOrder(node, list(range(1, n)))
                    lg.model().refreshLayerLegend(node)
        lg.setTitle(legend_title)
        lg.setFrameEnabled(True)
        lg.setBackgroundEnabled(True)
        for part, size, bold in ((QgsLegendStyle.Title, 10, True), (QgsLegendStyle.Subgroup, 9, True),
                                 (QgsLegendStyle.SymbolLabel, 8, False)):
            lg.rstyle(part).setTextFormat(_text(size, bold))
        lg.attemptMove(QgsLayoutPoint(m + 3, top + 3))
        layout.addLayoutItem(lg)
        lg.adjustBoxSize()
    return layout, mp


def export_layout(layout, outputs, dpi=300):
    """Export to every path in `outputs` by extension (.pdf, .png, .jpg, .svg, .tif)."""
    exporter = QgsLayoutExporter(layout)
    done = []
    for out in outputs:
        out = os.path.abspath(out)
        os.makedirs(os.path.dirname(out), exist_ok=True)
        ext = os.path.splitext(out)[1].lower()
        if ext == ".pdf":
            s = QgsLayoutExporter.PdfExportSettings()
            s.dpi = dpi
            s.rasterizeWholeImage = False
            s.forceVectorOutput = True
            # QGIS defaults to text-as-outlines: the PDF looks right but its title and
            # labels can't be searched, copied or read by a screen reader.
            s.textRenderFormat = Qgis.TextRenderFormat.AlwaysText
            res = exporter.exportToPdf(out, s)
        elif ext == ".svg":
            s = QgsLayoutExporter.SvgExportSettings()
            s.dpi = dpi
            res = exporter.exportToSvg(out, s)
        elif ext in (".png", ".jpg", ".jpeg", ".tif", ".tiff"):
            s = QgsLayoutExporter.ImageExportSettings()
            s.dpi = dpi
            s.generateWorldFile = False  # avoids the GDAL "PNG update access" error
            res = exporter.exportToImage(out, s)
        else:
            fail(f"unsupported output type {ext} (use .pdf, .png, .jpg, .svg or .tif)", EXIT_USAGE)
        if res != QgsLayoutExporter.Success:
            fail(f"layout export to {out} failed: {exporter.errorMessage() or res}", EXIT_QGIS)
        done.append({"path": out, "bytes": os.path.getsize(out)})
    return done
