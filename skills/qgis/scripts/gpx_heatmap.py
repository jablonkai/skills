"""Build a kernel-density heatmap from many GPX files (or any line/point layers).

    bash qgis.sh python gpx_heatmap.py runs/ [more.gpx ...] -o heatmap.tif
        [--png heatmap.png] [--pdf heatmap.pdf] [--title "Training heatmap"]
        [--radius 150] [--pixel 10] [--spacing 10] [--raw-points]
        [--crs EPSG:23700] [--ramp Inferno] [--basemap none|osm] [--dpi 300]

Every track is resampled to one point every --spacing metres before the density is
computed, so a watch that logs every second doesn't outweigh one that logs every 10 s
and pauses don't leave hot spots (--raw-points uses the logged points instead). The
heatmap is computed in a metric CRS (default: the local UTM zone), because the radius
and pixel size are in layer units: in EPSG:4326 they would be degrees. The GeoTIFF
holds density values; --png/--pdf add a styled map (tracks in grey under the heat
layer, zero density transparent, legend, scale bar, north arrow).

Prints JSON: inputs used, point count, CRS, raster size and stats, and the WGS 84
location of the densest cell.
"""

import argparse
import glob
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from qgis_boot import (  # noqa: E402
    EXIT_INPUT,
    EXIT_QGIS,
    EXIT_USAGE,
    band_stats,
    emit,
    export_layout,
    fail,
    load_raster,
    map_layout,
    start,
    sublayers,
    utm_crs,
)

from qgis.core import (  # noqa: E402
    QgsColorRampShader,
    QgsCoordinateReferenceSystem,
    QgsCoordinateTransform,
    QgsFeature,
    QgsGeometry,
    QgsLineSymbol,
    QgsProject,
    QgsRasterLayer,
    QgsRasterShader,
    QgsRectangle,
    QgsSingleBandPseudoColorRenderer,
    QgsSingleSymbolRenderer,
    QgsStyle,
    QgsVectorLayer,
    QgsWkbTypes,
)
from qgis.PyQt.QtGui import QColor  # noqa: E402

WGS84 = QgsCoordinateReferenceSystem("EPSG:4326")
VECTOR_EXT = (".gpx", ".geojson", ".json", ".gpkg", ".shp", ".kml", ".fgb")


def collect(paths):
    files = []
    for p in paths:
        if os.path.isdir(p):
            for ext in VECTOR_EXT:
                files += glob.glob(os.path.join(p, f"*{ext}")) + glob.glob(os.path.join(p, f"*{ext.upper()}"))
        elif os.path.exists(p):
            files.append(p)
        else:
            fail(f"no such file or folder: {p}", EXIT_INPUT)
    files = sorted(set(files))
    if not files:
        fail("no GPX/vector files found in the inputs", EXIT_INPUT)
    return files


def layers_for(path, raw):
    """The layers to sample from one file: GPX tracks (lines) or track points."""
    subs = dict(sublayers(path))
    if path.lower().endswith(".gpx"):
        order = ["track_points", "route_points", "waypoints"] if raw else ["tracks", "routes", "track_points", "waypoints"]
        for name in order:
            if name in subs:
                lyr = QgsVectorLayer(subs[name], name, "ogr")
                if lyr.isValid() and lyr.featureCount() > 0:
                    return [lyr]
        return []
    out = []
    for name, uri in (subs.items() if subs else [(os.path.basename(path), path)]):
        lyr = QgsVectorLayer(uri, name, "ogr")
        if lyr.isValid() and lyr.featureCount() > 0:
            out.append(lyr)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("inputs", nargs="+", help="GPX files and/or folders")
    ap.add_argument("-o", "--output", required=True, help="GeoTIFF with the density values")
    ap.add_argument("--png", action="append", default=[], help="styled map image; repeatable")
    ap.add_argument("--pdf", action="append", default=[], help="styled map PDF; repeatable")
    ap.add_argument("--title", default="Heatmap")
    ap.add_argument("--radius", type=float, help="kernel radius in metres (default: max(150, 8 px))")
    ap.add_argument("--pixel", type=float, help="pixel size in metres (default: extent / 1500, ≥ 5)")
    ap.add_argument("--spacing", type=float, default=10.0, help="resampling step along tracks, metres")
    ap.add_argument("--raw-points", action="store_true", help="use logged points, no resampling")
    ap.add_argument("--crs", help="metric CRS for the computation (default: local UTM zone)")
    ap.add_argument("--ramp", default="Inferno", help="QGIS style ramp for the styled map")
    ap.add_argument("--no-tracks", action="store_true", help="don't draw the grey tracks under the heat")
    ap.add_argument("--basemap", choices=["none", "osm"], default="none")
    ap.add_argument("--page", default="A4")
    ap.add_argument("--dpi", type=int, default=300)
    ap.add_argument("--keep-points", help="also write the sampled points to this GeoPackage")
    a = ap.parse_args()
    start(processing=True)
    import processing  # after Processing.initialize()

    files = collect(a.inputs)
    sources, skipped = [], []
    for f in files:
        lyrs = layers_for(f, a.raw_points)
        if lyrs:
            sources += [(f, lyr) for lyr in lyrs]
        else:
            skipped.append(f)
    if not sources:
        fail("none of the inputs had features", EXIT_INPUT, skipped=skipped)

    # Combined WGS 84 extent → metric CRS.
    ext = QgsRectangle()
    ext.setNull()
    for _, lyr in sources:
        ext.combineExtentWith(QgsCoordinateTransform(lyr.crs(), WGS84, QgsProject.instance())
                              .transformBoundingBox(lyr.extent()))
    crs = QgsCoordinateReferenceSystem(a.crs) if a.crs else utm_crs(ext.center().x(), ext.center().y())
    if not crs.isValid():
        fail(f"unknown CRS {a.crs}", EXIT_USAGE)
    if crs.isGeographic():
        fail(f"{crs.authid()} is geographic (degrees); pick a metric CRS — radius and pixel are in layer units",
             EXIT_USAGE)

    pts = QgsVectorLayer(f"Point?crs={crs.authid()}&field=src:string", "points", "memory")
    tracks = QgsVectorLayer(f"MultiLineString?crs={crs.authid()}&field=src:string", "Tracks", "memory")
    feats, track_feats, per_file = [], [], {}
    for path, lyr in sources:
        xf = QgsCoordinateTransform(lyr.crs(), crs, QgsProject.instance())
        name = os.path.basename(path)
        n0 = len(feats)
        for f in lyr.getFeatures():
            g = QgsGeometry(f.geometry())
            if g.isEmpty():
                continue
            g.transform(xf)
            gtype = QgsWkbTypes.geometryType(g.wkbType())
            if gtype == QgsWkbTypes.LineGeometry:
                tf = QgsFeature(tracks.fields())
                tf.setGeometry(g)
                tf.setAttributes([name])
                track_feats.append(tf)
                length, d = g.length(), 0.0
                while d <= length:
                    p = QgsFeature(pts.fields())
                    p.setGeometry(g.interpolate(d))
                    p.setAttributes([name])
                    feats.append(p)
                    d += a.spacing
            elif gtype == QgsWkbTypes.PointGeometry:
                for part in g.asGeometryCollection() if g.isMultipart() else [g]:
                    p = QgsFeature(pts.fields())
                    p.setGeometry(part)
                    p.setAttributes([name])
                    feats.append(p)
        per_file[name] = per_file.get(name, 0) + len(feats) - n0
    pts.dataProvider().addFeatures(feats)
    pts.updateExtents()
    tracks.dataProvider().addFeatures(track_feats)
    tracks.updateExtents()
    if pts.featureCount() == 0:
        fail("no points to build the heatmap from", EXIT_INPUT)

    e = pts.extent()
    pixel = a.pixel or max(5.0, round(max(e.width(), e.height()) / 1500.0, 1))
    radius = a.radius or max(150.0, 8 * pixel)

    work = tempfile.mkdtemp(prefix="qgis-heatmap-")
    src_path = a.keep_points or os.path.join(work, "points.gpkg")
    res = processing.run("native:savefeatures", {"INPUT": pts, "OUTPUT": src_path, "LAYER_NAME": "points"})
    out = os.path.abspath(a.output)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    try:
        processing.run("native:heatmapkerneldensityestimation", {
            "INPUT": res["OUTPUT"], "RADIUS": radius, "PIXEL_SIZE": pixel, "KERNEL": 0,
            "OUTPUT_VALUE": 0, "DECAY": 0, "OUTPUT": out})
    except Exception as exc:  # noqa: BLE001 - processing raises QgsProcessingException
        fail(f"heatmap failed: {exc}", EXIT_QGIS)

    try:  # names the band; the legend otherwise reads "Band 1 (Gray)"
        from osgeo import gdal

        ds = gdal.Open(out, gdal.GA_Update)
        ds.GetRasterBand(1).SetDescription(f"Kernel density (radius {radius:g} m)")
        ds = None
    except Exception:  # noqa: BLE001,S110 - cosmetic only
        pass
    heat = load_raster(out, "Density")
    prov = heat.dataProvider()
    st = band_stats(prov)
    peak = None
    try:
        from osgeo import gdal

        ds = gdal.Open(out)
        arr = ds.GetRasterBand(1).ReadAsArray()
        r, c = divmod(int(arr.argmax()), arr.shape[1])
        gt = ds.GetGeoTransform()
        x, y = gt[0] + (c + 0.5) * gt[1], gt[3] + (r + 0.5) * gt[5]
        pw = QgsCoordinateTransform(crs, WGS84, QgsProject.instance()).transform(x, y)
        peak = {"lon": round(pw.x(), 6), "lat": round(pw.y(), 6), "value": float(arr.max()),
                "nonzero_cells": int((arr > 0).sum()), "cells": int(arr.size)}
        ds = None
    except Exception as exc:  # noqa: BLE001 - the stats are a bonus, not a failure
        sys.stderr.write(f"warning: peak search skipped: {exc}\n")

    result = {"ok": True, "raster": out, "crs": crs.authid(), "radius_m": radius, "pixel_m": pixel,
              "sampling": "raw points" if a.raw_points else f"every {a.spacing:g} m along tracks",
              "files_used": len(per_file), "points": pts.featureCount(), "points_per_file": per_file,
              "skipped": skipped, "size": [heat.width(), heat.height()],
              "stats": {"min": st.minimumValue, "max": st.maximumValue, "mean": st.mean},
              "extent_wgs84": [round(v, 6) for v in (ext.xMinimum(), ext.yMinimum(), ext.xMaximum(), ext.yMaximum())],
              "peak": peak}

    if a.png or a.pdf:
        ramp = QgsStyle.defaultStyle().colorRamp(a.ramp)
        vmax = st.maximumValue or 1.0
        items = [QgsColorRampShader.ColorRampItem(0, QColor(0, 0, 0, 0), "0")]
        for i in range(1, 11):
            v = vmax * i / 10
            col = ramp.color(0.15 + 0.85 * i / 10) if ramp else QColor.fromHsvF(0.15 * (1 - i / 10), 1, 1)
            items.append(QgsColorRampShader.ColorRampItem(v, col, f"{v:.3g}"))
        crs_shader = QgsColorRampShader(0, vmax)
        crs_shader.setColorRampType(QgsColorRampShader.Interpolated)
        crs_shader.setColorRampItemList(items)
        legend = crs_shader.legendSettings()
        legend.setMinimumLabel("low")
        legend.setMaximumLabel("high")
        crs_shader.setLegendSettings(legend)
        shader = QgsRasterShader()
        shader.setRasterShaderFunction(crs_shader)
        heat.setRenderer(QgsSingleBandPseudoColorRenderer(prov, 1, shader))
        heat.setOpacity(0.9)
        tracks.setRenderer(QgsSingleSymbolRenderer(QgsLineSymbol.createSimple(
            {"line_width": "0.2", "line_color": "120,120,120,160"})))

        project = QgsProject.instance()
        project.setCrs(crs)
        layers = [heat] + ([] if a.no_tracks or not track_feats else [tracks])
        if a.basemap == "osm":
            osm = QgsRasterLayer("type=xyz&url=https://tile.openstreetmap.org/{z}/{x}/{y}.png&zmax=19&zmin=0",
                                 "OpenStreetMap", "wms")
            if osm.isValid():
                layers.append(osm)
        project.addMapLayers(list(reversed(layers)))
        sub = (f"{len(per_file)} files · {pts.featureCount()} points · radius {radius:g} m · "
               f"pixel {pixel:g} m · {crs.authid()}")
        layout, _ = map_layout(project, layers, heat.extent(), title=a.title, subtitle=sub,
                               legend_layers=[heat], legend_title="Density", page=a.page, crs=crs, margin=0.03)
        result["maps"] = export_layout(layout, a.png + a.pdf, a.dpi)
    emit(result)


if __name__ == "__main__":
    main()
