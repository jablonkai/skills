# Gotchas

| # | Symptom | Cause | Fix |
|---|---|---|---|
| 1 | Installed template isn't in FCP's Titles browser | FCP scans Motion Templates **at launch**; a running FCP never shows a new one | Relaunch FCP (ask first), then `motn-fcp-browser.sh NAME` |
| 2 | Template still missing after relaunch | It sits directly in `Titles.localized/`, or the folder and file names differ | `<Kind>.localized/<Category>/<Name>/<Name>.ext`, which is what `motn-install.py` writes |
| 3 | Title imported from FCPXML shows Helvetica, white, wrong size | FCPXML `text-style` (even an empty `<text-style/>`) overrides the template styling | Plain `<text>…</text>` without text-style; the final-cut-pro builder does this for a `{"name","uid"}` template without font/size/color |
| 4 | FCPXML import reports no warning, but the title is wrong or empty | FCP silently accepts an unknown effect uid | `motn-install.py --in-library LIB` lists the templates FCP resolved (from the library's Effects.map); a bad uid never appears there |
| 5 | A colour edit vanishes when the editor picks a ColorWay option (or a checkbox hides the plate) | A rig widget stores per-option values (snapshots) that override the channel | `motn-edit` also writes the current option's snapshot; `motn-read.py` lists `rigged`; `--unrig` drops the rig |
| 6 | Render shows Helvetica | Font not installed: Motion substitutes without a word | `motn-edit` refuses missing fonts; `--fonts FRAGMENT` finds the PostScript name. FCP/Motion's private fonts (Proxima Nova, Avenir LT Com…) count as available |
| 7 | Colours sample darker in the render (#1A1A1A → 24, not 26) | The template holds sRGB; the render is Rec. 709 with gamma 1.961 | `motn-render --expect` converts; compare against `expected_rgb`, not the hex |
| 8 | `Unable to submit to queue`, `Failed: 2x job controller down`, or a batch stuck in `Waiting` | Transient Compressor queue hiccups | `motn-render` retries the submit 3×, re-renders once on "controller down", and cancels at `--timeout`; if it persists, quit and reopen Compressor |
| 9 | Grey square with an arrow in the render | The drop-zone placeholder: FCP shows the clip underneath there | Normal for titles/effects; sample colours elsewhere |
| 10 | Text cut short, or extra characters unstyled | `styleRun` length didn't match the new text | Change text only with `motn-edit --text` (counts UTF-16 units) |
| 11 | Motion refuses the file | Not well-formed, or the header/DOCTYPE went missing | All scripts write through ElementTree with the header and re-parse after saving |
| 12 | Many templates share a name ("Lower Third", "Bug") | Stock categories repeat names | `motn-find.py --copy "Category/Name"` |
| 13 | After hand-editing in Motion, ids and layer order changed | Motion renumbers on save | Re-run `motn-read.py` before scripting further edits |
| 14 | `motn-fcp-browser.sh` exits 2 | FCP not running, no library open, or Accessibility denied for the terminal | System Settings ▸ Privacy & Security ▸ Accessibility |
| 15 | The backplate covers only the first line | `Lower Third Text & Subhead` sizes its plate to the headline, and a rig keeps it there | Seed with `Lower Thirds/Information Bar` (one bar behind both lines); don't try to move the rigged plate |
| 16 | Plate colour samples darker than expected (20 instead of 25 for #1A1A1A) | The layer is semi-transparent: Information Bar's bar is at 65 % | `motn-read` prints `opacity` under Shapes; `--opacity LAYER=1` |
