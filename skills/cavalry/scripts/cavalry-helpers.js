// Cavalry helpers — shared functions for bridge build scripts.
//
// Load at the top of a script sent through cavalry-send.sh:
//   api.load("/abs/path/to/cavalry-helpers.js");
// Every send runs in a fresh scope, so load it in each script that needs it.
// Checked against Cavalry 2.7.2.

// api.set silently ignores attribute names the layer doesn't have — a typo or
// a name from another Cavalry version just does nothing. setAttrs refuses
// instead, naming the attribute and layer type, so the send fails loudly.
function setAttrs(layerId, attrs) {
    for (var key in attrs) {
        if (!api.hasAttribute(layerId, key)) {
            throw new Error("no attribute '" + key + "' on " + api.getLayerType(layerId) +
                " '" + api.getNiceName(layerId) + "' — list them with api.getAttributes(id)");
        }
    }
    api.set(layerId, attrs);
}

// api.keyframe is stricter than api.set and just as silent: it creates no
// keyframe (and returns "") for an ARRAY value — {"position": [x, y]} — or for
// a plain number on a vector attribute — {"rotation": 45}, where rotation is
// x/y/z since 2.x. keyAttrs splits arrays into .x/.y/.z children, sends a bare
// rotation number to rotation.z (2D spin), checks every name, then keys them.
function keyAttrs(layerId, frame, attrs) {
    var flat = {}, axes = ["x", "y", "z"];
    for (var key in attrs) {
        var v = attrs[key];
        if (Array.isArray(v)) {
            for (var i = 0; i < v.length; i++) flat[key + "." + axes[i]] = v[i];
        } else if (typeof v === "number" && /^double[23]$/.test(api.getAttrType(layerId, key))) {
            if (key !== "rotation") {
                throw new Error("'" + key + "' is a vector — key '" + key + ".x'/'" + key +
                    ".y' or pass an array");
            }
            flat["rotation.z"] = v;
        } else {
            flat[key] = v;
        }
    }
    for (var k in flat) {
        if (!api.hasAttribute(layerId, k)) {
            throw new Error("no attribute '" + k + "' on " + api.getLayerType(layerId) +
                " '" + api.getNiceName(layerId) + "' — list them with api.getAttributes(id)");
        }
    }
    api.keyframe(layerId, frame, flat);
}

// Return the id of the comp with this name, or null.
function findComp(name) {
    var comps = api.getComps();
    for (var i = 0; i < comps.length; i++) {
        if (api.getNiceName(comps[i]) === name) return comps[i];
    }
    return null;
}

// Create a comp and make it active. opts: {width, height, fps, frames, background}
// frames = total length (endFrame = frames - 1); background = "#rrggbb", or
// "transparent" for alpha output. New comps default to an OPAQUE background
// (white unless the user's preferences say otherwise), so always pass one.
function newComp(name, opts) {
    var comp = api.createComp(name);
    api.setActiveComp(comp);
    var a = {"resolution": [opts.width, opts.height], "fps": opts.fps,
             "startFrame": 0, "endFrame": opts.frames - 1};
    if (opts.background === "transparent") a["backgroundColor"] = "#00000000";
    else if (opts.background) a["backgroundColor"] = opts.background;
    setAttrs(comp, a);
    return comp;
}

// Make a previously built comp active again — the active comp is UI state
// that the user or another caller may have changed since the last send.
function useComp(name) {
    var comp = findComp(name);
    if (!comp) throw new Error("no comp named '" + name + "'");
    api.setActiveComp(comp);
    return comp;
}

// Render frames first..last (inclusive) of the active comp to
// dir/prefix_0000.png … at scale percent. Returns the file count.
function renderFrames(dir, prefix, first, last, scale) {
    if (!api.filePathExists(dir)) api.makeFolder(dir);
    api.stop();
    var n = 0;
    for (var f = first; f <= last; f++) {
        api.setFrame(f);
        api.renderPNGFrame(dir + "/" + prefix + "_" + ("0000" + f).slice(-4), scale || 100);
        n++;
    }
    return n;
}

function writeJSON(path, value) {
    api.writeToFile(path, JSON.stringify(value, null, 1), true);
}

// Split one line of text into a textShape per glyph (spaces skipped), each
// placed where it sits in the whole string — kerning included — with the line
// centred on [cx, cy]. style: text attrs such as {"fontSize", "font.font",
// "font.style", "material.materialColor"}. Returns the glyph layer ids in
// reading order; keyframe each one with its own delay. Use it when glyphs need
// individual easing/colour/paths — plain staggered motion is simpler with a
// Sub-Mesh + Stagger on one text layer (see SKILL.md).
function splitLetters(str, style, cx, cy) {
    function make(s, name) {
        var t = api.create("textShape", name);
        var a = {"text": s, "horizontalAlignment": 0, "verticalAlignment": 1,
                 "autoWidth": true, "autoHeight": true, "position": [0, cy]};
        for (var k in style) a[k] = style[k];
        setAttrs(t, a);
        return t;
    }
    var whole = make(str, "tmp");
    var wb = api.getBoundingBox(whole, true);
    api.deleteLayer(whole);
    var ids = [];
    for (var i = 0; i < str.length; i++) {
        if (str[i] === " ") continue;
        var prefix = make(str.slice(0, i + 1), "tmp");
        var right = api.getBoundingBox(prefix, true).right;
        api.deleteLayer(prefix);
        var g = make(str[i], "Letter " + i + " " + str[i]);
        // move the glyph so its ink right edge matches the prefix's, then centre the line
        var gb = api.getBoundingBox(g, true);
        api.set(g, {"position": [right - gb.right - (wb.left + wb.width / 2) + cx, cy]});
        ids.push(g);
    }
    return ids;
}
