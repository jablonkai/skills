# aubio 0.4.9 CLI reference

`aubio <command> [options] <source_uri>`. These are the raw commands that
`scripts/aubio_tool.py` wraps; use them directly only for something the script doesn't
cover. All commands accept:

| Option | Meaning | Default |
|--------|---------|---------|
| `-i, --input FILE` | input (or positional) | — |
| `-r, --samplerate HZ` | resample before analysis (**avoid**, see gotchas) | 0 = file rate |
| `-B, --bufsize N` | analysis window in samples | per command |
| `-H, --hopsize N` | step in samples = time resolution | per command |
| `-T, --time-format` | `samples`, `ms` or `seconds` | seconds |
| `-v` / `-q` | verbose (default) / quiet | — |

Output goes to stdout, one event per line, with tab-separated columns and a trailing
tab. `-v` adds a `read N.NNs …` summary on stderr for some commands.

## onset — start times of sound events
`-B 512 -H 256`. Options:

- `-m METHOD`: `default` (= hfc), `energy`, `hfc`, `complex`, `phase`, `specdiff`, `kl`,
  `mkl`, `specflux`.
- `-t THRESHOLD`: peak picking, default 0.3. Higher gives fewer onsets.
- `-s DB`: silence gate, default −70.
- `-M SEC`: minimum inter-onset interval, default 12 ms. Takes units such as `50ms`
  or a bare number.

Output is one time per line. Accurate to about ±5 ms on percussive material. Methods
to try:

- `hfc` for percussion.
- `complex` or `specflux` for pitched or legato material.
- `energy` for simple level jumps.

## beat / tempo — beat times / global BPM
`-B 1024 -H 512`, with no method or threshold options.

- `beat` prints one time per line.
- `tempo` prints `NN.NN bpm`, sometimes followed by ` (uncertain)`. The figure is
  60 / the median gap of `beat`'s own output.

Both are unreliable in 0.4.9 (see gotchas); `aubio_tool.py beats` replaces them.

## pitch — f0 track (monophonic)
`-B 2048 -H 256`. Options:

- `-m`: `default` (= yinfft), `yin`, `mcomb`, `fcomb`, `schmitt`.
- `-t`: tolerance.
- `-u`: `Hz` (default), `midi`, `bin` or `cent`.
- `-s DB`: silence gate.

Output is `time value` per hop. An unvoiced or silent frame prints `0`.

## notes — MIDI-like note events (monophonic)
`-B 512 -H 256`. Options: `-s DB` (silence gate) and `-d DB` (release drop: how far
the level falls before a note ends).

Output:

- The first line is a lone timestamp, the time of the first onset.
- Each line after that is `midi start end`, with `midi` a whole number such as
  `60.000000`.
- The last line is another lone timestamp, the end of the file.

## quiet — quiet/loud transitions
`-H 256`, `-s DB` (default −70, compared with the RMS dBFS of each hop). Output:

```
NOISY: 0.000000
QUIET: 4.005442
NOISY: 5.497324
```

Each line marks a transition. A region runs until the next line. The **last region
has no end time**: it runs to the end of the file, which `ffprobe` can give.

## cut — slice a file at onsets
Options as `onset`, plus:

- `-o DIR`: where the slices go.
- `--cut-until-nsamples N`: extra samples added after each slice.
- `--cut-every-nslices N`: join every N slices into one file.
- `--cut-until-nslices N`: add N following slices to each one.
- `--create-first`: always include the first slice.

It writes one WAV per slice. This command **writes files**, so give it a fresh
`-o` dir.

## mfcc / melbands
Frame-wise MFCCs and mel-band energies, one row per hop. They are feature extraction
for ML or for your own analysis, and the skill has no wrapper for them.
