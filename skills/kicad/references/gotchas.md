# KiCad 10 gotchas (measured on 10.0.6, macOS)

## kicad-cli

| Trap | What happens | Handling |
|------|--------------|----------|
| Localised output | Console text **and** JSON `description` fields follow the KiCad UI language (`system.language` in `kicad_common.json`, "Default" = macOS language). `LANG`/`LC_ALL`/`LANGUAGE` change nothing. | Run with `KICAD_CONFIG_HOME` pointing at a temp copy of the user config with `"language": "English"` (what `kicad.py` does). Only `type` keys (`clearance`, `courtyards_overlap`…) are stable across languages. |
| Partial config | A temp `KICAD_CONFIG_HOME` holding only `kicad_common.json` adds 17 `lib_footprint_issues` (no `fp-lib-table`). | Copy the whole `~/Library/Preferences/kicad/10.0/` directory (≈ 120 KB), then change the language. |
| DRC exit codes | `--exit-code-violations` → 5 when violations exist; missing file → 3; success → 0. | `kicad.py drc` maps to 0/2/3. |
| ERC exit code | `sch erc` exits **0** even with 51 violations. | Read the JSON. |
| ERC JSON coordinates | `pos` values are **1/100** of `coordinate_units` (J1 at 24.92, 100 mm reported as 0.2492, 1.0; the same in `in` and `mils`). The `--format report` text is right. DRC JSON is right. | `kicad.py erc` compares against a text report and rescales (`pos_scale_applied: 100` in the JSON). |
| DRC JSON layout | `violations`, `unconnected_items`, `schematic_parity` are separate arrays. | Report unconnected items separately; they are often the most important errors. |
| Side files | `pcb drc` on a bare `.kicad_pcb` creates `.kicad_pro`/`.kicad_prl` next to it. The board file is not changed. | Expected; don't treat as a modification. |
| Gerbers without `-l` | Plots all ~20 layers including User.*, Fab, Courtyard, Margin. | Always pass an explicit list. |
| Bad layer name | `-l F.Cu,nonsense` prints "Invalid layer name" and **exits 0**, silently dropping it. | `kicad.py` treats that line as a failure. |
| BOM ranges | `sch export bom` writes `D1-D8` by default. | `--ref-range-delimiter ''` gives `D1,D2,…`. |
| Position file Y | `pos` CSV Y is negated (math Y-up: board Y=108 → `-108`). | Fine for fab houses (JLCPCB expects KiCad's sign). Don't "fix" it. |
| HPGL | `pcb export hpgl` is gone in 10.0. | Use PDF/SVG. |
| Fontconfig noise | Every call prints a Fontconfig cache warning on stderr. | Filtered by `kicad.py`. |

## IPC API

- **Off by default** (`api.enable_server: false`). The user enables it in Preferences ›
  Plugins. The socket is `/tmp/kicad/api.sock` (nng IPC, not TCP).
- **GUI only.** There is no headless IPC mode in 10.x; `kicad-cli` doesn't serve it.
- **One socket owner.** The first KiCad process to bind the socket owns it. If the
  project manager owns it, board requests fail with "no handler available" until a
  board is open in a PCB editor that process manages.
- **"KiCad is not ready to reply"** for a few seconds after the socket appears, while
  the board loads. `kicad_ipc.py` retries for up to 20 s.
- **Stale socket hangs clients.** After KiCad is killed, `/tmp/kicad/api.sock` stays and
  a kipy call can block far past `timeout_ms`. `kicad_ipc.py` enforces an overall
  `--timeout` (60 s). Restarting KiCad recreates the socket.
- **Gatekeeper:** the first launch of `pcbnew.app` (the standalone PCB Editor) can show
  macOS's "opening for the first time" prompt, which blocks the API until the user clicks Open.
- **Socket permissions:** `/tmp/kicad/api.sock` is created `srwxr-xr-x` by the user, so
  only that user's processes can connect.
- **Undo:** one `begin_commit`/`push_commit` is one Cmd+Z (verified with 8 footprints).
  Title-block changes via `set_title_block_info` are not undoable.
- **Units are nanometres.** `Vector2.from_xy_mm()` / `.x / 1e6`. Angles are `Angle.from_degrees()`.
- **Setting `fp.position` moves children client-side.** kipy's setter shifts pads,
  fields and graphics by the delta before `update_items()`. Editing the proto directly
  leaves them behind.
- **Edits aren't saved** until `board.save()`. Unsaved edits are lost if KiCad closes.
- **External clients send an empty token.** `KICAD_API_TOKEN` is only set for plugins
  KiCad launches itself, so an outside script is not authenticated by a token.

## Security posture

- `kicad.py` only reads the board/schematic it is given and writes the reports, exports
  and renders the user asked for. It never changes the user's KiCad config. The English
  locale uses a temp copy that is deleted on exit.
- **Enabling the KiCad API lets any local process running as the user drive the open
  editor** (the socket is user-only, `srwxr-xr-x`), including saving files. There is no per-client authentication for external
  scripts. The socket is local-only (no network or browser reachability, so no
  cross-origin surface). Advise switching the API off when the session ends.
- `kicad_ipc.py` adds no server or port of its own. Stop path: each command is one
  commit (single Cmd+Z undoes it), nothing is saved without `--save`, `--dry-run`
  previews, and every request has `--timeout-ms` (default 5000).
- Every `kicad-cli` call runs in its own process group with `--timeout` (default 600 s).
  A timeout or Ctrl-C kills the group.
