# Scene collections

A scene collection is one JSON file per collection in OBS's config directory:

| OS | Directory |
|---|---|
| macOS | `~/Library/Application Support/obs-studio/basic/scenes/` |
| Windows | `%APPDATA%\obs-studio\basic\scenes\` |
| Linux | `~/.config/obs-studio/basic/scenes/` |

`<name>.json` holds every scene, input, filter and scene item. OBS keeps a `.bak` next to it.
Its `name` field is what OBS displays — the filename does not have to match.

## Two routes, one spec

[scripts/obs_collection.py](../scripts/obs_collection.py) takes a compact **spec** and produces
the same scenes either way:

| OBS state | Route | Commands |
|---|---|---|
| running (the usual case) | **live** — build through obs-websocket | `obs_collection.py apply spec.json` (into the open collection) or `… apply spec.json --new-collection` (create/switch to one named after the spec) |
| closed, or a file is the deliverable | **file** — write the collection JSON | `obs_collection.py build spec.json out.json` → `validate out.json` → `install out.json` → `obs-start.sh --collection "<name>"` |

Why two: OBS reads the list of collection files only at startup, and it rewrites the open
collection's file from memory on every change and on exit. A file installed while OBS runs is
invisible (`SetCurrentSceneCollection` → 600), and an edit to the open one is lost. `install`
therefore refuses while OBS is reachable. Only the user should quit OBS — ask.

When the request is "make me a collection" and OBS runs, use `--new-collection`: switching
collections saves the current one first and is undone with one `SetCurrentSceneCollection`, so
it costs the user nothing — building into the open collection instead mixes the new scenes into
their show. Without `--new-collection`, `apply` is for "add these scenes to what I have".

`apply` is re-runnable: scenes and inputs are created or updated, items are re-positioned and
re-stacked, filters updated. It never removes anything that is not in the spec, except the
empty default scene of a collection it just created.

## Spec format

```json
{
  "name": "Stream",
  "current_scene": "Starting Soon",
  "scenes": [
    {"name": "Starting Soon", "items": [
      {"source": "Stream · BG", "kind": "color_source_v3",
       "settings": {"color": "#0b1f3a", "width": 1920, "height": 1080}},
      {"source": "Stream · Soon", "kind": "text_ft2_source_v2", "pos": [960, 540], "align": 0,
       "settings": {"text": "Starting soon", "font": {"face": "Helvetica", "size": 96, "style": "Bold", "flags": 1},
                    "color1": "#ffffff", "color2": "#ffffff"}}
    ]},
    {"name": "Main", "items": [
      {"source": "Stream · BG"},
      {"source": "Stream · Cam", "kind": "macos-avcapture", "pos": [1880, 1040], "align": 10,
       "scale": [0.5, 0.5],
       "filters": [{"name": "Tone", "kind": "color_filter_v2", "settings": {"saturation": 0.1}}]}
    ]},
    {"name": "BRB", "items": [{"source": "Starting Soon", "scale": [0.5, 0.5]}]}
  ]
}
```

- `items` are listed **bottom to top**, like the file format and `GetSceneItemList`.
- An item whose `source` is another scene's name nests that scene. An item without `kind`
  reuses an input defined earlier in the spec (the same input in several scenes — one set of
  settings, one filter chain). Defining the same name twice with different kinds is an error.
- Position belongs to the *item*, not the input: an input reused in another scene starts at
  `[0, 0]` there unless that item has its own `pos`/`align`/`scale`.
- Item fields: `pos [x, y]` (canvas pixels of the anchor), `align` (bitmask, default 5 =
  top-left), `scale [x, y]`, `rot`, `visible`, `locked` (file route only), `filters`.
- Any string starting with `#` under a key containing `color` becomes OBS's ABGR integer.
- Kinds and settings keys are platform-specific — check them with `GetInputKindList` and
  `GetInputDefaultSettings` against the target OBS ([api-reference.md](api-reference.md#input-kinds-and-their-settings)).
  A text kind that does not exist on the machine makes the whole `apply` fail with 604.

## File format notes (for reading or hand-editing)

Top level: `name`, `sources` (inputs *and* scenes, each with `name`, `uuid`, `id` — unversioned
kind — `versioned_id`, `settings`, `filters`, audio fields), `scene_order [{name}]` (Scenes dock
order, top first), `current_scene`, `current_program_scene`, `transitions`,
`current_transition`, `groups`, `modules`, `version`. OBS 32 adds `canvases` and a
`canvas_uuid` per scene. Audio device inputs set in Settings ▸ Audio are top-level keys
(`AuxAudioDevice1`, `DesktopAudioDevice1`), not entries of `sources`.

A scene's `settings.items[]` entry references its source by `name` **and** `source_uuid` (both
must agree) and stores `pos`, `scale`, `rot`, `align`, `bounds_type`, `bounds`, `crop_*`,
`visible`, `locked`, and a per-scene unique `id`. OBS 31+ also writes `pos_rel`/`scale_rel`/
`scale_ref` (canvas-relative); `build` omits them and OBS derives them from `pos`/`scale` on load.

`obs_collection.py dump NAME` prints a readable summary of any collection on disk;
`validate` checks the cross-references above before anything is installed.
