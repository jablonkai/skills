# Compressor settings

## Where settings live

| Kind | Location |
|---|---|
| Built-in (5.4: 94 files in 21 groups) | `/Applications/Compressor.app/Contents/PlugIns/Compressor/CompressorKit.bundle/Contents/Frameworks/Compressor.framework/Versions/A/Frameworks/StompUI.framework/Versions/A/Resources/BuiltInSettings/<Group>/` |
| Display names of built-ins | `…/Frameworks/StompTypes.framework/Versions/A/Resources/en.lproj/Localizable.strings` (key = `<setting name="…">` or `<nameKey>`) |
| Custom (the app's "Custom" section) | `~/Library/Application Support/Compressor/Settings/*.compressorsetting` |

`python3 scripts/cmp-settings.py` lists all of them. `--resolve NAME` gives the path. The
built-in groups match the sidebar: Apple Devices, Audio Files, Create Blu-ray, Create DVD,
HTTP Live Streaming (H.264/HEVC), Immersive Streaming, MPEG Files, MXF, Motion Graphics,
Podcasting, ProRes, Proxy Settings, Publish to YouTube/Vimeo/Facebook, Social Platforms
HEVC, Uncompressed, Website Sharing. The Blu-ray, DVD and HLS groups also contain
`setting-group-*.group` files that bundle several settings with a job action. Only their
individual settings files were considered here. Group-level output (disc images, HLS
packages) through the CLI is untested.

## Common built-ins (5.4)

| Display name | Ext | Video | Size |
|---|---|---|---|
| Apple ProRes 422 Proxy / LT / 422 / HQ | mov | apco / apcs / apcn / apch | source |
| Apple ProRes 4444 / 4444 XQ | mov | ap4h / ap4x | source |
| ProRes Proxy half / quarter / eighth size | mov | apco | 50 / 25 / 12.5 % |
| H264 Proxy … size, HEVC Proxy … size | mov | avc1, hvc1 | 50 / 25 / 12.5 % |
| HD 1080p, HD 720p, Up to 4K (Website Sharing) | mov | avc1 | fit 1920×1080 / 1280×720 / 3840×2160 |
| Apple Devices HD (Best Quality / Most Compatible) | m4v | avc1 | fit |
| Apple Devices 4K (HEVC 8-bit / 10-bit) | m4v | hvc1 | fit 3840×2160 |
| HEVC 8-bit 420 / 10-bit 420 (Social Platforms HEVC) | mp4 | hvc1 | fit 4096×2304 |
| Uncompressed 8-bit 422 / 10-bit 422 | mov | 2vuy / v210 | source |
| TIFF Image Sequence, OpenEXR Image Sequence | folder | tiff / exr | source |
| Apple ProRes … (MXF group) | mxf | ProRes (MTCompression…) | source |

## Setting file format

Each setting is one XML document:

```xml
<setting name="proRes422ProxyName">            <!-- name or l10n key; custom: %-encoded literal -->
  <description>…</description><nameKey>…</nameKey><descriptionKey>…</descriptionKey>
  <encoder name="QT">                           <!-- QT, MPEG4, H264iPod, MXF, TIFF, CoreAudio, … -->
    <file-extension>mov</file-extension>
    <audio-encode name="QT" isEnabled="yes">…<codec-type>lpcm</codec-type>…</audio-encode>
    <video-encode name="QT" isEnabled="yes">
      <bounds width="-100" height="-100" pixelAspect="0"/>
      <automatic … width="-100" height="-100" frame-rate="-100" …/>   <!-- the size that counts -->
      <codec-type>apco</codec-type>                                    <!-- FourCC -->
      <data-rate>0</data-rate> …
    </video-encode>
  </encoder>
  <filter-set/>
</setting>
```

MXF settings name the codec as `<codec>MTCompressionPRORES422PROXY</codec>` instead of a
FourCC. Image-sequence settings use `<encoder name="TIFF">` with `file-extension` `tiff` or
`exr` (`gif` is an animated GIF, a single file).

### Frame size: `<automatic width height>`

| Values | Meaning | Example setting |
|---|---|---|
| `-100 -100` | source size | Apple ProRes 422 Proxy |
| `-P -P` | P % of the source (P may be fractional) | `-50 -50` half size, `-12.5 -12.5` eighth |
| `-W H` | scale down to fit inside W×H, keep the aspect ratio, never upscale | `-1920 1080` HD 1080p |
| `W H` | exactly W×H | written by `cmp-setting-new.py --size` |

`<bounds>` alone is ignored for sizing (tested). `cmp-setting-new.py` writes both: exact
sizes go into both elements, and fit/percent sizes go into `<automatic>` with `<bounds>`
left at `-100`.

## Custom settings

`cmp-setting-new.py --from BASE --name NAME [--size WxH | --fit WxH | --scale PCT]`:

- copies BASE's XML, so its codec, container, audio and quality are kept
- sets `<setting name>`, `<nameKey>`, `<description>` and `<descriptionKey>` to the
  percent-encoded literal name, the way Compressor stores literal names
  (`H264%20Proxy%20half%20size`)
- checks that the result is well-formed XML and writes it atomically to the custom folder
  (or `--out-dir`)

For anything else (bitrate, frame rate, filters, colour, audio layout), build the setting
in the Compressor app, save it, and use it by name. Hand-editing those XML fields isn't
verified (see [gotchas.md](gotchas.md)).
