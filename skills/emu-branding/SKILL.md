---
name: emu-branding
description: "Brand guidelines and visual identity for EMU (Egyesület a Magyar Ultrafutásért). Use when creating any EMU-related visual content: social media posts, race posters, event presentations, documents, charts, data visualizations, or marketing materials. Covers logo usage, the EMU Blue (#00ADEF) color palette, Nebula Sans typography, and photography style. Also use when someone mentions the EMU 6-Day Race, ultrarunning branding, or needs on-brand design assets — even if they don't explicitly say 'brand guidelines'. Hungarian triggers: 'EMU-s poszt', 'EMU arculat', 'plakát a 6 napos versenyre', 'EMU színekkel'."
summary: "brand guidelines and visual identity for EMU (Egyesület a Magyar Ultrafutásért), including logo, color palette, and typography"
category: branding
risk: low
tags:
  - branding
  - visual-identity
  - emu
  - ultrarunning
  - design-assets
allowed-tools: Read, Glob
---

# EMU Branding

Official brand guidelines for **EMU** (Egyesület a Magyar Ultrafutásért).

Asset paths below are relative to this skill's directory. Resolve them to absolute paths
before use — the output you build almost always lives somewhere else. For the concrete
code (embedding fonts in HTML, matplotlib/Pillow setup, Office documents) read
[references/implementation.md](references/implementation.md) once you know the medium.

## Brand Identity

| Property | Value |
|---|---|
| Full name | Egyesület a Magyar Ultrafutásért |
| Short name / acronym | EMU |
| Mission | Promoting and supporting ultrarunning in Hungary and around the world! |
| Flagship event | EMU 6-Day Race |

The logo features a stylized running emu bird — a wordplay on the association's acronym —
with a gray body (`#4F4C4D`), an EMU Blue neck and black head, above a lowercase slab-serif
**emu** wordmark in EMU Blue.

## Logo

| Asset | Path | When to use |
|---|---|---|
| Badge logo | `assets/images/emu-logo.png` | On white circular badge — dark or busy backgrounds, avatars, favicons |
| Transparent logo | `assets/images/emu-logo-transparent.png` | Transparent background, higher resolution — default choice on white/light backgrounds, posters, headers, documents |

Prefer the transparent version whenever it's placed directly on a light surface; use the badge version when the background is dark, textured, a photo, or EMU Blue itself — the gray body disappears on dark surfaces and the blue neck and wordmark disappear on blue ones.

### Usage Rules

- Provide adequate clear space around the logo (minimum 10% of logo height on each side)
- Do not distort, rotate, or recolor
- Minimum size: 40px height for digital, 15mm for print
- On dark, photographic or EMU Blue backgrounds, use the badge version (`emu-logo.png`)
- Always place the logo image; never retype the "emu" wordmark in Nebula Sans or any other font — the slab-serif wordmark is part of the mark

## Color Palette

### Primary — EMU Blue

The single most important brand color, defined in code as EMU Blue:

| Property | Value |
|---|---|
| Hex | `#00ADEF` |
| RGB | `0, 173, 239` |
| Usage | Primary accent, single-series charts, area chart fills, histogram bars, CTA buttons |

When used as a fill with transparency (e.g., area chart backgrounds), use EMU Blue with 50% alpha.

### Supporting Colors

These colors complement EMU Blue in designs and marketing materials:

| Color | Hex | Usage |
|---|---|---|
| White | `#FFFFFF` | Backgrounds, negative space |
| Light Gray | `#F5F5F5` | Cards, background variation |
| Dark (near-black) | `#1A1A1A` | Headlines, emphasized text |
| Medium Gray | `#5A5A5A` | Body text, secondary elements |
| Dark Blue | `#006BA6` | Hover states, links and blue text on light backgrounds |
| Emu Gray | `#4F4C4D` | The logo's body color — secondary graphic accent, chart series |

### Contrast — where EMU Blue can and cannot go

EMU Blue is bright: on white it reaches only **2.5:1**, below the 4.5:1 needed for readable
text. That shapes a few recurring decisions:

| Combination | Ratio | Use for |
|---|---|---|
| `#1A1A1A` text on EMU Blue | 6.8:1 | Buttons, badges, banners — the default on a blue fill |
| White text on EMU Blue | 2.5:1 | Only very large display type (≥ 40px bold), never body or button labels |
| EMU Blue text on white | 2.5:1 | Large headlines and decorative accents only |
| Dark Blue `#006BA6` on white | 5.8:1 | Links and small blue text on light backgrounds |
| White on Dark Blue `#006BA6` | 5.8:1 | Alternative button style when white text is wanted |
| EMU Blue on `#121212` | 7.3:1 | Links and accents in dark mode — EMU Blue shines here |

## Typography

### Official Brand Font — Nebula Sans

The brand font is **Nebula Sans**, bundled in the skill assets at `assets/fonts/NebulaSans/` in OTF, TTF, and WOFF2 formats.

**Available weights:**

| Weight | File name | Recommended usage |
|---|---|---|
| Light | `NebulaSans-Light` | Decorative, large display text |
| Book | `NebulaSans-Book` | Body text, paragraphs |
| Medium | `NebulaSans-Medium` | Subheadings, UI labels |
| Semibold | `NebulaSans-Semibold` | Section titles, emphasis |
| Bold | `NebulaSans-Bold` | Headlines, CTAs |
| Black | `NebulaSans-Black` | Hero titles, poster headlines |

All weights also have **Italic** variants (e.g., `NebulaSans-BoldItalic`).

**Fallback stack:** Montserrat, Open Sans, Roboto, system sans-serif

Nebula Sans covers the full Hungarian alphabet (ő, ű, Ő, Ű), typographic quotes („ ”) and
en dashes, so Hungarian copy needs no fallback font.

### Font Sizes (Web / Print)

| Level | Size | Weight |
|---|---|---|
| H1 | 36–48px | Bold or Black |
| H2 | 28–32px | Bold |
| H3 | 20–24px | Semibold |
| Body | 16px | Book |
| Small | 14px | Book or Light |

### Loading the font

The font is only on-brand if it actually renders — a page that names `'Nebula Sans'`
without loading it silently falls back to Arial. Weight mapping: Light=300, Book=400,
Medium=500, Semibold=600, Bold=700, Black=900.

- **HTML:** `python3 scripts/font_face_css.py Book Bold Black` prints `@font-face` rules
  with the WOFF2 files base64-embedded, so a single-file page works anywhere; add
  `--href fonts` to link copied files instead.
- **matplotlib / Pillow:** register or open the TTF files by absolute path.
- **Word / PowerPoint:** fonts are referenced by name, not embedded — tell the user.

Details and snippets for each: [references/implementation.md](references/implementation.md).

## Visual Style

### Photography

- Ultrarunning action photos — runners on roads
- Hungarian landscapes and race events (especially the EMU 6-Day Race venue)
- Dynamic, energetic compositions with natural lighting
- Avoid overly staged or stock-photo feel

### Graphic Elements

- Clean, modern lines — avoid heavy ornamentation
- The emu silhouette can serve as a decorative element or pattern
- EMU Blue as the dominant accent color
- Simple geometric shapes for backgrounds and framing

## Data Visualization & Charts

When creating charts or data visualizations:

| Element | Style |
|---|---|
| Single series | EMU Blue `#00ADEF` solid |
| Area fills | EMU Blue at 50% opacity |
| Multi-series palette | In order: `#00ADEF`, `#006BA6`, `#4F4C4D`, `#80D6F7`, `#1A1A1A`, `#A7A5A6` — more than 6 series is a sign to split the chart |
| Highlight one item | That item in EMU Blue, every other bar/line in `#C8C8C8` |
| Grid lines | `#E0E0E0`, 1px |
| Axis labels | Nebula Sans Book, `#5A5A5A`, 14px |
| Chart title | Nebula Sans Semibold, `#1A1A1A`, 20px |
| Annotations | Nebula Sans Medium, EMU Blue |

Use clean, minimal chart styles — avoid 3D effects, excessive gridlines, or heavy borders. White background by default. Left-align the title, drop the top and right spines, and label values directly on bars when there are few enough to read. A small logo in a corner is welcome on charts meant for social media; skip it on charts embedded in EMU's own documents.

## Dark Mode

When creating content for dark backgrounds or dark-mode UIs:

| Element | Light mode | Dark mode |
|---|---|---|
| Background | `#FFFFFF` | `#121212` |
| Card surface | `#F5F5F5` | `#1E1E1E` |
| Primary text | `#1A1A1A` | `#E0E0E0` |
| Secondary text | `#5A5A5A` | `#9E9E9E` |
| EMU Blue | `#00ADEF` (unchanged) | `#00ADEF` (unchanged) |
| Grid lines | `#E0E0E0` | `#333333` |

EMU Blue reads even better on dark backgrounds than on light ones (7.3:1 on `#121212`), so in dark mode it can carry links and small accent text too. On dark backgrounds use the badge logo (`emu-logo.png`) — its white circle provides the needed contrast.

## Social Media

### Post Dimensions

| Platform | Format | Dimensions |
|---|---|---|
| Instagram post | Portrait (preferred — fills the feed) | 1080×1350px |
| Instagram post | Square | 1080×1080px |
| Instagram story | Vertical | 1080×1920px |
| Facebook post | Landscape | 1200×630px |
| Facebook cover | Wide | 1640×924px |
| X/Twitter post | Landscape | 1600×900px |

### Hashtags
- `#EMU6DayRace`
- `#6DayRace`
- `#6DayRun`
- `#ultrafutás` (Hungarian)
- `#ultrarunning`

### Tone of Voice

- Enthusiastic, motivating — celebrating runner achievements
- Community-building — inclusive of all ultrarunners
- Professional yet friendly and accessible
- Bilingual: English for international audience, Hungarian for local events
- Hungarian copy uses Hungarian conventions: „idézőjel”, decimal comma (`812,3 km`), date
  as `2026. május 18.`, and thin-space or space thousands separators (`1 000 km`)
