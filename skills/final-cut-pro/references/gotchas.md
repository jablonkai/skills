# Gotchas — verified on Final Cut Pro 12.4 (FCPXML 1.14), macOS 27

| # | Behaviour | Handling |
|---|---|---|
| 1 | **Off-grid clip start.** When a clip's `start` isn't a whole number of *sequence* frames (typically a 29.97 clip in 25p, or a start relative to an off-grid timecode origin), FCP floors it and appends a **one-frame copy of the clip after the last item**. The project gets one frame longer, and no warning appears. | The builder snaps starts to the sequence grid in absolute source time. `fcpxml-verify.py` → `grid`. |
| 2 | **Transition without handles.** FCP drops it and shows "Encountered an unexpected value (…/transition[1])" in an *Import XML* warnings dialog. | The builder refuses and says which side lacks media. Verify → `handles`. |
| 3 | **Missing media: no warning.** The clip imports offline. | Build and verify check every `src`. |
| 4 | **Library chooser.** Without `<import-options><option key="library location" …>`, FCP opens "Open Library — Which library do you want to import X into?" and waits. The `location` attribute on `<library>` doesn't prevent it. | Build/edit with `--library`. `fcp-import.py --library` picks the row by name; otherwise it stops and says so. |
| 5 | **Same-named project, same-named event.** FCP imports into a temporary `<event> 2`, merges it into `<event>` in the background, and **silently keeps the old project**. The new one ends up in the library's `__Trash`. This happens even when the new project differs. | `fcp-import.py` refuses up front (`--allow-existing` to override). Rename the project (the editor's default is `<name> edited`). |
| 6 | **Connected storyline drift.** Children of `<spine lane=…>` count from 0. If the first child has offset 3s, FCP moves the storyline 3 s later and rewrites its `offset`, and it does this again on every round trip (3 → 6 → 9 s). | The reader uses 0-based storylines. Verify → `storyline`. |
| 7 | **`copy assets` defaults to copy.** Without the option, FCP copies media into `<library>/<event>/Original Media`, and exports then point there. | The builder writes `copy assets` = 0 unless `--copy-media`. |
| 8 | **Paths come back NFD and `/tmp`.** Exports write `U%CC%88` (decomposed Ü) and `/tmp/…` for `/private/tmp/…`. | `url_to_path` normalises to NFC. Existence checks try NFC and NFD. |
| 9 | **xmllint can't read the bundled DTD in place.** It fails with `xmlSAX2ResolveEntity` / "Could not parse DTD" because of the space in `Final Cut Pro.app`. | The DTD is copied to `$TMPDIR/fcp-skill-dtd/`. |
| 10 | **AppleScript is read-only and slow when FCP is in the background.** Every property read is an Apple event. With FCP paged out under memory pressure, each one took 8–20 s and `get` timed out (-1712). Two clients at once make it worse. | `list_projects` makes 7 bulk calls, with `FCP_AE_TIMEOUT` (default 180 s). Don't run two FCP queries in parallel. |
| 11 | **AppleScript names.** `st` is a reserved word (an ordinal suffix), and identifiers are case-insensitive, so `sT` fails too. `media time` records (`value`, `timescale`) need `using terms from application id "com.apple.FinalCut"` outside the `tell` block. | Handled in `fcpxml_common.LIST_SCRIPT`. |
| 12 | **Export XML scope.** It exports the browser selection: the library, an event, or a project. Right after an import the imported item is selected. Selecting a sidebar row through Accessibility does **not** enable the menu item. | Exporting is a manual step for the user. |
| 13 | **Keystrokes go to the frontmost app.** A save panel driven with ⌘⇧G and typed paths while another app had focus typed into that app instead. | Scripts press only buttons (`AXPress`/`click`) and set text fields' values. They never send keystrokes. |
| 14 | **Exports add noise.** `uid`, `sig`, base64 `<bookmark>`, `<metadata>`, title `<param>`s, `fontFace`, `audioRole="dialogue"`, smart collections, and an automatic Audio Crossfade in each transition. | The reader ignores them. The editor keeps them, and FCP re-imports them without trouble. |
| 15 | **Template names repeat.** 15 titles are called "Bug" (one per category). Basic Title and Basic Lower Third live in `PETemplates.localized`, not `Templates.localized`. | `find_template` accepts `Category/Name` and refuses ambiguous names. `fcp.sh --templates`. |
| 16 | **Timeline timecode ≠ time.** Primary-spine offsets start at `tcStart` (3600s for 01:00:00:00). At 29.97 DF, 01:00:00;00 is 107 892 frames = `107999892/30000s`, which FCP reports as its start time. | `fcptime.py` handles DF. The builder writes `tcStart` exactly. |
| 17 | **Speed changes** are written back normalised: half speed over an 8 s asset becomes `timept time="16s" value="8s"`. | The reader flags `retimed` and gives no source out. |
| 18 | **Transition length.** A cross dissolve is centred on the cut, so each half must be whole frames. | The builder rounds to an even frame count (1 s at 25p → 26 frames) and reports it. |

## Reading the warnings dialog

The *Import XML* window has an outline: row 1 is the file name, and the rows after it
are the warnings, each with the XPath of the element FCP rejected.
`fcp-import.py` collects them and presses OK, and any warning makes the run fail. To
look manually, run `bash scripts/fcp.sh --dialogs`.
