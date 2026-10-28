# Recipes

`S=<this skill>/scripts`. Every recipe writes new files and leaves its inputs alone.

## Deck from an outline

```markdown
# Northwind Field Trial 2026
Results from the spring pilot

## Why we ran the pilot
- Three regional depots
  - one per region
- Eight weeks, February to April

Notes: Open with the problem the depots had last winter.

## The depot at Kestrel Bay
![Kestrel Bay depot](photo.jpg)

# Part two                        ← a later H1 is a section header slide
```

```sh
python3 $S/dk_build.py outline.md --dry-run            # check the parse first
python3 $S/dk_build.py outline.md --out out/deck.deckcraft --theme Harbor \
    --pptx out/deck.pptx --pdf out/deck.pdf --png-dir out/png
```

The JSON report lists every slide's title, layout, bullet count, pictures and whether it
has notes, plus `problems` (empty = the read-back matched). Then look at `out/png/`.

Outlines that don't follow these rules (e.g. bold lines as titles, numbered "Slide 3:"
headings) are easier to rewrite into this shape first than to build by hand.

## Open, edit, export

Inspect, then write the edits against what you saw:

```sh
python3 $S/dk_verify.py deck in/quarterly.pptx          # titles, layouts, text per slide
python3 $S/dk_edit.py in/quarterly.pptx out/quarterly-q3.pptx '[
  {"op": "title", "slide": 1, "text": "Q3 2026 Update"},
  {"op": "delete", "slide": 4},
  {"op": "move", "slide": "last", "to": 2}
]' --pdf out/quarterly-q3.pdf \
   --expect-titles "Q3 2026 Update" Questions Agenda Highlights Risks
python3 $S/dk_verify.py pdf out/quarterly-q3.pdf --pages 5 \
   --order "Q3 2026 Update" Questions Agenda Highlights Risks
```

Edits are applied in order to the deck as it is after the previous edit — "delete slide
4, then move the last slide to 2" reads naturally. When the user lists positions in the
*original* deck ("delete 3 and 5"), use one delete with a list (`"slide": [3, 5]`), which
resolves both against the same state.

The same with raw `run` (ids from `slide.inspect`; this is what `dk_edit.py` automates):

```sh
deckcraft-cli run --in in.pptx --print --cmd 'slide.inspect={"index":0}'   # title id, e.g. 258
deckcraft-cli run --in in.pptx --cmd 'slide.go={"index":0}' \
  --cmd 'text.set={"id":258,"text":"Q3 2026 Update"}' \
  --cmd 'slide.delete={"index":3}' --cmd 'slide.move={"from":4,"to":1}' \
  --save out.pptx --export out.pdf
```

## Folder conversion with thumbnails

```sh
python3 $S/dk_convert.py in/decks out --to pdf,png --thumb-width 480
# out/alpha.pdf, out/alpha.png (slide 1, 480×270) …; pages checked against slide counts
python3 $S/dk_convert.py in/decks out --to png --all-slides --scale 1   # out/NAME/slide-01.png …
```

## Notes pages and handouts

```sh
deckcraft-cli run --in deck.pptx --export notes.pdf --export-params '{"layout":"notes","paper":"a4"}'
deckcraft-cli run --in deck.pptx --export handout.pdf --export-params '{"layout":"handouts","perPage":3}'
```

## Animated GIF of a deck

```sh
deckcraft-cli run --in deck.pptx --export deck.gif \
  --export-params '{"width":"medium","secondsPerSlide":3,"loop":true}'
```

## Table, chart, transitions, slide numbers

```sh
deckcraft-cli run --in deck.deckcraft --print \
  --cmd 'slide.new={"at":5,"layout":"titleOnly","title":"Numbers"}' \
  --cmd 'insert.table={"rows":3,"cols":2,"rect":[80,150,800,200]}' \
  --cmd 'text.set={"cell":[0,0],"text":"Depot"}' \
  --cmd 'slide.new={"at":6,"layout":"titleOnly","title":"Revenue"}' \
  --cmd 'insert.chart={"type":"column","rect":[80,140,800,360],"categories":["Q1","Q2"],"series":[{"name":"Revenue","values":[3,5]}]}' \
  --cmd 'chart.options={"title":null}' \
  --cmd 'transition.set={"kind":"fade","index":1}' \
  --cmd 'design.headerFooter={"slideNumber":true,"hideOnTitle":true}' \
  --save out/deck-v2.deckcraft
deckcraft-cli render out/deck-v2.deckcraft --all out/png
```

A freshly inserted table or chart is selected, so `text.set {cell}` and `chart.options`
right after it act on it; later, pass its `id`.

## Bring slides from another deck

```sh
deckcraft-cli run --in main.pptx --print --cmd 'slide.reuseList={"path":"/abs/other.pptx"}'
deckcraft-cli run --in main.pptx --cmd 'slide.reuse={"path":"/abs/other.pptx","slides":[0,2],"at":3}' --save merged.pptx
```
