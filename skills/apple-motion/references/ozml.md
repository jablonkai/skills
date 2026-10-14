# The ozml format (Motion 6.4)

Reverse-engineered from the templates shipped with Final Cut Pro 12.4 / Motion 6.4,
then checked by editing and rendering through Compressor and importing into FCP.
Apple doesn't document it. Treat what isn't listed here as opaque and leave it alone.

## File anatomy

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE ozxmlscene>
<ozml version="5.13">                       <!-- 5.8 in older templates; both load -->
<displayversion>5.7</displayversion>
<factory id="25" uuid="…"><description>Text</description>…</factory>   <!-- one per object type -->
…
<scene>
  <sceneSettings>  width, height, duration (frames), frameRate, NTSC, workingGamut …
  <publishSettings> <version>2</version> <target …/>* </publishSettings>
  <timeRange/> <playRange/> <timemarkerset/> …
  <scenenode name="Project" …/>             <!-- Build In / Build Out live here -->
  <scenenode name="Controls" factoryID=Rig> <!-- rig widgets: checkboxes, popups, sliders -->
  <layer name="Content"> <group …> <scenenode …/> … </group> </layer>
  <group name="Footage"> … drop zone (Title Background) … </group>
</scene>
</ozml>
```

- `factoryID` on an object points at a `<factory>`, whose `<description>` names the
  type: `Text`, `Shape`, `Image`, `Group`, `Widget`, `Rig`, `Rig Behavior`,
  `Sequence Text`, `Style`, `Generator`… The ids are per file, so compare by
  description and never hard-code them.
- Every object (`scenenode`, `layer`, `group`, `style`, `behavior`, `filter`,
  `paragraphStyle`) has a document-unique numeric `id`. Parameters have small ids that
  are only unique among their siblings.
- A parameter at its default is often **absent**, or listed without the component
  that is at its default. Text face colour `Red` is missing when it is 1.0, for
  example. A reader must treat an absent value as the default, and a writer has to
  create it (`ozml.param_at(…, create=…)`).
- Only template identity: the file path. There is no uuid in the file; FCP keys
  templates by their path under Motion Templates.

## Channel paths

A channel is a path of parameter ids below an object, written `./a/b/c`.

| What | Object | Channel |
|---|---|---|
| Text string | text scenenode | `./2/369` (`<text>` child) |
| Font (PostScript name) | the text's `<style>` | `./83` (`<font>` child; `<defaultFont>` is the fallback) |
| Size | `<style>` | `./3` |
| Face colour | `<style>` | `./14/16` → Red `1`, Green `2`, Blue `3` |
| All caps | `<style>` | `./12` |
| Drop shadow on/off | `<style>` | `./21` |
| Shape fill colour | shape scenenode | `./2/353/113/111` → R/G/B |
| Shape fill opacity | shape scenenode | `./2/353/113/141` |
| Colour Solid generator colour | generator scenenode | `./2/1/1` |
| Opacity | any layer | `./1/200/202` |
| Position | any layer | `./1/100/101` (X `1`, Y `2`) |
| Scale | any layer | `./1/100/105` |
| Widget value (checkbox 0/1, popup index, slider) | widget scenenode | `./2/100` |
| Build In / Build Out | Project | `./2/101`, `./2/102` |
| Graphics HDR Level | Project | `./1/103` |

`motn-read.py` resolves every published target, so read a template first and copy
the paths it reports, not guesses.

## Text layers

```xml
<scenenode name="Headline Text" id="3296674397" factoryID="25" version="5">
  <paragraphStyle id="…"> …
  <style name="Style" id="3296674399" factoryID="2">
    <parameter name="Font" id="83"><font>HelveticaNeue-Bold</font><defaultFont>Helvetica</defaultFont></parameter>
    <parameter name="Size" id="3" default="48" value="170"/>
    <parameter name="Face" id="14"> <parameter name="Color" id="16"> R/G/B … </parameter> </parameter>
  </style>
  <styleRun style="3296674399" offset="0" length="13"/>
  …
  <parameter name="Object" id="2"> <parameter name="Text" id="369"><text>Headline Text</text></parameter> …
```

- `styleRun` gives which style covers which characters: offset/length in **UTF-16
  code units**, so an emoji counts 2. Verified with "Run 🏃 fast 🏃 end".
  `motn-edit.py --text` collapses the runs into one covering the new text.
- A line break is a literal newline in `<text>`. One text layer can hold several
  lines.
- **FCP text-field order is document order of the text scenenodes.** The first
  `<text>` of an FCPXML title fills the first one.
- FCP lets the editor type into every text layer without publishing it. Publishing
  `./2/369` as well adds a text box to the inspector.

## Colours

Values are **sRGB-encoded floats 0–1** in the template's working space
(`sceneSettings/workingGamut` 1 = Rec. 709). `#00ADEF` is written 0 / 0.678 / 0.937.
Measured renders: (0,1,0) → (0,255,0), (1,0,0) → (255,2,1), #1A1A1A → 24, 0.5 grey → 116,
#00ADEF → (0,163,236). The output is the sRGB value **linearised, then encoded with
Apple's Rec. 709 gamma 1/1.961** (not the piecewise BT.709 OETF, which misses dark
tones by half). `motn-render.py --expect` predicts exactly that. Stock templates
contain wide-gamut values outside 0–1 (e.g. 1.027 / 0.858 / −0.289).

## publishSettings

```xml
<publishSettings>
  <version>2</version>
  <target object="10972" channel="./2/353/113/111" name="Backplate Color"/>
  <target object="3296674399" channel="./14/16" name="Name Color"/>
</publishSettings>
```

FCP shows these, **in this order**, under *Published Parameters* in the Title
inspector, with the right control for the type: colour well, font popup with weight,
checkbox, popup, slider. Adding a `<target>` is enough. The parameter itself must
exist, so the edit script creates a missing colour param. Verified in FCP 12.4: "Name
Color" and "Role Font" added by the script appeared with working controls.

## Rigs

A rig is a `Controls` scenenode (factory `Rig`) holding `Widget` scenenodes (popup,
checkbox, slider). Each driven channel has a `Rig Behavior` attached to the driven
object:

```xml
<behavior name="Rig Behavior" factoryID=…>
  <channelBehavior affectingFactory="…" affectingChannel="./2/323"/>
  <parameter name="Affecting Object (Hidden)" id="199" value="3296674397"/>  <!-- driven object -->
  <parameter name="Widget" id="200" value="10002"/>                           <!-- driving widget -->
  <parameter name="Snapshots" id="202"> one value per widget state … </parameter>
</behavior>
```

The widget's own `./2/101` list maps each option (Value) to a snapshot id. ColorWay
option 2 is snapshot 3 in the Clean styles, for example. The snapshot of an option
is applied when the editor picks that option in FCP, and a checkbox's state also
applies at render (Backplate off hides the plate even with opacity 1). Measured:
after `--set "ColorWay=3"` the render shows option 3's colours, not the edited value.
So an edit to a rigged channel has to go into the parameter **and** the snapshot of
the widget's current option, which `motn-edit` does by default. Alternatively,
`--unrig` deletes the Rig Behavior for that channel. Rigged text-style channels appear in
two forms: on the style (`./14/16`) or on the text layer via its style list
(`./5/<style id>/14/16`). Both are checked. Common rigs: the lower-third "Widget"
(margins, aspect), "Backplate" (opacity), "ColorWay" (colours), "FontOption" (fonts,
which can only be `--unrig`ged).

## Media

Stock templates reference built-in media by name (`<pathURL>Drop Zone.tiff</pathURL>`),
and the app resolves it. User templates keep media in a `Media/` folder next to the
file (`<relativeURL>Media/Drop_Zone.png</relativeURL>`). `motn-find --copy` and
`motn-install` carry that folder along.

## Rendering

`Compressor -jobpath file:///abs/path.moti -settingpath X.compressorsetting -locationpath out.mov`
renders any template type headless, provided Motion is installed. Titles and effects
render over the drop-zone placeholder (a grey square with an arrow), and the length is
the template's own (`sceneSettings/duration`). The built-in "H264 Proxy half size"
setting renders a 10 s 4K title in about 15 s.
