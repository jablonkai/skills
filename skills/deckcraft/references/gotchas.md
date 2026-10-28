# Gotchas (DeckCraft 0.11.1)

Each of these was hit while building and verifying the skill.

## Building decks

- **Every new presentation starts with one empty title slide** — `run` without `--in`,
  `file.new`, MCP `new_presentation`. Commands that add slides insert *after* it, so a
  deck built by hand is one slide too long, with an empty first slide. Delete it before
  adding slides (`slide.delete {"index":0}` works on the only slide; the deck may be
  empty until the next `slide.new`).
- **`slide.fromOutline {markdown: true}`** turns every heading (`#` and `##` alike) into a
  *Title and Content* slide and list items into bullets. It makes no title slide, drops
  images and puts `Notes:` lines in the body. Fine for a quick draft, wrong for a
  finished deck — use `dk_build.py`.
- **Insert position:** `slide.new` and `slide.fromOutline` insert after the current
  slide. `slide.fromOutline` does not move the current slide, so a `slide.new` after it
  lands at index 1, before the outline's slides. Pass `at` (`slide.new {"at": N}`).
- **`pictureWithCaption` is a trap.** `slide.new {"layout":"pictureWithCaption",
  "body":"…"}` puts the body text into the *picture* placeholder, and `insert.picture`
  never fills a placeholder (it adds a free picture, even with the placeholder selected).
  For an image slide use `titleOnly` + `insert.picture {path, rect}` sized to the
  image's aspect ratio; for image + bullets, `twoContent` with the picture over the empty
  right-hand box.
- **`insert.picture` without `rect`** centres the image at its natural size, which may
  cover the title. Always pass a rect; `dklib.fit()` keeps the aspect ratio.
- **Bullet levels** come from leading tabs in `body`/`text.set` text (`"one\n\tsub"`);
  `text` in `slide.inspect` shows the text without the tabs.
- **Charts** show a literal "Chart Title" until `chart.options {"title": "…"}` (or
  `null` for none).

## Silent no-ops

- **Unknown parameters are ignored.** `slide.new {"titel": "x"}` makes an untitled slide
  and returns success. Copy parameter names from `describe`.
- **An unknown theme falls back to the default** — `file.new {"theme":"Harbour"}`,
  `design.theme {"name":"Harbour"}` and MCP `new_presentation {theme}` all succeed and
  leave DeckCraft. Check the name against `design.themes` and read `theme` back from
  `info`.
- `slide.notes` returns `null` on success; `text.set` too. Read back to know.

## Indices and ids

- Commands, `render --slide` and `file.export {slide}` count slides from 0; people count
  from 1. Convert once, at the boundary (`dk_edit.py` takes 1-based numbers).
- `file.export {"slides": [0, 2]}` is 0-based, but the **range string `"slides": "1-3"`
  is 1-based**, as in the app's dialog.
- `file.export {"all": true, "path": "x/slide.png"}` writes `slide1.png`, `slide2.png` …
  (1-based, no padding); `render --all DIR` writes `slide-01.png` ….
- **Shape ids are looked up on the current slide only.** `text.set {"id": 258}` on the
  wrong slide fails with `no such shape` and, in `run`, aborts the whole batch. `slide.go`
  first; take ids from `slide.inspect` in the same session.
- Slide ids (from `info`) are global: `slide.delete {"ids": [...]}` deletes several
  slides without the index shift that sequential `slide.delete {index}` calls cause.
- Placeholder types: the title slide's title is `ctrTitle` and its subtitle `subTitle`;
  other slides use `title`, and `obj` (Title and Content) or `body` for the text box.

## Export and conversion

- **Hidden slides are left out of PDF exports** (and `convert X.pdf`) unless
  `includeHidden: true`. A PDF with fewer pages than `info` has slides is usually this.
- `--export x.png` / `convert X x.png` write **one slide** (the current one / the first),
  not the deck.
- Notes pages and handouts default to US Letter portrait; pass `paper`.
- `convert X.md` writes the outline with tab-indented lines, not Markdown bullets.
- `.pptx` round trips keep titles, layouts, notes, pictures, tables and charts in
  0.11.1; check anything exotic (SmartArt, media, animations) with `info` and a render.

## Running it

- **One failing `--cmd` stops `run`; nothing is saved.** Fix the command and rerun the
  batch — partial output never appears.
- **`deckcraft-cli mcp` takes one `--automation-read-root` and one
  `--automation-write-root`**; a second one is an error (`--automation-read-root given
  twice`) and the server exits before answering. `dklib.Session` uses the common parent
  of the folders and refuses a parent as wide as `/` or `/Users`.
- Paths in commands should be absolute; `run` resolves relative ones against the
  current directory, MCP roots compare resolved paths (`/tmp` → `/private/tmp` on macOS).
- Do not run the app binary (`/Applications/DeckCraft.app/Contents/MacOS/DeckCraft`)
  to probe options — it opens the GUI. Everything headless goes through `deckcraft-cli`.
