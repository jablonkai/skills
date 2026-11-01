# Formats (CADCraft 0.16.0)

| Format | Read | Write | Notes |
|---|---|---|---|
| DXF | yes | yes | Writes ASCII R2018 (AC1032). A file that declares no units (`$INSUNITS` 0) stays unitless when saved — set `units {insunits}` if the job needs mm. `saveas {version: 2000…2018, binary?}` for older or binary DXF. |
| DWG | yes | yes | Writes R2018 (`file`: "AutoCAD 2018/2019/2020"). Via `convert`, `--save x.dwg` or `save`. |
| DWT | as template | yes | `new {template}`; `convert`/`--save x.dwt` writes one |
| PDF | — | yes | One page, white; since 0.13.0 written by krilla with a `/PageLabel` (`Model`) object — count pages with `pdfinfo` or `cc_verify.py files --pdf-pages`, not a bare `/Type /Page` grep. `convert`/`--export`: landscape A4 (metric) or Letter (imperial), fit to framing. `exportpdf`/`plot`: paper, scale, layouts. `publish`: one file per sheet. |
| SVG | yes (also .svgz) | yes | Import gives polylines (one test drawing: 505 Polyline); export is model space, framing as PNG. Parses as XML. |
| PNG | — | yes | 2400×1600 RGBA via CLI; `render` 1600×1000 default; dark background. |
| CSV | — | yes | `tableexport`, `eattext`/`dataextraction` return rows. |

- `info` `skipped` lists DXF sections it didn't read — report it when non-empty.
- `open` returns `warnings` for anything lost on read; report them.
- The output format is always picked by extension.
