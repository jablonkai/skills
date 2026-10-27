# Recipes

`S=<skill>/scripts`. Paths in steps must be absolute. Each recipe saves to a new
`.fcproj`, reads it back, and exports last. Probe the media first
(`filmcraft-cli probe clip.mov`) so the sequence matches the footage's size and rate.

## 1. Rough cut: clips on V1, opening title, cross dissolve, H.264 1080p

`cut.jsonl`:

```jsonl
{"id":"file.newProject","params":{"name":"Rough cut"}}
{"id":"file.import","params":{"paths":["/abs/a.mov","/abs/b.mov","/abs/c.mov"]},"as":"imp"}
{"id":"file.newSequence","params":{"name":"Rough cut","width":1920,"height":1080,"fps":25},"as":"seq"}
{"id":"timeline.place","params":{"items":"$imp.items","track":"V1","seconds":0},"as":"cut"}
# dissolve over the cut between clip 1 and clip 2: the in-edge of the 2nd clip's video
{"id":"sequence.applyVideoTransition","params":{"clip":"$cut.placed[1][0]","effect":"cross_dissolve","frames":25,"edge":"in"}}
{"id":"graphics.newText","params":{"text":"Opening Title","seconds":3,"time":0,"track":1,"size":120},"as":"title"}
{"id":"graphics.align","params":{"clip":"$title.clip","layers":[0],"align":"hcenter"}}
{"id":"graphics.align","params":{"clip":"$title.clip","layers":[0],"align":"vcenter"}}
```

```sh
python3 $S/fc_run.py --out ~/Movies/rough.fcproj cut.jsonl
python3 $S/fc_verify.py seq ~/Movies/rough.fcproj '{"tracks":{"V1":[{"name":"a.mov","start":0},{"name":"b.mov"},{"name":"c.mov"}],"V2":[{"name":"Opening Title","start":0}]},"transitions":[{"effect":"cross_dissolve","at":100}]}'
filmcraft-cli --project ~/Movies/rough.fcproj render --seconds 1 --out /tmp/title.png --scale 0.25   # look at it
python3 $S/fc_export.py ~/Movies/rough.fcproj --range entire ~/Movies/rough.mp4="High Quality 1080p HD"
```

A transition shortens nothing: the clips stay butted, and the dissolve is centred on the
cut (`frames` 25 → 12 frames each side). Use `at` = the cut frame in the verify spec. To
trim a clip before placing it, give `timeline.place` `sourceIn` and `duration` in ticks
(seconds × 254016000000), one `place` per clip, with `seconds` set to where the previous
one ends.

## 2. B-roll on V2 over the interview

```jsonl
{"id":"timeline.place","params":{"item":7,"track":"V2","seconds":12.0,"sourceIn":508032000000,"duration":1270080000000,"audio":false}}
```

That places 5 s of item 7, starting 2 s into the source, at 12 s on V2, without its sound.
Find item ids with `inspect project`. Do B-roll **before** titles, or give titles an
explicit `track` (a 0-based index: 1 = V2), because a title takes the lowest free track.

## 3. Markers from a timecode list, then the in/out range as ProRes

`notes.csv`:

```csv
timecode,name,comment,color
00:00:02:00,Intro,,Yellow
00:00:07:12,Cut here,tighten,red
```

```sh
python3 $S/fc_markers.py proj.fcproj notes.csv > markers.jsonl      # exits 1 if one is off the end
cat >> markers.jsonl <<'EOF'
{"id":"markers.markIn","params":{"timecode":"00:00:02:00"}}
{"id":"markers.markOut","params":{"timecode":"00:00:10:00"}}
EOF
python3 $S/fc_run.py --project proj.fcproj --out proj-marked.fcproj markers.jsonl
python3 $S/fc_export.py proj-marked.fcproj --range inOut proj-inout.mov="Apple ProRes 422"
```

The out frame is included, so 2 s → 10 s at 25 fps is 201 frames (8.04 s). If the user
means "up to but not including 10 s", mark out one frame earlier (`frame` = 249). Say
which one you did. Keep the source project unchanged unless the user asked to edit it in
place (`--overwrite` with the same path).

## 4. Several deliverables in one go

```sh
python3 $S/fc_export.py proj.fcproj --range entire \
  out/yt.mp4="YouTube 1080p Full HD" \
  out/preview.mp4="Match Source – Adaptive Medium Bitrate@0.5" \
  out/master.mov="Apple ProRes 422 HQ"
```

Preset names contain an en dash (`Match Source – …`). Copy them from
`filmcraft-cli export --list-presets`. `fc_export.py` suggests the closest name when one
doesn't match. A half-scale version of a fixed-size preset (`"YouTube 1080p Full HD@0.5"`)
gets an explicit 960×540.

## 5. Image sequence, audio only, other sequence

```sh
python3 $S/fc_export.py proj.fcproj --range 0-2 frames/shot.png=fmt:png     # numbered stills
python3 $S/fc_export.py proj.fcproj mix.wav="Waveform Audio 48 kHz 24-bit"
python3 $S/fc_export.py proj.fcproj --sequence "Teaser" teaser.mp4="Vimeo 1080p Full HD"
```

## 6. Edit an existing timeline

Inspect, then act on clip ids from the read-back:

```jsonl
{"id":"timeline.razor","params":{"time":762048000000,"track":"V1"}}
{"id":"timeline.trim","params":{"clip":15,"edge":"out","mode":"ripple","deltaFrames":-12}}
{"id":"edit.rippleDelete","params":{"clips":[18,19]}}
{"id":"clip.speedDuration","params":{"clips":[21],"speed":50,"ripple":true}}
```

A razor creates new clip ids. Run `fc_verify.py show` again before addressing the pieces.

## 7. Sequence matching a clip

`{"id":"file.newSequence","params":{"name":"Interview","fromItem":1}}` creates a sequence
with that clip's size and rate, places the clip on V1/A1 and makes the sequence active.
