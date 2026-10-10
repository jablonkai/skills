"""Export print layouts from an existing QGIS project (.qgz/.qgs) headless.

    bash qgis.sh python layout_export.py PROJECT.qgz --list
    bash qgis.sh python layout_export.py PROJECT.qgz -o map.pdf [--layout "A3 map"]
    bash qgis.sh python layout_export.py PROJECT.qgz --out-dir out/ --format png [--dpi 300]
    bash qgis.sh python layout_export.py PROJECT.qgz --layout Atlas --atlas --out-dir pages/ --format pdf

-o writes one file (the project must have exactly one layout, or name it with
--layout). --out-dir writes one file per layout, named after it; with --atlas, one
file per atlas feature (PDF: --single-pdf for one multi-page file). Broken layer paths
are reported, not silently rendered as empty maps: exit 4 unless --allow-missing.
"""

import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from qgis_boot import EXIT_INPUT, EXIT_QGIS, EXIT_USAGE, EXIT_VERIFY, emit, export_layout, fail, start  # noqa: E402

from qgis.core import Qgis, QgsLayoutExporter, QgsProject  # noqa: E402


def safe(name):
    return re.sub(r"[^\w.-]+", "_", name).strip("_") or "layout"


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("project")
    ap.add_argument("--list", action="store_true", help="list layouts (with atlas info) and layers")
    ap.add_argument("--layout", action="append", default=[], help="layout name; repeatable (default: all)")
    ap.add_argument("-o", "--output", help="single output file (.pdf/.png/.jpg/.svg/.tif)")
    ap.add_argument("--out-dir", help="one file per layout (or atlas page)")
    ap.add_argument("--format", default="pdf", choices=["pdf", "png", "jpg", "svg", "tif"])
    ap.add_argument("--dpi", type=int, default=300)
    ap.add_argument("--atlas", action="store_true", help="export each atlas feature")
    ap.add_argument("--single-pdf", action="store_true", help="atlas into one multi-page PDF")
    ap.add_argument("--allow-missing", action="store_true", help="export even if layers are broken")
    a = ap.parse_args()
    if not os.path.exists(a.project):
        fail(f"no such project: {a.project}", EXIT_INPUT)
    start(processing=False)

    proj = QgsProject.instance()
    if not proj.read(os.path.abspath(a.project)):
        fail(f"could not read {a.project}: {proj.error()}", EXIT_INPUT)
    broken = [{"name": lyr.name(), "source": lyr.source()} for lyr in proj.mapLayers().values() if not lyr.isValid()]
    layouts = proj.layoutManager().printLayouts()

    if a.list:
        emit({"ok": True, "project": os.path.abspath(a.project), "crs": proj.crs().authid(),
              "layouts": [{"name": lay.name(), "pages": lay.pageCollection().pageCount(),
                           "atlas": lay.atlas().enabled(),
                           "atlas_layer": lay.atlas().coverageLayer().name() if lay.atlas().coverageLayer() else None}
                          for lay in layouts],
              "layers": [{"name": lyr.name(), "valid": lyr.isValid(), "crs": lyr.crs().authid()}
                         for lyr in proj.mapLayers().values()],
              "broken_layers": broken})

    if broken and not a.allow_missing:
        fail("project has broken layer sources (maps would render empty); fix the paths or pass --allow-missing",
             EXIT_VERIFY, broken_layers=broken)
    if a.layout:
        by_name = {lay.name(): lay for lay in layouts}
        missing = [n for n in a.layout if n not in by_name]
        if missing:
            fail(f"no layout named {missing}; available: {sorted(by_name)}", EXIT_INPUT)
        layouts = [by_name[n] for n in a.layout]
    if not layouts:
        fail("the project has no print layouts", EXIT_INPUT)
    if bool(a.output) == bool(a.out_dir):
        fail("give exactly one of -o FILE or --out-dir DIR", EXIT_USAGE)
    if a.output and (len(layouts) > 1 or a.atlas and not a.single_pdf):
        fail("-o needs a single layout (use --layout NAME) and no per-page atlas; use --out-dir", EXIT_USAGE)

    results = []
    for lay in layouts:
        if a.atlas:
            atlas = lay.atlas()
            if not atlas.enabled():
                fail(f"layout {lay.name()!r} has no atlas enabled", EXIT_USAGE)
            if a.out_dir:
                os.makedirs(a.out_dir, exist_ok=True)
            if a.format == "pdf":
                s = QgsLayoutExporter.PdfExportSettings()
                s.dpi = a.dpi
                s.textRenderFormat = Qgis.TextRenderFormat.AlwaysText
                if a.single_pdf:
                    path = os.path.abspath(a.output or os.path.join(a.out_dir, safe(lay.name()) + ".pdf"))
                    res, err = QgsLayoutExporter.exportToPdf(atlas, path, s)
                else:
                    atlas.setFilenameExpression(f"'{safe(lay.name())}_' || @atlas_featurenumber")
                    # exportToPdfs treats its argument as a file path and writes next to it.
                    path = os.path.join(os.path.abspath(a.out_dir), safe(lay.name()))
                    res, err = QgsLayoutExporter.exportToPdfs(atlas, path, s)
                    path = os.path.dirname(path)
            else:
                s = QgsLayoutExporter.ImageExportSettings()
                s.dpi = a.dpi
                s.generateWorldFile = False
                atlas.setFilenameExpression(f"'{safe(lay.name())}_' || @atlas_featurenumber")
                path = os.path.join(os.path.abspath(a.out_dir), safe(lay.name()))
                res, err = QgsLayoutExporter.exportToImage(atlas, path, a.format, s)
                path = os.path.dirname(path)
            if res != QgsLayoutExporter.Success:
                fail(f"atlas export of {lay.name()!r} failed: {err}", EXIT_QGIS)
            results.append({"layout": lay.name(), "atlas_features": atlas.count(), "path": path})
        else:
            out = a.output or os.path.join(a.out_dir, f"{safe(lay.name())}.{a.format}")
            results.append({"layout": lay.name(), "outputs": export_layout(lay, [out], a.dpi)})
    emit({"ok": True, "exports": results, "broken_layers": broken})


if __name__ == "__main__":
    main()
