// Batch-convert every DXF (and DWG, with the Pro plugin) under a folder to
// PDF and/or PNG in a single QCAD launch.
//
//   qcad-run.sh batch-export.js IN_DIR OUT_DIR [pdf] [png] [paper=A3] [color] [flat]
//
//   pdf / png   formats to write (default: pdf)
//   paper=NAME  A4 (default), A3, Letter, ... or WxH in mm such as 420x297
//   color       keep entity colors (default: black on white)
//   flat        write every output directly into OUT_DIR instead of mirroring
//               the input sub-folders (name clashes then get a numeric suffix)
//
// Inputs are only read. Prints one "OK <in> -> <out>" or "FAIL <in>: <why>"
// line per file and a final "SUMMARY ok=N fail=M" line; any failure makes
// qcad-run.sh exit non-zero.

(function () {
    var positional = [], formats = [], paper = "A4", mono = true, flat = false;
    for (var i = 0; i < ARGS.length; i++) {
        var a = ARGS[i];
        if (a === "pdf" || a === "png") formats.push(a);
        else if (a.indexOf("paper=") === 0) paper = a.substring(6);
        else if (a === "color") mono = false;
        else if (a === "flat") flat = true;
        else positional.push(a);
    }
    if (positional.length !== 2) {
        print("ERROR usage: batch-export.js IN_DIR OUT_DIR [pdf] [png] [paper=A4] [color] [flat]");
        return;
    }
    if (formats.length === 0) formats = ["pdf"];
    var inDir = resolve(positional[0]);
    var outDir = resolve(positional[1]);
    mkdirs(outDir);

    var files = listFiles(inDir, ["dxf", "dwg"], true);
    var used = {}, ok = 0, fail = 0;
    for (var f = 0; f < files.length; f++) {
        var src = files[f];
        var fi = new QFileInfo(src);
        var rel = new QDir(inDir).relativeFilePath(fi.absolutePath());
        var dir = (flat || rel === ".") ? outDir : outDir + "/" + rel;
        var base = fi.completeBaseName();
        if (flat) {
            var key = base.toLowerCase(), n = 1;
            while (used[key]) { key = (base + "-" + (++n)).toLowerCase(); }
            if (n > 1) base = base + "-" + n;
            used[key] = true;
        }
        try {
            mkdirs(dir);
            var ctx = openDrawing(src);
            var outs = [];
            for (var k = 0; k < formats.length; k++) {
                var out = dir + "/" + base + "." + formats[k];
                if (formats[k] === "pdf") exportPdf(ctx, out, { paper: paper, monochrome: mono });
                else exportImage(ctx, out, { width: 2000 });
                outs.push(out);
            }
            print("OK " + src + " -> " + outs.join(", "));
            ok++;
        } catch (e) {
            print("FAIL " + src + ": " + e);
            fail++;
        }
    }
    print("SUMMARY ok=" + ok + " fail=" + fail);
    if (fail > 0 || files.length === 0) {
        print("ERROR " + (files.length === 0 ? "no DXF/DWG files under " + inDir : fail + " file(s) failed"));
    }
})();
