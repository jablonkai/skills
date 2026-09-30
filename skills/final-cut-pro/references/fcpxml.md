# FCPXML subset used by the skill

Checked against `FCPXMLv1_14.dtd` bundled with Final Cut Pro 12.4
(`Contents/Frameworks/Interchange.framework/Versions/A/Resources/`, which holds DTDs
1.0–1.14) and against what FCP 12.4 writes on File ▸ Export XML. FCP 12.4 exports
1.14 (default), 1.13 or 1.12.

## Document skeleton

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE fcpxml>
<fcpxml version="1.14">
  <import-options>                                  <!-- optional, first child -->
    <option key="library location" value="file:///Users/me/Movies/X.fcpbundle/"/>
    <option key="copy assets" value="0"/>           <!-- 0: reference media in place -->
    <option key="suppress warnings" value="0"/>     <!-- 0: show the warnings dialog -->
  </import-options>
  <resources> format, asset, effect, media … </resources>
  <library>
    <event name="…">
      <project name="…">
        <sequence format="r1" duration="…" tcStart="3600s" tcFormat="NDF|DF"
                  audioLayout="stereo" audioRate="48k">
          <spine> … primary storyline … </spine>
        </sequence>
      </project>
    </event>
  </library>
</fcpxml>
```

`<fcpxml>` content order: `import-options?, resources?, (library | event* | clips*)`.
Without `library location`, FCP shows an "Open Library — Which library do you want to
import X into?" chooser. Verified with an existing, open library; point it at a library
that exists. `.fcpxmld` (what FCP 12.4 exports) is a folder holding `Info.fcpxml`.
FCP opens both forms.

## Resources

| Element | Key attributes | Notes |
|---|---|---|
| `format` | `id`, `name`, `frameDuration`, `width`, `height`, `colorSpace` | Names: `FFVideoFormat1080p25`, `FFVideoFormat1080p2997`, `FFVideoFormat720p50`, `FFVideoFormat3840x2160p25`. FCP writes `frameDuration="100/2500s"` for 25p and `1001/30000s` for 29.97. |
| `asset` | `id`, `name`, `start`, `duration`, `hasVideo`, `hasAudio`, `format`, `videoSources`, `audioSources`, `audioChannels`, `audioRate` | Holds `<media-rep kind="original-media" src="file:///…"/>`. The `src` is an absolute, percent-encoded file URL. `start` is the media's timecode origin (0s without embedded timecode). |
| `effect` | `id`, `name`, `uid` | Titles, generators and transitions (below). |
| `media` | `id`, `name` + `<sequence>` | A compound clip, used by `ref-clip`. `<multicam>` for multicam. |

FCP adds to assets on export: `uid`, `sig`, a `<bookmark>` (a base64 security-scoped
bookmark, which can be dropped when editing) and `<metadata>`. Resources may appear in
any order before use. FCP writes formats and assets interleaved.

### Effect uids verified on FCP 12.4

| Effect | uid |
|---|---|
| Basic Title | `.../Titles.localized/Bumper:Opener.localized/Basic Title.localized/Basic Title.moti` |
| Basic Lower Third | `.../Titles.localized/Lower Thirds.localized/Basic Lower Third.localized/Basic Lower Third.moti` |
| Formal (lower third) | `.../Titles.localized/Lower Thirds.localized/Formal.localized/Formal.moti` |
| Cross Dissolve | `FxPlug:4731E73A-8DAC-4113-9A30-AE85B1761265` |
| Audio Crossfade | `FFAudioTransition` (FCP adds it to transitions on its own) |

`...` stands for the template root inside the app
(`Contents/PlugIns/MediaProviders/MotionEffect.fxp/Contents/Resources/Templates.localized`
or `PETemplates.localized`). Basic Title and Basic Lower Third live in `PETemplates`.
`bash scripts/fcp.sh --templates RE` lists every installed title and transition with
its uid. Many names repeat across categories (15 titles are called "Bug"), so the
category is part of the identity.

## Story elements

| Element | Where | Timing attributes |
|---|---|---|
| `spine` | sequence (primary), or anchored in a clip with `lane` (connected storyline) | `offset` (anchored only) |
| `asset-clip` | spine or anchored (`lane`) | `offset`, `start` (source), `duration` |
| `gap` | spine | `offset`, `start` (FCP uses 3600s), `duration` |
| `title` | spine or anchored | `offset`, `start` (3600s), `duration` |
| `transition` | spine, between two items | `offset` (= cut − duration/2), `duration` |
| `ref-clip` | compound instance | `offset`, `start` (in the compound's time), `duration` |
| `sync-clip`, `mc-clip`, `clip`, `video`, `audio` | read by fcpxml-read.py | as above |

- `offset` is in the **parent's** time: sequence time (starting at `tcStart`) for the
  primary spine, and the parent clip's source time for anchored items. An item anchored
  to a clip with `start="1s"` at 2 s into that clip has `offset="3s"`.
- `lane`: positive above, negative below the primary storyline. Anchored items attach to
  one parent clip and move with it.
- A connected storyline (`<spine lane="1" offset=…>`) is its own time space: its
  children's offsets start at `0s`.
- `srcEnable="video|audio"`, `enabled="0"`, `audioRole="dialogue|music|effects"`.

### Child order inside a clip (DTD)

`note?, conform-rate?, timeMap?, adjust-*…, (anchored items)*, (marker | chapter-marker
| rating | keyword | analysis-marker)*, audio-channel-source*, filter-video*,
filter-audio*, metadata?`. A title must come before the clip's markers. A marker after
a filter fails DTD validation. `fcpxml_common.insert_child` keeps this order.

### Titles

```xml
<title ref="e1" lane="2" offset="37/25s" name="Kovács Anna – Race director" start="3600s" duration="3s">
  <text><text-style ref="ts1">Kovács Anna</text-style></text>
  <text><text-style ref="ts2">Race director</text-style></text>
  <text-style-def id="ts1"><text-style font="Helvetica Neue" fontSize="50" fontColor="1 1 1 1"/></text-style-def>
  <text-style-def id="ts2"><text-style font="Helvetica Neue" fontSize="36" fontColor="1 1 1 1"/></text-style-def>
</title>
```

Each `<text>` fills the template's next text field in order (a lower third has two).
`text-style-def` ids are document-wide ids, so they must not collide with resource ids.
FCP adds `fontFace="Regular"` and a few `<param>`s on export.

### Markers and keywords

```xml
<marker start="2s" duration="1/25s" value="note" [note="…"] [completed="0|1"]/>   <!-- completed = to-do -->
<chapter-marker start="1s" duration="1/25s" value="Chapter 1" posterOffset="0s"/>
<keyword start="1s" duration="6s" value="intro, wide"/>
```

`start` is in the owning clip's local time (for a gap: 3600s + position). FCP draws
markers on the owning clip, and they move with it.
