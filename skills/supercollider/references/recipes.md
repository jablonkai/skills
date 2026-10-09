# Recipes

Every NRT recipe here is a complete render file, tested with `sc.py render`. Copy a
recipe, change the sound, keep the shape.

## Contents
- [Generative ambient piece (NRT)](#generative-ambient-piece-nrt)
- [Timbre → SynthDef, with test notes](#timbre--synthdef-with-test-notes)
- [Drum kit and a pattern loop](#drum-kit-and-a-pattern-loop)
- [Live changes with Pdef](#live-changes-with-pdef)
- [Exact-length files](#exact-length-files)

## Generative ambient piece (NRT)

The parts are a slow pad chord sequence, sparse bell tones and a filtered noise
wash, each a `Pbind` combined with `Ppar`, plus a reverb bus. Render it with
`render ambient.scd -o ambient.wav --duration 30 --tail 6`.

```supercollider
SynthDef(\pad, { |out = 0, freq = 220, amp = 0.1, dur = 4, pan = 0|
    var env = EnvGen.kr(Env.linen(dur * 0.4, dur * 0.2, dur * 0.4, curve: \sine), doneAction: 2);
    var sig = Mix(Saw.ar(freq * [0.995, 1, 1.005])) * 0.3;
    sig = RLPF.ar(sig, LFNoise2.kr(0.2).range(600, 2400), 0.3);
    Out.ar(out, Pan2.ar(sig * env * amp, pan));
}).add;

SynthDef(\bell, { |out = 0, freq = 880, amp = 0.08, pan = 0|
    var partials = [1, 2.76, 5.4, 8.93];
    var sig = Mix(partials.collect { |p, i|
        SinOsc.ar(freq * p) * EnvGen.kr(Env.perc(0.005, 4 / (i + 1))) / (i + 1)
    });
    DetectSilence.ar(sig, 0.0001, doneAction: 2);
    Out.ar(out, Pan2.ar(sig * amp, pan));
}).add;

SynthDef(\wash, { |out = 0, amp = 0.03, dur = 8|
    var env = EnvGen.kr(Env.sine(dur), doneAction: 2);
    var sig = BPF.ar(PinkNoise.ar([1, 1]), LFNoise1.kr(0.1).exprange(300, 3000), 0.5);
    Out.ar(out, sig * env * amp);
}).add;

// a reverb on the main output: started first, at the tail of the node tree
SynthDef(\verb, { |out = 0, mix = 0.35|
    var dry = In.ar(out, 2);
    ReplaceOut.ar(out, FreeVerb2.ar(dry[0], dry[1], mix, 0.9, 0.4));
}).add;

Ppar([
    Pmono(\verb, \dur, Pseq([30 + 6], 1), \addAction, \addToTail),
    Pbind(\instrument, \pad,
        \scale, Scale.dorian, \octave, 4,
        \degree, Pseq([[0, 2, 4], [-2, 0, 3], [-3, 0, 2], [-1, 1, 4]], inf),
        \dur, 6, \legato, 1.1, \amp, 0.22,
        \pan, Pwhite(-0.4, 0.4)),
    Pbind(\instrument, \bell,
        \scale, Scale.dorian, \octave, 6,
        \degree, Pwhite(0, 7), \dur, Pwhite(1.5, 4.5),
        \amp, Pwhite(0.08, 0.16), \pan, Pwhite(-0.8, 0.8)),
    Pbind(\instrument, \wash, \dur, 8, \amp, 0.08),
])
```

- `Pmono(\verb, …)` starts one long-lived reverb synth. `\addAction, \addToTail` puts
  it after the voices, so it hears them.
- `\dur` in a `Pbind` is the time to the next event. A SynthDef's own `dur` argument
  is *not* the same key: here `\pad` gets `dur` = 6 from the event, because the
  event passes its `\dur` to any SynthDef argument with that name.
- `Env.linen`, `Env.sine` and `DetectSilence` all free the synth (`doneAction: 2`);
  a synth that never frees keeps using CPU and nodes to the end.
- For more variety per seed, use `Pwrand`, `Pbrown` (random walk) and
  `Pseq([...], inf).collect` transformations.

## Timbre → SynthDef, with test notes

Pick the synthesis method from the description, then render a short `Pbind` of test
notes. Use `\midinote` for named pitches (C4 = 60).

| Timbre | Method | Core |
|-------|--------|------|
| plucked string, harp, guitar | Karplus-Strong | `Pluck.ar(WhiteNoise.ar, Impulse.kr(0), 0.05, freq.reciprocal, decay, coef)` |
| warm pad, strings | detuned saws + low-pass | `Mix(Saw.ar(freq * [0.99, 1, 1.01]))` → `RLPF`/`LPF`, slow `Env.asr` |
| bass | saw/square + resonant LPF with envelope | `RLPF.ar(Pulse.ar(freq), EnvGen.kr(Env.perc(0.01, 0.3)).exprange(200, 3000))` |
| bell, metal | inharmonic additive | partials at ratios like 1, 2.76, 5.4, 8.93, shorter decay for higher ones |
| electric piano, brass | 2-operator FM | `SinOsc.ar(freq + SinOsc.ar(freq * ratio, 0, freq * index * env))` |
| kick | sine with pitch drop | `SinOsc.ar(XLine.ar(150, 45, 0.08))` × `Env.perc(0.001, 0.4)` |
| snare | noise + body tone | `HPF.ar(WhiteNoise.ar, 1500)` + `SinOsc.ar(180)` with short envelopes |
| hi-hat | high-passed noise | `HPF.ar(WhiteNoise.ar, 7000)` × `Env.perc(0.001, 0.05)` |

A bright plucked string, five test notes C4–G4, one every 0.5 s:

```supercollider
SynthDef(\pluck, { |out = 0, freq = 440, amp = 0.3, pan = 0, decay = 2, bright = 0.2|
    var sig = Pluck.ar(WhiteNoise.ar(0.8), Impulse.kr(0), 0.05, freq.reciprocal, decay, bright);
    sig = HPF.ar(sig, 80);
    DetectSilence.ar(sig, 0.0001, 0.1, doneAction: 2);
    Out.ar(out, Pan2.ar(sig * amp, pan));
}).add;

Pbind(\instrument, \pluck,
    \midinote, Pseq([60, 62, 64, 65, 67], 1),
    \dur, 0.5, \decay, 0.6, \amp, 0.4)
```

`render pluck.scd -o pluck.wav --duration 2.5 --tail 1`

- `Pluck`'s `coef` is brightness, from 0 (bright) to 0.99 (dull).
- Test notes are clearer with a short `decay`/release, so they don't overlap: the
  onset count in the report then equals the number of notes.
- Always give a SynthDef `out`, `freq`, `amp` and `pan` arguments, so patterns can
  set them. Name the gate argument `gate` for sustained (`Env.adsr`/`Env.asr`)
  sounds; the event releases it after `\sustain`.

## Drum kit and a pattern loop

```supercollider
SynthDef(\kick, { |out = 0, amp = 0.3|
    var env = EnvGen.ar(Env.perc(0.001, 0.35), doneAction: 2);
    var sig = SinOsc.ar(XLine.ar(150, 45, 0.08)) + (HPF.ar(WhiteNoise.ar, 3000) * Line.ar(0.3, 0, 0.01));
    Out.ar(out, (sig * env * amp).dup);
}).add;
SynthDef(\snare, { |out = 0, amp = 0.2|
    var noise = HPF.ar(WhiteNoise.ar, 1500) * EnvGen.ar(Env.perc(0.001, 0.18));
    var body = SinOsc.ar(185) * EnvGen.ar(Env.perc(0.001, 0.08));
    DetectSilence.ar(noise + body, doneAction: 2);
    Out.ar(out, ((noise + (body * 0.6)) * amp).dup);
}).add;
SynthDef(\hat, { |out = 0, amp = 0.12, rel = 0.05|
    var env = EnvGen.ar(Env.perc(0.001, rel), doneAction: 2);
    Out.ar(out, (HPF.ar(WhiteNoise.ar, 7000) * env * amp).dup);
}).add;

// 120 BPM: TempoClock in beats per second; \dur is in beats
Pdef(\drums, Ppar([
    Pbind(\instrument, \kick,  \dur, Pseq([1, 1, 1, 0.5, 0.5], inf)),
    Pbind(\instrument, \snare, \dur, 2, \timingOffset, 1),
    Pbind(\instrument, \hat,   \dur, 0.25, \amp, Pseq([0.15, 0.06, 0.1, 0.06], inf)),
]));
```

- Levels: hits that land together add up. These amps peak around −3 dBTP. Put
  `Limiter.ar(sig, 0.9)` in a master effect if you raise them.
- **Live:** add `TempoClock.default.tempo = 120 / 60;` and
  `Pdef(\drums).play(quant: 4);`, then
  `sc.py record -o loop.wav --seconds 8 --lead-in 2 -f drums.scd`. `quant: 4` waits
  for the next bar line, up to one bar (2 s at 120 BPM), so `--lead-in` of one bar
  starts the take once the loop is already playing.
- **NRT:** end the file with `Pdef(\drums).source` (a `Pdef` itself is a Pattern
  too). Tempo in NRT comes from `asScore`'s clock, so state durations in **seconds**,
  or wrap the pattern: `Pbindf(pattern, \stretch, 60 / 120)` turns beats at 120 BPM
  into seconds.
- `\timingOffset, 1` delays the snare by one beat, onto beats 2 and 4.
- Expected hits in S seconds at B BPM: S × B / 60 × (hits per beat), summed over the
  parts. Simultaneous hits count as one onset in the report.

## Live changes with Pdef

```bash
python3 $S/sc.py start
python3 $S/sc.py record-start live.wav
python3 $S/sc.py run -f v1.scd     # Pdef(\drums, <kick only>).play(quant: 4)
sleep 8
python3 $S/sc.py run -f v2.scd     # Pdef(\drums, <kick + hats>) — same name, no .play needed
sleep 8
python3 $S/sc.py record-stop
python3 $S/sc.py stop
```

- Redefining `Pdef(\drums, …)` swaps the pattern at the next quant boundary while it
  plays. Keep the name and don't `stop` in between.
- `Ndef(\pad, { … })` does the same for a continuous sound, with a crossfade of
  `Ndef(\pad).fadeTime = 2` seconds.
- `Pdef(\drums).stop` stops one part; `stop` (CmdPeriod) stops everything.

## Exact-length files

- NRT: `--duration 30 --tail 0` writes exactly 30 s. Patterns are cut at the
  duration, so fade the end with an `\amp` envelope (`Env([0.3, 0.3, 0], [24, 6])` as
  a `Pseg` or `Env` stream in `\amp`) instead of a hard stop.
- Live: `record --seconds S` gives exactly S seconds (±1 block) from record start.
