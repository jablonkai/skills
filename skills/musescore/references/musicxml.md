# MusicXML: the builder spec and hand-written XML

## Contents
- [Builder spec](#builder-spec): top level, parts, measures, note tokens, chord symbols
- [Instruments](#instruments): names, clefs, transposition
- [Hand-writing MusicXML](#hand-writing-musicxml): when you need to, element order, and what MuseScore reads

## Builder spec

`scripts/musicxml-build.py spec.json out.musicxml` emits MusicXML 4.0 partwise and
validates each bar's length against the time signature. A spec error exits 1
with a message that names the measure.

### Top level

| Key | Example | Notes |
|-----|---------|-------|
| `title` | `"Evening Walk"` | work title + centred title credit |
| `subtitle`, `composer`, `lyricist`, `arranger` | | credits / creators. Only names the user gave |
| `key` | `"F"`, `"Bb"`, `"F#m"`, `"D minor"`, `-1` | concert key; minor uses the relative major's signature |
| `time` | `"4/4"`, `"6/8"`, `"3/4"` | |
| `tempo` | `96` | quarter-note BPM; metronome mark + playback tempo on bar 1 |
| `pitch` | `"concert"` (default) or `"written"` | how notes of transposing instruments are given |
| `bars_per_line` | `4` | forced system break every N bars (counted from bar 1, a pickup excluded) |
| `parts` | list | all parts must have the same number of measures |

### Parts

```json
{"name": "Clarinet in Bb", "instrument": "clarinet", "abbreviation": "Cl.",
 "clef": "treble", "program": 72, "staves": 1, "measures": [...]}
```

Only `measures` is required. `instrument` defaults to `name`. Both are matched
against the instrument table below, case-insensitively, also as a substring
("Lead Trumpet" → trumpet). `clef` overrides the instrument's clef: `treble bass
alto tenor treble8vb bass8vb percussion`. For two-staff parts (piano by default,
or `"staves": 2`), `clef`/`clef2` set the upper and lower clefs.

### Measures

A measure is a string (just notes) or an object:

| Key | Meaning |
|-----|---------|
| `notes` | note tokens, upper staff |
| `notes2` | lower staff of a two-staff part (defaults to a whole-bar rest) |
| `chords` | chord symbols, see below |
| `pickup` | first measure only: shorter anacrusis, numbered 0 |
| `key`, `time` | change from this bar on |
| `repeat_start`, `repeat_end` | repeat barlines |
| `double` | double barline at the end of the bar (the last bar always gets a final barline) |
| `text` | staff text above (e.g. `"Swing"`, `"rit."`) |
| `rehearsal` | rehearsal mark (`"A"`) |
| `break` | `true` starts a new system at this bar; `false` suppresses a `bars_per_line` break here |
| `page_break` | start a new page at this bar |

### Note tokens

`PITCH/DUR[.][.][3][~][|lyric]`

- PITCH: `C4` is middle C, `Bb3`, `F#5`, `Ebb4`, `Fx4` (double sharp); `r` is a rest;
  `[C4,E4,G4]` is a chord (all notes share the duration).
- DUR: `w` whole, `h` half, `q` quarter, `e` eighth, `s` 16th, `t` 32nd.
- `.` / `..` dotted / double-dotted.
- `3` triplet member: three `e3` fill one quarter. Brackets are added per group.
- `~` ties into the next note of the same pitch, across barlines too.
- `|syl` lyric syllable. End it with `-` when the word continues: `C5/q|Hel- D5/q|lo`.
  Lyrics can't contain spaces; use one syllable per note.

Accidentals are sounding alterations: write `Bb4` in F major and `B4` for a
B natural. MuseScore decides which accidentals to print from the key.

### Chord symbols

`"chords": "F Dm7 Bb/D C7b9@3"`. Symbols are space-separated; `@beat` (1-based, in the
time signature's beat unit) places one exactly. Without `@`, n symbols are
spread evenly: 1 → beat 1, 2 → beats 1 and 3 in 4/4, 4 → every beat.

| Suffix | Kind | Suffix | Kind |
|--------|------|--------|------|
| (none) | major | `m` `min` `-` | minor |
| `7` | dominant | `maj7` `M7` `Maj7` | major-seventh |
| `m7` `min7` `-7` | minor-seventh | `m7b5` `ø` `ø7` | half-diminished |
| `dim` `o` | diminished | `dim7` `o7` | diminished-seventh |
| `aug` `+` | augmented | `aug7` `+7` | augmented-seventh |
| `6` / `m6` | major-/minor-sixth | `mMaj7` | major-minor |
| `9` `maj9` `m9` | ninths | `11` `m11`, `13` `maj13` `m13` | 11ths / 13ths |
| `sus2` `sus4` `sus` | suspended | `7sus4` | dominant + add 4, subtract 3 (renders "7sus4") |
| `5` | power | | |

After the quality you can add alterations: `b9 #9 #11 b13 b5 #5 add9`, as in `C7b9`, `G7#5`,
`Cadd9` or `Bb7(#11)`. A slash bass works on any chord: `Bb/D`. An unknown suffix is an error, not a guess.

MuseScore renders symbols from `kind` + `degree` using its own chord style
and **ignores the `text=` attribute**. That's why `7sus4` is encoded as dominant +
add 4 − 3: the naive `suspended-fourth + add b7` renders as "Csus4♭7".

## Instruments

Notes go in at concert pitch. The builder writes each part's `<transpose>` and
its written pitch and key, and MuseScore plays it back at concert pitch. This was
verified by MIDI round trip on 4.7.5.

| Name (aliases) | Clef | Written vs sounding |
|----------------|------|---------------------|
| piano (grand piano) | treble + bass | — |
| voice (vocals, melody, lead), soprano, alto voice, bass voice | treble/bass | — |
| tenor voice | treble 8vb | octave |
| flute, oboe, violin | treble | — |
| clarinet (clarinet in bb) | treble | M2 higher |
| trumpet (trumpet in bb) | treble | M2 higher |
| horn (french horn, horn in f) | treble | P5 higher |
| alto sax (alto saxophone) | treble | M6 higher |
| tenor sax (tenor saxophone) | treble | M9 higher |
| bassoon, trombone, cello | bass | — |
| viola | alto | — |
| double bass (contrabass, upright bass) | bass | octave higher |
| guitar (acoustic guitar) | treble 8vb | octave higher |
| bass guitar (electric bass) | bass | octave higher |

Unknown names fall back to a treble-clef voice sound. Set `clef` and `program`
(General MIDI 1–128) yourself, and if the instrument transposes, write
its notes with `"pitch": "written"` and hand-add `<transpose>`.

## Hand-writing MusicXML

Write raw XML only for what the builder can't express: several voices on one staff,
dynamics (`<direction><direction-type><dynamics><mf/>`), articulations and slurs
(`<notations>`), grace notes, percussion maps. Or let the builder write the
skeleton and add those elements to its output. It keeps a fixed
`<divisions>24</divisions>` (quarter = 24, eighth = 12, triplet eighth = 8, 16th = 6).

Order rules the XSD enforces (and `score-check.py --xsd` reports):

- `<note>`: `chord? (pitch|rest) duration tie* voice? type? dot* accidental?
  time-modification? stem? staff? beam* notations* lyric*`
- `<attributes>`: `divisions key time staves clef transpose`
- `<harmony>` comes before the note it sits on; use `<offset>` (in divisions) for a
  position between note onsets.
- Use `<backup><duration>` to rewind for the next voice or staff, and `<forward>` to skip.
- Score-wide items live in part 1 only: tempo `<sound tempo>` and the metronome mark.

What MuseScore 4.7 does with imported MusicXML:

- It recognises instruments from `<instrument-sound>` and the part name. The `--score-meta`
  `instrumentId` shows what it chose (`bb-clarinet`, `guitar-nylon-treble-clef`…).
- It auto-beams when no `<beam>` elements are present, which is usually what you want.
- It plays chord symbols back, so expect extra notes on that part's MIDI/MP3 track.
- `--musicxml-use-default-font` and `--musicxml-infer-text-type` change how imported
  text is styled. Both are off by default.
