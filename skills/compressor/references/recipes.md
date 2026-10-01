# Recipes

`H=scripts`, with paths relative to the skill directory. Every recipe ends with
`cmp-verify.py`. Report its lines, not just "done".

## Card dump → ProRes Proxy next to the originals

```bash
python3 $H/cmp-encode.py /Volumes/Card/DCIM --recursive \
    --setting "Apple ProRes 422 Proxy" --suffix _proxy --summary /tmp/proxy.json
python3 $H/cmp-verify.py --summary /tmp/proxy.json
```

Each `clip.mp4` gets a `clip_proxy.mov` beside it at full resolution. Re-running skips
finished proxies and doesn't treat `*_proxy.mov` as new sources. For smaller proxies, use
`"ProRes Proxy half size"` and the frame size halves (verify checks that too). If the card
is read-only, write elsewhere with `--out-dir ~/Proxies/Card01 --recursive`, which mirrors
the subfolders.

## One master → several deliverables

```bash
python3 $H/cmp-encode.py Promo_Master.mov --out-dir deliverables \
    --setting "HD 1080p" --suffix _web_h264 \
    --setting "Apple Devices 4K (HEVC 8-bit)" --suffix _hevc \
    --setting "Apple ProRes 422 HQ" --suffix _archive \
    --summary deliverables/summary.json
python3 $H/cmp-verify.py --summary deliverables/summary.json --audio
```

That's one batch with three jobs. HD 1080p and Apple Devices 4K **fit within** their size
and never upscale, so a 1080p master stays 1080p.

## Custom setting, then reuse

```bash
python3 $H/cmp-setting-new.py --from "Apple Devices 4K (HEVC 8-bit)" \
    --name "HEVC 720p Review" --size 1280x720
python3 $H/cmp-settings.py --user                      # shows it, with "1280x720"
python3 $H/cmp-encode.py cuts/ --setting "HEVC 720p Review" --out-dir review \
    --summary review/summary.json
python3 $H/cmp-verify.py --summary review/summary.json --size 1280x720
```

`--size` is exact: every output is 1280×720 whatever the source's aspect ratio. Use
`--fit 1280x720` to keep the aspect ratio. A setting someone shares with you (`X.compressorsetting`) works directly as
`--setting /path/X.compressorsetting`. Copy it into the custom folder if you want to use
it by name.

## Image sequence

```bash
python3 $H/cmp-encode.py shot010.mov --setting "TIFF Image Sequence" --out-dir frames
# → frames/shot010_tiff-image-sequence/frame-000000.tiff …
python3 $H/cmp-verify.py --summary …   # frame count = duration × fps
```

## Long or unattended batches

```bash
python3 $H/cmp-encode.py footage/ --recursive --setting "Apple ProRes 422 LT" \
    --out-dir /Volumes/Raid/LT --summary /Volumes/Raid/LT/summary.json --timeout 7200
# exit 124 → stopped at the limit: run the same command again to continue
```

You can also submit and return straight away, then check later:

```bash
python3 $H/cmp-encode.py … --no-wait --summary s.json   # prints the batch id
bash $H/cmp.sh --status <batch-id>                       # JSON status, once
bash $H/cmp.sh --kill <batch-id>                         # cancel; partial files removed
```

The batch also appears in the Compressor app's Activity window under the `--batch-name`.

## Find a setting

```bash
python3 $H/cmp-settings.py                 # everything, grouped like the sidebar
python3 $H/cmp-settings.py --codec apco    # every ProRes Proxy variant
python3 $H/cmp-settings.py youtube         # by name, group or path fragment
python3 $H/cmp-settings.py --resolve "HD 720p" --json
```
