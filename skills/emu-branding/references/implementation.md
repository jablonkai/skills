# Applying the brand in code

Recipes for getting Nebula Sans, the logo and the palette into each output medium.
`SKILL_DIR` below means the absolute path of the `emu-branding` skill directory —
resolve it once and use absolute paths, because the output usually lives elsewhere.

## Contents

- [HTML / CSS](#html--css)
- [Screenshots of HTML (PNG social posts)](#screenshots-of-html-png-social-posts)
- [matplotlib charts](#matplotlib-charts)
- [Pillow images](#pillow-images)
- [Word, PowerPoint, PDF](#word-powerpoint-pdf)

## HTML / CSS

A single-file page (artifact, email preview, a post rendered to PNG) cannot reach the
skill's font files, so embed them. The bundled script prints ready `@font-face` rules:

```bash
python3 SKILL_DIR/scripts/font_face_css.py Book Semibold Bold Black > fonts.css   # base64-embedded
python3 SKILL_DIR/scripts/font_face_css.py --href fonts Book Bold                  # link to ./fonts/
```

Each weight is ~70 KB of base64, so embed only the weights the page uses. For a
multi-file site, copy the `.woff2` files next to the page and use `--href`.

Logos go the same way: embed as `data:image/png;base64,...` in single-file output, or copy
the PNG next to the page. Never hot-link a path inside the skill directory.

Starter tokens:

```css
:root {
  --emu-blue: #00ADEF;  --emu-blue-dark: #006BA6;  --emu-gray: #4F4C4D;
  --text: #1A1A1A;  --text-2: #5A5A5A;  --bg: #FFFFFF;  --surface: #F5F5F5;  --grid: #E0E0E0;
  font-family: 'Nebula Sans', Montserrat, 'Open Sans', Roboto, system-ui, sans-serif;
}
@media (prefers-color-scheme: dark) {
  :root { --text: #E0E0E0; --text-2: #9E9E9E; --bg: #121212; --surface: #1E1E1E; --grid: #333333; }
}
body { background: var(--bg); color: var(--text); }
a { color: var(--emu-blue-dark); }                     /* EMU Blue fails contrast as text on white */
@media (prefers-color-scheme: dark) { a { color: var(--emu-blue); } }
.cta { background: var(--emu-blue); color: #1A1A1A; }  /* dark text on EMU Blue: 6.8:1 */
```

Swap the logo per theme with `<picture>`: the transparent logo on light, the badge on dark.

```html
<picture>
  <source srcset="emu-logo.png" media="(prefers-color-scheme: dark)">
  <img src="emu-logo-transparent.png" alt="EMU logo" height="64">
</picture>
```

## Screenshots of HTML (PNG social posts)

Set the viewport to the exact post size and wait for fonts before capturing, otherwise
the fallback font gets baked into the image:

```js
await page.setViewportSize({ width: 1080, height: 1350 });
await page.goto(`file://${htmlPath}`);
await page.evaluate(() => document.fonts.ready);
await page.screenshot({ path: 'post.png' });
```

## matplotlib charts

matplotlib does not see fonts that are not installed; register the TTFs explicitly:

```python
from pathlib import Path
import matplotlib as mpl
from matplotlib import font_manager

ttf = Path(SKILL_DIR) / "assets/fonts/NebulaSans/TTF"
for f in ttf.glob("NebulaSans-*.ttf"):
    font_manager.fontManager.addfont(str(f))

mpl.rcParams.update({
    "font.family": "Nebula Sans",
    "axes.edgecolor": "#E0E0E0", "axes.labelcolor": "#5A5A5A",
    "xtick.color": "#5A5A5A", "ytick.color": "#5A5A5A",
    "axes.grid": True, "grid.color": "#E0E0E0", "grid.linewidth": 1,
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.prop_cycle": mpl.cycler(color=["#00ADEF", "#006BA6", "#4F4C4D", "#80D6F7", "#1A1A1A", "#A7A5A6"]),
    "figure.facecolor": "white", "axes.facecolor": "white",
})
ax.set_title("…", fontsize=20, fontweight="semibold", color="#1A1A1A", loc="left")
```

Check that it took: `font_manager.findfont("Nebula Sans")` should return a path inside
the skill, not DejaVuSans.

On some recent macOS versions importing `font_manager` dies with `KeyError: '_items'`
while matplotlib scans system fonts through `system_profiler`. The chart only needs the
bundled TTFs, so skip the macOS scan for that one import:

```python
import sys
try:
    from matplotlib import font_manager
except KeyError:  # macOS system_profiler format change breaks the system-font scan
    for m in [k for k in sys.modules if k.startswith("matplotlib.")]:
        del sys.modules[m]
    real, sys.platform = sys.platform, "linux"
    try:
        from matplotlib import font_manager
    finally:
        sys.platform = real
``` Put the logo in a corner with `fig.figimage` or an
`OffsetImage`, small enough not to compete with the data.

## Pillow images

```python
from PIL import ImageFont
headline = ImageFont.truetype(f"{SKILL_DIR}/assets/fonts/NebulaSans/TTF/NebulaSans-Black.ttf", 96)
body = ImageFont.truetype(f"{SKILL_DIR}/assets/fonts/NebulaSans/TTF/NebulaSans-Book.ttf", 36)
```

Paste the logo with its own alpha as the mask: `canvas.paste(logo, (x, y), logo)`.

## Word, PowerPoint, PDF

- **.docx / .pptx** reference fonts by name and do not embed them via python-docx /
  python-pptx. Set `Nebula Sans` on the text, and tell the user that recipients need the
  font installed (the TTFs are in `assets/fonts/NebulaSans/TTF/`) — otherwise Office
  substitutes it. If the file will circulate widely, offer to export a PDF as well.
- **PDF** (reportlab, WeasyPrint, a browser print) embeds whatever font it renders with,
  so register the TTF/WOFF2 files and the result is portable.
- Accent colour for headings, rules and table headers is EMU Blue; body text stays
  `#1A1A1A` / `#5A5A5A`.
