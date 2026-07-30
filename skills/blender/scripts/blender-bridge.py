# Blender Bridge — runs INSIDE a running Blender GUI and executes whatever build
# script is POSTed to it, in the LIVE session, on the MAIN thread — so bpy.data
# writes are legal, the viewport updates, and bpy.ops works.
#
# Blender exposes no Qt-style event loop to Python, so this is a daemon HTTP
# thread + a queue + a bpy.app.timers pump on the main thread. The HTTP thread
# NEVER touches bpy; it hands work to the pump and waits for the result.
#
#   GET  /ping         -> {"ok": true, "bridge": "blender", "version": ..., "file": ...}
#   GET  /state        -> cheap scene summary (objects, collections, frame range, engine)
#   POST /run  {code}  -> exec inline code   ; {path} -> exec a .py file
#                         optional {out} sets the OUT dir (env + an injected global)
#
# Install (any one):
#   1. ~/Library/Application Support/Blender/5.2/scripts/startup/blender_bridge.py
#      -> starts automatically on every launch (recommended)
#   2. Scripting workspace -> text editor -> paste -> Run Script (Alt+P)
#   3. Preferences > Add-ons > Install... (it carries bl_info)
#
# Env (read at start): BLENDER_BRIDGE_PORT (8736).
bl_info = {
    "name": "Blender Bridge",
    "author": "agent-tools",
    "version": (1, 0, 0),
    "blender": (4, 2, 0),
    "location": "Runs a localhost HTTP server on 127.0.0.1:8736",
    "description": "Execute Python sent over localhost HTTP in the live session, on the main thread.",
    "category": "Development",
}

import bpy
import bmesh  # noqa: F401  (injected into script namespaces)
import mathutils
import contextlib
import io
import json
import math
import os
import queue
import threading
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

BRIDGE_VERSION = "1.0.0"
PORT = int(os.environ.get("BLENDER_BRIDGE_PORT", "8736"))

_jobs = queue.Queue()
_server = None
_server_thread = None


# --------------------------------------------------------------------------
# Helpers injected into every script's namespace
# --------------------------------------------------------------------------

def stage(name, clear=True, activate=True):
    """Get-or-recreate a named collection and make it active.

    This is what makes build scripts re-runnable against a LIVE session: the
    script owns `name` and nothing else, so a re-send replaces its own output
    instead of stacking duplicates or touching the user's other work.
    """
    coll = bpy.data.collections.get(name)
    if coll is not None and clear:
        for child in list(coll.children):
            _purge_collection(child)
        for ob in list(coll.objects):
            bpy.data.objects.remove(ob, do_unlink=True)
    if coll is None:
        coll = bpy.data.collections.new(name)
    scene = bpy.context.scene
    if coll.name not in scene.collection.children:
        scene.collection.children.link(coll)
    if activate:
        layer = _find_layer_collection(bpy.context.view_layer.layer_collection, coll)
        if layer is not None:
            bpy.context.view_layer.active_layer_collection = layer
    return coll


def _purge_collection(coll):
    for child in list(coll.children):
        _purge_collection(child)
    for ob in list(coll.objects):
        bpy.data.objects.remove(ob, do_unlink=True)
    bpy.data.collections.remove(coll)


def _find_layer_collection(root, target):
    if root.collection == target:
        return root
    for child in root.children:
        found = _find_layer_collection(child, target)
        if found is not None:
            return found
    return None


@contextlib.contextmanager
def ui_override(area_type="VIEW_3D", region_type="WINDOW"):
    """Context override for bpy.ops that need a real editor.

    The timer pump runs with an area-less context, so operators like
    render.opengl or view3d.* fail with "context is incorrect" without this.
    Prefer the data API; reach for this only when there is no data-API path.
    """
    wm = bpy.context.window_manager
    for win in wm.windows:
        screen = win.screen
        for area in screen.areas:
            if area.type != area_type:
                continue
            for region in area.regions:
                if region.type != region_type:
                    continue
                with bpy.context.temp_override(
                    window=win, screen=screen, area=area, region=region
                ):
                    yield area
                return
    raise RuntimeError(
        "no %s area in any open window — switch a Blender editor to it" % area_type
    )


def _resolve_render_output(target, what="render"):
    """Blender writes stills to frame_path() (frame number appended). Move it.

    bpy.ops.render.render() returns {'FINISHED'} even when it writes NOTHING —
    an empty scene.compositing_node_group or an empty sequencer silently
    swallows the output. Fail loudly here instead of returning a phantom path.
    """
    actual = bpy.path.abspath(bpy.context.scene.render.frame_path())
    target = os.path.abspath(target)
    if actual != target and os.path.exists(actual):
        os.makedirs(os.path.dirname(target) or ".", exist_ok=True)
        os.replace(actual, target)
    if not os.path.exists(target):
        scene = bpy.context.scene
        hints = []
        if scene.render.use_compositing and getattr(scene, "compositing_node_group", None):
            hints.append("scene.compositing_node_group is set — it must end in a "
                         "NodeGroupOutput, or set render.use_compositing = False")
        if scene.render.use_sequencer and scene.sequence_editor:
            hints.append("the scene has a sequence editor — set "
                         "render.use_sequencer = False to render the 3D view")
        if scene.camera is None:
            hints.append("scene.camera is None")
        raise RuntimeError(
            "%s reported success but wrote no file to %s%s"
            % (what, target, (". Likely cause: " + "; ".join(hints)) if hints else "")
        )
    return target


# Standard view orientations as view_rotation Euler angles (radians applied below).
_VIEWS = {
    "TOP": (0, 0, 0),
    "BOTTOM": (180, 0, 0),
    "FRONT": (90, 0, 0),
    "BACK": (90, 0, 180),
    "RIGHT": (90, 0, 90),
    "LEFT": (90, 0, -90),
    "ISO": (60, 0, 45),
}


def sync():
    """Flush pending transform changes into matrix_world.

    Assigning ob.location / rotation / parent does NOT update ob.matrix_world —
    that happens on depsgraph evaluation. Anything that reads matrix_world in
    the same script must call this first or it silently reads stale identity
    matrices. Every helper here calls it for you.
    """
    bpy.context.view_layer.update()


def world_bounds(objs):
    """World-space (min, max) corners over objs, from their bounding boxes."""
    sync()
    lo = mathutils.Vector((math.inf,) * 3)
    hi = mathutils.Vector((-math.inf,) * 3)
    found = False
    for ob in objs:
        if ob.type in {"CAMERA", "LIGHT", "SPEAKER", "EMPTY"}:
            continue
        for corner in ob.bound_box:
            world = ob.matrix_world @ mathutils.Vector(corner)
            for i in range(3):
                lo[i] = min(lo[i], world[i])
                hi[i] = max(hi[i], world[i])
            found = True
    if not found:
        return mathutils.Vector((-1, -1, -1)), mathutils.Vector((1, 1, 1))
    return lo, hi


def frame_view(objs=None, view=None, margin=1.15, refit=True, aspect=None):
    """Aim the 3D viewport at objs — pure data API on region_3d.

    bpy.ops.view3d.view_all / view_selected are NO-OPS from the bridge: they
    stage a smooth-view transition that only lands on the next region redraw,
    which never happens inside one timer callback. Writing region_3d directly
    is immediate and deterministic.
    """
    if objs is None:
        objs = list(bpy.context.scene.objects)
    elif isinstance(objs, (bpy.types.Object, str)):
        objs = [objs]
    objs = [bpy.data.objects[o] if isinstance(o, str) else o for o in objs]
    with ui_override("VIEW_3D") as area:
        space = area.spaces.active
        rv3d = space.region_3d
        region = next(r for r in area.regions if r.type == "WINDOW")
        if view == "CAMERA":
            rv3d.view_perspective = "CAMERA"
            return rv3d
        rv3d.view_perspective = "PERSP"
        if view:
            angles = _VIEWS[view.upper()]
            rv3d.view_rotation = mathutils.Euler(
                [math.radians(a) for a in angles], "XYZ"
            ).to_quaternion()
        if not refit:
            return rv3d
        lo, hi = world_bounds(objs)
        rv3d.view_location = (lo + hi) / 2.0
        radius = max((hi - lo).length / 2.0, 1e-4)
        # Blender's viewport maps `space.lens` onto a 72mm sensor across the
        # LARGER axis; fit the bounding sphere in the narrower one. Use the
        # RENDER aspect when snapshotting — render.opengl reprojects to it.
        w, h = (aspect if aspect else (region.width, region.height))
        fov_wide = 2.0 * math.atan(36.0 / max(space.lens, 1e-3))
        ratio = min(w, h) / max(w, h, 1)
        fov_narrow = 2.0 * math.atan(math.tan(fov_wide / 2.0) * ratio)
        rv3d.view_distance = margin * radius / math.sin(fov_narrow / 2.0)
        return rv3d


def snapshot(path, width=960, height=600, shading="MATERIAL", fit="all", view=None,
             objs=None, overlays=False):
    """Viewport OpenGL PNG — the fast visual feedback signal (no full render).

    fit: "all" (whole scene) | "selected" | None (leave the view alone).
    view: "ISO" | "FRONT" | "TOP" | "CAMERA" | ... | None (keep current angle).
    shading: "WIREFRAME" | "SOLID" | "MATERIAL" | "RENDERED".
    """
    scene = bpy.context.scene
    r = scene.render
    saved = (
        r.filepath, r.resolution_x, r.resolution_y, r.resolution_percentage,
        r.image_settings.file_format,
    )
    r.filepath = os.path.abspath(path)
    r.resolution_x, r.resolution_y, r.resolution_percentage = width, height, 100
    r.image_settings.file_format = "PNG"
    try:
        if fit == "selected":
            frame_view(objs or bpy.context.selected_objects, view=view,
                       aspect=(width, height))
        elif fit or view:
            frame_view(objs, view=view, refit=bool(fit), aspect=(width, height))
        with ui_override("VIEW_3D") as area:
            space = area.spaces.active
            prev = (space.shading.type, space.overlay.show_overlays)
            space.shading.type = shading
            space.overlay.show_overlays = overlays
            try:
                bpy.ops.render.opengl(write_still=True)
            finally:
                space.shading.type, space.overlay.show_overlays = prev
        return _resolve_render_output(path, "snapshot()")
    finally:
        (r.filepath, r.resolution_x, r.resolution_y, r.resolution_percentage,
         r.image_settings.file_format) = saved


def render(path, engine=None, samples=None, frame=None, width=None, height=None,
           transparent=None):
    """Real EEVEE/Cycles still. BLOCKS the main thread — the UI freezes until done."""
    scene = bpy.context.scene
    r = scene.render
    saved = (
        r.filepath, r.engine, r.resolution_x, r.resolution_y,
        r.resolution_percentage, r.image_settings.file_format, r.film_transparent,
    )
    saved_frame = scene.frame_current
    try:
        if engine:
            r.engine = engine
        if width:
            r.resolution_x = width
        if height:
            r.resolution_y = height
        if transparent is not None:
            r.film_transparent = transparent
        r.resolution_percentage = 100
        r.image_settings.file_format = "PNG"
        r.filepath = os.path.abspath(path)
        if samples is not None:
            if r.engine == "CYCLES":
                scene.cycles.samples = samples
            elif r.engine.startswith("BLENDER_EEVEE"):
                scene.eevee.taa_render_samples = samples
        if frame is not None:
            scene.frame_set(frame)
        bpy.ops.render.render(write_still=True)
        return _resolve_render_output(path, "render()")
    finally:
        (r.filepath, r.engine, r.resolution_x, r.resolution_y,
         r.resolution_percentage, r.image_settings.file_format,
         r.film_transparent) = saved
        scene.frame_set(saved_frame)


def evaluated(obj):
    """Modifier / geometry-nodes result. The depsgraph is Blender's recompute()."""
    return obj.evaluated_get(bpy.context.evaluated_depsgraph_get())


def frame(n):
    bpy.context.scene.frame_set(n)
    bpy.context.evaluated_depsgraph_get().update()
    return n


def channelbag(target, ensure=True):
    """The channelbag holding target's F-curves under the slotted-action system.

    Blender 5.x REMOVED Action.fcurves. Curves now live at
    action.layers[i].strips[j].channelbag(slot). This walks (and with
    ensure=True creates) that chain for an ID that has animation_data.
    """
    ad = getattr(target, "animation_data", None)
    if ad is None:
        if not ensure:
            return None
        ad = target.animation_data_create()
    act = ad.action
    if act is None:
        if not ensure:
            return None
        act = bpy.data.actions.new(target.name + "Action")
        ad.action = act
    if not act.slots:
        if not ensure:
            return None
        ad.action_slot = act.slots.new(id_type=target.id_type, name=target.name)
    slot = ad.action_slot or act.slots[0]
    if not act.layers:
        if not ensure:
            return None
        act.layers.new("Layer")
    layer = act.layers[0]
    if not layer.strips:
        if not ensure:
            return None
        layer.strips.new(type="KEYFRAME")
    return layer.strips[0].channelbag(slot, ensure=ensure)


def fcurves(target):
    """List of F-curves driving target (empty if it has no action)."""
    cb = channelbag(target, ensure=False)
    return list(cb.fcurves) if cb else []


def fcurve(target, data_path, index=0, ensure=True):
    """One F-curve by data path, created if missing."""
    cb = channelbag(target, ensure=ensure)
    if cb is None:
        return None
    existing = cb.fcurves.find(data_path, index=index)
    if existing or not ensure:
        return existing
    return cb.fcurves.new(data_path, index=index)


def metrics(objs=None, path=None):
    """Structured geometry check — verify without eyeballing a picture."""
    scene = bpy.context.scene
    if objs is None:
        objs = [o for o in scene.objects]
    elif isinstance(objs, (bpy.types.Object, str)):
        objs = [objs]
    objs = [bpy.data.objects[o] if isinstance(o, str) else o for o in objs]
    sync()
    dg = bpy.context.evaluated_depsgraph_get()
    lo = mathutils.Vector((math.inf,) * 3)
    hi = mathutils.Vector((-math.inf,) * 3)
    verts = tris = 0
    for ob in objs:
        for corner in ob.bound_box:
            world = ob.matrix_world @ mathutils.Vector(corner)
            for i in range(3):
                lo[i] = min(lo[i], world[i])
                hi[i] = max(hi[i], world[i])
        ev = ob.evaluated_get(dg)
        mesh = None
        try:
            mesh = ev.to_mesh()
        except Exception:
            mesh = None
        if mesh is not None:
            verts += len(mesh.vertices)
            mesh.calc_loop_triangles()
            tris += len(mesh.loop_triangles)
            ev.to_mesh_clear()
    data = {
        "objects": len(objs),
        "types": sorted({o.type for o in objs}),
        "verts": verts,
        "tris": tris,
        "bbox_min": [round(v, 4) for v in lo] if verts or objs else None,
        "bbox_max": [round(v, 4) for v in hi] if verts or objs else None,
        "materials": sorted({m.name for o in objs for m in o.data.materials
                             if getattr(o.data, "materials", None) and m}),
        "frame_range": [scene.frame_start, scene.frame_end],
        "engine": scene.render.engine,
        "fps": scene.render.fps,
    }
    if path:
        with open(path, "w") as fh:
            json.dump(data, fh, indent=2)
    return data


def _state():
    scene = bpy.context.scene
    return {
        "ok": True,
        "file": bpy.data.filepath or None,
        "scene": scene.name,
        "engine": scene.render.engine,
        "engines": [i.identifier for i in
                    bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items],
        "frame_range": [scene.frame_start, scene.frame_end, scene.frame_current],
        "fps": scene.render.fps,
        "resolution": [scene.render.resolution_x, scene.render.resolution_y],
        "collections": [c.name for c in bpy.data.collections],
        "objects": [{"name": o.name, "type": o.type} for o in scene.objects],
        "materials": [m.name for m in bpy.data.materials],
        "images": [i.name for i in bpy.data.images],
        "node_groups": [g.name for g in bpy.data.node_groups],
        "unsaved": bpy.data.is_dirty,
    }


_HELPERS = {
    "sync": sync,
    "channelbag": channelbag,
    "fcurves": fcurves,
    "fcurve": fcurve,
    "frame_view": frame_view,
    "world_bounds": world_bounds,
    "stage": stage,
    "ui_override": ui_override,
    "snapshot": snapshot,
    "render": render,
    "evaluated": evaluated,
    "frame": frame,
    "metrics": metrics,
}


# --------------------------------------------------------------------------
# Main-thread pump
# --------------------------------------------------------------------------

def _make_namespace(out):
    import bmesh as _bmesh
    ns = {
        "__name__": "__bridge__",
        "bpy": bpy,
        "bmesh": _bmesh,
        "mathutils": mathutils,
        "Vector": mathutils.Vector,
        "Matrix": mathutils.Matrix,
        "Euler": mathutils.Euler,
        "Quaternion": mathutils.Quaternion,
        "math": math,
        "os": os,
        "json": json,
        "OUT": out,
    }
    ns.update(_HELPERS)
    return ns


def _execute(job):
    out = job.get("out") or ""
    if out:
        os.makedirs(out, exist_ok=True)
        os.environ["OUT"] = out
    ns = _make_namespace(out)
    code = job.get("code")
    filename = "<bridge>"
    if not code:
        path = job.get("path")
        with open(path) as fh:
            code = fh.read()
        filename = path
        ns["__file__"] = path
    buf = io.StringIO()
    result = {"ok": True, "output": "", "error": None}
    try:
        with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
            exec(compile(code, filename, "exec"), ns)
    except Exception:
        result["ok"] = False
        result["error"] = traceback.format_exc()
    result["output"] = buf.getvalue()
    return result


def _pump():
    while True:
        try:
            job = _jobs.get_nowait()
        except queue.Empty:
            break
        try:
            if job["kind"] == "ping":
                job["result"] = {
                    "ok": True,
                    "bridge": "blender",
                    "bridge_version": BRIDGE_VERSION,
                    "version": bpy.app.version_string,
                    "file": bpy.data.filepath or None,
                    "engine": bpy.context.scene.render.engine,
                }
            elif job["kind"] == "state":
                job["result"] = _state()
            else:
                job["result"] = _execute(job)
        except Exception:
            job["result"] = {"ok": False, "output": "", "error": traceback.format_exc()}
        finally:
            job["done"].set()
    return 0.05


# --------------------------------------------------------------------------
# HTTP thread (never touches bpy)
# --------------------------------------------------------------------------

class _Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *args):
        pass

    def _reply(self, obj, status=200):
        body = json.dumps(obj).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _dispatch(self, kind, payload=None, timeout=3600):
        job = {"kind": kind, "done": threading.Event(), "result": None}
        if payload:
            job.update(payload)
        _jobs.put(job)
        if not job["done"].wait(timeout):
            return {"ok": False, "output": "",
                    "error": "timed out waiting for Blender's main thread"}
        return job["result"]

    def do_GET(self):
        if self.path.startswith("/ping"):
            self._reply(self._dispatch("ping", timeout=10))
        elif self.path.startswith("/state"):
            self._reply(self._dispatch("state", timeout=30))
        else:
            self._reply({"ok": False, "error": "unknown endpoint"}, 404)

    def do_POST(self):
        if not self.path.startswith("/run"):
            self._reply({"ok": False, "error": "unknown endpoint"}, 404)
            return
        try:
            raw = self.rfile.read(int(self.headers.get("Content-Length", 0)))
            payload = json.loads(raw.decode())
        except Exception as exc:
            self._reply({"ok": False, "output": "", "error": "bad request: %s" % exc}, 400)
            return
        if not payload.get("code") and not payload.get("path"):
            self._reply({"ok": False, "output": "", "error": "need 'code' or 'path'"}, 400)
            return
        self._reply(self._dispatch("run", payload))


# --------------------------------------------------------------------------
# Lifecycle — idempotent, so re-running the script just restarts cleanly
# --------------------------------------------------------------------------

def _start_server():
    global _server, _server_thread
    _stop_server()
    _server = ThreadingHTTPServer(("127.0.0.1", PORT), _Handler)
    _server.daemon_threads = True
    _server_thread = threading.Thread(target=_server.serve_forever, daemon=True)
    _server_thread.start()


def _stop_server():
    global _server, _server_thread
    if _server is not None:
        try:
            _server.shutdown()
            _server.server_close()
        except Exception:
            pass
    _server = None
    _server_thread = None


def register():
    _start_server()
    if not bpy.app.timers.is_registered(_pump):
        bpy.app.timers.register(_pump, persistent=True)
    print("Blender Bridge %s listening on 127.0.0.1:%d" % (BRIDGE_VERSION, PORT))


def unregister():
    if bpy.app.timers.is_registered(_pump):
        bpy.app.timers.unregister(_pump)
    _stop_server()


# Auto-start when dropped in scripts/startup/ or run from the text editor.
# As an installed add-on, Blender calls register() itself — the guard keeps
# that from double-starting.
if __name__ in ("__main__", "blender_bridge"):
    register()
