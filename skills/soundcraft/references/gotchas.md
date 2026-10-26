# SoundCraft gotchas (0.13.1)

Each item was reproduced against soundcraft-cli 0.13.1.

## Time and units

- **Command params are samples; `--start/--end` flags are seconds.** `run --start 48000
  --end 144000` asks for 13–40 hours and fails with "bounces are limited to 4 hours".
  `--start 1s` fails with "cannot parse position". Use `--start 1.5` or `0:01.500`.
- Position params (`at`, `start`, `end`) also accept `"m:ss.fff"` strings, but fade
  `length` must be a positive sample count.
- `sc_session.py` takes seconds / `m:ss.fff` everywhere and converts with the session rate.

## Files and overwrites

- `session.new` has no `path`: a `path` key is silently ignored and the session lives in
  memory until `--save`.
- `--save` replaces an existing file, including the `--in` session, with no prompt. It
  keeps the previous version as `Backups/<name> backup N.scraft` beside the session, so
  a mistaken overwrite can be undone from there.
- `convert IN IN` overwrites the source in place. `sc_convert.sh` refuses OUT == IN.
- Saving copies imported audio to `Audio Files/` beside the `.scraft`
  (`audio_files_written` counts them). A second session in the same folder that imports
  a different `v.wav` gets `v_01.wav`; the first session's file is left alone.
- Saving to another folder copies the audio again, so a saved copy is self-contained.

## Errors and silence

- Unknown **top-level** param keys are ignored (`mix.volume {"db":-3,"bogus":1}` succeeds).
  Unknown plugin params, unknown tracks and malformed ids are errors. Check results
  with a read-back, not just the exit code.
- A script aborts at the first failing line (`FILE:LINE: ID: …`) and saves nothing.
- `mix.*`/`automation.*`/`clip.*` without `track`/`tracks`/`clips` act on the
  selection; in a fresh CLI session nothing is selected, so they fail with
  "nothing is selected". `describe` shows `enabled: false` for the same reason; that is
  not a missing feature.
- Clip ids are plain integers (`"clip": "m"` → "clip must be an id"). Track, clip and
  source ids share one counter, so a clip id is not predictable before the import.

## Mixing

- **No sidechain.** The compressor exposes `sc_hpf_on`/`sc_hpf_freq` but there is no
  key-input routing command; it always detects on its own input. Duck with volume
  automation.
- **A volume automation lane wins over the fader.** After `duck`, `mix.volume` changes
  nothing in the bounce; change the breakpoints, or set `volume_db` in the spec before
  the duck is written.
- `automation.write_range` makes hard 1-sample steps (audible clicks on a music bed);
  `automation.set_point` pairs with a ramp sound smoother. `duck` uses `set_point`.
- **Stereo pan moves only the left knob.** Stereo tracks have two pans (`[-1.0, 1.0]`);
  `mix.pan {"pan": 0.3}` without `index` sets index 0 only, giving `[0.3, 1.0]`, a
  narrowed image rather than a move. Send index 0 and 1. `index: 1` on a mono track is
  silently ignored. `sc_session.py`'s `pan` handles both cases.
- `mix.insert` without `slot` takes the next free slot, so on a track that already has
  inserts the new ones go after them. Read `sc_inspect.py session` first if the order
  matters, and use `slot`/`mix.insert_move` to reorder.

## Read-back

- `info S.scraft` is text and lists only files, tracks, clips and markers.
  For mixer state use `session.inspect` (`sc_inspect.py session` or `--inspect`).
- Bounce results already report `peak_db`, `true_peak_db` and integrated `lufs`;
  `info` on a WAV does not report levels, so `sc_verify.py` measures them from samples.
- `engine.plugins` ignores any filter and returns every plugin (~30 KB);
  `sc_inspect.py plugin ID` prints one.
- `soundcraft-cli` subcommands have no `--help` (`run --help` → "unknown option").
