# Krita Bridge example — build → verify → export, the whole loop in one script.
#
#   OUT=/tmp/poster bash krita-send.sh example-poster.py
#
# Builds a small poster document from scratch: a QPainter-drawn gradient
# background pushed into a paint layer, a blurred blob, an SVG text/vector
# layer, then writes a projection PNG (to look at), metrics.json (to check
# numerically), a flattened PNG and the re-editable .kra.
import json
import os

from krita import Krita, InfoObject, ManagedColor
from PyQt5.QtCore import QByteArray, QPoint, QPointF, QRectF, Qt
from PyQt5.QtGui import QColor, QImage, QLinearGradient, QPainter

OUT = globals().get("OUT") or os.environ["OUT"]
os.makedirs(OUT, exist_ok=True)
W, H = 1200, 1600
app = Krita.instance()


def push(node, image, x=0, y=0):
    """QImage (ARGB32) -> paint layer pixels. Krita's RGBA8 wants BGRA bytes,
    which is exactly the memory layout of QImage.Format_ARGB32 on little-endian
    machines — so the buffer can go straight in without a channel swap."""
    img = image.convertToFormat(QImage.Format_ARGB32)
    ptr = img.constBits()
    ptr.setsize(img.byteCount())
    node.setPixelData(QByteArray(ptr.asstring()), x, y, img.width(), img.height())


doc = app.createDocument(W, H, "poster_v1", "RGBA", "U8", "", 300.0)
view = app.activeWindow().addView(doc)   # show it — and paint* needs a view
doc.setBatchmode(True)                   # no export/save dialogs

# --- background: a gradient painted with QPainter -----------------------------
bg = doc.createNode("background", "paintlayer")
doc.rootNode().addChildNode(bg, None)

img = QImage(W, H, QImage.Format_ARGB32)
img.fill(Qt.transparent)
p = QPainter(img)
p.setRenderHint(QPainter.Antialiasing)
grad = QLinearGradient(QPointF(0, 0), QPointF(0, H))
grad.setColorAt(0.0, QColor("#12263a"))
grad.setColorAt(1.0, QColor("#06121f"))
p.fillRect(QRectF(0, 0, W, H), grad)
p.setBrush(QColor("#ff6b35"))
p.setPen(Qt.NoPen)
p.drawEllipse(QPointF(W * 0.62, H * 0.34), 260, 260)
p.end()
push(bg, img)

# --- a blurred copy of the blob, on its own layer ------------------------------
glow = doc.createNode("glow", "paintlayer")
doc.rootNode().addChildNode(glow, None)
blob = QImage(W, H, QImage.Format_ARGB32)
blob.fill(Qt.transparent)
p = QPainter(blob)
p.setRenderHint(QPainter.Antialiasing)
p.setBrush(QColor(255, 107, 53, 150))
p.setPen(Qt.NoPen)
p.drawEllipse(QPointF(W * 0.62, H * 0.34), 320, 320)
p.end()
push(glow, blob)

blur = app.filter("blur")
cfg = blur.configuration()
cfg.setProperty("halfWidth", 40)
cfg.setProperty("halfHeight", 40)
blur.setConfiguration(cfg)
blur.apply(glow, 0, 0, W, H)
glow.setBlendingMode("add")
glow.setOpacity(180)

# --- an accent stroke from the real brush engine --------------------------------
stroke = doc.createNode("stroke", "paintlayer")
doc.rootNode().addChildNode(stroke, None)
doc.setActiveNode(stroke)
presets = app.resources("preset")
name = next((n for n in sorted(presets) if "Basic-5 Size" in n), sorted(presets)[0])
view.setCurrentBrushPreset(presets[name])
view.setBrushSize(26.0)
view.setPaintingOpacity(1.0)
view.setForeGroundColor(ManagedColor.fromQColor(QColor("#f5f5f5")))
if stroke.paintAbility() == "PAINT":     # UNPAINTABLE without a view, or on vector layers
    # paintLine takes QPoint — a QPointF is a TypeError here, unlike the rect calls
    stroke.paintLine(QPoint(90, 1180), QPoint(1110, 1180), 1.0, 0.15, "ForegroundColor")
else:
    print("WARNING: cannot paint on this node:", stroke.paintAbility())

# --- headline as real vector text (SVG on a vector layer) ----------------------
text = doc.createVectorLayer("headline")
doc.rootNode().addChildNode(text, None)
text.addShapesFromSvg(
    '<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d">'
    '<text x="90" y="1320" fill="#f5f5f5" font-family="Helvetica" font-size="150">'
    'KRITA</text>'
    '<text x="90" y="1420" fill="#ff6b35" font-family="Helvetica" font-size="60">'
    'scripted from the bridge</text></svg>' % (W, H))

doc.refreshProjection()
doc.waitForDone()

# --- verify: a picture to Read, and numbers to assert on -----------------------
doc.projection(0, 0, W, H).scaledToWidth(600).save(os.path.join(OUT, "check.png"))
metrics = {
    "size": [doc.width(), doc.height()],
    "resolution": doc.resolution(),
    "layers": [(n.name(), n.type(), n.bounds().width(), n.bounds().height())
               for n in doc.rootNode().childNodes()],
}
json.dump(metrics, open(os.path.join(OUT, "metrics.json"), "w"), indent=2)
print("METRICS", json.dumps(metrics))

# --- deliverables ---------------------------------------------------------------
doc.exportImage(os.path.join(OUT, "poster.png"), InfoObject())
doc.saveAs(os.path.join(OUT, "poster.kra"))
doc.waitForDone()
print("wrote", OUT)
