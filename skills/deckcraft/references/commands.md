# Command ids by task (pinned to 0.12.0)

The registry has 330 commands. These are the ones the common tasks need; for anything
else, `scripts/dk_commands.py WORD…` or `deckcraft-cli describe ID`. Indices are
0-based. Unknown parameters are **ignored, not rejected** — copy names from here or from
`describe`.

## Presentation

| Id | Params | Notes |
|---|---|---|
| `file.new` | `{theme?, template?, size?: [w,h] pt, blank?}` | Always one starter slide (title layout). |
| `file.templates` | → `[{name, summary, theme, slides}]` | Starter templates for `file.new {template}`. |
| `file.open` | `{path}` | `.deckcraft` or `.pptx`. |
| `file.saveAs` | `{path, format?: deckcraft\|pptx}` | Format from the extension. |
| `file.export` | see [cli.md](cli.md#fileexport-options-also---export-params-mcp-export) | |
| `file.info` | → `{title, path, format, slides, hiddenSlides, sections, properties}` | |
| `file.properties` | `{title?, subject?, author?, keywords?, comments?, category?, company?}` | |
| `design.themes` | → `{themes: [{name, colors, major, minor}], colorSchemes, fontSchemes, effectSchemes}` | Themes: DeckCraft, Harbor, Ember, Meadow, Nocturne, Paper, Coral Reef, Slate. |
| `design.theme` | `{name}` | Unknown name: silently nothing. |
| `design.colors` / `design.fonts` / `design.variant` | `{name}` · `{colors:{accent1…}}` / `{name}` · `{major, minor}` / `{index: 0..3}` | |
| `design.slideSize` | `{preset: widescreen\|standard…, scale?: maximize\|ensureFit\|none}` or `{w, h}` | |
| `design.background` | `{color? \| gradient? \| picture?: base64 \| style?: 1..12, all?, index?}` | |
| `design.headerFooter` | `{slideNumber?, footer?, footerText?, date?, dateText?, hideOnTitle?, all?}` | |
| `design.browseTheme` | `{path}` | Apply a .pptx/.potx master or .thmx theme. |

## Slides

| Id | Params | Notes |
|---|---|---|
| `slide.new` | `{layout?, title?, body?, at?}` | Layout kinds: `title`, `titleAndContent`, `sectionHeader`, `twoContent`, `comparison`, `titleOnly`, `blank`, `contentWithCaption`, `pictureWithCaption` (or a layout name). Without `at`, inserts after the current slide. `body`: `\n` new paragraph, leading `\t` = level. |
| `slide.fromOutline` | `{text, markdown?}` | Every heading → Title and Content; inserted after the current slide. |
| `slide.delete` | `{index?}` or `{ids: [slide id]}` | Ids (from `info`) delete several at once without index shifting. |
| `slide.move` | `{from?, to}` | `to` is the final index. |
| `slide.duplicate` | `{index?}` | |
| `slide.go` | `{index}` or `{id}` | Makes a slide current: shape commands act there. |
| `slide.layout` | `{layout, index?}` | |
| `slide.hide` | `{index?, hidden?}` | Hidden slides leave PDFs unless `includeHidden`. |
| `slide.notes` | `{text, index?}` or `{body, index?}` | Plain text; `body` is `slide.inspect`'s `notesBody`. |
| `slide.rename` | `{name, index?}` | |
| `slide.reuseList` / `slide.reuse` | `{path}` / `{path, slides?: [index], keepFormatting?, at?}` | Bring slides in from another deck. |
| `slide.inspect` | `{index?}` → shapes `[{id, kind, name, placeholder?, box, text?, …}]`, notes, notesBody, layout, transition | Placeholder types: `ctrTitle`/`title`, `subTitle`, `body`, `obj`, `pic`, `dt`, `ftr`, `sldNum`. |
| `section.add` / `section.rename` / `section.remove` | `{name?, at?}` / `{index, name}` / `{index, slides?}` | |

## Text

| Id | Params | Notes |
|---|---|---|
| `text.set` | `{id?, text, cell?: [r,c]}` | Whole text of a shape (current slide) or table cell; keeps the first run's formatting. |
| `text.get` | `{id?}` → `{text, paragraphs}` | |
| `text.find` | `{text, matchCase?, wholeWords?}` → `[{slide, shape, para, start, end}]` | Whole deck, notes too (`shape: null`). |
| `text.replace` | `{text, with, matchCase?, wholeWords?, at?}` → `{replaced}` | All matches in the deck unless `at`. |
| `format.size` / `format.bold` / `format.font` / `format.color` | `{size}` / `{on?}` / `{family}` / `{color: #RRGGBB\|accent1…}` | Act on the selection: `edit.select {ids}` first. |
| `format.fontDialog` | `{family?, size?, bold?, italic?, underline?, color?, caps?…}` | Several at once. |

## Pictures, shapes, tables, charts

| Id | Params | Notes |
|---|---|---|
| `insert.picture` | `{path \| data, name?, rect?}` | Always a free picture (never fills a placeholder). Without `rect`, centred at natural size. |
| `picture.change` | `{path \| data, ids?}` | Swap the image, keep box and formatting. |
| `picture.crop` / `picture.adjust` | `{left?, top?, right?, bottom?: 0..1, ids?}` / `{brightness?, contrast?, …}` | |
| `shape.insert` | `{preset, rect, text?}` | Presets: `shape.presets`. |
| `insert.textBox` | `{rect?, text?}` | |
| `insert.table` | `{rows, cols, rect?}` then `text.set {cell: [r,c], text}` | `table.style {style}`, `table.options {headerRow…}`. |
| `insert.chart` | `{type, rect?, categories, series: [{name, values}]}` | Shows a literal "Chart Title" until `chart.options {title}` (or `title: null`). |
| `edit.select` / `edit.delete` | `{ids}` / `{ids?}` | |
| `edit.undo` | | |

## Motion and show

| Id | Params |
|---|---|
| `transition.set` | `{kind: fade\|push\|wipe\|morph\|…, option?, duration?: ms, index?}` (`transition.list`) |
| `transition.applyAll` | |
| `animation.add` | `{effect, class?, start?: onClick\|withPrevious\|afterPrevious, duration?, delay?, ids?}` |
| `show.setup` / `show.customShow` | `{type?, loop?, from?, to?}` / `{name, slides}` |
