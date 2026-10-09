---
name: supercollider
description: 'Make sound with SuperCollider 3 from the command line: write SynthDefs and patterns (Pbind, Pdef, Pseq, Pwhite), render them offline in non-real-time (NRT) mode to WAV faster than realtime with no audio device, or boot a headless live session (sclang + scsynth) to play, live re-evaluate, record exact-length takes and stop; reports sclang post-window errors (parse errors with line and char) and checks every WAV for duration, loudness and clipping. Use for "design a SynthDef for a warm pad and render a few test notes", "render a 30 second generative ambient piece with SuperCollider", "run a drum pattern on scsynth and record 8 seconds", "turn this Pbind into a wav", "why does my .scd throw Message not understood", "write an NRT Score". Not for Sonic Pi code or live_loop (use sonic-pi), transcoding or compressing existing audio/video (handbrake), editing audio on a video timeline (davinci-resolve, final-cut-pro), notation or sheet music (musescore), or DAW projects (Logic, GarageBand, Ableton).'
summary: "make sound with SuperCollider 3 — SynthDefs and patterns rendered offline in NRT mode to WAV, or a headless live sclang/scsynth session to play, re-evaluate, record and stop, with post-window errors surfaced"
category: audio
risk: medium
tags:
    - supercollider
    - sclang
    - scsynth
    - synthesis
    - nrt
    - music
    - audio
    - wav
metadata:
  version: "1.0.0"
---

# SuperCollider from the command line

SuperCollider (free, GPL-3.0) is a language (**sclang**) that drives a synthesis
server (**scsynth**). This skill runs both without the IDE, in one of two modes:

| Mode | Use it for | Speed | Sound device |
|------|-----------|-------|--------------|
| **NRT render** (`sc.py render`) | anything that ends as a WAV file: pieces, SynthDef test notes, stems | faster than realtime (30 s renders in ~1 s) | not used |
| **Live session** (`sc.py start` … `shutdown`) | the user wants to *hear* it, live changes while it plays, or explicitly asks for a live server | realtime | default output |

Prefer NRT whenever the deliverable is a file. It is deterministic, needs no audio
device and makes reproducible takes. Verified against **SuperCollider 3.14.1** on
macOS 27 (arm64).

- [scripts/sc.py](scripts/sc.py): the helper (stdlib Python 3.9+). The subcommands
  are `check`, `render`, `start`, `status`, `run`, `stop`, `record-start`,
  `record-stop`, `record`, `logs` and `shutdown`. It condenses sclang's error dumps
  to message, position and receiver. Exit codes: **2** means SuperCollider reported
  an error, **3** a timeout (the process was killed).
- [scripts/wav_check.py](scripts/wav_check.py): duration, EBU R128 loudness, true
  peak, clipping, rough onset count, with optional time window and high-pass, as
  JSON. `render` and `record` already print this report.
- [references/sclang-reference.md](references/sclang-reference.md): SynthDef/UGen
  essentials, envelopes and freeing, patterns and event keys, tempo, randomness.
- [references/nrt.md](references/nrt.md): the render file contract in depth, Score
  format, buffers and samples in NRT, what does not work offline.
- [references/recipes.md](references/recipes.md): generative ambient, timbre →
  SynthDef (pad, pluck, bass, bell, FM, drums) with test notes, drum loops, live
  changes.
- [references/gotchas.md](references/gotchas.md): **read before debugging silence, a
  hang or a session that won't die.** It also covers the security posture.

## NRT render (the default)

Write a `.scd` file whose **last expression** is what to render: a `Pattern`, a
`Score`, or an Array of `[time, [msg...]]` events. Define the SynthDefs above it with
`SynthDef(...).add`. The wrapper finds every SynthDef the score uses and embeds it,
so nothing else is needed:

```supercollider
SynthDef(\pluck, { |out = 0, freq = 440, amp = 0.2, pan = 0|
    var sig = Pluck.ar(WhiteNoise.ar(0.5), Impulse.kr(0), 0.05, freq.reciprocal, 3, 0.4);
    DetectSilence.ar(sig, doneAction: 2);            // frees the synth when it dies out
    Out.ar(out, Pan2.ar(sig * amp, pan));
}).add;

Pbind(\instrument, \pluck, \scale, Scale.minorPentatonic,
      \degree, Pwhite(0, 9), \dur, Prand([0.25, 0.5], inf), \amp, 0.25);
```

```bash
S=scripts   # paths are relative to this skill's directory
python3 $S/sc.py check                                  # app, version, ffmpeg
python3 $S/sc.py render piece.scd -o piece.wav --duration 30 --tail 4
```

- `--duration S` is the music's length and is **required for a Pattern** (patterns
  are often infinite). `--tail S` (default 2) adds release and reverb time after it,
  so the file is `duration + tail` seconds. For an exact file length, fold the tail
  into the duration and pass `--tail 0`.
- `--seed N` (default 1234) seeds both the language (`Pwhite`, `rrand`, `Prand`) and
  the server's noise generators (`WhiteNoise`, `LFNoise*`, `Rand`, `Dust`), so the
  same seed gives a byte-identical WAV. To get a variation, change the seed. Don't
  add your own `RandSeed`.
- Defaults are 48 kHz, 24-bit, stereo (`--sample-rate`, `--sample-format`,
  `--channels`).
- `render` prints the post window (your `postln`s), then `render: synthdefs=…
  events=…`, then the WAV report. It exits 2 on any error, including a WAV that
  came out **silent**.
- Declare a render file's `var`s on its first lines. A `( var x; … )` block after
  other statements is a parse error; use `~x` or `{ var x; … }.value` there.
- Things that need a running server do not work in a render file: `s.sync`, `fork`
  with waits, `Ndef`, `.play`, or `Buffer.read`. See [nrt.md](references/nrt.md) for
  samples and buffers.

## Live session

```bash
python3 $S/sc.py start                       # sclang + scsynth on 127.0.0.1:57115, ~3 s
python3 $S/sc.py run -f loop.scd             # evaluate; prints "-> result" and errors
python3 $S/sc.py record -o take.wav --seconds 8 -f loop.scd   # exact 8 s take + report
python3 $S/sc.py stop                        # CmdPeriod: silence everything
python3 $S/sc.py shutdown                    # always end with this
```

- In the session, `s` is the session's server, so write code exactly as in the IDE.
  Port 57115 is used so it runs alongside an open SC IDE (which uses 57110). Never
  quit or kill the user's IDE; `sclang -i scqt` is theirs.
- `run -f FILE` evaluates the whole file as **one** block, like selecting all and
  pressing Cmd-Return. Separate statements with `;`. Several `( … )` blocks in a row
  without `;` between them are a parse error.
- **Code that waits** (`s.sync`, `x.wait`) must run inside `fork { … }` or a
  `Routine`. At top level it fails with *yield was called outside of a Routine*.
  `SynthDef(...).add` followed by playing a pattern in the same file is fine without
  `s.sync`.
- **Live changes:** use `Pdef(\name, ...)` / `Ndef(\name, ...)`. Re-running the file
  with the same name swaps the pattern or sound in place, quantised with
  `.play(quant: 4)` or `Pdef(\name).quant = 4`. Don't call `stop` between versions;
  it silences everything.
- `record --seconds S` starts the server recorder, runs the code, stops after exactly
  S seconds, then runs CmdPeriod and prints the WAV report. If the code starts with
  `.play(quant: N)`, the music waits for the next bar line. Add `--lead-in <one bar
  in seconds>` so the code runs first and the take starts once the loop is playing;
  without it, the take opens with silence.
  `record-start OUT.wav [--seconds S]` / `record-stop` capture across several runs.
- Errors inside a routine or pattern arrive **after** `run` returns. `run` waits
  `--settle` seconds (0.5) for them. For anything that keeps playing, check
  `sc.py logs --errors` before reporting success.
- A `run` that does not finish in `--timeout` (an endless loop) exits 3. The
  interpreter stays stuck, so `shutdown` and `start` again.

## Reading errors

`sc.py` prints errors condensed:

```
ERROR: Message 'ar' not understood.
PATH: /path/to/piece.scd
RECEIVER: nil
```

- `Message 'x' not understood` with `RECEIVER: nil` means something was nil: an
  unset `~envVar`, a misspelled `Pdef`/`Ndef` name, or a method that returned nil.
  With another receiver, the method name is wrong for that class (for example `.ar`
  on a number).
- `Variable 'foo' not defined` is a parse error. Top-level names must be declared
  with `var` at the top of the block, or be `~envVar`s or single letters `a`–`z`.
- **Parse errors** give `line N char M` with the source line and a caret. Fix that
  line first; later errors usually cascade from it.
- `FAILURE IN SERVER /s_new SynthDef not found`: the SynthDef wasn't added, or its
  name is misspelled in `\instrument`.
- `SC_SKILL_FAIL …` lines come from the render wrapper and say exactly what is
  missing (no Pattern returned, undefined SynthDef, no duration).

Report the message and the position to the user, fix the code and run it again.
Don't hide an error with `try`.

## Verifying output

Every `render` and `record` prints the `wav_check` report. Before calling the work
done, check that it meets all of these:

- `silent: false` and `clipping: false` (true peak below 0 dBTP; above it, lower
  `amp` or add `Limiter.ar(sig, 0.9)`).
- `duration_s` matches what was asked for.
- `integrated_lufs` is roughly −30…−10 for music. Much lower than that means the
  `amp`s are too quiet.
- For note-based tasks, `onsets` is close to the expected note count (it is a rough
  silence-gap count, so it only works for detached notes).
- For drums, `wav_check.py take.wav --highpass 6000` shows the hats are there.

## Clean-up

End every live session with `sc.py shutdown`. It quits the server and sclang, and
kills anything left over, even after an endless loop or a crashed helper. `start`
also reaps leftovers of a dead session before booting. A `render` never leaves a
process behind: on timeout it kills sclang and the NRT scsynth together.
