"""Describe GIS files as JSON, and optionally assert what they must contain.

    bash qgis.sh python qgis_inspect.py FILE [FILE...] [--stats]
        [--expect-crs EPSG:23700] [--expect-count N] [--expect-layers N]

Vector files (GPX, GeoJSON, GeoPackage, Shapefile, KML, ...): every sublayer with
feature count, geometry type, CRS, extent (native and WGS 84) and fields.
Rasters (GeoTIFF, ...): size, bands, CRS, extent, pixel size, nodata, and with
--stats min/max/mean per band. Projects (.qgz/.qgs): layers and print layouts.

The --expect-* checks apply to every vector layer (count, CRS) or file (layers) and
exit 4 when one fails, so this doubles as the verification step after a write.
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from qgis_boot import EXIT_INPUT, EXIT_OK, EXIT_VERIFY, band_stats, emit, start, sublayers  # noqa: E402

from qgis.core import (  # noqa: E402
    QgsCoordinateReferenceSystem,
    QgsCoordinateTransform,
    QgsProject,
    QgsRasterLayer,
    QgsUnitTypes,
    QgsVectorLayer,
    QgsWkbTypes,
)

WGS84 = QgsCoordinateReferenceSystem("EPSG:4326")


def rect(r, digits=6):
    return [round(v, digits) for v in (r.xMinimum(), r.yMinimum(), r.xMaximum(), r.yMaximum())]


def crs_info(crs):
    return {"authid": crs.authid() or None, "description": crs.description(),
            "units": QgsUnitTypes.toString(crs.mapUnits()),
            "geographic": crs.isGeographic()} if crs.isValid() else None


def wgs84_extent(extent, crs):
    if not crs.isValid() or extent.isEmpty():
        return None
    try:
        return rect(QgsCoordinateTransform(crs, WGS84, QgsProject.instance()).transformBoundingBox(extent))
    except Exception:  # noqa: BLE001 - a broken CRS should not abort the inspection
        return None


def vector_info(layer, name):
    ext = layer.extent()
    info = {
        "name": name,
        "kind": "vector",
        "features": layer.featureCount(),
        "geometry": QgsWkbTypes.displayString(layer.wkbType()),
        "crs": crs_info(layer.crs()),
        "extent": rect(ext) if not ext.isEmpty() else None,
        "extent_wgs84": wgs84_extent(ext, layer.crs()),
        "fields": [{"name": f.name(), "type": f.typeName()} for f in layer.fields()],
    }
    return info


def raster_info(layer, stats):
    p = layer.dataProvider()
    info = {
        "name": layer.name(),
        "kind": "raster",
        "width": layer.width(),
        "height": layer.height(),
        "bands": layer.bandCount(),
        "crs": crs_info(layer.crs()),
        "extent": rect(layer.extent()),
        "extent_wgs84": wgs84_extent(layer.extent(), layer.crs()),
        "pixel_size": [layer.rasterUnitsPerPixelX(), layer.rasterUnitsPerPixelY()],
        "nodata": [p.sourceNoDataValue(b) if p.sourceHasNoDataValue(b) else None
                   for b in range(1, layer.bandCount() + 1)],
    }
    if stats:
        out = []
        for b in range(1, layer.bandCount() + 1):
            s = band_stats(p, b)
            out.append({"band": b, "min": s.minimumValue, "max": s.maximumValue,
                        "mean": s.mean, "stddev": s.stdDev, "sum": s.sum, "count": s.elementCount})
        info["stats"] = out
    return info


def project_info(path):
    proj = QgsProject.instance()
    if not proj.read(path):
        return {"path": path, "kind": "project", "error": "could not read project"}
    layers = []
    for lyr in proj.mapLayers().values():
        layers.append({"name": lyr.name(), "type": type(lyr).__name__, "valid": lyr.isValid(),
                       "source": lyr.source(), "crs": lyr.crs().authid()})
    layouts = [lay.name() for lay in proj.layoutManager().printLayouts()]
    return {"path": path, "kind": "project", "crs": proj.crs().authid(), "layers": layers, "layouts": layouts}


def inspect(path, stats):
    if not os.path.exists(path.split("|", 1)[0]):
        return {"path": path, "error": "no such file"}
    if path.lower().endswith((".qgz", ".qgs")):
        return project_info(path)
    if "|" in path:
        lyr = QgsVectorLayer(path, os.path.basename(path), "ogr")
        if lyr.isValid():
            return {"path": path, "layers": [vector_info(lyr, path.split("layername=")[-1])]}
    layers = []
    subs = sublayers(path)
    for name, uri in subs:
        lyr = QgsVectorLayer(uri, name, "ogr")
        if lyr.isValid():
            layers.append(vector_info(lyr, name))
    if layers:
        return {"path": path, "layers": layers}
    rl = QgsRasterLayer(path, os.path.basename(path))
    if rl.isValid():
        return {"path": path, "layers": [raster_info(rl, stats)]}
    return {"path": path, "error": "not a readable vector, raster or project"}


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("files", nargs="+")
    ap.add_argument("--stats", action="store_true", help="raster band statistics")
    ap.add_argument("--expect-crs", help="every layer must be in this CRS (e.g. EPSG:23700)")
    ap.add_argument("--expect-count", type=int, help="every vector layer must have N features")
    ap.add_argument("--expect-layers", type=int, help="every file must hold N layers")
    a = ap.parse_args()
    start()

    results, problems = [], []
    for f in a.files:
        r = inspect(f, a.stats)
        results.append(r)
        if "error" in r:
            problems.append(f"{f}: {r['error']}")
            continue
        lyrs = r.get("layers", [])
        if a.expect_layers is not None and r.get("kind") != "project" and len(lyrs) != a.expect_layers:
            problems.append(f"{f}: {len(lyrs)} layers, expected {a.expect_layers}")
        for lyr in lyrs if isinstance(lyrs, list) else []:
            if not isinstance(lyr, dict) or "kind" not in lyr:
                continue
            got = (lyr.get("crs") or {}).get("authid")
            if a.expect_crs and got != a.expect_crs.upper():
                problems.append(f"{f}:{lyr['name']}: CRS {got}, expected {a.expect_crs}")
            if a.expect_count is not None and lyr["kind"] == "vector" and lyr["features"] != a.expect_count:
                problems.append(f"{f}:{lyr['name']}: {lyr['features']} features, expected {a.expect_count}")

    missing = any(r.get("error") == "no such file" for r in results)
    code = EXIT_INPUT if missing else (EXIT_VERIFY if problems else EXIT_OK)
    emit({"ok": not problems, "files": results, "problems": problems}, code)


if __name__ == "__main__":
    main()
