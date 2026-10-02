# mscore CLI reference (MuseScore Studio 4.7)

The binary is at `/Applications/MuseScore 4.app/Contents/MacOS/mscore` (`mscore-run.sh --which`).
Run `mscore --help` for the authoritative list on the installed version. Everything
below was exercised on 4.7.5 unless marked *untested*.

## Contents
- [Export](#export-o)
- [Job files](#job-files-j)
- [JSON modes](#json-modes-stdout)
- [Transpose options](#transpose-options)
- [Other flags](#other-flags)

## Export (`-o`)

`mscore [options] -o OUT INPUT`. The output format comes from OUT's extension.

| Ext | Notes |
|-----|-------|
| `.pdf` | all pages; `--page N` for one page |
| `.png` `.svg` | one file per page: `out-1.png`…; `-r DPI` (PNG), `-T MARGIN` trims to the music |
| `.mp3` | `-b KBPS` (default 128); `--sound-profile "MuseScore Basic"\|"MuseSounds"` |
| `.wav` `.ogg` `.flac` | audio, same soundfont as MP3 |
| `.mid` `.midi` | includes chord-symbol playback |
| `.musicxml` `.xml` | uncompressed MusicXML 4.0 |
| `.mxl` | compressed MusicXML |
| `.mscz` `.mscx` | native; `.mscz` is a zip (`score.mscx`, `score_style.mss`, thumbnail…) |
| `.brf` | Braille. Wrote nothing on 4.7.5 (rc 30) |

Inputs are anything MuseScore imports: `.mscz .mscx .musicxml .mxl .xml .mid .midi .kar
.gp .gp3–5 .gpx .gtp .ptb .cap .capx .mei .md .bww .ove .scw` and a few others.

Modifiers for `-o`:

| Flag | Effect |
|------|--------|
| `--transpose JSON` | transpose before exporting (see below) |
| `-S file.mss` | apply a style file (page size, spatium, fonts) |
| `--page N` | export one page (PDF/PNG/SVG/MSCZ) |
| `--region …` | export a region to its own mscz (*untested*) |
| `--unroll-repeats` | expand repeats (useful for audio/MIDI) |
| `-M ops.xml` | MIDI import operations: quantisation, voices (*untested*; see the handbook) |
| `-f` | ignore "corrupted / newer version" warnings |
| `-P` | score + parts in one PDF. **Wrote nothing on 4.7.5**: use `--score-parts-pdf` |

## Job files (`-j`)

```json
[{"in": "/abs/a.mid", "out": ["/abs/out/a.pdf", "/abs/out/a.musicxml", "/abs/out/a.png"]},
 {"in": "/abs/b.mscz", "out": "/abs/out/b.pdf"}]
```

- Use one launch for many conversions; that is where the speed of a batch comes from.
- `"out"` is a string or a list of strings. PNG/SVG get page-numbered as with `-o`.
  The `[prefix, suffix]` pair form some docs mention **writes nothing** on 4.7.5.
- **Don't mix audio with score/image outputs in one entry.** It segfaults mid-job,
  so `batch-convert.py` runs them as two jobs.
- `--sound-profile` applies to the whole job.
- Use absolute paths. Relative ones resolve against mscore's CWD, which is fragile.

## JSON modes (stdout)

| Mode | Output |
|------|--------|
| `--score-meta FILE` | `{"metadata": {title, subtitle, composer, poet, measures, duration (s), keysig (fifths, concert), timesig, tempo, tempoText, pages, pageFormat, hasHarmonies, hasLyrics, lyrics, parts:[{name, instrumentId, program, harmonyCount, lyricCount, hasPitchedStaff, hasTabStaff, hasDrumStaff}], textFramesData, mscoreVersion}}` |
| `--score-parts-pdf FILE` | `{parts:[names], partsBin:[base64 PDF], score, scoreBin (full score PDF), scoreFullBin (score+parts PDF), scoreFullPostfix}` |
| `--score-parts FILE` | `{parts:[names], partsBin:[base64 .mscz per part]}`. It prints rather than writing files |
| `--score-media FILE` | `{pngs, svgs, pdf, midi, mxml, metadata, sposXML, mposXML, devinfo}`, all base64 |
| `--score-elements FILE` | `[{elements:[{type, name, measureIdx, staffIdx, voiceIdx, beat, duration…}]}]` |
| `--score-transpose JSON FILE` | the transposed score as JSON media (*untested*; prefer `--transpose` + `-o`) |

The output can be preceded by log lines. Parse from the first `{` (`ms_lib.json_from_stdout`).
`--score-meta` also works on MusicXML and MIDI inputs directly.

## Transpose options

```json
{"mode": "by_key", "targetKey": 2, "direction": "closest",
 "transposeKeySignatures": true, "transposeChordNames": true, "useDoubleSharpsFlats": false}
{"mode": "by_interval", "transposeInterval": 4, "direction": "up", ...}
```

- `mode`: `by_key` | `by_interval` | `diatonically` (*untested*)
- `targetKey`: the concert key in fifths (−7 Cb … 0 C … 7 C#). Minor keys use the relative major's number.
- `direction`: `up` | `down` | `closest`
- `transposeInterval`: an index into MuseScore's interval list. Verified on 4.7.5: 4 = M2,
  7 = m3, 11 = P4, 14 = P5, 21 = m7.

| # | Ivl | # | Ivl | # | Ivl | # | Ivl |
|---|-----|---|-----|---|-----|---|-----|
| 0 | P1 | 7 | m3 | 14 | P5 | 21 | m7 |
| 1 | A1 | 8 | M3 | 15 | A5 | 22 | M7 |
| 2 | d2 | 9 | A3 | 16 | d6 | 23 | A7 |
| 3 | m2 | 10 | d4 | 17 | m6 | 24 | d8 |
| 4 | M2 | 11 | P4 | 18 | M6 | 25 | P8 |
| 5 | A2 | 12 | A4 | 19 | A6 | | |
| 6 | d3 | 13 | d5 | 20 | d7 | | |

## Other flags

`-v` / `--long-version` print the version, `-F` resets to factory settings, `-R` reverts settings
but keeps preferences, `--score-video` (`--resolution`, `--fps`, `--no-audio`) renders a
scrolling-score video (*untested*), `--gp-linked` creates linked tab staves on Guitar Pro import.
