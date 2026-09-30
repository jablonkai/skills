# Raw FCPXML recipes

For what `fcpxml-build.py` doesn't build. Every snippet below was imported into FCP 12.4
without warnings, exported back, and read with `fcpxml-read.py`. Paste the snippets into
a builder output (or an export) and run `fcpxml-verify.py` before `fcp-import.py`.
Keep the DTD child order: anchored items, then markers, then filters
([fcpxml.md](fcpxml.md)).

## Music bed under the whole timeline, with roles and levels

An audio-only asset connected **below** the first clip (`lane="-1"`), running the full
length:

```xml
<asset id="a4" name="music" start="0s" duration="960000/48000s" hasVideo="0" hasAudio="1"
       audioSources="1" audioChannels="2" audioRate="48000">
  <media-rep kind="original-media" src="file:///…/music.wav"/>
</asset>
…
<asset-clip ref="a1" name="clip1" offset="0s" start="0s" duration="4s" audioRole="dialogue">
  <adjust-volume amount="-6dB"/>
  <asset-clip ref="a4" name="music" lane="-1" offset="0s" start="0s" duration="12s" audioRole="music">
    <adjust-volume amount="-12dB"/>
  </asset-clip>
</asset-clip>
```

`adjust-volume` goes before anchored items. The builder does the connected part
(`"connected": [{"clip": "music.wav", "at": 0, "lane": -1}]`); add the level and role by
hand.

## Connected storyline (B-roll sequence above one clip)

```xml
<asset-clip ref="a1" name="clip1" offset="0s" start="0s" duration="4s">
  <spine lane="1" offset="1s" name="B-roll">
    <asset-clip ref="a2" name="b1" offset="0s" start="4s" duration="1s"/>
    <asset-clip ref="a3" name="b2" offset="1s" start="4s" duration="1s"/>
  </spine>
</asset-clip>
```

The storyline's `offset` is in the parent clip's time (`start` + position). Its
children's offsets count **from 0** and play back to back. A non-zero first offset
drifts on every import (gotcha 6).

## Compound clip

```xml
<resources>
  <media id="m1" name="Compound A">
    <sequence format="r1" duration="4s" tcStart="0s" tcFormat="NDF" audioLayout="stereo" audioRate="48k">
      <spine>
        <asset-clip ref="a2" name="c2" offset="0s" start="1s" duration="2s"/>
        <asset-clip ref="a3" name="c3" offset="2s" start="1s" duration="2s"/>
      </spine>
    </sequence>
  </media>
</resources>
…
<ref-clip ref="m1" name="Compound A" offset="4s" duration="4s"/>
```

A `ref-clip`'s `start` (default 0) is a time in the compound's own sequence.
`fcpxml-read.py --expand` lists its contents on the parent timeline.

## Speed change (half speed)

```xml
<asset-clip ref="a1" name="slow" offset="8s" start="0s" duration="4s">
  <timeMap>
    <timept time="0s" value="0s" interp="linear"/>
    <timept time="16s" value="8s" interp="linear"/>
  </timeMap>
</asset-clip>
```

`time` is clip time and `value` is source time. FCP normalises the map to cover the
whole asset (this is its own form on export). A 4 s clip at half speed plays 2 s of
source.

## Standalone title slate on the primary storyline

The builder's `{"title": {...}}` spine item writes this:

```xml
<title ref="e1" name="The End" offset="3610s" start="3600s" duration="2s">
  <text><text-style ref="ts1">The End</text-style></text>
  <text-style-def id="ts1"><text-style font="Helvetica Neue" fontSize="63" fontColor="1 1 1 1"/></text-style-def>
</title>
```

## Other titles

Take the uid from `bash scripts/fcp.sh --templates 'Lower Thirds'` and fill its text
fields in order with `<text>` elements. The "Formal" lower third (two fields) was
verified. Check how many fields a template has by exporting one placed by hand in FCP.
