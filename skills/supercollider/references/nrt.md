# NRT rendering in depth

`sc.py render FILE.scd -o OUT.wav` runs [`scripts/nrt_wrap.scd`](../scripts/nrt_wrap.scd)
in sclang. The wrapper:

1. Seeds the interpreter thread with `--seed`.
2. Evaluates FILE with `executeFile`.
3. Turns the result into a `Score`.
4. Embeds every SynthDef that the score's `/s_new`s name as `/d_recv` at time 0.
5. Runs `Score.recordNRT`, where scsynth renders the score as fast as it can, with no
   audio device.

## What the file may return

| Last expression | Rendered as | `--duration` |
|-----------------|-------------|--------------|
| a `Pattern` (`Pbind`, `Ppar`, `Pseq` of events, `Pdef(\x).source` …) | `pattern.asScore(duration)` | required |
| a `Score` | as is | optional; default is the last event's time |
| an `Array` of `[time, [cmd, args...]]` | `Score(array)` | optional |

`--tail` is always added after the duration, so a release or reverb isn't cut off.

## Raw score events

Score events are OSC server commands with a time in seconds:

```supercollider
SynthDef(\tone, { |out = 0, freq = 440, amp = 0.2, gate = 1|
    var env = EnvGen.kr(Env.asr(0.01, 1, 0.5), gate, doneAction: 2);
    Out.ar(out, SinOsc.ar(freq, 0, amp * env).dup);
}).add;
[
    [0.0, [\s_new, \tone, 1000, 0, 0, \freq, 440]],   // nodeID 1000, addToHead, group 0
    [1.0, [\n_set, 1000, \freq, 660]],
    [2.0, [\n_set, 1000, \gate, 0]],                  // release; frees itself 0.5 s later
    [2.5, [\s_new, \tone, 1001, 0, 0, \freq, 330]],
    [3.0, [\n_set, 1001, \gate, 0]],
]
```

- Use explicit node IDs (1000 and up) for synths you address later (`n_set`,
  `n_free`). Use -1 for fire-and-forget synths that free themselves.
- Add actions: 0 = head, 1 = tail of the target group (group 0 is the root). Put
  effect synths at the tail, so they read what the voices wrote.
- Several commands at one time: `[t, [msg1], [msg2]]`.
- Keep events in time order for readability. The wrapper sorts them anyway.

## Samples and buffers

`Buffer.read` needs a running server. In NRT, allocate and load at time 0 inside the
score, and refer to the buffer by number:

```supercollider
var path = Platform.resourceDir +/+ "sounds/a11wlk01.wav";   // any WAV/AIFF path
SynthDef(\play, { |out = 0, buf = 0, rate = 1, amp = 0.5|
    var sig = PlayBuf.ar(1, buf, rate * BufRateScale.kr(buf), doneAction: 2);
    Out.ar(out, (sig * amp).dup);
}).add;
[
    [0.0, [\b_allocRead, 0, path]],                  // buffer 0 ← file
    [0.1, [\s_new, \play, -1, 0, 0, \buf, 0]],
    [2.0, [\s_new, \play, -1, 0, 0, \buf, 0, \rate, 0.5]],
]
```

- Match `PlayBuf`'s channel count to the file (1 for mono).
- For delay or wavetable buffers: `[0.0, [\b_alloc, 1, 48000 * 2, 1]]` (2 s mono).
- A Pattern can use a buffer loaded this way, but only if the file returns a Score.
  Merge them with `Score([[0.0, [\b_allocRead, 0, path]]] ++
  pattern.asScore(30).score)`. Then pass `--duration 30`, because the end marker
  from `asScore` is dropped.

## Effects buses in a pattern render

Use a long-lived effect synth on the main bus at the tail (see the ambient recipe:
`Pmono(\verb, …, \addAction, \addToTail)`), or a private bus. For a private bus,
send voices to `\out, 16` and run an effect that reads `In.ar(16, 2)` and writes to
0. Buses 0 and 1 are the output in NRT, as they are live.

## Tempo and timing

`asScore` plays the pattern on a TempoClock at **1 beat per second**, so a `\dur` of
0.5 is half a second. To think in beats at B BPM, wrap the pattern:
`Pbindf(pattern, \stretch, 60 / B)`. `TempoClock.default.tempo` does not affect
`asScore`.

## Not available offline

| Live feature | NRT replacement |
|--------------|-----------------|
| `s.sync`, `fork { … wait … }`, `.play`, `Synth(...)` | write the events into a pattern or score |
| `Ndef`, `ProxySpace`, `JITLib` | a SynthDef plus `\s_new` / `Pmono` |
| `Buffer.read`, `Buffer.alloc` | `\b_allocRead` / `\b_alloc` at time 0 |
| `s.record` | NRT already writes the file |
| `MIDIIn`, `In.ar` from a sound card | none (no devices) |

## Reproducibility

The wrapper seeds the language with `--seed`, and it reseeds the server's random
generator 0 with a one-shot synth at time 0. This makes `WhiteNoise`, `LFNoise*`,
`Dust`, `Rand` and the rest repeat exactly. The reseed must land before any synth is
created, so every event in the file starts 128 samples late (2.7 ms at 48 kHz). The
file keeps its exact length. A SynthDef that calls `RandID` to use another generator
is not covered; seed it yourself with `RandSeed`.

## Output format

Defaults are WAV, 48 kHz, int24, 2 channels. With `--sample-format float`, peaks
above 0 dBFS survive in the file but clip on playback. Keep the true peak below 0 at
any format. The OSC score file and the full post log are kept in the temp dir that
`render` prints (`full log: …`).
