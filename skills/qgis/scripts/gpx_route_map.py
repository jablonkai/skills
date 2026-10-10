"""Render a GPX route as a print-ready map with the line coloured by elevation.

    bash qgis.sh python gpx_route_map.py ROUTE.gpx -o map.pdf [-o map.png]
        [--title "Buda Hills 25K"] [--classes 7] [--ramp Spectral] [--mode jenks]
        [--width 1.4] [--page A4] [--orientation auto] [--dpi 300]
        [--km-every auto|N|0] [--basemap none|osm] [--project map.qgz] [--save-segments segs.gpkg]

The track points become one line segment per pair of consecutive points, carrying the
mean elevation of its two ends; a graduated renderer colours the segments (low = cool,
high = warm with the default inverted Spectral ramp). The map is drawn in the local
UTM zone, so the scale bar is in true kilometres. The layout has the title, a subtitle
with distance / ascent / elevation range, a legend, a scale bar and a north arrow, and
labelled distance markers along the course (every 1/5/10/25 km by length; --km-every).

--basemap osm adds OpenStreetMap tiles (needs network; the attribution is added).
Prints JSON: outputs, segment count, CRS, stats. Exit 3 when the GPX has no
elevation, 5 on an export failure.
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from qgis_boot import (  # noqa: E402
    EXIT_INPUT,
    EXIT_USAGE,
    emit,
    export_layout,
    fail,
    load_vector,
    map_layout,
    start,
    utm_crs,
)

from qgis.core import (  # noqa: E402
    Qgis,
    QgsClassificationEqualInterval,
    QgsClassificationJenks,
    QgsClassificationPrettyBreaks,
    QgsClassificationQuantile,
    QgsCoordinateReferenceSystem,
    QgsCoordinateTransform,
    QgsDistanceArea,
    QgsFeature,
    QgsField,
    QgsGeometry,
    QgsGradientColorRamp,
    QgsGraduatedSymbolRenderer,
    QgsLayoutItemLabel,
    QgsLayoutPoint,
    QgsLayoutSize,
    QgsLineSymbol,
    QgsMarkerSymbol,
    QgsPalLayerSettings,
    QgsPointXY,
    QgsProject,
    QgsRasterLayer,
    QgsSingleSymbolRenderer,
    QgsStyle,
    QgsTextBufferSettings,
    QgsTextFormat,
    QgsVectorFileWriter,
    QgsVectorLayer,
    QgsVectorLayerSimpleLabeling,
)
from qgis.PyQt.QtCore import QVariant  # noqa: E402
from qgis.PyQt.QtGui import QColor  # noqa: E402

WGS84 = QgsCoordinateReferenceSystem("EPSG:4326")
MODES = {"jenks": QgsClassificationJenks, "equal": QgsClassificationEqualInterval,
         "quantile": QgsClassificationQuantile, "pretty": QgsClassificationPrettyBreaks}


def read_points(layer, field):
    """[(track_key, seq, lon, lat, ele)] in file order; ele from `field` or the Z value."""
    names = layer.fields().names()
    has_field = field in names
    pts = []
    for n, f in enumerate(layer.getFeatures()):
        g = f.geometry()
        if g.isEmpty():
            continue
        p = g.constGet()
        ele = f[field] if has_field else None
        if ele in (None, "") or (hasattr(ele, "isNull") and ele.isNull()):
            ele = p.z() if p.is3D() else None
        key = tuple(f[k] for k in ("track_fid", "track_seg_id", "route_fid") if k in names)
        seq = f["track_seg_point_id"] if "track_seg_point_id" in names else (
            f["route_point_id"] if "route_point_id" in names else n)
        pts.append((key, seq, p.x(), p.y(), None if ele is None else float(ele)))
    pts.sort(key=lambda t: (t[0], t[1]))
    return pts


def build_segments(pts, crs_src):
    seg = QgsVectorLayer(f"LineString?crs={crs_src.authid()}", "Elevation", "memory")
    pr = seg.dataProvider()
    pr.addAttributes([QgsField("seg", QVariant.Int), QgsField("ele", QVariant.Double),
                      QgsField("ele_from", QVariant.Double), QgsField("ele_to", QVariant.Double)])
    seg.updateFields()
    feats = []
    for i in range(1, len(pts)):
        a, b = pts[i - 1], pts[i]
        if a[0] != b[0] or a[4] is None or b[4] is None:
            continue  # a new track/segment starts, or a point lacks elevation
        f = QgsFeature(seg.fields())
        f.setGeometry(QgsGeometry.fromPolylineXY([QgsPointXY(a[2], a[3]), QgsPointXY(b[2], b[3])]))
        f.setAttributes([i, (a[4] + b[4]) / 2, a[4], b[4]])
        feats.append(f)
    pr.addFeatures(feats)
    seg.updateExtents()
    return seg


def stats(pts):
    da = QgsDistanceArea()
    da.setSourceCrs(WGS84, QgsProject.instance().transformContext())
    da.setEllipsoid("EPSG:7030")
    dist = ascent = descent = 0.0
    eles = [p[4] for p in pts if p[4] is not None]
    for i in range(1, len(pts)):
        a, b = pts[i - 1], pts[i]
        if a[0] != b[0]:
            continue
        dist += da.measureLine(QgsPointXY(a[2], a[3]), QgsPointXY(b[2], b[3]))
        if a[4] is not None and b[4] is not None:
            d = b[4] - a[4]
            ascent += max(d, 0)
            descent += max(-d, 0)
    return {"distance_km": round(dist / 1000, 2), "ascent_m": round(ascent), "descent_m": round(descent),
            "ele_min": round(min(eles), 1) if eles else None, "ele_max": round(max(eles), 1) if eles else None,
            "points": len(pts), "points_with_ele": len(eles)}


def km_markers(pts, step_km, crs_src):
    """Point layer with a labelled marker every `step_km` along the course."""
    lyr = QgsVectorLayer(f"Point?crs={crs_src.authid()}&field=km:double&field=label:string", "Distance", "memory")
    da = QgsDistanceArea()
    da.setSourceCrs(WGS84, QgsProject.instance().transformContext())
    da.setEllipsoid("EPSG:7030")
    feats, done, nxt = [], 0.0, step_km * 1000
    for i in range(1, len(pts)):
        a, b = pts[i - 1], pts[i]
        if a[0] != b[0]:
            continue
        d = da.measureLine(QgsPointXY(a[2], a[3]), QgsPointXY(b[2], b[3]))
        while d > 0 and done + d >= nxt:
            t = (nxt - done) / d
            f = QgsFeature(lyr.fields())
            f.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(a[2] + t * (b[2] - a[2]), a[3] + t * (b[3] - a[3]))))
            km = nxt / 1000
            f.setAttributes([km, f"{km:g} km"])
            feats.append(f)
            nxt += step_km * 1000
        done += d
    lyr.dataProvider().addFeatures(feats)
    lyr.setRenderer(QgsSingleSymbolRenderer(QgsMarkerSymbol.createSimple(
        {"name": "circle", "size": "1.8", "color": "black", "outline_color": "white", "outline_width": "0.3"})))
    pal = QgsPalLayerSettings()
    pal.fieldName = "label"
    pal.enabled = True
    pal.placement = Qgis.LabelPlacement.AroundPoint
    pal.dist = 1.2
    fmt = QgsTextFormat()
    font = fmt.font()
    font.setFamily("Helvetica")
    fmt.setFont(font)
    fmt.setSize(8)
    buf = QgsTextBufferSettings()
    buf.setEnabled(True)
    buf.setSize(0.8)
    buf.setColor(QColor("white"))
    fmt.setBuffer(buf)
    pal.setFormat(fmt)
    lyr.setLabeling(QgsVectorLayerSimpleLabeling(pal))
    lyr.setLabelsEnabled(True)
    return lyr


def auto_step(distance_km):
    for limit, step in ((15, 1), (60, 5), (150, 10)):
        if distance_km <= limit:
            return step
    return 25


def gpx_name(path):
    """The first track (or route) name in a GPX file, if any."""
    path = path.split("|", 1)[0]
    if not path.lower().endswith(".gpx"):
        return None
    for sub in ("tracks", "routes"):
        lyr = QgsVectorLayer(f"{path}|layername={sub}", sub, "ogr")
        if lyr.isValid() and "name" in lyr.fields().names():
            for f in lyr.getFeatures():
                if f["name"]:
                    return str(f["name"])
    return None


def persist(layer, gpkg, name, context):
    """Write a memory layer into `gpkg` and repoint the layer at it (style kept)."""
    opts = QgsVectorFileWriter.SaveVectorOptions()
    opts.driverName = "GPKG"
    opts.layerName = name
    if os.path.exists(gpkg):
        opts.actionOnExistingFile = QgsVectorFileWriter.CreateOrOverwriteLayer
    err = QgsVectorFileWriter.writeAsVectorFormatV3(layer, gpkg, context, opts)
    if err[0] != QgsVectorFileWriter.NoError:
        fail(f"writing {gpkg}:{name} failed: {err[1]}")
    layer.setDataSource(f"{os.path.abspath(gpkg)}|layername={name}", layer.name(), "ogr")


def ramp(name, invert):
    r = QgsStyle.defaultStyle().colorRamp(name)
    if r is None:
        r = QgsGradientColorRamp(QColor("#2b83ba"), QColor("#d7191c"))
    if invert:
        r.invert()
    return r


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("gpx")
    ap.add_argument("-o", "--output", action="append", required=True, help=".pdf/.png/.jpg/.svg; repeatable")
    ap.add_argument("--title", help="default: the GPX track name or file name")
    ap.add_argument("--subtitle", help="default: distance, ascent and elevation range")
    ap.add_argument("--field", default="ele", help="elevation attribute (default ele, falls back to Z)")
    ap.add_argument("--layer", help="GPX sublayer (default track_points, else route_points)")
    ap.add_argument("--classes", type=int, default=7)
    ap.add_argument("--mode", choices=sorted(MODES), default="jenks")
    ap.add_argument("--ramp", default="Spectral", help="QGIS style ramp name (Spectral, Viridis, Turbo, RdYlGn ...)")
    ap.add_argument("--no-invert", action="store_true", help="don't invert the ramp (Spectral inverted = blue→red)")
    ap.add_argument("--width", type=float, default=1.4, help="line width in mm")
    ap.add_argument("--page", default="A4")
    ap.add_argument("--orientation", choices=["auto", "landscape", "portrait"], default="auto")
    ap.add_argument("--dpi", type=int, default=300)
    ap.add_argument("--crs", help="map CRS (default: local UTM zone)")
    ap.add_argument("--km-every", default="auto", help="distance markers every N km; auto (default) or 0 for none")
    ap.add_argument("--basemap", choices=["none", "osm"], default="none")
    ap.add_argument("--project", help="also save a .qgz with the layers and the layout")
    ap.add_argument("--save-segments", help="also write the coloured segments to a GeoPackage")
    a = ap.parse_args()
    if a.classes < 2:
        fail("--classes must be at least 2", EXIT_USAGE)
    start()

    src = a.gpx if not a.layer else f"{a.gpx}|layername={a.layer}"
    pts_layer = load_vector(src, prefer=["track_points", "route_points", "waypoints"])
    pts = read_points(pts_layer, a.field)
    if len(pts) < 2:
        fail(f"{a.gpx}: fewer than 2 points in {pts_layer.name()}", EXIT_INPUT)
    st = stats(pts)
    if st["points_with_ele"] < 2:
        fail(f"{a.gpx}: no elevation (no '{a.field}' values and no Z); nothing to colour by", EXIT_INPUT)

    seg = build_segments(pts, pts_layer.crs())
    if seg.featureCount() == 0:
        fail("no segment had elevation at both ends", EXIT_INPUT)

    rnd = QgsGraduatedSymbolRenderer("ele")
    sym = QgsLineSymbol.createSimple({"line_width": str(a.width), "capstyle": "round", "joinstyle": "round"})
    rnd.setSourceSymbol(sym)
    rnd.setSourceColorRamp(ramp(a.ramp, not a.no_invert))
    rnd.setClassificationMethod(MODES[a.mode]())
    rnd.updateClasses(seg, min(a.classes, seg.featureCount()))
    for i, r in enumerate(rnd.ranges()):
        rnd.updateRangeLabel(i, f"{r.lowerValue():.0f}–{r.upperValue():.0f} m")
    seg.setRenderer(rnd)

    # A thin dark casing under the coloured line keeps pale classes readable.
    casing = QgsVectorLayer(f"LineString?crs={pts_layer.crs().authid()}", "casing", "memory")
    casing.dataProvider().addFeatures(list(seg.getFeatures()))
    casing.setRenderer(QgsSingleSymbolRenderer(QgsLineSymbol.createSimple(
        {"line_width": str(a.width + 0.6), "line_color": "40,40,40,200", "capstyle": "round", "joinstyle": "round"})))

    ends = QgsVectorLayer(f"Point?crs={pts_layer.crs().authid()}&field=label:string", "Start / finish", "memory")
    for (k, s, x, y, e), lbl in ((pts[0], "Start"), (pts[-1], "Finish")):
        f = QgsFeature(ends.fields())
        f.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(x, y)))
        f.setAttributes([lbl])
        ends.dataProvider().addFeature(f)
    ends.setRenderer(QgsSingleSymbolRenderer(QgsMarkerSymbol.createSimple(
        {"name": "circle", "size": "3", "color": "white", "outline_color": "black", "outline_width": "0.6"})))

    project = QgsProject.instance()
    c = pts_layer.extent().center()
    map_crs = QgsCoordinateReferenceSystem(a.crs) if a.crs else utm_crs(c.x(), c.y())
    if not map_crs.isValid():
        fail(f"unknown CRS {a.crs}", EXIT_USAGE)
    project.setCrs(map_crs)
    layers = [ends, seg, casing]
    try:
        step = auto_step(st["distance_km"]) if a.km_every == "auto" else float(a.km_every)
    except ValueError:
        fail(f"--km-every must be auto or a number of km, not {a.km_every!r}", EXIT_USAGE)
    kms = None
    if step > 0:
        kms = km_markers(pts, step, pts_layer.crs())
        if kms.featureCount():
            layers.insert(0, kms)
    if a.basemap == "osm":
        osm = QgsRasterLayer("type=xyz&url=https://tile.openstreetmap.org/{z}/{x}/{y}.png&zmax=19&zmin=0",
                             "OpenStreetMap", "wms")
        if osm.isValid():
            layers.append(osm)
        else:
            sys.stderr.write("warning: OSM basemap unavailable, continuing without it\n")
    project.addMapLayers(list(reversed(layers)))

    extent = QgsCoordinateTransform(pts_layer.crs(), map_crs, project).transformBoundingBox(seg.extent())
    title = a.title or gpx_name(a.gpx) or os.path.splitext(os.path.basename(a.gpx.split("|")[0]))[0]
    subtitle = a.subtitle or (f"{st['distance_km']:.1f} km · +{st['ascent_m']} m / −{st['descent_m']} m · "
                              f"elevation {st['ele_min']:.0f}–{st['ele_max']:.0f} m")
    layout, mp = map_layout(project, layers, extent, title=title, subtitle=subtitle, legend_layers=[seg],
                            legend_title="Elevation", page=a.page, orientation=a.orientation, crs=map_crs)
    if any(lyr.name() == "OpenStreetMap" for lyr in layers):
        att = QgsLayoutItemLabel(layout)
        att.setText("© OpenStreetMap contributors")
        page = layout.pageCollection().page(0).pageSize()
        att.attemptMove(QgsLayoutPoint(page.width() - 70, page.height() - 8))
        att.attemptResize(QgsLayoutSize(60, 5))
        layout.addLayoutItem(att)
    project.layoutManager().addLayout(layout)

    outputs = export_layout(layout, a.output, a.dpi)
    result = {"ok": True, "outputs": outputs, "title": title, "source_layer": pts_layer.name(),
              "segments": seg.featureCount(), "map_crs": map_crs.authid(), "stats": st,
              "km_markers": {"every_km": step, "count": kms.featureCount() if kms else 0},
              "classes": [{"lower": round(r.lowerValue(), 1), "upper": round(r.upperValue(), 1),
                           "color": r.symbol().color().name()} for r in rnd.ranges()]}
    ctx = project.transformContext()
    if a.save_segments:
        persist(seg, a.save_segments, "elevation_segments", ctx)
        result["segments_file"] = os.path.abspath(a.save_segments)
    if a.project:
        # Memory layers vanish from a saved project, so the project gets a sidecar
        # GeoPackage holding all three layers.
        data = os.path.splitext(a.project)[0] + "_data.gpkg"
        if os.path.exists(data):
            os.remove(data)
        for lyr, name in ((seg, "elevation_segments"), (casing, "casing"), (ends, "start_finish"), (kms, "km_markers")):
            if lyr is not None:
                persist(lyr, data, name, ctx)
        if not project.write(a.project):
            fail(f"could not save project {a.project}")
        result["project"] = os.path.abspath(a.project)
        result["project_data"] = os.path.abspath(data)
    emit(result)


if __name__ == "__main__":
    main()
