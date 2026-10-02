# Gotchas (MuseScore Studio 4.7.5, macOS)

## The process

- **The exit code is not the result.** A healthy run often ends with
  `libc++abi: terminating … mutex lock failed`, rc 134, and ~90 lines of crashpad
  output, *after* writing the file. Some modes write nothing (`-P`, `.brf`, a job
  entry mixing audio and PDF). Judge by the file: it exists, is non-empty and is newer
  than the start of the run. The scripts do this for you.
- **Freshness in bash:** macOS bash 3.2's `[[ a -nt b ]]` compares whole seconds.
  A stamp file made just before a fast export looks "not older". `mscore-run.sh`
  back-dates its stamp by 2 s for this reason. Do the same if you script it yourself.
- **No `timeout` on macOS.** `mscore-run.sh` uses a perl fork/alarm supervisor,
  which also stops bash printing "Abort trap: 6" for the crash at shutdown.
- **Crash dumps** pile up in `~/Library/Application Support/MuseScore/MuseScore4/logs/dumps/`
  (`pending/`, `completed/`). They are harmless and safe to delete.
- **Startup cost** is ~1–3 s per launch, and audio takes longer. Batch with job files
  (`batch-convert.py`) instead of one launch per file.
- **The GUI being open doesn't matter.** The CLI runs as a separate process.

## Files

- `-o` **overwrites** silently, including the input if you name it as the output.
- PNG/SVG are page-numbered (`x-1.png`). An old `x-2.png` from a longer earlier score
  survives a new one-page export. The scripts delete stale pages first.
- An `.mscz` is a zip: `<name>.mscx` (the XML score), `score_style.mss`, a thumbnail and
  `audiosettings.json`. Unzip it to grep or patch the XML, then zip it again (or export
  `.mscx` directly with `-o`).
- `--score-meta` `measures` counts a pickup bar as a measure.

## Audio

- MP3/WAV use the bundled **MS Basic** soundfont
  (`MuseScore 4.app/Contents/Resources/sound/MS Basic.sf3`). That needs no MuseSounds or Muse Hub.
- If MuseSounds instruments are installed, a score may default to them and render far
  slower. Pass `--sound-profile "MuseScore Basic"` for speed and determinism.
- Chord symbols are played back, so MIDI/MP3 contain the chords too. To silence them,
  open the score in MuseScore (Properties › Play) or don't write chords into the audio version.
- `score-check.py` flags `silent: true` when the peak is below −60 dB. A silent MP3
  of the right length is the typical symptom of a missing sound.
- The audio length is the score duration (`--score-meta` `duration`) plus a ~3 s release tail.

## MusicXML import

- MuseScore draws chord symbols from `<kind>` + `<degree>` with its own style and **ignores
  `kind/@text`**. The builder encodes `7sus4` as dominant + add 4 + subtract 3; the
  literal sus4 + b7 encoding renders "Csus4♭7".
- Missing `<beam>` elements mean auto-beaming, which is fine. Explicit beams are kept.
- Part names drive instrument detection, together with `<instrument-sound>`. Check `instrumentId` in
  `--score-meta` if the playback sound or the clef looks wrong.
- Credits: the `<work-title>` and `<credit>` words become title/composer frames. A score with
  neither has no title, and `--score-meta` `title` comes back empty.
- MusicXML from other apps can carry layout (`<print>`, `<defaults>`). If the import looks
  cramped, re-export with `-S` and a style file, or strip `<print new-system>` elements.

## MIDI import

- Quantisation, voice splitting and tuplet detection are guesses. Always look at a PNG
  of the result. Ragged rhythms usually mean the MIDI wasn't quantised.
- Track names become part names and General MIDI programs pick the instruments. Drum tracks
  (channel 10) become a drumset staff.
- Key signatures come from MIDI key meta events. Without them the score is in C/Am.
- `-M ops.xml` sets the import options (quantise value, voices, tuplets); see the
  MuseScore handbook, "Command line usage".

## Transposition

- `--transpose` changes **concert** pitch. Each part's written key follows its instrument,
  so a score in D shows E for Bb clarinet and B for Eb alto sax.
- `--score-meta` `keysig` is the concert key of the first measure.
- `by_key` + `closest` can go up or down. Pass `up`/`down` when the octave matters
  (e.g. a vocal range).
- `transposeChordNames: false` leaves chord symbols as they were, which is almost never what you want.

## Not available headless

- **QML plugins** (`~/Documents/MuseScore4/Plugins`) run only inside the GUI. 4.x
  has no command-line plugin runner. For in-app edits, ask the user to run the
  plugin, or do the edit in MusicXML/.mscx and re-import.
- No "save as" with a template, and no layout editing (system breaks, spacing) except via
  a style file (`-S`) or `<print new-system="yes"/>` in MusicXML. The builder writes those
  with `bars_per_line`/`break`, and MuseScore 4.7 honours them on import. Parts lay out on
  their own: `--score-parts-pdf` parts ignore the score's forced breaks.
