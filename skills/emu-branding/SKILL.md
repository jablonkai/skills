---
name: emu-branding
description: "Brand guidelines and visual identity for EMU (Egyesület a Magyar Ultrafutásért — Association for Hungarian Ultrarunning). Use when creating any EMU-related visual content: social media posts, race posters, event presentations, documents, charts, data visualizations, or marketing materials. Covers logo usage, the EMU Blue (#00ADEF) color palette, Nebula Sans typography, and photography style. Also use when someone mentions the EMU 6-Day Race, ultrarunning branding, or needs on-brand design assets — even if they don't explicitly say 'brand guidelines'."
---

# EMU Branding

Official brand guidelines for **EMU** (Egyesület a Magyar Ultrafutásért — Association for Hungarian Ultrarunning).

## Brand Identity

| Property | Value |
|---|---|
| Full name | Egyesület a Magyar Ultrafutásért |
| Short name / acronym | EMU |
| Mission | Promoting and supporting ultrarunning in Hungary and around the world! |
| Flagship event | EMU 6-Day Race |

The logo features a stylized running emu bird — a wordplay on the association's acronym.

## Logo

| Asset | Path | When to use |
|---|---|---|
| Badge logo | `assets/images/emu-logo.png` | On white circular badge — dark or busy backgrounds, avatars, favicons |
| Transparent logo | `assets/images/emu-logo-transparent.png` | Transparent background, higher resolution — default choice on white/light backgrounds, posters, headers, documents |

Prefer the transparent version whenever it's placed directly on a light surface; use the badge version when the background is dark or textured, since the emu body is dark gray and needs the white badge for contrast.

### Usage Rules

- Provide adequate clear space around the logo (minimum 10% of logo height on each side)
- Do not distort, rotate, or recolor
- Minimum size: 40px height for digital, 15mm for print
- On dark backgrounds, use the badge version (`emu-logo.png`) — the transparent logo's dark gray body loses contrast

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
| Dark Blue | `#006BA6` | Hover states, darker accents (darken EMU Blue) |

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

### Font Sizes (Web / Print)

| Level | Size | Weight |
|---|---|---|
| H1 | 36–48px | Bold or Black |
| H2 | 28–32px | Bold |
| H3 | 20–24px | Semibold |
| Body | 16px | Book |
| Small | 14px | Book or Light |

### Font Usage — Web (@font-face)

When building web content, load Nebula Sans from the bundled WOFF2 files:

```css
@font-face {
  font-family: 'Nebula Sans';
  src: url('path/to/NebulaSans-Book.woff2') format('woff2');
  font-weight: 400;
  font-style: normal;
}
@font-face {
  font-family: 'Nebula Sans';
  src: url('path/to/NebulaSans-Bold.woff2') format('woff2');
  font-weight: 700;
  font-style: normal;
}
```

Add additional `@font-face` blocks for each weight used. Map weights: Light=300, Book=400, Medium=500, Semibold=600, Bold=700, Black=900.

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
| Multi-series palette | `#00ADEF`, `#006BA6`, `#5A5A5A`, `#1A1A1A` (max 4, then cycle lighter variants) |
| Grid lines | `#E0E0E0`, 1px |
| Axis labels | Nebula Sans Book, `#5A5A5A`, 14px |
| Chart title | Nebula Sans Semibold, `#1A1A1A`, 20px |
| Annotations | Nebula Sans Medium, EMU Blue |

Use clean, minimal chart styles — avoid 3D effects, excessive gridlines, or heavy borders. White background by default.

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

EMU Blue works well on both light and dark backgrounds. On dark backgrounds use the badge logo (`emu-logo.png`) — its white circle provides the needed contrast.

## Social Media

### Post Dimensions

| Platform | Format | Dimensions |
|---|---|---|
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
