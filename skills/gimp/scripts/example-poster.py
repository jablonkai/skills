"""A complete build -> verify -> export script for the GIMP bridge.

Run it with:  OUT=/some/dir bash scripts/gimp-send.sh scripts/example-poster.py

It shows the shape every build script should have: make a fresh image so a
re-send cannot stack layers onto the previous attempt, show it so the user
watches the build happen, then write a check PNG and a metrics JSON that can be
read back -- print() alone tells you the script ran, not that it looks right.
"""

import json
import os

import gi

gi.require_version("Babl", "0.1")
gi.require_version("Gegl", "0.4")
gi.require_version("Gimp", "3.0")
from gi.repository import Babl, Gegl, Gimp, Gio  # noqa: E402

Gegl.init(None)

OUT = os.environ.get("OUT", "/tmp")
W, H = 1000, 1400
VERSION = "v1"                      # bump per attempt; the name identifies the run

INK = "#0d1b2a"
ACCENT = "#00adef"
WARM = "#ffb703"


def rgb(css):
    """sRGB from a CSS string. Never Gegl.Color.set_rgba() -- that takes linear."""
    return Gegl.Color.new(css)


image = Gimp.Image.new(W, H, Gimp.ImageBaseType.RGB)
image.undo_group_start()

background = Gimp.Layer.new(image, "background", W, H, Gimp.ImageType.RGBA_IMAGE,
                            100.0, Gimp.LayerMode.NORMAL)
image.insert_layer(background, None, 0)
Gimp.context_set_foreground(rgb(INK))
background.fill(Gimp.FillType.FOREGROUND)

# A gradient band, drawn into its own layer so it stays editable for the user.
band = Gimp.Layer.new(image, "band", W, H, Gimp.ImageType.RGBA_IMAGE,
                      100.0, Gimp.LayerMode.NORMAL)
image.insert_layer(band, None, 0)
band.fill(Gimp.FillType.TRANSPARENT)
image.select_rectangle(Gimp.ChannelOps.REPLACE, 0, 760, W, 300)
Gimp.context_set_gradient_fg_bg_rgb()
Gimp.context_set_foreground(rgb(ACCENT))
Gimp.context_set_background(rgb(WARM))
band.edit_gradient_fill(Gimp.GradientType.LINEAR, 0.0, False, 1.0, 0.0, True,
                        0, 760, W, 1060)
Gimp.Selection.none(image)

# A soft glow behind the headline: a non-destructive filter, so the user can
# still dial it back by hand afterwards.
glow = Gimp.Layer.new(image, "glow", W, H, Gimp.ImageType.RGBA_IMAGE,
                      70.0, Gimp.LayerMode.SCREEN)
image.insert_layer(glow, None, 0)
glow.fill(Gimp.FillType.TRANSPARENT)
image.select_ellipse(Gimp.ChannelOps.REPLACE, 180, 200, 640, 380)
Gimp.context_set_foreground(rgb(ACCENT))
glow.edit_fill(Gimp.FillType.FOREGROUND)
Gimp.Selection.none(image)
blur = Gimp.DrawableFilter.new(glow, "gegl:gaussian-blur", "glow blur")
blur_config = blur.get_config()
blur_config.set_property("std-dev-x", 90.0)
blur_config.set_property("std-dev-y", 90.0)
blur.update()
glow.append_filter(blur)

# Text. Ask the context for the font rather than naming one: font names are
# system-dependent and Gimp.Font.get_by_name returns None for a miss, which
# then blows up inside TextLayer.new with a confusing "does not allow None".
font = Gimp.context_get_font()
headline = Gimp.TextLayer.new(image, "GIMP\nBRIDGE", font, 150.0, Gimp.Unit.pixel())
image.insert_layer(headline, None, 0)
headline.set_color(rgb("#f8f9fa"))
headline.set_justification(Gimp.TextJustification.CENTER)
headline.set_line_spacing(-18.0)
headline.set_offsets((W - headline.get_width()) // 2, 300)

caption = Gimp.TextLayer.new(image, "scripted in the live session", font, 42.0,
                             Gimp.Unit.pixel())
image.insert_layer(caption, None, 0)
caption.set_color(rgb(INK))
caption.set_offsets((W - caption.get_width()) // 2, 880)

image.undo_group_end()

# Show it: the point of driving a running GIMP is that the user sees this.
Gimp.Display.new(image)
Gimp.displays_flush()

# --- verification -----------------------------------------------------------
check_png = os.path.join(OUT, "poster_%s_check.png" % VERSION)
image.get_thumbnail(500, 700, Gimp.PixbufTransparency.SMALL_CHECKS).savev(
    check_png, "png", [], [])

srgb_u8 = Babl.format("R'G'B'A u8")
_, sampled = image.pick_color(image.get_layers(), 40.0, 40.0, True, False, 0.0)

metrics = {
    "version": VERSION,
    "size": [image.get_width(), image.get_height()],
    "corner_srgb": list(sampled.get_bytes(srgb_u8).get_data()),
    "layers": [
        {
            "name": layer.get_name(),
            "size": [layer.get_width(), layer.get_height()],
            "offsets": list(layer.get_offsets())[1:],
            "opacity": round(layer.get_opacity(), 1),
            "mode": layer.get_mode().value_nick,
            "filters": [f.get_operation_name() for f in layer.get_filters()],
        }
        for layer in image.get_layers()
    ],
}
with open(os.path.join(OUT, "poster_%s_metrics.json" % VERSION), "w") as fh:
    json.dump(metrics, fh, indent=2)

# --- deliverables -----------------------------------------------------------
# .xcf keeps every layer, mask and non-destructive filter editable for the user;
# the PNG is the thing they can hand on. Flatten a duplicate for the export so
# the live image keeps its stack.
Gimp.file_save(Gimp.RunMode.NONINTERACTIVE, image,
               Gio.File.new_for_path(os.path.join(OUT, "poster_%s.xcf" % VERSION)), None)

flat = image.duplicate()
flat.flatten()
Gimp.file_save(Gimp.RunMode.NONINTERACTIVE, flat,
               Gio.File.new_for_path(os.path.join(OUT, "poster_%s.png" % VERSION)), None)
flat.delete()

print("built %s (%dx%d), %d layers" % (VERSION, W, H, len(image.get_layers())))
print("check image:", check_png)
