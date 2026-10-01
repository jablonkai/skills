// Add a title block to existing DXF drawings.
//
//   qcad-run.sh title-block.js [key=value ...] [FILE.dxf:key=value ...]
//       [out=DIR] [suffix=-tb] [factor=N] [pdf] FILE.dxf...
//
// Fields (all optional, shown in this order): title= number= scale= date=
// author= company= sheet= rev=. Values with spaces must be quoted by the
// shell: 'title=Ground floor plan'. A field prefixed with a file name applies
// to that file only and wins over the shared value — per-sheet drawing
// numbers: a.dxf:number=WX-101 b.dxf:number=WX-102.
//
// Each drawing gets a block TITLEBLOCK (180 x 40 units at factor 1: frame,
// grid, labels and the field values as text) and exactly one INSERT of it on
// layer TITLE. The insert sits outside the drawing, right-aligned under its
// lower-right corner, scaled to the drawing: about 40% of its larger side,
// never below 1 in mm/unitless drawings (factor= overrides the auto factor).
// Output: OUT/<name><suffix>.dxf — default out is the input's folder and
// suffix "-tb"; with out= set, suffix= (empty) keeps the file names. An
// output path equal to its input is refused. "pdf" also writes a PDF.
// Files that already contain a TITLEBLOCK block are skipped, not doubled.

(function () {
    var fields = {}, perFile = {}, files = [], outDir = null, suffix = "-tb", factor = null, pdf = false;
    var order = ["title", "number", "scale", "date", "author", "company", "sheet", "rev"];
    var labels = { title: "TITLE", number: "DRAWING NO.", scale: "SCALE", date: "DATE",
                   author: "DRAWN BY", company: "COMPANY", sheet: "SHEET", rev: "REV" };
    for (var i = 0; i < ARGS.length; i++) {
        var a = ARGS[i];
        var pf = /^(.+\.(?:dxf|dwg)):([a-z]+)=(.*)$/i.exec(a);
        if (pf) {
            if (!labels[pf[2]]) { print("ERROR unknown field " + pf[2] + " (use: " + order.join(", ") + ")"); return; }
            var key0 = resolve(pf[1]);
            perFile[key0] = perFile[key0] || {};
            perFile[key0][pf[2]] = pf[3];
            continue;
        }
        var eq = a.indexOf("=");
        var k = eq > 0 ? a.substring(0, eq) : null, val = eq > 0 ? a.substring(eq + 1) : null;
        if (k === "out") outDir = val;
        else if (k === "suffix") suffix = val;
        else if (k === "factor") factor = parseFloat(val);
        else if (k !== null && labels[k]) fields[k] = val;
        else if (a === "pdf") pdf = true;
        else if (k !== null) { print("ERROR unknown field " + k + " (use: " + order.join(", ") + ")"); return; }
        else files.push(a);
    }
    if (files.length === 0) {
        print("ERROR usage: title-block.js title=... number=... FILE.dxf...");
        return;
    }
    if (isNull(fields.date)) fields.date = new Date().toISOString().substring(0, 10);

    var W = 180, H = 40, ok = 0, fail = 0;
    for (var f = 0; f < files.length; f++) {
        var src = resolve(files[f]);
        var ff = {};
        for (var fk in fields) ff[fk] = fields[fk];
        for (var pk in (perFile[src] || {})) ff[pk] = perFile[src][pk];
        try {
            var ctx = openDrawing(src);
            if (ctx.doc.getBlockId("TITLEBLOCK") !== RObject.INVALID_ID) {
                print("SKIP " + src + ": already has a TITLEBLOCK block");
                continue;
            }
            var ext = extents(ctx);
            var s = factor;
            if (isNull(s) || !(s > 0)) {
                // block width about 40% of the drawing's larger side, rounded to 1/2/5 steps
                var raw = Math.max(ext.w, ext.h, 1) * 0.4 / W;
                var p = Math.pow(10, Math.floor(Math.log(raw) / Math.LN10));
                var m = raw / p;
                s = (m < 1.5 ? 1 : m < 3.5 ? 2 : m < 7.5 ? 5 : 10) * p;
                // in mm (or unitless) drawings a title block is never below full size
                var u = ctx.doc.getUnit();
                if ((u === RS.Millimeter || u === RS.None) && s < 1) s = 1;
            }
            addLayer(ctx, "TITLE", "white", "CONTINUOUS", RLineweight.Weight035);
            defineBlock(ctx, "TITLEBLOCK", v(W, 0), function (c) {
                // base point = lower-right corner, so the insert right-aligns
                addRect(c, v(0, 0), v(W, H));
                addLine(c, v(0, 20), v(W, 20));
                addLine(c, v(100, 0), v(100, 20));
                addLine(c, v(140, 0), v(140, 20));
                addLine(c, v(0, 10), v(W, 10));
                // top band: title (and company to the right)
                // [field, x, bottom y, row height]
                var cells = [
                    ["title", 2, 20, 20], ["company", 122, 20, 20],
                    ["number", 2, 10, 10], ["scale", 102, 10, 10], ["sheet", 142, 10, 10],
                    ["author", 2, 0, 10], ["date", 102, 0, 10], ["rev", 142, 0, 10]];
                for (var j = 0; j < cells.length; j++) {
                    var key = cells[j][0], x = cells[j][1], y = cells[j][2], rh = cells[j][3];
                    addText(c, v(x, y + rh - 2.8), labels[key], { height: 1.8 });
                    if (!isNull(ff[key])) {
                        addText(c, v(x, y + 1.5), ff[key], { height: rh > 10 ? 6 : 3.5 });
                    }
                }
                addLine(c, v(120, 20), v(120, H));
            });
            var gap = Math.max(ext.w, ext.h) * 0.03;
            insertBlock(ctx, "TITLEBLOCK", v(ext.maxX, ext.minY - gap - H * s), s);
            var fi = new QFileInfo(src);
            var dir = isNull(outDir) ? fi.absolutePath() : resolve(outDir);
            mkdirs(dir);
            var out = dir + "/" + fi.completeBaseName() + suffix + ".dxf";
            if (new QFileInfo(out).absoluteFilePath() === fi.absoluteFilePath()) {
                throw new Error("refusing to overwrite the input; pass a suffix or out=");
            }
            saveDrawing(ctx, out);
            if (pdf) exportPdf(ctx, out.replace(/\.dxf$/, ".pdf"), { paper: "A3" });
            print("OK " + src + " -> " + out + " (factor " + s + ")");
            ok++;
        } catch (e) {
            print("FAIL " + src + ": " + e);
            fail++;
        }
    }
    print("SUMMARY ok=" + ok + " fail=" + fail);
    if (fail > 0) print("ERROR " + fail + " file(s) failed");
})();
