# Recipes (DesignCraft 0.14.0)

`S=<skill>/scripts`. Every recipe ends with a read-back; don't skip it.

## Contents

- [Brochure from a spec](#brochure-from-a-spec)
- [Name badges from CSV](#name-badges-from-csv)
- [Open, edit, export](#open-edit-export)
- [The same by hand: a command script](#the-same-by-hand-a-command-script)
- [IDML in and out](#idml-in-and-out)

## Brochure from a spec

4 A4 pages, facing; a parent with a header and an auto page number; a cover photo; body
text threaded across pages 2–3 with headings styled by a rule; PDF/X-4 with 3 mm bleed.

```json
{
  "document": "out/brochure.designcraft",
  "setup": {"preset": "A4", "pages": 4, "facingPages": true, "margins": "15mm", "bleed": "3mm"},
  "styles": {"paragraph": [
    {"name": "Header", "chars": {"fontFamily": "Helvetica", "size": 9}},
    {"name": "Folio", "chars": {"fontFamily": "Helvetica", "size": 9}, "para": {"align": "center"}},
    {"name": "Body", "chars": {"fontFamily": "Helvetica", "size": 10.5,
      "leading": {"kind": "points", "value": 14}}, "para": {"spaceAfter": 6}},
    {"name": "Heading", "basedOn": "Body", "chars": {"fontStyle": "Bold", "size": 13},
      "para": {"spaceBefore": 8}}
  ]},
  "parent": [
    {"type": "text", "rect": ["15mm", "6mm", "-15mm", "12mm"], "text": "Northwind Trails", "style": "Header"},
    {"type": "text", "rect": ["15mm", "-11mm", "-15mm", "-5mm"], "text": "{page}", "style": "Folio"}
  ],
  "items": [
    {"type": "image", "page": 1, "rect": [0, 0, "-0", "-0"], "bleed": true, "image": "photo1.jpg"},
    {"type": "text", "frames": [{"page": 2, "rect": "margins"}, {"page": 3, "rect": "margins"}],
     "textFile": "body.txt", "style": "Body", "rules": [{"regex": "^.{1,40}$", "style": "Heading"}]},
    {"type": "image", "page": 4, "rect": ["15mm", "20mm", "-15mm", "150mm"], "image": "photo2.jpg",
     "fit": "fitProportionally"}
  ],
  "png": [{"page": 2, "scale": 1, "out": "out/p2.png"}],
  "pdf": {"out": "out/brochure.pdf", "standard": "x4", "bleed": true, "marks": true}
}
```

```sh
python3 $S/dc_build.py spec.json
python3 $S/dc_verify.py doc out/brochure.designcraft --pages 4 --size A4 --no-overset \
  --style Body:size=10.5 --thread 'The ridge trail=2,3' --image photo1.jpg@1 photo2.jpg@4 \
  --parent-text 'Northwind Trails' --page-number
python3 $S/dc_verify.py pdf out/brochure.pdf --x4 --pages 4 --bleed 3mm --marks --page-numbers
```

Then look at `out/p2.png`. Notes:

- Parent items go on both pages of a facing parent spread by default (`"on": "left"` /
  `"right"` for one side). On facing pages `"margins"` uses inside/outside correctly per side.
- A rule's regex is matched per paragraph; here short lines (the headings in body.txt) get
  `Heading`. Body text with no headings needs no rules.
- Overset fails the build before anything is saved: add a frame to `frames`, enlarge
  them, or reduce the size/leading. `--allow-overset` only when the user accepts it.
- Fonts: give `fontFamily` (and `fontStyle`) in styles; the default is the bundled serif.
  `font.list` after the build shows any missing font.

## Name badges from CSV

85 × 55 mm badges, eight per A4 sheet. Build the template with `"data"` and `{{column}}`
fields, then merge:

```json
{
  "document": "out/badge-template.designcraft",
  "setup": {"preset": "A4", "pages": 1, "facingPages": false, "margins": "10mm"},
  "data": "attendees.csv",
  "styles": {"paragraph": [
    {"name": "Name", "chars": {"fontFamily": "Helvetica", "fontStyle": "Bold", "size": 18}, "para": {"align": "center"}},
    {"name": "Role", "chars": {"fontFamily": "Helvetica", "size": 10}, "para": {"align": "center"}}
  ]},
  "items": [
    {"type": "rect", "page": 1, "rect": ["10mm", "10mm", "95mm", "65mm"]},
    {"type": "text", "page": 1, "rect": ["14mm", "25mm", "91mm", "35mm"], "text": "{{name}}", "style": "Name"},
    {"type": "text", "page": 1, "rect": ["14mm", "40mm", "91mm", "55mm"], "text": "{{title}}\n{{company}}", "style": "Role"}
  ]
}
```

```sh
python3 $S/dc_build.py badge-spec.json
python3 $S/dc_merge.py out/badge-template.designcraft --pdf out/badges.pdf \
  --per-page multiple --row-spacing 5 --column-spacing 5 --png out/sheet1.png
python3 $S/dc_verify.py pdf out/badges.pdf --text 'Ada Lovelace' 'Edsger Dijkstra' --once
```

- `rect` without fill or stroke is the cut line: an `unassigned` frame gets a 1 pt black
  stroke from `[Basic Graphics Frame]`. Give `"fill"` a swatch name for a coloured badge.
- `--per-page multiple` tiles the whole page content (everything on page 1) as one record;
  the template page must be single and non-facing. One badge per page: make the page the
  badge size (`"setup": {"width": "85mm", "height": "55mm", …}`) and leave `--per-page`
  at `single`.
- `dc_merge.py` refuses when a `<<field>>` isn't a column; `--dry-run` shows fields and
  record count without merging.

## Open, edit, export

Restyle, swap a photo and export page 1 at 2×, never touching the original:

```sh
cp in/newsletter.designcraft out/newsletter-edited.designcraft
python3 $S/dc_verify.py doc out/newsletter-edited.designcraft      # styles, images per page
designcraft-cli run --in out/newsletter-edited.designcraft --cmd links.list   # asset ids
designcraft-cli run --in out/newsletter-edited.designcraft \
  --cmd 'style.paragraph.edit={"name":"Body","chars":{"size":12}}' \
  --cmd 'links.relink={"asset":11,"path":"/abs/in/photo-new.jpg"}' \
  --cmd 'file.save={}' \
  --scale 2 --page 0 --export out/page1.png
python3 $S/dc_verify.py doc out/newsletter-edited.designcraft --style Body:size=12 \
  --image photo-new.jpg@1 photo2.jpg@2 --no-overset
python3 $S/dc_verify.py png out/page1.png --size 1191x1684
```

- `style.paragraph.edit` changes only the attributes it names; other attributes and the
  text using the style follow automatically. A bigger size can push a story into overset —
  check it.
- `links.relink` swaps the file for **every** placement of that asset. To replace one
  placement only, `file.place {path, frame: <item id>}` into that frame instead.
- Text: `story.setText {story, text}` replaces a whole story; `find.change` for a word.

## The same by hand: a command script

When `dc_build.py` doesn't cover something (tables, a second parent, sections), write a
script; `$N.path` takes values from earlier steps (0-based):

```text
# steps.dcs
file.new {"preset": "A4", "pages": 3, "facingPages": false, "margins": 42, "bleed": 8.504}
style.paragraph.create {"name": "Body", "chars": {"size": 10.5}}
frame.create {"spread": {"kind": "parent", "index": 0}, "rect": [42, 806, 553, 822], "content": "text", "text": "\ue000"}
frame.create {"spread": 0, "rect": [42, 42, 553, 800], "content": "text", "text": " "}
file.place {"path": "/abs/body.txt", "frame": "$3.id"}
text.thread {"from": "$3.id", "rect": [42, 42, 553, 800], "spread": 1}
text.select {"story": "$3.story", "anchor": 0, "focus": 999999}
style.paragraph.apply {"name": "Body"}
file.exportPdf {"path": "/abs/out/doc.pdf", "standard": "x4", "bleed": true, "marks": true}
```

```sh
designcraft-cli script steps.dcs --save out/doc.designcraft
```

A `focus` past the end selects to the end of the story. Paths in scripts are best
absolute: they resolve against the CLI's working directory.

## IDML in and out

```sh
designcraft-cli run --in brochure.idml --cmd document.inspect      # open IDML directly
designcraft-cli run --in brochure.idml --export brochure.designcraft
designcraft-cli run --in brochure.designcraft --export brochure.idml
```

Check what came across with `dc_verify.py doc` (pages, styles, missing links); IDML's
linked images must be reachable from the IDML's folder.
