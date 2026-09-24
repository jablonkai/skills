// ---------------------------------------------------------------------------
// Creates a new document, adds a circle, then fills it with a mesh fill that
// renders a soap-bubble — concentric violet / yellow / cyan / violet bands,
// an S-shaped dark area in the middle band, and 4 bright highlight dots on
// a 45-degree diagonal.
// ---------------------------------------------------------------------------

'use strict';

const { AddChildNodesCommandBuilder, DocumentCommand } = require('/commands');
const { Colour } = require('/colours');
const { Document, NewDocumentOptions } = require('/document');
const { ColourMesh, FillDescriptor, MeshFill } = require('/fills');
const { MeshDirection, Rectangle, Transform } = require('/geometry');
const { NodeChildType, ShapeNodeDefinition } = require('/nodes');
const { Selection } = require('/selections');
const { ShapeEllipse } = require('/shapes');

// ---------------------------------------------------------------------------
// Small helpers
// ---------------------------------------------------------------------------

const rgba = (r, g, b, a) => Colour.createRGBA8({
    r: Math.max(0, Math.min(255, Math.round(r))),
    g: Math.max(0, Math.min(255, Math.round(g))),
    b: Math.max(0, Math.min(255, Math.round(b))),
    alpha: Math.max(0, Math.min(255, Math.round(a))),
});
const clamp01 = x => Math.max(0, Math.min(1, x));

function hsvRGB(h, s, v) {
    h = ((h % 1) + 1) % 1;
    const i = Math.floor(h * 6), f = h * 6 - i;
    const p = v * (1 - s), q = v * (1 - f * s), t = v * (1 - (1 - f) * s);
    let R, G, B;
    switch (i % 6) {
        case 0: R = v; G = t; B = p; break;
        case 1: R = q; G = v; B = p; break;
        case 2: R = p; G = v; B = t; break;
        case 3: R = p; G = q; B = v; break;
        case 4: R = t; G = p; B = v; break;
        case 5: R = v; G = p; B = q; break;
    }
    return [R * 255, G * 255, B * 255];
}

function interpHue(h0, h1, t) {
    if (h1 - h0 > 0.5) h1 -= 1;
    else if (h0 - h1 > 0.5) h0 -= 1;
    return ((h0 + (h1 - h0) * t) % 1 + 1) % 1;
}

function hash(a, b, c = 0) {
    const s = Math.sin(a * 127.1 + b * 311.7 + c * 74.7) * 43758.5453;
    return s - Math.floor(s);
}
const srand = (a, b, c) => 2 * hash(a, b, c) - 1;
const urand = (a, b, c) => hash(a, b, c);

// ---------------------------------------------------------------------------
// Concentric colour bands. Reading OUTWARD from the centre:
//   inner violet -> yellow -> cyan -> outer violet.
// ---------------------------------------------------------------------------

const BAND_STOPS = [
    { r: 0.00, h: 0.78, s: 0.30, v: 0.80 },
    { r: 0.20, h: 0.78, s: 0.35, v: 0.82 },
    { r: 0.36, h: 0.15, s: 0.50, v: 0.95 },
    { r: 0.52, h: 0.15, s: 0.55, v: 0.95 },
    { r: 0.66, h: 0.50, s: 0.50, v: 0.90 },
    { r: 0.82, h: 0.50, s: 0.45, v: 0.88 },
    { r: 0.93, h: 0.78, s: 0.55, v: 0.85 },
    { r: 1.00, h: 0.78, s: 0.60, v: 0.85 },
];

function bandHSV(rad) {
    for (let i = 0; i < BAND_STOPS.length - 1; i++) {
        const a = BAND_STOPS[i], b = BAND_STOPS[i + 1];
        if (rad <= b.r) {
            const t = (rad - a.r) / (b.r - a.r);
            const s = t * t * (3 - 2 * t);
            return {
                h: interpHue(a.h, b.h, s),
                s: a.s + (b.s - a.s) * s,
                v: a.v + (b.v - a.v) * s,
            };
        }
    }
    const last = BAND_STOPS[BAND_STOPS.length - 1];
    return { h: last.h, s: last.s, v: last.v };
}

// ---------------------------------------------------------------------------
// 4 highlight points on the 45-degree diagonal, snapped to actual mesh nodes.
// The 15-patch (16-node) grid puts diagonal nodes at offsets (k-7.5)/15 from
// centre. k = {3, 5, 9, 11} gives 2 distinct bright dots each side of centre.
// ---------------------------------------------------------------------------

const NODES = 15;

const HL_POINTS = [3, 5, 9, 11].map(k => {
    const o = (k - 7.5) / NODES;
    return { x: o, y: o, i: 1.0 };
});

// Diagonal node spacing is sqrt(2)/15 ~= 0.094.
// HL_RADIUS just covers the target node (no spill to diagonal neighbours).
// HL_FIELD reaches the 4 axial neighbours (distance 1/15 ~= 0.067) so each
// highlight reads as a small bright + cluster rather than a single pixel.
const HL_RADIUS = 0.035;
const HL_FIELD  = 0.075;

function highlightContribution(dx, dy) {
    let core = 0, halo = 0;
    for (const p of HL_POINTS) {
        const d = Math.hypot(dx - p.x, dy - p.y);
        if (d < HL_RADIUS) {
            const f = Math.pow(1 - d / HL_RADIUS, 1.4) * p.i;
            if (f > core) core = f;
        }
        if (d < HL_FIELD) {
            const f = Math.pow(1 - d / HL_FIELD, 1.6) * p.i;
            if (f > halo) halo = f;
        }
    }
    return { core, halo };
}

// ---------------------------------------------------------------------------
// S-curve dark band in the middle radial annulus.
// ---------------------------------------------------------------------------

function darkS(dx, dy) {
    const rad = Math.min(1, Math.hypot(dx, dy) * 2);
    if (rad < 0.15 || rad > 0.55) return 0;
    const yOnS = 0.13 * Math.sin(Math.PI * dx / 0.45);
    const d = Math.abs(dy - yOnS);
    if (d > 0.05) return 0;
    const proximity = Math.pow(1 - d / 0.05, 1.2);
    const radFade = 1 - Math.abs((rad - 0.35) / 0.20);
    return clamp01(proximity * clamp01(radFade)) * 0.55;
}

// ---------------------------------------------------------------------------
// Alpha field: centre soft, rim opaque, highlight nodes forced to alpha = 1.
// ---------------------------------------------------------------------------

function alphaForNode(dx, dy, rSeed, cSeed) {
    const rad = Math.min(1, Math.hypot(dx, dy) * 2);
    const jitter = 0.45 + 0.08 * urand(rSeed * 2.1, cSeed * 1.9, 41);
    let aBase;
    if (rad <= 0.18)      aBase = 0.40;
    else if (rad >= 0.55) aBase = jitter;
    else {
        const t = (rad - 0.18) / 0.37;
        const s = t * t * (3 - 2 * t);
        aBase = 0.40 + (jitter - 0.40) * s;
    }
    if (rad > 0.85) {
        const t = (rad - 0.85) / 0.15;
        const s = t * t * (3 - 2 * t);
        aBase = aBase + (0.85 - aBase) * s;
    }
    const { core, halo } = highlightContribution(dx, dy);
    const sDark = darkS(dx, dy);
    const haloA = Math.pow(halo, 0.5);
    let a = clamp01(Math.max(aBase, haloA, core));
    if (core > 0.5) a = 1.0;
    if (sDark > 0) a *= (1 - 0.55 * sDark);
    return a;
}

// ---------------------------------------------------------------------------
// Per-node colour: band hue + halo glow + core white-out + S-shape darkening.
// ---------------------------------------------------------------------------

function bubbleNodeColour(u, v, rSeed, cSeed) {
    const dx = u - 0.5, dy = v - 0.5;
    const rad = Math.min(1, Math.hypot(dx, dy) * 2);
    const { h: bh, s: bs, v: bv } = bandHSV(rad);

    let h   = bh + 0.01 * srand(rSeed * 1.7, cSeed * 2.3, 11);
    let sat = clamp01(bs + 0.03 * srand(rSeed, cSeed, 7));
    let val = clamp01(bv + 0.02 * srand(rSeed, cSeed, 5));

    const dark = darkS(dx, dy);
    if (dark > 0) {
        val *= (1 - 0.60 * dark);
        sat *= (1 - 0.25 * dark);
    }

    const { core, halo } = highlightContribution(dx, dy);
    if (halo > 0) {
        const g = Math.pow(halo, 0.85) * 0.95;
        val = val * (1 - g) + 1.00 * g;
        sat = sat * (1 - g) + 0.08 * g;
        h = interpHue(h, 0.55, g * 0.4);
    }
    if (core > 0) {
        sat = 0.0;
        val = 1.0;
        h = 0.58;
    }

    const [R, G, B] = hsvRGB(h, sat, val);
    const alpha = alphaForNode(dx, dy, rSeed, cSeed);
    return rgba(R, G, B, alpha * 255);
}

// ---------------------------------------------------------------------------
// Build the mesh fill and apply it to the supplied shape node.
// ---------------------------------------------------------------------------

function applyBubbleFill(doc, shapeNode) {
    const mesh = ColourMesh.createFromColour(rgba(255, 255, 255, 255), NODES);

    const sz       = mesh.size;
    const denomR   = sz.ySize, denomC = sz.xSize;
    const rowNodes = denomR + 1, colNodes = denomC + 1;

    const gridPos = (r, c) => ({ x: c / denomC, y: r / denomR });

    for (let r = 0; r < rowNodes; r++) {
        for (let c = 0; c < colNodes; c++) {
            const p = gridPos(r, c);
            mesh.setNodePosition(c, r, p);
            mesh.setNodeColour(c, r, bubbleNodeColour(p.x, p.y, r, c));
        }
    }

    // Catmull-Rom-style tangent handles — keeps the bands smooth.
    function tangentHandle(r, c, dr, dc) {
        const cn = c + dc, rn = r + dr;
        if (cn < 0 || cn >= colNodes || rn < 0 || rn >= rowNodes) return null;
        const here = gridPos(r, c), next = gridPos(rn, cn);
        const prev = gridPos(r - dr, c - dc);
        let hx, hy;
        if (r - dr >= 0 && r - dr < rowNodes && c - dc >= 0 && c - dc < colNodes) {
            hx = here.x + (next.x - prev.x) * (1 / 6);
            hy = here.y + (next.y - prev.y) * (1 / 6);
        } else {
            hx = here.x + (next.x - here.x) * (1 / 3);
            hy = here.y + (next.y - here.y) * (1 / 3);
        }
        return { x: hx, y: hy };
    }

    for (let r = 0; r < rowNodes; r++) {
        for (let c = 0; c < colNodes; c++) {
            if (c > 0)      { const h = tangentHandle(r, c,  0, -1); if (h) mesh.setCurveNodePosition(c, r, MeshDirection.Left,  h); }
            if (c < denomC) { const h = tangentHandle(r, c,  0, +1); if (h) mesh.setCurveNodePosition(c, r, MeshDirection.Right, h); }
            if (r > 0)      { const h = tangentHandle(r, c, -1,  0); if (h) mesh.setCurveNodePosition(c, r, MeshDirection.Up,    h); }
            if (r < denomR) { const h = tangentHandle(r, c, +1,  0); if (h) mesh.setCurveNodePosition(c, r, MeshDirection.Down,  h); }
        }
    }

    const bbox = shapeNode.baseBoxInterface.baseBox;
    const m    = new Transform(bbox.width, 0, bbox.x, 0, bbox.height, bbox.y);
    const desc = FillDescriptor.create(MeshFill.create(mesh), true, m, undefined, false);
    const sel  = Selection.createEmpty(doc);
    sel.addNode(shapeNode);
    doc.executeCommand(DocumentCommand.createSetBrushFill(sel, desc));
}

// ---------------------------------------------------------------------------
// Entry point
// ---------------------------------------------------------------------------

function main() {
    // 1. New document.
    const doc = Document.createFromOptions(NewDocumentOptions.createDefault());

    // 2. Add a centred circle that fills most of the spread.
    const { width, height } = doc.sizePixels;
    const size = Math.min(width, height) * 0.8;
    const rect = new Rectangle((width - size) / 2, (height - size) / 2, size, size);

    const def = ShapeNodeDefinition.createDefault();
    def.shape = ShapeEllipse.create();
    def.setBoundingRectangle(rect);

    const builder = AddChildNodesCommandBuilder.create();
    builder.addNode(def);
    doc.executeCommand(builder.createCommand(true, NodeChildType.Main));

    // 3. Fill it with the bubble mesh.
    applyBubbleFill(doc, doc.layers.last);
}

module.exports.main = main;
