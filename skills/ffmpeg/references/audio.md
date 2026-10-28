# Audio jobs

## Loudness normalization (EBU R128)

Use `ff_loudnorm.py IN -o OUT --I -16 --TP -1.5`. What it does by hand:

1. Measure: `ffmpeg -i IN -map 0:a:0 -af loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json -f null -`
   → read `input_i input_tp input_lra input_thresh target_offset` from the JSON
   block at the end of stderr.
2. Apply: `-af loudnorm=I=-16:TP=-1.5:LRA=11:measured_I=…:measured_TP=…:measured_LRA=…:measured_thresh=…:offset=…:linear=true`
   plus **`-ar 48000`** (loudnorm outputs 192 kHz), with `-c:v copy` so the video
   is untouched.
3. Verify: `-af ebur128=peak=true -f null -` → `I:` and `Peak:` in the summary.

| Target | I | TP |
|---|---|---|
| Podcasts, YouTube, most streaming | −16 (stereo), −19 (mono) | −1 to −1.5 |
| Spotify / Apple Music | −14 / −16 | −1 |
| EBU R128 broadcast | −23 | −1 |
| US broadcast (ATSC A/85) | −24 | −2 |

Linear mode applies one gain and keeps the dynamics. It works only when
`input_tp + (I − input_i) ≤ TP`. Otherwise loudnorm switches to dynamic mode
(limiter and AGC), which is fine for speech and less so for music. If the result
must be linear, lower the target or accept a lower true-peak headroom. Very short
files (< 3 s) can't be measured reliably.

Peak normalization only (no loudness model): measure with `volumedetect`, then
`volume=XdB`.

## Extract, replace, mix

```
ffmpeg -i in.mp4 -map 0:a:0 -c:a copy out.m4a                    # lossless when the codec fits the container
ffmpeg -i in.mp4 -map 0:a:0 -c:a pcm_s16le out.wav                # for editing/analysis
ffmpeg -i video.mp4 -i new.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -shortest out.mp4
ffmpeg -i v.mp4 -i music.mp3 -filter_complex "[1:a]volume=0.25[m];[0:a][m]amix=inputs=2:duration=first:normalize=0[a]" -map 0:v -map "[a]" -c:v copy out.mp4
```
`ff_recipe.py extract-audio` / `replace-audio` pick copy versus re-encode based on
the container. Ducking music under voice:
`[m][0:a]sidechaincompress=threshold=0.05:ratio=8:attack=20:release=400[duck]`
(the first input is the one compressed, the second is the key), then `amix`.

## Sync and cleanup

- Shift audio later by 200 ms: `-itsoffset 0.2 -i in.mp4 -i in.mp4 -map 1:v -map 0:a -c copy`,
  or `-af adelay=200|200`. Earlier: `-af atrim=start=0.2,asetpts=PTS-STARTPTS`.
- Remove silence at the ends: `silenceremove=start_periods=1:start_threshold=-50dB:stop_periods=1:stop_threshold=-50dB`.
- Find silences: `-af silencedetect=n=-45dB:d=0.8 -f null -`.
- Hum / noise: `highpass=f=80`, `afftdn=nf=-25`, `anlmdn`. Voice EQ: `equalizer=f=3000:t=q:w=1:g=3`.
- Fades: `afade=t=in:d=1,afade=t=out:st=58:d=2`.
- Split stereo channels: `-filter_complex "channelsplit=channel_layout=stereo[l][r]" -map "[l]" l.wav -map "[r]" r.wav`.
