---
name: soundcraft
description: 'Automate SoundCraft, the Pro Tools-style DAW and audio editor, headless with soundcraft-cli: build multitrack sessions from a spec (import clips, place them, fades, clip gain, pan, volume and automation, music ducked under a voice-over), add built-in plugins (EQ, compressor, de-esser, reverb, delay, maximizer...) with exact parameters, edit existing .scraft sessions, bounce the mix or a time range to WAV/AIFF/FLAC at a set bit depth, convert or normalize audio files and folders with dither, and verify every result by reading the session and the bounce back. Use when the user mentions SoundCraft, soundcraft-cli or a .scraft file, or wants a podcast or voice-over mix, a ducked music bed, a bounce or a sample-rate/bit-depth conversion done with SoundCraft. Not for synthesis or live-coded music (supercollider, sonic-pi), beat or onset analysis, video timelines (davinci-resolve, final-cut-pro), or a plain ffmpeg/sox conversion with no SoundCraft involved.'
summary: "automate SoundCraft headless with soundcraft-cli — multitrack sessions from a spec with clips, fades, clip gain, pan, volume automation and ducking, built-in EQ, dynamics and reverb inserts, range or full bounces, batch conversion with normalize and dither, inspect read-back verified"
category: audio
compatibility: "Built for SoundCraft 0.14.0 and soundcraft-cli 0.14.0 on macOS 27 (arm64); pre-1.0, so command ids may change. Scripts need Python 3.9+ (standard library only)."
risk: medium
tags: [soundcraft, daw, audio-editing, mixing, bounce, podcast, voice-over, headless]
metadata:
  version: "1.1.1"
  author: "Tamás Jablonkai"
---

# SoundCraft via soundcraft-cli

SoundCraft is a Pro Tools-style DAW. Every menu item and mixer control is a command in one
engine registry (482 in 0.14.0): `session.*`, `file.*`, `track.*`, `edit.*`, `clip.*`,
`mix.*`, `automation.*`. The CLI runs those commands headless against a `.scraft`
session, with no window or audio device, and the same registry drives the running app.
Verified against **SoundCraft 0.14.0** and **soundcraft-cli 0.14.0** on macOS. The
software is pre-1.0: when a pinned id or param fails, look it up with `describe`.

```sh
command -v soundcraft-cli || ls ~/.local/bin/soundcraft-cli
soundcraft-cli --version
```

## Pick the route

| Task | Route |
|---|---|
| Build a session (tracks, clips, fades, gain, pan, inserts, ducking) and bounce it | `scripts/sc_session.py spec.json` |
| Edit an existing `.scraft` (add plugins, fades, automation) and bounce all or a range | `sc_session.py` with `"open"` |
| One-off commands on a session | `soundcraft-cli run --in S.scraft --cmd ID=JSON … --save OUT.scraft` |
| A long hand-written command list | `soundcraft-cli script FILE --in S --save S2 --bounce OUT` |
| Convert one file (rate, depth, normalize, dither) | `soundcraft-cli convert IN OUT …` |
| Convert a folder | `scripts/sc_convert.sh IN_DIR OUT_DIR …` |
| The user wants to watch it happen in the app | `soundcraft-cli app` ([live-app.md](references/live-app.md)) |

Headless is the default. Don't launch the app to read help: `soundcraft-cli commands`,
`describe ID` and `sc_inspect.py` cover it.

## Scripts

Call them as `python3 $S/<script>` (or `bash $S/sc_convert.sh`) with `S=<this skill>/scripts`.

- **`sc_session.py SPEC.json [--dry-run] [--overwrite]`** builds (`"new"`) or edits
  (`"open"`) a session from a spec: tracks with files placed `at` a time, `fade_in`/
  `fade_out` (+`fade_shape`), clip `gain_db`, `volume_db`, `pan`, `inserts` with params,
  automation points, `duck` (dip this track under another track's clips), raw `commands`,
  then `save` and an optional `bounce` (`path`, `bit_depth`, `format`, `start`/`end`).
  Times are seconds or `"m:ss.fff"`; the script converts them to samples. It prints a JSON
  summary read back from the saved session plus the bounce's rate, format, peak and LUFS.
  It refuses to overwrite the opened session, an existing save or an existing bounce
  without `--overwrite`. `--dry-run` prints the command scripts it would run. Full spec:
  the docstring, and [recipes.md](references/recipes.md).
- **`sc_inspect.py`**
  - `session FILE`: tracks, inserts with changed params, sends, automation, clips with
    ids, times, gain and fades. Run it before editing any session you didn't just build.
  - `commands WORD...`: matching registry ids with their params signature.
  - `plugin [ID...]`: the built-in plugins, or one plugin's parameter ids, ranges,
    defaults and choice indexes.
- **`sc_verify.py`** prints JSON and exits 1 on any failed check:
  - `audio FILE --rate 48000 --depth 24 --seconds 10 --max-peak -1 --level 4:8`
    (`--level` reports peak/RMS in a window: use it to prove a duck or a fade is audible)
  - `session FILE --tracks 2 --inserts Voice=eq_7band,compressor --automation Music=volume --fades Music`
  - `hash DIR [--compare manifest.json]`
- **`sc_convert.sh IN OUT [--ext flac] [--overwrite] [convert flags]`**: every
  wav/aiff/flac in IN to OUT, with an `info` read-back per file. It refuses OUT == IN.

## Workflow

1. **Inspect first**: `sc_inspect.py session` on any session you were given,
   `soundcraft-cli info` on input audio (rate, channels, length), and
   `sc_inspect.py commands`/`plugin` for any id or plugin param you haven't used yet.
   Unknown plugin params and track names are errors, which is good; guessed command
   params are not always.
2. **Keep the originals.** Save to a new `.scraft` path and convert into a new folder
   unless the user asked for in-place. Snapshot input folders with `sc_verify.py hash`.
3. **Do the work** with the route from the table. Use absolute paths in command JSON.
4. **Read back**: `sc_verify.py session` for tracks, inserts, automation and fades;
   `sc_verify.py audio` for the bounce's rate, depth, duration and peak, and `--level`
   windows for anything that should be audible (ducking, fades, a muted track).
5. **Report** the output paths, the verified numbers (rate/depth/duration/peak/LUFS) and
   anything you couldn't do (for example sidechain ducking, see below).

## The traps that cost the most (details in [gotchas.md](references/gotchas.md))

- **Two time units.** Command params (`at`, `start`, `end`, `length`, `by`) are
  **samples** (strings like `"0:05.000"` also work, except fade `length`), but the
  CLI flags `run/script --start/--end` are **seconds** or `m:ss.fff`. `--start 48000`
  means 13 hours and fails with "bounces are limited to 4 hours".
- **`--save` equal to `--in` is refused** (0.14.0) unless `--in-place` is passed; any other
  existing `--save` file is replaced, and `convert` overwrites its output, even when that is
  the input. Choose new paths.
- **`session.new` ignores `path`.** Nothing is written until `--save`. Audio is copied
  into `Audio Files/` beside the saved session; name clashes become `name_01.wav`.
- **A script stops at its first error and saves nothing**, so a failed run leaves no
  partial session. Fix the line it names and rerun the whole script.
- **Clip ids are numbers** that only exist after the import. Fades and clip gain need
  them; `sc_session.py` handles this with two passes, so by hand you run, inspect, then
  edit.
- **`mix.*` and `automation.*` need `track`/`tracks`**, otherwise they fail with
  "nothing is selected".
- **No sidechain input.** The compressor has no key-input routing in 0.14.0. Duck with
  volume automation (`duck` in the spec); say so if the user asked for sidechain.
- **Volume automation overrides the fader.** With a volume lane present, `mix.volume`
  no longer sets the level; `duck` writes its breakpoints relative to the spec's `volume_db`.
- **Stereo `mix.pan` without `index` moves only the left knob**, narrowing the image.
  Set index 0 and 1, or use the spec's `pan`.
- **`.scraft` `info` is text and shows no mixer state.** Plugins, pan, gain and
  automation only show in `session.inspect` (`sc_inspect.py session`).

## Common jobs

- **Voice-over with a ducked music bed**: two tracks in a spec, `duck` on the music,
  fades on the bed, bounce at the asked rate and depth. Then `sc_verify.py audio --level`
  on a window inside and one outside the voice.
- **Plugins on a track and a range bounce**: `"open"` spec with `inserts`, `bounce` with
  `start`/`end`; check the insert order with `sc_verify.py session --inserts`.
- **Folder conversion**: `sc_convert.sh in out --rate 44100 --bit-depth 16 --normalize --dither`
  (normalize targets −0.1 dBFS peak), then `sc_verify.py audio` per file and `hash in --compare`.
- **Stems, markers, strip silence, AudioSuite processing**: [recipes.md](references/recipes.md).

## References

- [references/cli.md](references/cli.md): every subcommand, its flags and verified output.
- [references/commands.md](references/commands.md): the pinned command ids by task, with params.
- [references/recipes.md](references/recipes.md): specs and command lines for each job.
- [references/gotchas.md](references/gotchas.md): the full list of silent and surprising behaviour.
- [references/live-app.md](references/live-app.md): the running app's control port, `mcp`
  and their security posture.
