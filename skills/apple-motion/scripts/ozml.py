"""Shared helpers for Apple Motion template files (.moti/.motn/.moef/.motr).

The files are ozml XML (<!DOCTYPE ozxmlscene>). Everything here is standard library.
Objects (scenenode, layer, group, style, behavior, filter ...) carry a document-unique
numeric `id`; their settings are nested <parameter> elements addressed by parameter
ids, so a published target such as object="10972" channel="./2/353/113/111" means
"object 10972 -> parameter 2 -> 353 -> 113 -> 111". See references/ozml.md.
"""
import os
import re
import struct
import subprocess
import xml.etree.ElementTree as ET

HEADER = '<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE ozxmlscene>\n'
KINDS = {".moti": "Titles", ".motn": "Generators", ".moef": "Effects", ".motr": "Transitions"}
USER_ROOT = os.path.expanduser("~/Movies/Motion Templates.localized")
FCP_APP = "/Applications/Final Cut Pro.app"
MOTION_APP = "/Applications/Motion.app"
STOCK_ROOTS = [
    os.path.join(FCP_APP, "Contents/PlugIns/MediaProviders/MotionEffect.fxp/Contents/Resources", d)
    for d in ("Templates.localized", "PETemplates.localized", "METemplates.localized")
] + [os.path.join(MOTION_APP, "Contents/Resources/Templates.localized")]

# parameter-id paths, relative to the object named in the comment
TEXT_PARAM = ("2", "369")                 # text scenenode -> Object -> Text
STYLE_FONT = ("83",)                      # style -> Font (<font>PostScript name</font>)
STYLE_SIZE = ("3",)                       # style -> Size
STYLE_COLOR = ("14", "16")                # style -> Face -> Color
SHAPE_FILL = ("2", "353", "113", "111")   # shape scenenode -> Object -> Style -> Fill -> Fill Color
OPACITY = ("1", "200", "202")             # any layer -> Properties -> Blending -> Opacity
POSITION = ("1", "100", "101")            # any layer -> Properties -> Transform -> Position
WIDGET_VALUE = ("2", "100")               # rig widget -> Object -> value
COLOR_FLAGS = {"style": ("8589938704", "8606711824"), "shape": ("12884906000", "8589934608")}
RGB = (("1", "Red"), ("2", "Green"), ("3", "Blue"))


class OzmlError(Exception):
    pass


# ----------------------------------------------------------------------- load / save

class Doc:
    def __init__(self, path):
        self.path = path
        try:
            self.tree = ET.parse(path)
        except ET.ParseError as e:
            raise OzmlError(f"{path}: not well-formed XML ({e})")
        self.root = self.tree.getroot()
        if self.root.tag != "ozml":
            raise OzmlError(f"{path}: root is <{self.root.tag}>, not <ozml> — not a Motion file")
        self.factories = {f.get("id"): (f.findtext("description") or "") for f in self.root.findall("factory")}
        self.scene = self.root.find("scene")
        if self.scene is None:
            raise OzmlError(f"{path}: no <scene> element")
        self.reindex()

    def reindex(self):
        self.parent = {c: p for p in self.root.iter() for c in p}
        self.objects = {}
        for e in self.root.iter():
            if e.tag not in ("parameter", "factory", "target", "styleRun") and e.get("id"):
                self.objects.setdefault(e.get("id"), e)

    def factory(self, el):
        return self.factories.get(el.get("factoryID"), "")

    def save(self, path):
        body = ET.tostring(self.root, encoding="unicode")
        with open(path, "w", encoding="utf-8") as f:
            f.write(HEADER + body + "\n")
        Doc(path)  # re-parse: never leave a file Motion cannot load


# ------------------------------------------------------------------------- objects

def kind_of(path):
    return KINDS.get(os.path.splitext(path)[1].lower())


def text_layers(doc):
    """Text scenenodes in document order — the order FCP fills its text fields."""
    return [n for n in doc.root.iter("scenenode") if doc.factory(n) == "Text"]


def shape_layers(doc):
    return [n for n in doc.root.iter("scenenode") if doc.factory(n) == "Shape"]


def widgets(doc):
    return [n for n in doc.root.iter("scenenode") if doc.factory(n) == "Widget"]


def pick(nodes, sel, what):
    """`sel` is a layer name (case-insensitive), '#N' (1-based) or '*' (all)."""
    if sel == "*":
        return list(nodes)
    m = re.fullmatch(r"#(\d+)", sel.strip())
    if m:
        i = int(m.group(1))
        if not 1 <= i <= len(nodes):
            raise OzmlError(f"{what} {sel}: there are {len(nodes)}")
        return [nodes[i - 1]]
    hits = [n for n in nodes if (n.get("name") or "").lower() == sel.strip().lower()]
    if not hits:
        names = ", ".join(repr(n.get("name")) for n in nodes) or "none"
        raise OzmlError(f"no {what} named {sel!r} (have: {names})")
    return hits


def styles_of(text_node):
    return text_node.findall("style")


# ---------------------------------------------------------------------- parameters

def param_at(el, path, create=None):
    """Walk parameter ids below `el`. With `create` (a list of (name, flags) per
    missing level) absent levels are added; otherwise a missing level returns None."""
    cur = el
    for depth, pid in enumerate(path):
        nxt = cur.find(f"./parameter[@id='{pid}']")
        if nxt is None:
            if not create:
                return None
            name, flags = create[depth] if depth < len(create) else (f"Param {pid}", "8589938704")
            nxt = ET.SubElement(cur, "parameter", {"name": name, "id": pid, "flags": flags})
            _tidy(cur, nxt)
        cur = nxt
    return cur


def _tidy(parent, child):
    """Indent a newly added child like its siblings (cosmetic only)."""
    sibs = list(parent)
    if len(sibs) > 1:
        prev = sibs[-2]                      # the old last child
        child.tail = prev.tail               # closing indentation moves to the new last child
        prev.tail = parent.text or "\n"      # and the old one gets the inner indentation
    else:
        outer = parent.tail if parent.tail and not parent.tail.strip() else "\n"
        parent.text = outer + "\t"
        child.tail = outer


def is_color(p):
    return p is not None and (p.find("./parameter[@name='Red']") is not None
                              or "color" in (p.get("name") or "").lower())


def get_rgb(p):
    """Missing components are at their default (1.0 for Motion colour params)."""
    out = []
    for cid, _ in RGB:
        c = p.find(f"./parameter[@id='{cid}']") if p is not None else None
        out.append(float(c.get("value", c.get("default", "1"))) if c is not None else 1.0)
    return tuple(out)


def set_rgb(p, rgb, comp_flags="8606711824"):
    for (cid, cname), v in zip(RGB, rgb):
        c = p.find(f"./parameter[@id='{cid}']")
        if c is None:
            c = ET.SubElement(p, "parameter", {"name": cname, "id": cid, "flags": comp_flags,
                                               "default": "1", "value": "1"})
            _tidy(p, c)
        c.set("value", fmt_num(v))


def fmt_num(v):
    s = repr(float(v))
    return s[:-2] if s.endswith(".0") else s


def parse_color(s):
    """'#00ADEF', '00ADEF', '#0AE' or '0,0.678,0.937' (0..1) -> (r, g, b) floats."""
    s = s.strip()
    m = re.fullmatch(r"#?([0-9a-fA-F]{6}|[0-9a-fA-F]{3})", s)
    if m:
        h = m.group(1)
        if len(h) == 3:
            h = "".join(c * 2 for c in h)
        return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
    parts = [x for x in re.split(r"[,\s]+", s) if x]
    if len(parts) == 3:
        vals = [float(x) for x in parts]
        if all(0 <= v <= 1.5 for v in vals):
            return tuple(vals)
    raise OzmlError(f"colour {s!r}: use #RRGGBB or r,g,b in 0..1")


def hex_of(rgb):
    return "#" + "".join(f"{max(0, min(255, round(v * 255))):02X}" for v in rgb)


# ------------------------------------------------------------------------ text

def get_text(node):
    p = param_at(node, TEXT_PARAM)
    t = p.find("text") if p is not None else None
    return t.text or "" if t is not None else ""


def set_text(node, value):
    p = param_at(node, TEXT_PARAM)
    t = p.find("text") if p is not None else None
    if t is None:
        raise OzmlError(f"text layer {node.get('name')!r} has no Text parameter")
    t.text = value
    # styleRun lengths count UTF-16 code units; one run keeps the first run's style
    runs = node.findall("styleRun")
    n = len(value.encode("utf-16-le")) // 2
    if runs:
        runs[0].set("offset", "0")
        runs[0].set("length", str(n))
        for r in runs[1:]:
            node.remove(r)


# ------------------------------------------------------------------------- rigs

def rigged(doc):
    """{(object_id, channel): widget name} for every Rig Behavior."""
    out = {}
    for b in doc.root.iter("behavior"):
        if doc.factory(b) != "Rig Behavior":
            continue
        cb = b.find("channelBehavior")
        o = b.find("./parameter[@id='199']")
        w = b.find("./parameter[@id='200']")
        if cb is None or o is None:
            continue
        wname = doc.objects.get(w.get("value")).get("name") if w is not None and w.get("value") in doc.objects else "?"
        out[(o.get("value"), cb.get("affectingChannel"))] = (wname, b)
    return out


def channel_of(path):
    return "./" + "/".join(path)


def _widget_snapshot_id(doc, widget_id):
    """Snapshot id of the widget's current option (its ./2/101 list maps Value -> id)."""
    w = doc.objects.get(widget_id)
    cur = param_at(w, WIDGET_VALUE) if w is not None else None
    snaps = param_at(w, ("2", "101")) if w is not None else None
    if cur is None or snaps is None:
        return None
    for sp in snaps.findall("parameter"):
        v = sp.find("./parameter[@id='1']")
        if v is not None and abs(float(v.get("value", "nan")) - float(cur.get("value", "nan"))) < 1e-6:
            return sp.get("id")
    return None


def check_rig(doc, obj_id, path, unrig=False, value=None):
    """Keep an edit to a rigged channel from being undone by its rig widget.

    A Rig Behavior stores one value per widget option (snapshot). The option the
    widget is set to is applied when the editor picks it in FCP (a checkbox state also
    at render). Default: write `value` (an (r,g,b) tuple or a number) into the
    snapshot of the widget's current option as well, so the template renders and
    re-selects with the new value and the other options keep working.
    unrig=True deletes the channel's Rig Behavior instead. Returns a log note or None.
    """
    hit = rigged(doc).get((obj_id, channel_of(path)))
    if not hit:
        return None
    wname, beh = hit
    if unrig:
        doc.parent[beh].remove(beh)
        doc.reindex()
        return f"removed {wname!r} rig on {channel_of(path)}"
    w = beh.find("./parameter[@id='200']")
    sid = _widget_snapshot_id(doc, w.get("value")) if w is not None else None
    snap = beh.find(f"./parameter[@id='202']/parameter[@id='{sid}']") if sid else None
    if snap is None or value is None:
        raise OzmlError(f"object {obj_id} channel {channel_of(path)} is driven by rig widget {wname!r} "
                        f"and its current option can't be updated here; --set the widget, or pass --unrig")
    if isinstance(value, tuple):
        for (cid, _), v in zip(RGB, value):
            c = snap.find(f"./parameter[@id='{cid}']/curve")
            if c is None:
                raise OzmlError(f"rig {wname!r} snapshot {sid} has no {cid} component; pass --unrig")
            c.set("value", fmt_num(v))
    else:
        c = snap.find("curve")
        if c is None:
            raise OzmlError(f"rig {wname!r} snapshot {sid} holds no plain value; pass --unrig")
        c.set("value", fmt_num(float(value)))
    return f"also set {wname!r} option snapshot {sid} (the widget's current option)"


def check_style_rig(doc, text_node, style, path, unrig=False, value=None):
    """A text style's channel can be rigged two ways: on the style object (./14/16) or
    on the text layer through its style list (./5/<style id>/14/16)."""
    notes = [check_rig(doc, style.get("id"), path, unrig, value),
             check_rig(doc, text_node.get("id"), ("5", style.get("id")) + tuple(path), unrig, value)]
    return [n for n in notes if n]


# --------------------------------------------------------------------- publishing

def publish_settings(doc, create=False):
    ps = doc.scene.find("publishSettings")
    if ps is None and create:
        ps = ET.Element("publishSettings")
        ET.SubElement(ps, "version").text = "2"
        idx = list(doc.scene).index(doc.scene.find("sceneSettings")) + 1 if doc.scene.find("sceneSettings") is not None else 0
        doc.scene.insert(idx, ps)
        ps.text, ps.tail = "\n\t\t", "\n\t"
    return ps


def targets(doc):
    ps = publish_settings(doc)
    return [] if ps is None else ps.findall("target")


def resolve_target(doc, t):
    obj = doc.objects.get(t.get("object"))
    path = [x for x in (t.get("channel") or "").split("/") if x not in (".", "")]
    p = param_at(obj, path) if obj is not None else None
    return obj, path, p


def describe_param(p):
    if p is None:
        return "default", None
    if p.find("font") is not None:
        return "font", p.findtext("font")
    if p.find("text") is not None:
        return "text", p.findtext("text")
    if p.get("value") is not None and p.find("./parameter[@name='Red']") is None:
        return "value", p.get("value")
    if is_color(p):
        return "color", hex_of(get_rgb(p))
    return "group", None


def owner_name(doc, obj):
    if obj is None:
        return None
    if obj.tag == "style":
        par = doc.parent.get(obj)
        return f"{par.get('name')} (style)" if par is not None else "style"
    return obj.get("name")


# ------------------------------------------------------------------------ fonts

APP_FONT_DIRS = [os.path.join(app, "Contents/Frameworks/Flexo.framework/Versions/A/Resources/Fonts")
                 for app in (FCP_APP, MOTION_APP)]

_SYS_FONT_JS = ("ObjC.import('AppKit');function run(a){return a.map(function(n){return n+'\\t'+"
                "($.NSFont.fontWithNameSize(n,12).isNil()?'0':'1')}).join('\\n')}")


def _ps_names(path):
    """PostScript names (name ID 6) in an .otf/.ttf/.ttc file, read from its name table."""
    out = []
    try:
        with open(path, "rb") as f:
            data = f.read()
    except OSError:
        return out
    offsets = [0]
    if data[:4] == b"ttcf":
        n = struct.unpack(">I", data[8:12])[0]
        offsets = list(struct.unpack(f">{n}I", data[12:12 + 4 * n]))
    for off in offsets:
        try:
            num = struct.unpack(">H", data[off + 4:off + 6])[0]
            for i in range(num):
                tag, _, toff, _ = struct.unpack(">4sIII", data[off + 12 + 16 * i:off + 28 + 16 * i])
                if tag != b"name":
                    continue
                _, count, soff = struct.unpack(">HHH", data[toff:toff + 6])
                for r in range(count):
                    pid, eid, _, nid, ln, so = struct.unpack(">6H", data[toff + 6 + 12 * r:toff + 18 + 12 * r])
                    if nid != 6:
                        continue
                    raw = data[toff + soff + so:toff + soff + so + ln]
                    out.append(raw.decode("utf-16-be" if pid in (0, 3) else "latin-1", "replace"))
                    break
        except struct.error:
            continue
    return out


_APP_FONTS = None


def app_fonts():
    global _APP_FONTS
    if _APP_FONTS is None:
        _APP_FONTS = set()
        for d in APP_FONT_DIRS:
            if os.path.isdir(d):
                for f in os.listdir(d):
                    if f.lower().endswith((".otf", ".ttf", ".ttc")):
                        _APP_FONTS.update(_ps_names(os.path.join(d, f)))
    return _APP_FONTS


def font_check(names):
    """{postscript name: 'system' | 'app' | 'missing' | None}. 'app' = one of the fonts
    Final Cut Pro and Motion ship privately (fine inside FCP). Motion silently swaps a
    missing font for Helvetica, so a typo would otherwise only show in the render."""
    names = list(names)
    if not names:
        return {}
    try:
        p = subprocess.run(["osascript", "-l", "JavaScript", "-e", _SYS_FONT_JS] + names,
                           capture_output=True, text=True, timeout=30)
        sys_ok = dict(line.rsplit("\t", 1) for line in p.stdout.splitlines() if "\t" in line)
    except (OSError, subprocess.TimeoutExpired):
        return {n: None for n in names}
    bundled = app_fonts()
    return {n: "system" if sys_ok.get(n) == "1" else "app" if n in bundled
            else "missing" if n in sys_ok else None for n in names}


def font_suggest(fragment, limit=12):
    js = ("ObjC.import('AppKit');function run(a){var f=ObjC.deepUnwrap($.NSFontManager.sharedFontManager"
          ".availableFonts);var q=a[0].toLowerCase().replace(/[^a-z0-9]/g,'');return f.filter(x=>x.toLowerCase()"
          ".replace(/[^a-z0-9]/g,'').indexOf(q)>=0).slice(0," + str(limit) + ").join('\\n')}")
    p = subprocess.run(["osascript", "-l", "JavaScript", "-e", js, fragment],
                       capture_output=True, text=True, timeout=30)
    return [x for x in p.stdout.splitlines() if x]


# --------------------------------------------------------------------- templates

def scene_info(doc):
    s = doc.scene.find("sceneSettings")
    g = (lambda k: s.findtext(k) if s is not None else None)
    fps = float(g("frameRate") or 0) or None
    if fps and g("NTSC") == "1":
        fps = fps * 1000 / 1001
    frames = int(g("duration") or 0)
    return {"width": int(g("width") or 0), "height": int(g("height") or 0),
            "fps": round(fps, 3) if fps else None, "frames": frames,
            "seconds": round(frames / fps, 3) if fps else None}


def media_refs(doc):
    out = []
    for c in doc.root.iter("clip"):
        for tag in ("relativeURL", "pathURL"):
            v = c.findtext(tag)
            if v:
                out.append({"clip": c.get("name"), tag: v})
                break
    return out


def fcp_uid(installed_path):
    """FCPXML effect uid of a template under ~/Movies/Motion Templates.localized."""
    rel = os.path.relpath(installed_path, USER_ROOT)
    if rel.startswith(".."):
        raise OzmlError(f"{installed_path} is not under {USER_ROOT}")
    return "~/" + rel.replace(os.sep, "/")


def strip_localized(part):
    return part[:-len(".localized")] if part.endswith(".localized") else part


def walk_templates(roots):
    for root in roots:
        if not os.path.isdir(root):
            continue
        for dirpath, dirs, files in os.walk(root):
            dirs.sort()
            for f in sorted(files):
                ext = os.path.splitext(f)[1].lower()
                if ext in KINDS:
                    full = os.path.join(dirpath, f)
                    rel = os.path.relpath(full, root).split(os.sep)
                    yield {"name": os.path.splitext(f)[0], "kind": KINDS[ext],
                           "category": "/".join(strip_localized(x) for x in rel[1:-2]) or "",
                           "path": full, "root": root}


# ------------------------------------------------------------------------- edits

OPS = ("text", "font", "size", "color", "fill", "opacity", "set", "publish", "unpublish")
PUBLISHABLE = {  # prop -> (layer kind, path, parameter names to create)
    "color": ("text", STYLE_COLOR, [("Face", "8589938704"), ("Color", COLOR_FLAGS["style"][0])]),
    "font": ("text", STYLE_FONT, None),
    "size": ("text", STYLE_SIZE, None),
    "text": ("text", TEXT_PARAM, None),
    "fill": ("shape", SHAPE_FILL, None),
    "opacity": ("any", OPACITY, None),
    "position": ("any", POSITION, None),
}


def _style_color(st):
    face = param_at(st, ("14",), create=[("Face", "8589938704")])
    return param_at(face, ("16",), create=[("Color", COLOR_FLAGS["style"][0])])


def _any_layer(doc, sel):
    nodes = [n for n in doc.root.iter("scenenode") if doc.factory(n) not in ("Widget", "Project", "Rig")]
    nodes += list(doc.root.iter("group"))
    return pick(nodes, sel, "layer")


def apply_edits(doc, ops, unrig=False):
    """ops: [(op, target, value)] — see motn-edit.py for the grammar. Returns a log."""
    log = []
    for op, target, value in ops:
        if op == "text":
            for n in pick(text_layers(doc), target, "text layer"):
                note = check_rig(doc, n.get("id"), TEXT_PARAM, unrig)
                set_text(n, value)
                log += [note] if note else []
                log.append(f"text {n.get('name')!r} = {value!r}")
        elif op in ("font", "size", "color"):
            for n in pick(text_layers(doc), target, "text layer"):
                for st in styles_of(n):
                    path = {"font": STYLE_FONT, "size": STYLE_SIZE, "color": STYLE_COLOR}[op]
                    rv = parse_color(value) if op == "color" else float(value) if op == "size" else None
                    log += check_style_rig(doc, n, st, path, unrig, rv)
                    if op == "font":
                        p = param_at(st, STYLE_FONT)
                        if p is None or p.find("font") is None:
                            raise OzmlError(f"{n.get('name')!r}: style has no Font parameter")
                        p.find("font").text = value
                    elif op == "size":
                        p = param_at(st, STYLE_SIZE)
                        if p is None:
                            p = ET.SubElement(st, "parameter", {"name": "Size", "id": "3",
                                                                "flags": "8606711824", "default": "48"})
                            _tidy(st, p)
                        p.set("value", fmt_num(float(value)))
                    else:
                        set_rgb(_style_color(st), parse_color(value), COLOR_FLAGS["style"][1])
                log.append(f"{op} {n.get('name')!r} = {value}")
        elif op == "fill":
            for n in pick(shape_layers(doc), target, "shape"):
                note = check_rig(doc, n.get("id"), SHAPE_FILL, unrig, parse_color(value))
                log += [note] if note else []
                p = param_at(n, SHAPE_FILL, create=[("Object", "8589938704"), ("Style", "8589938704"),
                                                     ("Fill", "8589938704"), ("Fill Color", COLOR_FLAGS["shape"][0])])
                set_rgb(p, parse_color(value), COLOR_FLAGS["shape"][1])
                log.append(f"fill {n.get('name')!r} = {value}")
        elif op == "opacity":
            v = float(value)
            if not 0 <= v <= 1:
                raise OzmlError(f"--opacity {target}={value}: use 0..1")
            for n in _any_layer(doc, target):
                note = check_rig(doc, n.get("id"), OPACITY, unrig, v)
                log += [note] if note else []
                p = param_at(n, OPACITY, create=[("Properties", "8589938704"), ("Blending", "8589938704"),
                                                 ("Opacity", "8606711824")])
                if p.get("default") is None:
                    p.set("default", "1")
                p.set("value", fmt_num(v))
                log.append(f"opacity {n.get('name')!r} = {value}")
        elif op == "set":
            ts = [t for t in targets(doc) if (t.get("name") or "").lower() == target.lower()]
            if not ts:
                have = ", ".join(repr(t.get("name")) for t in targets(doc)) or "none"
                raise OzmlError(f"no published parameter named {target!r} (have: {have})")
            for t in ts:
                obj, path, p = resolve_target(doc, t)
                if obj is None:
                    raise OzmlError(f"published {target!r} points at missing object {t.get('object')}")
                kind, _ = describe_param(p)
                is_col = kind == "color" or (p is None and "color" in target.lower())
                rv = parse_color(value) if is_col else None
                if rv is None and kind in ("value", "default"):
                    try:
                        rv = float(value)
                    except ValueError:
                        rv = None
                note = check_rig(doc, t.get("object"), path, unrig, rv)
                log += [note] if note else []
                obj, path, p = resolve_target(doc, t)
                if kind == "font":
                    p.find("font").text = value
                elif kind == "text":
                    if obj.tag == "scenenode" and doc.factory(obj) == "Text" and tuple(path) == TEXT_PARAM:
                        set_text(obj, value)
                    else:
                        p.find("text").text = value
                elif kind == "color" or (p is None and "color" in target.lower()):
                    if p is None:
                        p = param_at(obj, path, create=[(f"Param {x}", "8589938704") for x in path])
                    set_rgb(p, parse_color(value))
                else:
                    if p is None:
                        p = param_at(obj, path, create=[(f"Param {x}", "8589938704") for x in path])
                        p.set("flags", "8606711824")
                        p.set("default", value)
                    p.set("value", value)
                log.append(f"set {t.get('name')!r} = {value}")
        elif op == "publish":
            layer, _, prop = target.rpartition(":")
            if prop not in PUBLISHABLE or not layer:
                raise OzmlError(f"--publish {target!r}: use LAYER:PROP=Name, PROP one of {', '.join(PUBLISHABLE)}")
            if any((t.get("name") or "").lower() == value.lower() for t in targets(doc)):
                raise OzmlError(f"a published parameter is already named {value!r}")
            lk, path, create = PUBLISHABLE[prop]
            nodes = (pick(text_layers(doc), layer, "text layer") if lk == "text" else
                     pick(shape_layers(doc), layer, "shape") if lk == "shape" else _any_layer(doc, layer))
            if len(nodes) != 1:
                raise OzmlError(f"--publish needs exactly one layer, {layer!r} matches {len(nodes)}")
            n = nodes[0]
            obj = n.find("style") if prop in ("color", "font", "size") else n
            if obj is None:
                raise OzmlError(f"{n.get('name')!r} has no style")
            if prop == "color":
                _style_color(obj)
            elif param_at(obj, path) is None:
                raise OzmlError(f"{n.get('name')!r} has no {prop} parameter at {channel_of(path)}")
            ps = publish_settings(doc, create=True)
            t = ET.SubElement(ps, "target", {"object": obj.get("id"), "channel": channel_of(path), "name": value})
            _tidy(ps, t)
            log.append(f"published {n.get('name')} {prop} as {value!r}")
        elif op == "unpublish":
            ps = publish_settings(doc)
            hits = [t for t in targets(doc) if (t.get("name") or "").lower() == target.lower()]
            if not hits:
                raise OzmlError(f"no published parameter named {target!r}")
            for t in hits:
                ps.remove(t)
            log.append(f"unpublished {target!r}")
        else:
            raise OzmlError(f"unknown edit {op!r}")
        doc.reindex()
    return log
