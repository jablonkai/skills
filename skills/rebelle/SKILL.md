---
name: rebelle
description: 'Remote-control Rebelle (Escape Motions'' natural-media painting app) and Rebelle Motion IO with JSON events: paint real watercolour, oil, ink and pencil strokes programmatically, drive a live Rebelle Pro session over its WebSocket server, or batch-render painted animation frames and turn them into video. Use whenever the user wants to paint, sketch or generate artwork in Rebelle, script or automate Rebelle, produce a watercolour/ink/oil rendering of something, animate a painting frame by frame, render a .reb artwork, or says "Rebelle", "Motion IO", "paint this in watercolour", "make a painted animation" — even if they don''t mention scripting. Also covers Hungarian phrasings like "fesd meg Rebelle-ben", "akvarell kép", "festett animáció", "vezéreld a Rebelle-t". Not for photo editing or vector work (use Affinity) or for keyframed motion graphics (use Cavalry).'
summary: "remote-control Rebelle and Rebelle Motion IO with JSON events — live WebSocket painting in Rebelle Pro, batch-rendered painted animation frames, and visual verification through canvas exports"
category: design-automation
risk: medium
tags:
    - rebelle
    - painting
    - watercolor
    - animation
    - escape-motions
---

# Rebelle Control

Rebelle simulates real paint — water flows, pigments granulate, impasto catches light —
and both builds installed here take the **same JSON event vocabulary**:

| Build | How you drive it | Best for |
|---|---|---|
| `/Applications/Rebelle 8.app` (**Pro**) | WebSocket server, live | painting into the app the user is watching, exploring, one-off artwork |
| `/Applications/Rebelle 8 Motion IO.app` | `-batch-json` file, headless-ish | reproducible renders, animation frame sequences, data-layer in/out |

Start live unless the task is an animation or needs data layers: the round-trip is
seconds instead of a minute, and you can look at the canvas whenever you want.

- [references/json-events.md](references/json-events.md) — the full event vocabulary (both paths). Read before writing anything beyond simple strokes.
- [references/websocket.md](references/websocket.md) — live protocol, the undocumented `cmd` API, what is *not* supported live.
- [references/batch.md](references/batch.md) — Motion IO CLI, data layers, frames→video, licensing.
- [references/assets.md](references/assets.md) — resolving brush preset and paper names (they fail silently if wrong).
- [scripts/rebelle_ws.py](scripts/rebelle_ws.py) — dependency-free WebSocket client (library + CLI).
- [scripts/rebelle_events.py](scripts/rebelle_events.py) — builds event files; encodes the batch frame rules and the stroke geometry helpers.
- [scripts/rebelle-batch.sh](scripts/rebelle-batch.sh) — runs a batch and returns when it is actually done.

## Path A — live, over the WebSocket

Rebelle only listens when it was launched with the flag, and it does not have to be
restarted for each task — check first, ask second:

```bash
python3 scripts/rebelle_ws.py --ping     # prints e.g. "Rebelle 8 Pro here"
```

If nothing answers, ask the user before launching: a fresh instance is a new blank
document, and painting goes into whatever artwork is open, with no undo grouping.

```bash
"/Applications/Rebelle 8.app/Contents/MacOS/Rebelle 8" \
  -websocket-server-enable \
  -websocket-allowed-ip-addresses "::ffff:127.0.0.1,127.0.0.1" &
```

The allowlist is matched against the socket's literal peer address, and a local client
arrives as the IPv6-mapped `::ffff:127.0.0.1` — listing plain `127.0.0.1` alone refuses
your own connection (`... refused` in Rebelle's output).

Then drive it from Python:

```python
from rebelle_ws import Rebelle
from rebelle_events import catmull_rom, taper

with Rebelle() as r:
    r.event({"event_type": "NEW_ARTWORK", "width": 1200, "height": 800, "units": "px"})
    r.event({"event_type": "SET_BRUSH", "tool": "WATERCOLOR", "preset": "Watercolor/Round",
             "size": 55, "water": 70, "opacity": 90, "paint_type": "PAINT",
             "color": {"r": 30, "g": 90, "b": 200}})
    r.stroke(catmull_rom([(150, 450), (400, 250), (800, 600), (1050, 320)]),
             pressure=taper(0.95))
    r.event({"event_type": "SIMULATION", "repeats": 20})   # let the water spread
    r.sync()                                   # wait until Rebelle is really finished
    r.export("/tmp/check.png")                 # then Read the PNG
```

`sync()` sends a `BOOKMARK` and waits for the echo. Nothing else acknowledges anything,
so without it you are exporting a canvas that is still mid-stroke.

`SAVE`/`LOAD` events are rejected live — `export()` (`cmd: export_canvas`) is the only
way out, and it writes the composited canvas exactly as the user sees it.

## Path B — batch rendering with Motion IO

```bash
python3 build_painting.py                  # writes events.json via rebelle_events.Doc
bash scripts/rebelle-batch.sh events.json out/
```

Motion IO never exits by itself on macOS and reports progress only as
`batch frame end: i/n` on stdout, so always go through `rebelle-batch.sh` — it waits for
`i == n`, surfaces the `ERROR:` lines, then stops the app.

One frame = one output image + one implicit fluid-simulation step. That makes animation
natural: paint a bit, close the frame, repeat.

```python
from rebelle_events import Doc, catmull_rom, taper

d = Doc(1200, 800, paper={"preset": "Handmade/HM01 Handmade", "deckled_edges": True})
d.set_brush("WATERCOLOR", "Watercolor/Round", size=55, water=70, opacity=90,
            paint_type="PAINT", color=(30, 90, 200))
d.stroke(catmull_rom([(150, 450), (400, 250), (800, 600), (1050, 320)]), pressure=taper())
d.frame()                    # one animation frame ends here
d.simulation(15, frames=20)  # 20 frames of the paint spreading and drying
d.write("events.json")
```

### The frame rules that make batch work

`Doc` applies these already; hand-written JSON must too, or the run wedges forever or
loses work silently. Motion IO is still finishing its own startup while it reads the
first frames, and these are the shapes that survive it:

1. **Frame 0 is a warm-up that must load a brush.** A `SET_BRUSH` there is enough real
   work to let startup complete. A frame with only a `BOOKMARK` — or an empty frame —
   deadlocks before a single frame is processed.
2. **`NEW_ARTWORK` goes in frame 1, never frame 0.** In frame 0 it is dropped without a
   word and you silently get Rebelle's default A4 canvas (2339×1654 at 200 dpi).
3. **Something must follow `NEW_ARTWORK` in its frame** (another `SET_BRUSH` does).
   A frame that ends right after `NEW_ARTWORK` deadlocks.
4. **Don't paint in the `NEW_ARTWORK` frame** — the canvas re-init wipes it. Start
   painting in the next frame (`Doc.first_content_frame` is where real content begins;
   pass it to `ffmpeg -start_number`).

If you must skip `NEW_ARTWORK` entirely, `-input artwork.reb` opens an existing artwork
and is the sturdiest way to fix a canvas size — but the user has to have saved one.

## Painting that looks painted

- **Coordinates are canvas pixels, y down from the top-left**, and may go outside the
  canvas — start and end strokes off-canvas for edge-to-edge washes.
- **A `POINTER_MOVE` draws the previous segment**, so a stroke must end with a release
  at the last move's position. `stroke()`/`stroke_events()` handle it; hand-written
  events routinely lose their final segment to this.
- **Sample paths densely.** Rebelle interpolates between points, so four points give a
  smooth-but-generic curve; `catmull_rom()` at ~16 points per segment lets the brush
  texture, spacing and pressure actually show.
- **Vary pressure.** A constant 0.9 reads as machine-drawn. `taper()` thins both ends,
  `ramp()` builds up — that alone is most of the difference between a plot and a stroke.
- **Wet media need simulation time.** Water only spreads on simulation steps: paint,
  then spend frames (or `{"event_type":"SIMULATION","repeats":N}`) letting it bloom, and
  `DRY`/`FAST_DRY` before painting a layer that should not bleed into the one below.
- **Build in layers of colour**, as in real painting: pale washes first, `DRY`, then
  darker glazes over them. `SET_ENGINE_PARAMS` controls absorbency, drips, granulation.
- Pick brushes by simulation, not by name: `WATERCOLOR` for washes and bleeds,
  `INK_PEN` for line work that can be re-wetted, `OIL_AND_ACRYLIC` for impasto and
  colour mixing on the canvas, `PENCIL`/`PASTEL` for dry texture, `AIRBRUSH` for soft
  gradients.

## Always look at the result

Rebelle answers almost nothing, and a wrong paper or preset produces a plausible,
completely wrong image. Export and **Read the PNG** after each meaningful step, the same
way you would glance at the canvas: live via `r.export(path)`, in batch by reading the
last rendered frame. Judge it as a picture — coverage, colour, whether the water did
anything — and iterate. Then, when the user wants the finished artwork, export at full
size (`rgba_canvas`, or `SAVE` with `scaling` for a NanoPixel-scale export).

## Gotchas worth knowing before you hit them

- **Wrong preset name → loud error; wrong paper name → silence.** Resolve both against
  the filesystem first ([assets.md](references/assets.md)); the official quickstart's
  `"Default/HM01 Handmade"` is itself wrong for Rebelle 8.
- **`SET_BRUSH` without `preset` paints nothing** and logs `Preset for brush was not set`.
- **Only one Rebelle at a time.** Running the GUI build and Motion IO together is asking
  for trouble; stop one before starting the other.
- **Force-stopping the app leaves a `Data/Sessions/<pid>/` folder behind** in
  `~/Library/Application Support/Escape Motions/Rebelle 8/`. Harmless, but they pile up
  at tens of MB each — worth mentioning to the user rather than deleting behind their back.
- **Colours are 8-bit RGB objects** (`{"r":…,"g":…,"b":…}`) even though the engine mixes
  in 16-bit; 16-bit output only exists in Motion IO `.exr` exports.
- **The docs run ahead of the build.** The 8.3 docs promise `SAVE`/`LOAD` over
  WebSockets; the shipped 8.3.0 rejects them. Trust an export you have looked at over
  any documented behaviour.
- **Animation licensing has strings attached** — see the note at the end of
  [batch.md](references/batch.md) before helping with a commercial production.
