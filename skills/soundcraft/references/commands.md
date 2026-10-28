# Pinned command ids (SoundCraft 0.14.0)

The ids the recipes rely on, with their `describe` signatures as of 0.14.0. For anything
else: `python3 scripts/sc_inspect.py commands <words>` or `soundcraft-cli describe ID`.
Positions are samples unless noted; `track`/`tracks` take names or ids.

## Session and files

| Id | Params |
|---|---|
| `session.new` | `{name?: 'Untitled', sample_rate?: 48000, bit_depth?: 24, template?: blank\|demo}`; no `path` |
| `session.open` | `{path}` |
| `session.save` / `session.save_as` | `{path?, replace?: false}` / `{path, replace?: false}` |
| `session.inspect` | `{detail?: summary\|full}` |
| `track.inspect` / `clip.inspect` | `{track}` / `{clip}` |
| `file.import_audio` | `{path \| paths: [..], track?, at?, new_tracks?: true}`; `new_tracks:false` + `track` places on an existing track |
| `file.bounce_mix` | `{path, format?: wav\|aiff\|flac, bit_depth?: 16\|24\|32f, start?, end?, source?: main\|bus name, normalize?: false, dither?: true, fold_down?: stereo}` |
| `file.bounce_stems` | `{dir, format?, bit_depth?, start?, end?, dither?: true, fold_down?}` |
| `file.export_session_text` | session info as text |

## Tracks

| Id | Params |
|---|---|
| `track.new` | `{count?: 1, format?: mono\|stereo\|5.1…, kind?: audio\|aux\|master\|midi\|instrument\|vca\|folder, name?, timebase?, instrument?}` |
| `track.rename` | `{track, name}` |
| `track.delete` | `{tracks?}` |
| `track.duplicate`, `track.move`, `track.color`, `track.bounce` | see `describe` |

## Clips and editing

| Id | Params |
|---|---|
| `edit.select` | `{tracks?, start?, end?, clips?: [id], sources?, exact?}` |
| `edit.fades_create` | `{clip: id, side: in\|out, length: samples, shape?: linear\|equal power\|s-curve\|exponential\|logarithmic, curvature?: -1..1}` or the selection form `{shape?, tracks?, start?, end?}` |
| `edit.fades_delete` | `{tracks?, start?, end?}` |
| `clip.gain` | `{clips?, db \| delta_db}` |
| `edit.move_clips` | `{clips?, by?: samples, to?: position, track?}` |
| `edit.trim_clip`, `edit.separate`, `edit.strip_silence`, `edit.consolidate` | see `describe` |
| `audiosuite.process` | `{process: plugin id \| normalize \| reverse \| gain \| time_stretch \| pitch_shift \| …, params?, clips?, tracks?, start?, end?}` renders into the clip |
| `markers.add` | see `describe` |

## Mixer and plugins

| Id | Params |
|---|---|
| `mix.volume` | `{tracks?, db: -144..12 \| delta_db}` |
| `mix.pan` | `{tracks?, pan: -1..1, index?: 0\|1}`; stereo tracks have two pans (L, R) and no `index` means index 0 only |
| `mix.mute` / `mix.solo` | `{tracks?, value?: bool}` |
| `mix.insert` | `{track?, slot?: 0..9 \| a..j, plugin: id, params?: {id: value}}`; without `slot` it takes the next free one |
| `mix.insert_param` / `mix.insert_params` | `{track?, slot, param, value}` / `{track?, slot, params: {…}, preset?}` |
| `mix.insert_bypass` / `mix.insert_remove` / `mix.insert_move` | `{track?, slot, value?}` / `{track?, slot}` / see `describe` |
| `mix.new_bus` | `{name, format?: stereo}` |
| `mix.send` / `mix.send_level` | `{track?, slot?, bus: name, level_db?: 0, pre_fader?: false}` / `{track?, slot, db?, pan?, mute?, pre_fader?}` |

## Automation

| Id | Params |
|---|---|
| `automation.set_point` | `{track?, param: volume\|pan\|mute\|send_a_level\|plugin:a:<param id>, at, value, from?}` |
| `automation.write_range` | `{track?, param, start?, end?, value}`; steps with 1-sample edges |
| `automation.clear`, `automation.thin` | see `describe` |

Volume automation values are fader dB, and a lane overrides `mix.volume` during playback
and bounce.

## Introspection

`engine.plugins` (all plugins with params; ignores filters, ~30 KB), `engine.commands`,
`engine.history`, `session.audio_health`, `session.format_time {at, format?}`.

## Built-in plugins

`eq_1band eq_7band compressor expander_gate de_esser maximizer channel_strip room_reverb
plate_reverb mod_delay auto_pan chorus flanger phaser ring_mod saturator lofi rectifier
subharmonic pitch_shifter time_shift gain trim invert dc_offset_removal signal_generator
dither` and the instruments `subtractive_synth drum_synth sampler`. Parameter ids, ranges
and choice indexes: `sc_inspect.py plugin ID`. Choice params take the index (e.g.
`eq_1band` `type` 3 = High Pass).
