# SoundCraft recipes (0.15.0)

`S=<skill>/scripts`. Use absolute paths in hand-written command JSON; `sc_session.py`
resolves spec paths against the current directory.

## Voice-over with a ducked music bed

```json
{
  "new": {"name": "Episode 12", "sample_rate": 48000, "bit_depth": 24},
  "tracks": [
    {"name": "Voice", "file": "/abs/vo.wav", "at": 4.0,
     "fade_in": 0.02, "fade_out": 0.2,
     "inserts": [
       {"plugin": "eq_7band", "params": {"hpf_on": 1, "hpf_freq": 90}},
       {"plugin": "compressor", "params": {"threshold": -22, "ratio": 3, "makeup": 3}},
       {"plugin": "de_esser"}]},
    {"name": "Music", "file": "/abs/bed.wav", "at": 0, "volume_db": -6,
     "fade_in": 2.0, "fade_out": 4.0, "fade_shape": "s-curve",
     "duck": {"under": "Voice", "db": -14, "ramp": 0.4, "gap": 1.5}}
  ],
  "save": "/abs/out/Episode 12.scraft",
  "bounce": {"path": "/abs/out/Episode 12.wav", "bit_depth": 24}
}
```

```sh
python3 $S/sc_session.py spec.json
python3 $S/sc_verify.py session "/abs/out/Episode 12.scraft" --tracks 2 \
  --fades Music --automation Music=volume --inserts Voice=eq_7band,compressor,de_esser
# voice from 4 s: compare the bed inside vs outside the voice (mute Voice for a clean read)
soundcraft-cli run --in "/abs/out/Episode 12.scraft" --cmd 'mix.mute={"tracks":["Voice"],"value":true}' \
  --bounce /tmp/bed-only.wav
python3 $S/sc_verify.py audio /tmp/bed-only.wav --level 2.5:3.4 --level 6:10
python3 $S/sc_verify.py audio "/abs/out/Episode 12.wav" --rate 48000 --depth 24 --max-peak -0.1
```

The bounce takes the session's length, which ends at the last clip; the bed's fade-out
ends it. Without `--save`, the mute experiment doesn't touch the saved session. To end
the voice before the bed, place the bed so it outlasts the voice, or trim it with
`edit.trim_clip`.

If the user asked for **sidechain** ducking: there is no key input in 0.15.0. Use
`duck` and say it's done with volume automation.

## Plugins on one track of an existing session, then a range bounce

```json
{
  "open": "/abs/Song.scraft",
  "tracks": [{"name": "Pad", "inserts": [
    {"plugin": "eq_7band", "params": {"hpf_on": 1, "hpf_freq": 120, "mid_gain": -3}},
    {"plugin": "compressor", "params": {"threshold": -24, "ratio": 3}}]}],
  "save": "/abs/out/Song-edit.scraft",
  "bounce": {"path": "/abs/out/Song 0m20-0m30.wav", "start": "0:20", "end": "0:30", "bit_depth": 24}
}
```

Check the existing inserts first (`sc_inspect.py session`): new ones go into the next free
slots, after any already there. Verify with
`sc_verify.py session OUT --inserts Pad=<existing...>,eq_7band,compressor` and
`sc_verify.py audio OUT.wav --seconds 10 --tol 0.001`.

By hand, the same is:

```sh
soundcraft-cli run --in /abs/Song.scraft \
  --cmd 'mix.insert={"track":"Pad","plugin":"eq_7band","params":{"hpf_on":1,"hpf_freq":120}}' \
  --cmd 'mix.insert={"track":"Pad","plugin":"compressor","params":{"ratio":3}}' \
  --save /abs/out/Song-edit.scraft --bounce /abs/out/range.wav --start 0:20 --end 0:30
```

(`--start/--end` are seconds here, not samples.)

## Folder conversion

```sh
python3 $S/sc_verify.py hash /abs/in > /tmp/in.manifest.json
bash $S/sc_convert.sh /abs/in /abs/out-44k16 --rate 44100 --bit-depth 16 --normalize --dither
for f in /abs/out-44k16/*.wav; do
  python3 $S/sc_verify.py audio "$f" --rate 44100 --depth 16 --peak -0.1 --peak-tol 0.15 >/dev/null || echo "FAIL $f"
done
python3 $S/sc_verify.py hash /abs/in --compare /tmp/in.manifest.json
```

- `--dither` only matters when bit depth drops (24 → 16); it's the default then anyway,
  but saying it makes the intent explicit. `--no-dither` truncates.
- `--normalize` sets the peak to −0.1 dBFS. For a loudness target, bounce from a session
  instead (the bounce reports integrated LUFS) and adjust gain.
- Change the container with `--ext flac` (or aiff).

## Stems

```sh
soundcraft-cli run --in /abs/Mix.scraft --cmd 'file.bounce_stems={"dir":"/abs/stems","bit_depth":24}'
```

Writes `<session> - <track>.wav` per track and returns the file list.

## Markers, strip silence, AudioSuite

```sh
# a marker at 1:05
--cmd 'markers.add={"at":"1:05.000","name":"Ad break"}'
# strip silence needs an edit selection first
--cmd 'edit.select={"tracks":["Voice"],"start":0,"end":"10:00.000"}' \
--cmd 'edit.strip_silence={"threshold_db":-50,"min_length_ms":300,"pad_before_ms":20,"pad_after_ms":80}'
# render a process into clips (destructive to the clip, not the source file)
--cmd 'audiosuite.process={"process":"normalize","tracks":["Voice"],"start":0,"end":"0:30.000"}'
```

Read the result back with `sc_inspect.py session` (clip count after strip silence, clip
names after AudioSuite).

## Single file in, single file out (no session)

`soundcraft-cli convert in.wav out.flac --rate 48000 --bit-depth 24`, then
`soundcraft-cli info out.flac`. Never let OUT equal IN.
