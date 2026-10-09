# sclang essentials for sound design

This is not a language tutorial. It covers the parts an agent gets wrong most often
when writing music code. Look up anything else in the bundled help:
`/Applications/SuperCollider.app/Contents/Resources/HelpSource/Classes/<Class>.schelp`.

## Contents
- [Syntax traps](#syntax-traps)
- [SynthDefs](#synthdefs)
- [Envelopes and freeing](#envelopes-and-freeing)
- [Patterns and events](#patterns-and-events)
- [Pitch](#pitch)
- [Randomness](#randomness)
- [Tempo](#tempo)

## Syntax traps

- **Variables:** declare all `var`s at the **top** of a block or function, before any
  statement. A `var` after a statement is a parse error. Single letters `a`–`z` and
  `~name` need no declaration (`s` is the server).
- **Symbols** are `\name` or `'name'`. **Strings** use `"double quotes"`.
- Statements end with `;`. A function body's last expression is its return value.
- **Arguments:** `{ |freq = 440, amp = 0.1| … }` or `arg freq = 440;`.
- **Precedence is left to right** with no operator precedence: `1 + 2 * 3` is 9.
  Parenthesise.
- **Messaging:** `SinOsc.ar(440)` is a class method; `440.midicps` sends a unary
  message to a number. Keyword args: `Pan2.ar(sig, pos: 0.3)`.
- **Arrays expand:** `SinOsc.ar([440, 442])` is two channels. `Mix(...)` sums them,
  `Splay.ar(array)` spreads them across stereo.

## SynthDefs

```supercollider
SynthDef(\name, { |out = 0, freq = 440, amp = 0.2, pan = 0, gate = 1|
    var env = EnvGen.kr(Env.adsr(0.01, 0.2, 0.6, 0.5), gate, doneAction: 2);
    var sig = RLPF.ar(Saw.ar(freq), freq * 4, 0.3);
    Out.ar(out, Pan2.ar(sig * env * amp, pan));
}).add;
```

- `.ar` runs at audio rate (signals you hear), `.kr` at control rate (envelopes,
  LFOs).
- **Output must be explicit:** `Out.ar(bus, signal)`. A SynthDef without `Out`
  produces nothing.
- Keep stereo output 2 channels: `Pan2` for mono sources, `Balance2` for stereo,
  `.dup` for identical L/R.
- `.add` compiles the SynthDef and registers it (and sends it to any running
  server). Renders pick SynthDefs up from there.
- Useful UGens:
  - oscillators: `SinOsc`, `Saw`, `Pulse`, `LFTri`, `VarSaw`, `Blip`
  - noise: `WhiteNoise`, `PinkNoise`, `BrownNoise`, `Dust`
  - filters: `LPF`, `HPF`, `RLPF`, `BPF`, `MoogFF`
  - effects: `FreeVerb`, `FreeVerb2`, `GVerb`, `CombL`, `AllpassN`, `DelayN`
  - dynamics: `Limiter`, `Compander`, `tanh`
  - physical: `Pluck`, `Klank`, `Resonz`
  - modulation: `LFNoise1`/`LFNoise2` (smooth random), `SinOsc.kr` (LFO);
    `.range(lo, hi)` / `.exprange(lo, hi)` scale them
- `Line.kr(a, b, dur)` and `XLine.kr(a, b, dur)` ramp a value. `XLine` must not
  touch 0.

## Envelopes and freeing

Every synth must end, or it keeps using CPU and nodes:

| Sound | Envelope | Frees when |
|-------|----------|-----------|
| percussive, plucked | `Env.perc(atk, rel)` | the envelope ends (`doneAction: 2`) |
| sustained by the event | `Env.adsr` / `Env.asr` + a `gate` argument | the event sets `gate` 0 after `\sustain` |
| fixed length | `Env.linen(atk, sus, rel)`, `Env.sine(dur)` | the envelope ends |
| resonant tail of unknown length | `DetectSilence.ar(sig, 0.0001, doneAction: 2)` | the signal stays below the threshold |

A sustained SynthDef **without** a `gate` argument never gets released by a pattern.
It sounds until its own envelope ends, or forever.

## Patterns and events

```supercollider
Pbind(
    \instrument, \name,          // SynthDef name; default \default (a simple piano-ish synth)
    \degree, Pseq([0, 2, 4, 7], inf),   // scale degree; or \note, \midinote, \freq
    \scale, Scale.minor, \octave, 5,
    \dur, 0.25,                  // time to the next event (beats; 1 beat = 1 s at tempo 1)
    \legato, 0.8,                // sustain = dur * legato (for gated synths)
    \amp, Pwhite(0.1, 0.2),
)
```

- Every key that matches a SynthDef argument name is sent to the synth (`\cutoff, 2000`
  → `cutoff`).
- An array value makes a chord: `\degree, [0, 2, 4]`.
- `\dur, Rest(1)` or `\degree, \rest` makes a rest.
- **Value patterns:**
  - `Pseq(list, repeats)` steps through a list; `Prand(list, n)` picks at random;
    `Pxrand` picks at random without repeating the last pick; `Pwrand(list,
    weights.normalizeSum, n)` picks by weight.
  - `Pwhite(lo, hi)` gives uniform random values; `Pexprand` exponential;
    `Pbrown(lo, hi, step)` a random walk.
  - `Pseg(levels, durs)` is a time-based ramp, for fades.
  - `Pfunc { … }` takes any computed value.
- **Event-pattern combinators:**
  - `Ppar([p1, p2])` plays patterns in parallel; `Ptpar([0, p1, 4, p2])` in parallel
    with start offsets.
  - `Pseq([p1, p2])` plays them in sequence.
  - `Pfindur(seconds, p)` cuts a pattern to a length.
  - `Pbindf(p, \key, value)` adds or overrides a key; `Pchain(a, b)` composes two.
  - `Pmono(\synth, ...)` keeps one synth and updates it per event.
- **Named, live-replaceable patterns:** `Pdef(\x, pattern)`. Play one with
  `Pdef(\x).play(quant: 4)` and redefine it at any time. Inside a render file, return
  `Pdef(\x).source`.

## Pitch

- `\degree` is relative to `\scale`, `\root` and `\octave`. With the defaults
  (`\octave` 5, `\root` 0), degree 0 is middle C, MIDI 60. `\octave, 4` gives MIDI
  48, `\octave, 6` MIDI 72.
- `\midinote, 60` is C4 = 261.63 Hz. `\note` is semitones from the root;
  `\freq, 440` is raw Hz.
- Inside a SynthDef: `60.midicps` → 261.63, `440.cpsmidi` → 69.
- Scales: `Scale.major`, `.minor`, `.dorian`, `.minorPentatonic`, `.majorPentatonic`,
  `.chromatic`, `.whole` (see `Scale.directory`).

## Randomness

- In patterns and language code, `rrand(lo, hi)`, `exprand`, `[a, b].choose` and
  `0.5.coin` follow `thisThread.randSeed`. `render --seed N` sets it, so renders are
  reproducible. Live: `thisThread.randSeed = 42;` before the code.
- UGens like `LFNoise1`, `WhiteNoise`, `Dust` and `Rand` draw from the server's
  random generators, which scsynth seeds from the clock. `render` reseeds generator
  0 from `--seed` at time 0, so NRT renders are reproducible. Live, add
  `RandSeed.ir(1, 42)` in a SynthDef, or run a one-shot seeding synth first.
  `Rand(lo, hi)` in a SynthDef gives one random value per synth instance.

## Tempo

- Live: `TempoClock.default.tempo = bpm / 60;` makes `\dur` count in beats.
  `Pdef(\x).quant = 4` aligns changes to bar lines.
- NRT: patterns render at 1 beat per second. Use
  `Pbindf(pattern, \stretch, 60 / bpm)` (see [nrt.md](nrt.md#tempo-and-timing)).
- Seconds per bar = beats per bar × 60 / BPM. Eight bars of 4/4 at 120 BPM is 16 s.
