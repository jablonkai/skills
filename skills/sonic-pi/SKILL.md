---
name: sonic-pi
description: 'Live-code music with Sonic Pi 5 from the command line: boot a headless Sonic Pi session (no GUI needed), write and run Sonic Pi Ruby-DSL code (live_loop, synths, samples, FX, chords and scales), re-evaluate a running live_loop to change it without stopping the music, record exact-length takes to WAV, stop jobs, and report runtime and syntax errors with line numbers; can also send code to an already open Sonic Pi window. Use for "make a lo-fi beat in Sonic Pi and save it as a WAV", "live code a techno loop", "change the bass line in the running loop", "turn this CSV into sound", "sonify this data", "why does my Sonic Pi code throw an error". Not for transcoding or compressing existing audio/video files (use handbrake), editing or mixing audio in a video timeline (use davinci-resolve or final-cut-pro), screen or stream recording (use obs), generic Ruby scripts, or DAW projects (GarageBand, Logic, Ableton).'
summary: "live-code music in Sonic Pi 5 via a headless OSC session — run and live re-evaluate live_loops, record exact-length WAV takes, stop jobs, surface runtime and syntax errors with line numbers"
category: audio
risk: medium
tags:
    - sonic-pi
    - music
    - live-coding
    - osc
    - audio
    - wav
---

# Sonic Pi via a headless OSC session

Sonic Pi (free, MIT) is a live-coding music app: Ruby-DSL code is sent to its
**spider** server, which schedules sound on its audio engine (**SuperSonic** in v5).
The GUI is only one client, so this skill boots and owns a **headless** Sonic Pi
session in the background and drives it over local OSC. Verified against **Sonic Pi
5.0.0** on macOS 27 (arm64).

- [scripts/sp.py](scripts/sp.py): the session helper (stdlib Python, no installs).
  `check`, `start`, `attach`, `status`, `run`, `stop`, `record`, `record-start`,
  `record-stop`, `logs` and `shutdown`. `run` and `record` print the errors that the
  code raised, with line numbers, and **exit 2** on any error.
- [scripts/wav_check.py](scripts/wav_check.py): duration, EBU R128 loudness, true
  peak, rough onset count, an optional time window and high-pass band, as JSON. Use
  it to verify every take.
- [references/dsl-reference.md](references/dsl-reference.md): timing, bars ↔
  seconds, live_loop/sync, synths, samples (the full built-in list), FX, rings,
  randomness.
- [references/recipes.md](references/recipes.md): lo-fi beat, chord progressions,
  live changes, data sonification, fixed-length takes.
- [references/osc-protocol.md](references/osc-protocol.md): ports, token, the
  messages the helper sends and receives, for anything the helper does not cover.
- [references/gotchas.md](references/gotchas.md): **read before debugging timing,
  silence or a session that will not die.** It also covers the security posture.

## Workflow

```bash
S=scripts   # paths are relative to this skill's directory
python3 $S/sp.py check                       # 1. app present? (exit 2 → install it)
python3 $S/sp.py start                       # 2. headless session, ready in ~3 s
python3 $S/sp.py run -f song.rb              # 3. play it; errors → exit 2 with line
python3 $S/sp.py record -o take.wav --bars 32 --bpm 80 -f song.rb   # 4. exact take
python3 $S/wav_check.py take.wav --expect-seconds 96               # 5. verify
python3 $S/sp.py shutdown                    # 6. always end the session
```

Write the code to a `.rb` file and pass `-f`, rather than inlining it with `-e`, so
line numbers in errors match the file. Sound plays on the default output device
while it runs; recording is **realtime** (a 96 s take takes 96 s).

### Running and fixing code

`run` sends the code, waits `--wait` seconds (default 1.5) and prints the `puts`
output and errors from that window:

```
ERROR (run 2, line 3): Runtime Error Sonic Pi doesn't know a function called `foo_bar`
SYNTAX ERROR (run 3, line 1): ... expected a block beginning with `do` to end with `end`
```

An error inside a `live_loop` can surface later than the wait window (the loop body
runs each iteration). After a run that should keep going, check
`sp.py logs --errors` before reporting success. A loop that raises **stops**; the
others keep playing. `WARNING` lines are problems Sonic Pi only logs: a misspelled
sample name is skipped silently instead of raising. Report errors to the user with
the message **and** the line, then fix the code and re-run. Do not paper over an
error with `begin/rescue`.

### Changing music while it plays (live coding)

Re-running code that defines a `live_loop` with the **same name** swaps the loop's
body at its next iteration, in time and without a gap. This is how live changes work:

```bash
python3 $S/sp.py record-start                 # optional: capture the change
python3 $S/sp.py run -f v1.rb                 # live_loop :drums ... (kick only)
# ...later: edit the file, keep the loop name, run again. Do NOT call stop in between.
python3 $S/sp.py run -f v2.rb                 # live_loop :drums ... (kick + hats)
python3 $S/sp.py record-stop live.wav
python3 $S/sp.py stop
```

- `stop` kills every job, so the music stops. Calling it between versions breaks a
  live change.
- To remove one loop live, re-run it with `stop` as its body
  (`live_loop :hats do stop end`).
- Loops from earlier runs keep playing until they are stopped or redefined, so
  re-send all the loops you still want.

### Recording

- `sp.py record -o OUT.wav (--seconds S | --bars N --bpm B) -f FILE` stops old jobs,
  lets their notes drain, runs the code and records exactly the music's length
  (±10 ms). The take starts on the first note. `--tail S` adds release or reverb
  tail. `--beats-per-bar` defaults to 4. The BPM must match the code's `use_bpm`.
- `record-start` / `record-stop OUT.wav` record across several runs (live
  changes). The take includes the ~0.5 s before the first scheduled note.
- Takes are 48 kHz 24-bit stereo WAV from Sonic Pi's own recorder, taken before the
  output device. System volume does not matter, but `set_volume!` and `amp:` do.
- To make a random piece reproducible, put `use_random_seed N` at the top and in
  each live_loop that uses randomness.

Verify every take with `wav_check.py` before calling it done:

- `silent: false`
- `duration_ok: true`
- integrated loudness roughly −30…−10 LUFS
- `true_peak_dbtp` below 0 (above 0 means clipping: lower `amp:`)

For a live change, compare windows, for example
`--start 0 --end 8 --highpass 6000` against `--start 9 --end 16 --highpass 6000`.

### Attaching to an open Sonic Pi window

If the user has the Sonic Pi app open and wants the code to appear there,
`sp.py attach` finds the app's port and token from its process list. `run`, `stop`,
`record*` and `shutdown` then target the GUI. The GUI owns the reply port, so
**errors and `puts` show in the app's log pane, not here**: say so, and ask the user
to read it back, or work headless. `shutdown` only stops jobs and detaches; it never
quits the user's app. Start a headless session instead whenever you need error
feedback or verifiable takes.

## Writing the music

- **Bars to seconds:** seconds = bars × beats-per-bar × 60 / BPM. 32 bars of 4/4 at
  80 BPM is 96 s.
- Inside `use_bpm`, `sleep 1` is one beat. Keep each loop's total sleep a whole
  number of bars, so loops stay in phase.
- `live_loop` must contain a `sleep` (or `sync`), or it raises
  "did not sleep".
- Put `with_fx` **inside** the `live_loop` body, as in
  [recipes.md](references/recipes.md), so a re-run updates the FX too.
- Read data files directly (`File.readlines`) or embed the values as a Ruby array.
  Map values onto a scale (`scale(:c4, :major_pentatonic)`) for a musical result.
  See the sonification recipe.

## Clean-up

Always finish with `sp.py shutdown` (it stops jobs, ends the engine, and also reaps
a session whose helper crashed). If it was not called, an orphaned engine exits by
itself about 90 s after its helper dies.
