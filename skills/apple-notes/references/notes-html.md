# Notes HTML ↔ Markdown

What `body` returns and accepts on Notes 4.13. `scripts/notes_md.py` implements this mapping.

## Writing (Markdown → `body`)

| Markdown | HTML sent | Read back as |
|---|---|---|
| `# T` / `## T` / `### T` | `<div><h1>T</h1></div>` … | `<b><font face=".AppleSystemUIFontBold"><span style="font-size: 24px">` (18px for h2, no size for h3) |
| `#### T` and deeper | `<div><b>T</b></div>` | bold line (comes back as text) |
| `**b**` `*i*` `~~s~~` | `<b>` `<i>` `<strike>` | the same |
| `[text](https://x.org)` | `<a href>` | `<u><a href="https://x.org/">` (Notes may add a trailing slash) |
| `` `c` `` | `<tt>` | `<font face="Courier"><span style="font-size: 12px">` |
| fenced code | one `<div><tt>line</tt></div>` per line | Courier lines |
| `- x` / `1. x` / nested | `<ul>`/`<ol>`, nested inside `<li>` | nested list written as a **sibling** of its parent `<li>` |
| `- [ ] x` / `- [x] x` | `<li>☐ x</li>` / `<li>☑ x</li>` | the same glyphs (☐ wrapped in `<font face="AppleSymbols">`) |
| GFM table | `<div><table>…</table></div>` | `<div><object><table …style…>`: also counted as an attachment with no name |
| local `![](img.png)` | added with `make new attachment` after the body | a named attachment; `<img src="data:…">` in the body |
| blank line between blocks | `<div><br></div>` | the same |

Things Notes ignores or flattens: `class="checklist"`, `<input type=checkbox>`,
`<blockquote>`, `<pre>` (it becomes Courier lines), `<hr>`, and colours. **Two adjacent
lists merge into one** unless a block sits between them, which is why the converter
always puts a `<div><br></div>` between blocks.

## Reading (`body` → Markdown)

- Each top-level `<div>` is one line. `<div><br></div>` is a blank line.
- A line that is all bold in `.AppleSystemUIFontBold` is a heading: ≥ 22px gives `#`,
  ≥ 17px gives `##`, anything else `###`. So is an all-bold line with a size of ≥ 17px
  but no face, which is what a body rewrite leaves of a heading. Lines that are bold in
  the regular font at the normal size stay `**bold**` text.
- A line that is all Courier or `<tt>` is code, and consecutive code lines become one
  fenced block.
- Tables: the first row becomes the header row (Notes has no header concept).

## Images and attachments

There are three kinds:

1. **Legacy inline images**: `<img src="data:image/…;base64,…">` in the body, usually
   with a nameless attachment. The converter decodes them where they appear.
2. **File attachments** (pasted photos, PDFs, scans, attachments added by script): a
   `name` (sometimes without an extension) and saveable with `save`. The body may not
   contain them at all. The exporter saves each one, sniffs the type from its magic bytes,
   dedupes it against inline images by SHA-256, and links the rest under `## Attachments`.
3. **Images inserted through `body` as data URIs**: they show in Notes, but they
   become nameless attachments that are **not** in the body and can't be saved. The
   exporter counts them in `attachments_not_exportable`. That's why `nt-write.py` adds
   images with `make new attachment` instead.
