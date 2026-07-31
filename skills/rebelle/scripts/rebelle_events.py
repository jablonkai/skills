#!/usr/bin/env python3
"""Builder for Rebelle Motion IO event files.

The JSON format is simple, but three details bite every time you hand-write it:
NEW_ARTWORK is ignored in frame 0, a frame with no events stalls the batch, and
POINTER_RELEASE has to repeat the last move position. `Doc` takes care of all
three, so scripts can stay about the drawing.

    from rebelle_events import Doc, catmull_rom, taper

    d = Doc(1200, 800)                       # warm-up + NEW_ARTWORK frames
    d.set_brush("WATERCOLOR", "Watercolor/Round", size=45, water=60,
                color=(30, 90, 200))
    d.stroke(catmull_rom([(100, 400), (400, 250), (800, 550), (1100, 300)]),
             pressure=taper(0.9))
    d.frame()                                # end this animation frame
    d.simulation(20)                          # let the water diffuse
    d.write("events.json")

Then render it:  scripts/rebelle-batch.sh events.json out/
"""
from __future__ import annotations

import json
import math
from typing import Callable, Iterable, Sequence

Point = tuple[float, float]


# --- path helpers --------------------------------------------------------
def line(a: Point, b: Point, steps: int = 12) -> list[Point]:
    return [(a[0] + (b[0] - a[0]) * t / steps, a[1] + (b[1] - a[1]) * t / steps) for t in range(steps + 1)]


def bezier(p0: Point, p1: Point, p2: Point, p3: Point, steps: int = 32) -> list[Point]:
    out = []
    for i in range(steps + 1):
        t = i / steps
        u = 1 - t
        out.append(
            (
                u**3 * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t**3 * p3[0],
                u**3 * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t**3 * p3[1],
            )
        )
    return out


def catmull_rom(points: Sequence[Point], steps_per_segment: int = 16) -> list[Point]:
    """Smooth curve through every control point — the usual way to get a natural stroke."""
    pts = list(points)
    if len(pts) < 3:
        return line(pts[0], pts[-1]) if len(pts) == 2 else list(pts)
    ext = [pts[0]] + pts + [pts[-1]]
    out: list[Point] = []
    for i in range(len(ext) - 3):
        p0, p1, p2, p3 = ext[i : i + 4]
        for s in range(steps_per_segment):
            t = s / steps_per_segment
            t2, t3 = t * t, t * t * t
            out.append(
                (
                    0.5 * ((2 * p1[0]) + (-p0[0] + p2[0]) * t + (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * t2 + (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * t3),
                    0.5 * ((2 * p1[1]) + (-p0[1] + p2[1]) * t + (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t2 + (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t3),
                )
            )
    out.append(pts[-1])
    return out


def arc(cx: float, cy: float, r: float, a0_deg: float, a1_deg: float, steps: int = 48) -> list[Point]:
    a0, a1 = math.radians(a0_deg), math.radians(a1_deg)
    return [
        (cx + r * math.cos(a0 + (a1 - a0) * i / steps), cy + r * math.sin(a0 + (a1 - a0) * i / steps))
        for i in range(steps + 1)
    ]


# --- pressure profiles ---------------------------------------------------
def taper(peak: float = 0.9, ends: float = 0.15) -> Callable[[int, int], float]:
    """Thin at both ends, full in the middle — reads as a hand-made stroke."""

    def f(i: int, n: int) -> float:
        t = i / max(n - 1, 1)
        return ends + (peak - ends) * math.sin(math.pi * t)

    return f


def ramp(start: float = 0.2, end: float = 1.0) -> Callable[[int, int], float]:
    def f(i: int, n: int) -> float:
        t = i / max(n - 1, 1)
        return start + (end - start) * t

    return f


def rgb(color) -> dict:
    r, g, b = color
    return {"r": int(r), "g": int(g), "b": int(b)}


def stroke_events(points: Sequence[Point], pressure=0.8, tilt=None, rotation=None, stroke_id=None) -> list[dict]:
    """PRESS / MOVE.../ RELEASE for one stroke.

    Rebelle draws each segment one move event late, so the release repeats the
    final point; end it anywhere else and the last segment silently disappears.
    """
    pts = [(float(x), float(y)) for x, y in points]
    if len(pts) < 2:
        pts = pts * 2
    n = len(pts)

    def at(i: int, kind: str) -> dict:
        ev = {"event_type": kind, "pos": {"x": round(pts[i][0], 2), "y": round(pts[i][1], 2)}}
        if pressure is not None:
            ev["pressure"] = round(pressure(i, n) if callable(pressure) else float(pressure), 3)
        if tilt is not None:
            ev["pen_tilt"] = {"x": tilt[0], "y": tilt[1]}
        if rotation is not None:
            ev["rotation"] = rotation
        return ev

    first = at(0, "POINTER_PRESS")
    if stroke_id is not None:
        first["stroke_id"] = stroke_id
    return [first] + [at(i, "POINTER_MOVE") for i in range(1, n)] + [at(n - 1, "POINTER_RELEASE")]


class Doc:
    """Accumulates events into animation frames and writes the JSON file.

    The first two frames are setup, not artwork — see `first_content_frame`
    before turning the output into a video.
    """

    #: Warm-up brush. Loading any preset is what makes frame 0 do enough real
    #: work; a cheap frame 0 (BOOKMARK only, or empty) leaves Motion IO wedged
    #: before it processes anything at all.
    WARMUP_BRUSH = ("PENCIL", "Graphite Pencil/HB")

    def __init__(self, width: int | None = None, height: int | None = None, dpi: int = 200, paper: dict | None = None):
        self.frames: list[dict] = []
        self.pending: list[dict] = []
        tool, preset = self.WARMUP_BRUSH
        self.frames.append(
            {
                "events": [
                    {"event_type": "SET_BRUSH", "tool": tool, "preset": preset, "size": 20, "opacity": 100},
                    {"event_type": "BOOKMARK", "id": "warmup"},
                ]
            }
        )
        if width and height:
            # NEW_ARTWORK belongs in frame 1, never frame 0: in frame 0 it is
            # silently dropped (you get Rebelle's default canvas instead), and
            # whatever is painted in the same frame as it is wiped by the canvas
            # re-init. It also cannot end its frame — a frame that finishes right
            # after NEW_ARTWORK deadlocks — so a second SET_BRUSH follows it and
            # painting starts in the next frame.
            ev = {"event_type": "NEW_ARTWORK", "width": int(width), "height": int(height), "units": "px", "dpi": dpi}
            if paper:
                ev["paper"] = paper
            self.frames.append(
                {
                    "events": [
                        ev,
                        {"event_type": "SET_BRUSH", "tool": tool, "preset": preset, "size": 20, "opacity": 100},
                        {"event_type": "BOOKMARK", "id": "artwork_ready"},
                    ]
                }
            )
        #: Index of the first rendered frame that shows real painting — the setup
        #: frames before it still render (on the default canvas), so an animation
        #: assembled from frame 0 starts with a flash of blank A4.
        self.first_content_frame = len(self.frames)

    # --- events ---
    def add(self, *events: dict) -> "Doc":
        self.pending.extend(events)
        return self

    def set_brush(self, tool: str, preset: str, **params) -> "Doc":
        """SET_BRUSH always needs `preset`; without it Rebelle logs an error and paints nothing."""
        ev = {"event_type": "SET_BRUSH", "tool": tool, "preset": preset}
        if "color" in params:
            params["color"] = rgb(params["color"])
        ev.update(params)
        return self.add(ev)

    def color(self, color) -> "Doc":
        return self.add({"event_type": "SET_BRUSH_COLOR", "color": rgb(color)})

    def stroke(self, points: Iterable[Point], **kw) -> "Doc":
        return self.add(*stroke_events(list(points), **kw))

    def simulation(self, repeats: int = 1, frames: int = 1) -> "Doc":
        """Fluid steps. Each frame ends with one implicit step; `repeats` adds more."""
        for _ in range(frames):
            self.frame([{"event_type": "SIMULATION", "repeats": repeats}])
        return self

    def bookmark(self, tag: str, **extra) -> "Doc":
        return self.add({"event_type": "BOOKMARK", "id": tag, **extra})

    def save_layers(self, **layers) -> "Doc":
        """SAVE data layers, e.g. save_layers(rgba_canvas="out/final.png")."""
        return self.add({"event_type": "SAVE", **{k: {"filename": v} for k, v in layers.items()}})

    # --- frames ---
    def frame(self, events: list[dict] | None = None) -> "Doc":
        """Close the current animation frame (one output image, one simulation step)."""
        batch = self.pending + list(events or [])
        self.pending = []
        if not batch:
            # A frame with nothing in it can wedge the batch processor.
            batch = [{"event_type": "BOOKMARK", "id": f"frame_{len(self.frames)}"}]
        self.frames.append({"events": batch})
        return self

    def write(self, path: str) -> str:
        if self.pending:
            self.frame()
        with open(path, "w") as fh:
            json.dump({"frames": self.frames}, fh, indent=2)
        return path

    def events(self) -> list[dict]:
        """Flat event list — for replaying live over the WebSocket instead of batching."""
        frames = self.frames + ([{"events": self.pending}] if self.pending else [])
        return [ev for f in frames for ev in f["events"]]
