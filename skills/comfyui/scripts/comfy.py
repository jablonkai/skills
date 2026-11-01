#!/usr/bin/env python3
"""Drive a local ComfyUI server over its HTTP API — standard library only (Python 3.9+).

Commands (JSON on stdout, progress on stderr, exit 1 on failure):
  status                         server, version, device memory, queue
  server start|stop              start/stop a headless ComfyUI started by this script
  nodes [--search T] [--class C] node catalog from /object_info
  models [FOLDER] [--all]        model folders, or the files in one / all of them
  convert UI.json -o API.json    UI-format workflow (File > Save) -> API format
  inspect WF                     node ids, classes, titles and literal inputs
  validate WF [overrides]        check a workflow against /object_info before queuing
  run WF [overrides] --out DIR   queue, wait, download outputs + .params.json sidecars
  collect PROMPT_ID --out DIR    wait for / download an already queued prompt (after a timeout)
  batch WF --prompts F|--images D [--seeds S] --out DIR
  upload FILE                    copy a file into ComfyUI's input folder
  stop                           interrupt the running prompt and clear the queue
  history PROMPT_ID              raw /history entry

Overrides: --set TARGET.input=VALUE (TARGET = node id, _meta.title or unique class_type;
a bare param name exposed by a converted subgraph also works: --set prompt=...),
VALUE is JSON when it parses, else a string; @path uploads a local file and uses its
input name. Shortcuts: --prompt --negative --seed --steps --width --height --image --mask.
"""
import argparse
import copy
import difflib
import json
import mimetypes
import os
import re
import signal
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid

LOOPBACK = {"127.0.0.1", "localhost", "::1", "[::1]"}
DEFAULT_PORTS = (8188, 8000)  # headless / source install, Comfy Desktop
STATE_DIR = os.path.expanduser("~/.cache/comfyui-skill")
CLIENT_PREFIX = "comfyui-skill-"  # client_id prefix: lets `stop` tell our prompts from the editor's
VIRTUAL_NODES = {"Note", "MarkdownNote", "Reroute", "PrimitiveNode"}
DYNAMIC_TYPES = {"COMFY_AUTOGROW_V3", "COMFY_DYNAMICSLOT_V3", "COMFY_DYNAMICGROUP_V3"}
WIDGET_TYPES = {"INT", "FLOAT", "STRING", "BOOLEAN", "COMBO"}
TEXT_INPUTS = ("text", "prompt", "value", "string", "text_g")
NON_MODEL_FOLDERS = {"custom_nodes", "configs"}
IMAGE_EXT = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff"}


class ComfyError(Exception):
    def __init__(self, message, detail=None):
        super().__init__(message)
        self.detail = detail


def log(msg):
    print(msg, file=sys.stderr, flush=True)


# ---------------------------------------------------------------- HTTP client

class Client:
    def __init__(self, url):
        self.url = url.rstrip("/")
        self._oi = None

    def request(self, method, path, body=None, headers=None, raw=False, timeout=30):
        data = None
        hdrs = dict(headers or {})
        if body is not None and not isinstance(body, bytes):
            data = json.dumps(body).encode()
            hdrs["Content-Type"] = "application/json"
        elif body is not None:
            data = body
        req = urllib.request.Request(self.url + path, data=data, method=method, headers=hdrs)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                payload = r.read()
        except urllib.error.HTTPError as e:
            payload = e.read()
            try:
                detail = json.loads(payload)
            except ValueError:
                detail = payload.decode(errors="replace")[:2000]
            raise ComfyError("HTTP %d on %s %s" % (e.code, method, path), detail)
        except (urllib.error.URLError, OSError) as e:
            raise ComfyError("cannot reach ComfyUI at %s (%s)" % (self.url, getattr(e, "reason", e)))
        if raw:
            return payload
        return json.loads(payload) if payload else None

    def get(self, path, **kw):
        return self.request("GET", path, **kw)

    def post(self, path, body=None, **kw):
        return self.request("POST", path, body if body is not None else {}, **kw)

    def object_info(self):
        if self._oi is None:
            self._oi = self.get("/object_info", timeout=120)
        return self._oi

    def upload(self, path, subfolder="", overwrite=True, kind="image"):
        boundary = uuid.uuid4().hex
        name = os.path.basename(path)
        ctype = mimetypes.guess_type(name)[0] or "application/octet-stream"
        with open(path, "rb") as f:
            content = f.read()
        parts = []
        for key, val in (("type", "input"), ("subfolder", subfolder),
                         ("overwrite", "true" if overwrite else "false")):
            parts.append(("--%s\r\nContent-Disposition: form-data; name=\"%s\"\r\n\r\n%s\r\n"
                          % (boundary, key, val)).encode())
        parts.append(("--%s\r\nContent-Disposition: form-data; name=\"image\"; filename=\"%s\"\r\n"
                      "Content-Type: %s\r\n\r\n" % (boundary, name, ctype)).encode() + content + b"\r\n")
        parts.append(("--%s--\r\n" % boundary).encode())
        res = self.request("POST", "/upload/" + kind, b"".join(parts),
                           headers={"Content-Type": "multipart/form-data; boundary=" + boundary},
                           timeout=300)
        ref = res["name"] if not res.get("subfolder") else res["subfolder"] + "/" + res["name"]
        self._oi = None  # LoadImage's file list in /object_info is now stale
        return ref, res


def check_loopback(url, allow_remote):
    host = urllib.parse.urlparse(url).hostname or ""
    if host not in LOOPBACK and not allow_remote:
        raise ComfyError("refusing non-loopback ComfyUI URL %s: the API has no authentication. "
                         "Pass --allow-remote only if the user asked for that host." % url)


def find_server(args):
    if args.url:
        check_loopback(args.url, args.allow_remote)
        return Client(args.url)
    env = os.environ.get("COMFYUI_URL")
    if env:
        check_loopback(env, args.allow_remote)
        return Client(env)
    for port in DEFAULT_PORTS:
        c = Client("http://127.0.0.1:%d" % port)
        try:
            c.get("/system_stats", timeout=2)
            return c
        except ComfyError:
            continue
    raise ComfyError("no ComfyUI server on 127.0.0.1:%s — start one with `comfy.py server start` "
                     "(or open Comfy Desktop)" % "/".join(map(str, DEFAULT_PORTS)))


# ---------------------------------------------------------------- workflow loading

def is_ui_format(wf):
    return isinstance(wf, dict) and isinstance(wf.get("nodes"), list) and "links" in wf


def load_workflow(path, client, keep_previews=False):
    """Return (api_workflow, ui_workflow_or_None, conversion_warnings)."""
    with open(path) as f:
        wf = json.load(f)
    if isinstance(wf, dict) and "prompt" in wf and isinstance(wf["prompt"], dict) and not is_ui_format(wf):
        wf = wf["prompt"]  # a saved /prompt request body
    if is_ui_format(wf):
        api, warnings = convert_ui(wf, client.object_info(), keep_previews=keep_previews)
        return api, wf, warnings
    if not isinstance(wf, dict) or not all(isinstance(v, dict) and "class_type" in v for v in wf.values()):
        raise ComfyError("%s is neither an API-format workflow (node id -> {class_type, inputs}) "
                         "nor a UI-format workflow (nodes + links)" % path)
    return wf, None, []


# ---------------------------------------------------------------- UI -> API conversion

def spec_type(spec):
    t = spec[0] if isinstance(spec, (list, tuple)) and spec else spec
    return "COMBO" if isinstance(t, list) else t


def spec_opts(spec):
    return spec[1] if isinstance(spec, (list, tuple)) and len(spec) > 1 and isinstance(spec[1], dict) else {}


def ordered_inputs(info):
    order = info.get("input_order") or {}
    out = []
    for sect in ("required", "optional"):
        specs = info.get("input", {}).get(sect, {}) or {}
        for name in order.get(sect, list(specs)):
            if name in specs:
                out.append((name, specs[name], sect))
    return out


def widget_values(node, info):
    """Map a UI node's widget values to input names."""
    # widgets_values (positional) is what the editor executes; widgets_values_named can be
    # stale after edits, so it only supplies the names when its length matches.
    named = node.get("widgets_values_named")
    wv = node.get("widgets_values")
    if isinstance(wv, dict):
        return dict(wv)
    wv = wv or []
    if isinstance(named, dict):
        return dict(zip(named, wv)) if len(named) == len(wv) else dict(named)
    values, i = {}, 0
    for name, spec, _ in ordered_inputs(info):
        t, opts = spec_type(spec), spec_opts(spec)
        if t not in WIDGET_TYPES or opts.get("forceInput"):
            continue
        if i >= len(wv):
            break
        values[name] = wv[i]
        i += 1
        if opts.get("control_after_generate"):
            i += 1
        if any(k.endswith("_upload") and v for k, v in opts.items()):
            i += 1
    return values


def norm_links(links):
    out = {}
    for l in links or []:
        if isinstance(l, list):
            out[l[0]] = {"origin_id": l[1], "origin_slot": l[2], "target_id": l[3], "target_slot": l[4], "type": l[5]}
        else:
            out[l["id"]] = l
    return out


class Graph:
    def __init__(self, data, prefix, subgraphs, ext=None, sg_inputs=None):
        self.nodes = {n["id"]: n for n in data["nodes"]}
        self.links = norm_links(data.get("links"))
        self.prefix = prefix
        self.subgraphs = subgraphs
        self.ext = ext            # slot -> source, for subgraph input slots (-10)
        self.sg_inputs = sg_inputs or []
        self.children = {}

    def child(self, node):
        if node["id"] not in self.children:
            sg = self.subgraphs[node["type"]]
            inst_inputs = {i["name"]: i for i in node.get("inputs", [])}
            named = node.get("widgets_values_named")
            wv = node.get("widgets_values") or []
            if isinstance(named, dict) and len(named) == len(wv):
                named = dict(zip(named, wv))
            elif not isinstance(named, dict) or isinstance(wv, list) and len(wv) == len(sg.get("inputs", [])):
                named = {s["name"]: wv[k] for k, s in enumerate(sg.get("inputs", [])) if k < len(wv)}

            def ext(slot, sg=sg, inst_inputs=inst_inputs, named=named):
                sgi = sg["inputs"][slot]
                inp = inst_inputs.get(sgi["name"])
                if inp is not None and inp.get("link") is not None:
                    return self.resolve(inp["link"])
                if sgi["name"] in named:
                    return ("value", named[sgi["name"]], sgi.get("label") or sgi["name"])
                return None
            self.children[node["id"]] = Graph(sg, "%s%s:" % (self.prefix, node["id"]), self.subgraphs,
                                              ext, sg.get("inputs"))
        return self.children[node["id"]]

    def resolve(self, link_id, depth=0):
        """Source of a link: ('link', api_id, slot) | ('value', v, label) | None."""
        if depth > 64:
            raise ComfyError("link cycle while converting workflow")
        link = self.links.get(link_id)
        if link is None:
            return None
        oid, slot = link["origin_id"], link["origin_slot"]
        if oid == -10:
            return self.ext(slot) if self.ext else None
        node = self.nodes.get(oid)
        if node is None:
            return None
        if node["type"] in self.subgraphs:
            child = self.child(node)
            for cl in child.links.values():
                if cl["target_id"] == -20 and cl["target_slot"] == slot:
                    return child.resolve(next(k for k, v in child.links.items() if v is cl), depth + 1)
            return None
        if node["type"] == "Reroute":
            ins = node.get("inputs") or []
            return self.resolve(ins[0]["link"], depth + 1) if ins and ins[0].get("link") is not None else None
        if node["type"] == "PrimitiveNode":
            return ("value", (node.get("widgets_values") or [None])[0], node.get("title"))
        mode = node.get("mode", 0)
        if mode == 2:
            return None
        if mode == 4:  # bypassed: pass through the first linked input of the same type
            out_type = (node.get("outputs") or [{}])[slot].get("type") if slot < len(node.get("outputs") or []) else None
            ins = [i for i in node.get("inputs", []) if i.get("link") is not None]
            same = [i for i in ins if i.get("type") == out_type] or ins
            return self.resolve(same[0]["link"], depth + 1) if same else None
        return ("link", self.prefix + str(oid), slot)


def convert_ui(ui, oi, keep_previews=False):
    subgraphs = {sg["id"]: sg for sg in (ui.get("definitions") or {}).get("subgraphs", [])}
    api, warnings = {}, []

    def emit(graph):
        for node in graph.nodes.values():
            ntype, mode = node["type"], node.get("mode", 0)
            if mode in (2, 4):
                continue
            if ntype in graph.subgraphs:
                emit(graph.child(node))
                continue
            if ntype in VIRTUAL_NODES:
                continue
            info = oi.get(ntype)
            connected = any(i.get("link") is not None for i in node.get("inputs", [])) or \
                any(o.get("links") for o in node.get("outputs", []))
            if info is None and not connected:
                warnings.append("skipped unconnected unknown node %s%s (%s)" % (graph.prefix, node["id"], ntype))
                continue
            nid = graph.prefix + str(node["id"])
            inputs, params = {}, {}
            if info is None:
                warnings.append("node %s uses class %s, which this server does not have "
                                "(missing custom node?)" % (nid, ntype))
                info = {"input": {}}
            known = {name for name, _, _ in ordered_inputs(info)}
            for name, val in widget_values(node, info).items():
                if name in known or name.split(".")[0] in known:  # "format.bit_depth": dynamic sub-input
                    # a bare list would read as a [node_id, slot] link; the editor wraps it the same way
                    inputs[name] = {"__value__": val} if isinstance(val, list) else val
            for inp in node.get("inputs", []):
                if inp.get("link") is None:
                    continue
                src = graph.resolve(inp["link"])
                if src is None:
                    continue
                if src[0] == "link":
                    inputs[inp["name"]] = [src[1], src[2]]
                else:
                    inputs[inp["name"]] = src[1]
                    if src[2]:
                        params[inp["name"]] = src[2]
            meta = {"title": node.get("title") or info.get("display_name") or ntype}
            if params:
                meta["params"] = params
            api[nid] = {"class_type": ntype, "inputs": inputs, "_meta": meta}

    emit(Graph(ui, "", subgraphs))
    if not keep_previews:
        used = {str(v[0]) for n in api.values() for v in n["inputs"].values() if is_link(v)}
        dropped = [k for k, v in api.items() if k not in used and
                   (v["class_type"].startswith("Preview") or v["class_type"] == "ImageCompare")]
        for k in dropped:
            del api[k]
        if dropped:
            warnings.append("dropped preview-only nodes %s (keep them with --keep-previews)" % ", ".join(dropped))
    return prune_unreachable(api, oi, warnings), warnings


def prune_unreachable(api, oi, warnings):
    outputs = [k for k, v in api.items() if (oi.get(v["class_type"]) or {}).get("output_node")]
    keep, stack = set(), list(outputs)
    while stack:
        k = stack.pop()
        if k in keep or k not in api:
            continue
        keep.add(k)
        for v in api[k]["inputs"].values():
            if is_link(v):
                stack.append(str(v[0]))
    dropped = sorted(set(api) - keep)
    if dropped and outputs:
        warnings.append("dropped %d node(s) that feed no output: %s" % (len(dropped), ", ".join(dropped)))
        return {k: v for k, v in api.items() if k in keep}
    return api


# ---------------------------------------------------------------- overrides

def is_link(v):
    return isinstance(v, list) and len(v) == 2 and isinstance(v[0], (str, int)) and isinstance(v[1], int)


def parse_value(text):
    try:
        return json.loads(text)
    except ValueError:
        return text


def match_target(wf, target):
    if target in wf:
        return [target]
    by_title = [k for k, v in wf.items() if (v.get("_meta") or {}).get("title") == target]
    if by_title:
        return by_title
    return [k for k, v in wf.items() if v["class_type"] == target]


def apply_set(wf, spec, client, uploads):
    if "=" not in spec:
        raise ComfyError("--set needs TARGET.input=VALUE, got %r" % spec)
    key, raw = spec.split("=", 1)
    value = parse_value(raw)
    if isinstance(value, str) and value.startswith("@"):
        local = os.path.expanduser(value[1:])
        if local not in uploads:
            uploads[local] = client.upload(local)[0]
        value = uploads[local]
    for i in [m.start() for m in re.finditer(r"\.", key)]:
        target, inp = key[:i], key[i + 1:]
        ids = match_target(wf, target)
        if not ids:
            continue
        if len(ids) > 1:
            raise ComfyError("%r matches several nodes (%s); use the node id" % (target, ", ".join(ids)))
        node = wf[ids[0]]
        if inp == "class_type":
            node["class_type"] = value
        else:
            node["inputs"][inp] = value
        return ["%s.%s" % (ids[0], inp)]
    hits = []  # a bare param exposed by a converted subgraph, e.g. --set prompt=...
    for nid, node in wf.items():
        for inp, label in ((node.get("_meta") or {}).get("params") or {}).items():
            if key in (label, inp) and not is_link(node["inputs"].get(inp)):
                node["inputs"][inp] = value
                hits.append("%s.%s" % (nid, inp))
    if hits:
        return hits
    raise ComfyError("no node or exposed param matches %r (by id, _meta.title, class_type or param label)" % key)


def set_all(wf, names, value, label, oi, out_types=None):
    """Set every matching input; a link (e.g. from a ResolutionSelector) is replaced by the value."""
    hits = []
    for nid, node in wf.items():
        if out_types and not set((oi.get(node["class_type"]) or {}).get("output") or []) & out_types:
            continue
        for n in names:
            if n in node["inputs"]:
                hits.append("%s.%s%s" % (nid, n, " (replaced link)" if is_link(node["inputs"][n]) else ""))
                node["inputs"][n] = value
    if not hits:
        raise ComfyError("--%s: no %s input in this workflow; use --set ID.input=VALUE" % (label, "/".join(names)))
    return hits


def find_text_input(wf, role):
    """Literal text input feeding the sampler's positive/negative conditioning."""
    labels = {"positive": ("prompt", "positive", "text"), "negative": ("negative", "negative_prompt")}[role]
    for nid, node in wf.items():
        for inp, label in ((node.get("_meta") or {}).get("params") or {}).items():
            if label.lower() in labels and isinstance(node["inputs"].get(inp), str):
                return nid, inp
    starts = [node["inputs"][role] for node in wf.values() if is_link(node["inputs"].get(role))]
    seen, queue = set(), [str(s[0]) for s in starts]
    while queue:
        nid = queue.pop(0)
        if nid in seen or nid not in wf:
            continue
        seen.add(nid)
        ins = wf[nid]["inputs"]
        for name in TEXT_INPUTS:
            if isinstance(ins.get(name), str):
                return nid, name
        for name in TEXT_INPUTS:
            if is_link(ins.get(name)):
                queue.insert(0, str(ins[name][0]))
        queue.extend(str(v[0]) for k, v in ins.items() if is_link(v) and k not in TEXT_INPUTS)
    return None


def unique_class(wf, classes, flag):
    ids = [k for k, v in wf.items() if v["class_type"] in classes]
    if len(ids) != 1:
        raise ComfyError("--%s needs exactly one %s node, found %d%s; use --set ID.image=@file"
                         % (flag, "/".join(classes), len(ids), (" (" + ", ".join(ids) + ")") if ids else ""))
    return ids[0]


def apply_overrides(wf, args, client, uploads=None):
    wf = copy.deepcopy(wf)
    uploads = {} if uploads is None else uploads
    applied = []
    for role, text in (("positive", getattr(args, "prompt", None)), ("negative", getattr(args, "negative", None))):
        if text is None:
            continue
        hit = find_text_input(wf, role)
        if hit is None:
            raise ComfyError("could not find the %s prompt input; use --set ID.text=..." % role)
        wf[hit[0]]["inputs"][hit[1]] = text
        applied.append("%s.%s" % hit)
    oi = client.object_info()
    size_nodes = {"LATENT", "IMAGE"}  # latent/image generators and scalers, not e.g. bbox editors
    for flag, names, outs in (("seed", ("seed", "noise_seed"), None), ("steps", ("steps",), None),
                              ("width", ("width",), size_nodes), ("height", ("height",), size_nodes)):
        val = getattr(args, flag, None)
        if val is not None:
            applied += set_all(wf, names, val, flag, oi, outs)
    for flag, classes in (("image", ("LoadImage",)), ("mask", ("LoadImageMask",))):
        path = getattr(args, flag, None)
        if path:
            nid = unique_class(wf, classes, flag)
            local = os.path.expanduser(path)
            if local not in uploads:
                uploads[local] = client.upload(local)[0]
            wf[nid]["inputs"]["image"] = uploads[local]
            applied.append("%s.image" % nid)
    for spec in getattr(args, "set", None) or []:
        applied += apply_set(wf, spec, client, uploads)
    return wf, applied


# ---------------------------------------------------------------- validation

def combo_options(spec):
    t = spec[0] if isinstance(spec, (list, tuple)) and spec else None
    if isinstance(t, list):
        return t
    opts = spec_opts(spec).get("options")
    if not isinstance(opts, list):
        return None
    return [o["key"] if isinstance(o, dict) and "key" in o else o for o in opts]  # DynamicCombo


def types_ok(out_type, in_type):
    if "*" in (out_type, in_type) or out_type == in_type or "_V3" in str(in_type) + str(out_type):
        return True
    a, b = set(str(out_type).split(",")), set(str(in_type).split(","))
    return bool(a & b) or (in_type == "COMBO" and isinstance(out_type, (str, list)))


def validate(wf, oi):
    errors, warnings = {}, []

    def err(nid, kind, msg, inp=None):
        errors.setdefault(nid, []).append({"type": kind, "input": inp, "message": msg})

    has_output = False
    for nid, node in wf.items():
        ctype = node.get("class_type")
        info = oi.get(ctype)
        if info is None:
            close = difflib.get_close_matches(str(ctype), list(oi), n=3)
            err(nid, "unknown_class", "class %s is not installed on this server%s" % (
                ctype, ("; did you mean " + ", ".join(close)) if close else " (missing custom node?)"))
            continue
        has_output = has_output or bool(info.get("output_node"))
        ins = node.get("inputs", {})
        specs = {}
        for name, spec, sect in ordered_inputs(info):
            specs[name] = spec
            if sect == "required" and name not in ins and spec_type(spec) not in DYNAMIC_TYPES:
                err(nid, "required_input_missing", "required input %s is missing" % name, name)
        for name, val in ins.items():
            spec = specs.get(name)
            if is_link(val):
                src = wf.get(str(val[0]))
                if src is None:
                    err(nid, "bad_link", "input %s links to missing node %s" % (name, val[0]), name)
                    continue
                sinfo = oi.get(src.get("class_type")) or {}
                outs = sinfo.get("output") or []
                if sinfo and val[1] >= len(outs):
                    err(nid, "bad_link", "input %s links to output %d of %s, which has %d outputs"
                        % (name, val[1], src["class_type"], len(outs)), name)
                elif sinfo and spec is not None and not types_ok(outs[val[1]], spec_type(spec)):
                    err(nid, "return_type_mismatch", "input %s expects %s but %s output %d is %s"
                        % (name, spec_type(spec), src["class_type"], val[1], outs[val[1]]), name)
                continue
            if isinstance(val, list):
                err(nid, "bad_linked_input", "input %s is a list but not a [node_id, slot] link; "
                    "wrap literal lists as {\"__value__\": [...]}" % name, name)
                continue
            if isinstance(val, dict) and "__value__" in val:
                val = val["__value__"]
            if spec is None:
                if "." not in name:
                    warnings.append("node %s (%s): unknown input %s is ignored by the server" % (nid, ctype, name))
                continue
            t, opts = spec_type(spec), spec_opts(spec)
            options = combo_options(spec)
            if options is not None and val not in options:
                close = difflib.get_close_matches(str(val), [str(o) for o in options], n=3)
                err(nid, "value_not_in_list", "%s=%r is not installed/allowed%s" % (
                    name, val, ("; closest: " + ", ".join(close)) if close else
                    ("; options: " + ", ".join(map(str, options[:8])) if options else "; no options installed")), name)
            elif t in ("INT", "FLOAT"):
                if isinstance(val, bool) or not isinstance(val, (int, float)) or (t == "INT" and float(val) != int(val)):
                    err(nid, "invalid_input_type", "%s=%r is not %s" % (name, val, t), name)
                else:
                    if "min" in opts and val < opts["min"]:
                        err(nid, "value_smaller_than_min", "%s=%r < min %r" % (name, val, opts["min"]), name)
                    if "max" in opts and val > opts["max"]:
                        err(nid, "value_bigger_than_max", "%s=%r > max %r" % (name, val, opts["max"]), name)
            elif t == "BOOLEAN" and not isinstance(val, bool):
                err(nid, "invalid_input_type", "%s=%r is not BOOLEAN" % (name, val), name)
            elif t == "STRING" and not isinstance(val, str):
                err(nid, "invalid_input_type", "%s=%r is not STRING" % (name, val), name)
    if not has_output:
        err("_prompt", "prompt_no_outputs", "workflow has no output node (SaveImage or similar)")
    return {"valid": not errors, "errors": errors, "warnings": warnings}


# ---------------------------------------------------------------- running

def summarize(wf):
    s = {"seeds": {}, "steps": {}, "size": {}, "denoise": {}, "models": {}, "texts": {}, "images_in": {}}
    for nid, node in wf.items():
        for k, v in node["inputs"].items():
            if is_link(v):
                continue
            ref = "%s.%s" % (nid, k)
            if k in ("seed", "noise_seed"):
                s["seeds"][ref] = v
            elif k == "steps":
                s["steps"][ref] = v
            elif k in ("width", "height"):
                s["size"][ref] = v
            elif k == "denoise":
                s["denoise"][ref] = v
            elif k.endswith("_name") and isinstance(v, str) and "." in v:
                s["models"][ref] = v
            elif k in TEXT_INPUTS and isinstance(v, str):
                s["texts"][ref] = v
            elif node["class_type"] in ("LoadImage", "LoadImageMask") and k == "image":
                s["images_in"][ref] = v
    return {k: v for k, v in s.items() if v}


def submit(client, wf, ui=None):
    body = {"prompt": wf, "client_id": CLIENT_PREFIX + uuid.uuid4().hex}
    if ui is not None:
        body["extra_data"] = {"extra_pnginfo": {"workflow": ui}}
    try:
        res = client.post("/prompt", body)
    except ComfyError as e:
        if isinstance(e.detail, dict):
            raise ComfyError("server rejected the workflow: %s" % (e.detail.get("error") or {}).get("message", e),
                             e.detail)
        raise
    if res.get("node_errors"):
        # The server still queues the outputs that did validate; take the partial prompt back out.
        if res.get("prompt_id"):
            client.post("/queue", {"delete": [res["prompt_id"]]})
        raise ComfyError("server reported node_errors — the partially valid prompt was removed from the queue", res)
    return res["prompt_id"]


def wait(client, prompt_id, timeout):
    start, last = time.time(), 0.0
    while True:
        hist = client.get("/history/" + prompt_id)
        if hist and prompt_id in hist:
            entry = hist[prompt_id]
            status = entry.get("status") or {}
            if status.get("completed") or status.get("status_str") in ("success", "error"):
                return entry
        if time.time() - start > timeout:
            raise ComfyError("timed out after %ds waiting for %s — it is still queued/running; "
                             "`comfy.py collect %s --out DIR` picks the result up later (batch: --resume), "
                             "`comfy.py stop` cancels it" % (timeout, prompt_id, prompt_id),
                             {"prompt_id": prompt_id, "timed_out": True})
        if time.time() - last > 15:
            q = client.get("/queue")
            running = [i[1] for i in q.get("queue_running", [])]
            pending = [i[1] for i in q.get("queue_pending", [])]
            where = "running" if prompt_id in running else (
                "pending #%d" % (pending.index(prompt_id) + 1) if prompt_id in pending else "finishing")
            log("  %s: %s, %ds elapsed" % (prompt_id[:8], where, time.time() - start))
            last = time.time()
        time.sleep(1)


def exec_seconds(entry):
    """Server-side execution time from the status message timestamps (ms)."""
    stamps = [m[1].get("timestamp") for m in (entry.get("status") or {}).get("messages", [])
              if isinstance(m, list) and len(m) > 1 and isinstance(m[1], dict) and m[1].get("timestamp")]
    return round((max(stamps) - min(stamps)) / 1000.0, 1) if len(stamps) > 1 else None


def execution_error(entry):
    for kind, data in (entry.get("status") or {}).get("messages", []):
        if kind in ("execution_error", "execution_interrupted"):
            return {"kind": kind, "node_id": data.get("node_id"), "node_type": data.get("node_type"),
                    "message": data.get("exception_message", kind)}
    return None


def download_outputs(client, entry, out_dir, name_fmt, fields, include_temp=False):
    os.makedirs(out_dir, exist_ok=True)
    files, n = [], 0
    for nid, out in (entry.get("outputs") or {}).items():
        for kind, items in out.items():
            if not isinstance(items, list):
                continue
            for item in items:
                if not isinstance(item, dict) or "filename" not in item:
                    continue
                if item.get("type") != "output" and not include_temp:
                    continue
                q = urllib.parse.urlencode({"filename": item["filename"], "subfolder": item.get("subfolder", ""),
                                            "type": item.get("type", "output")})
                data = client.get("/view?" + q, raw=True, timeout=300)
                stem, ext = os.path.splitext(item["filename"])
                local = name_fmt.format(orig=stem, n=n, node=nid, **fields)
                if n and "{n}" not in name_fmt:
                    local += "_%d" % n
                local += ext
                path = os.path.join(out_dir, local)
                with open(path, "wb") as f:
                    f.write(data)
                files.append({"path": path, "node": nid, "kind": kind, "server_file": item})
                n += 1
    return files


def run_one(client, wf, ui, out_dir, name_fmt, fields, timeout, meta, include_temp=False, prompt_id=None):
    """Validate, queue and collect — or, given prompt_id, only collect an already queued prompt."""
    if prompt_id is None:
        report = validate(wf, client.object_info())
        if not report["valid"]:
            raise ComfyError("workflow failed validation — nothing was queued", report)
        prompt_id = submit(client, wf, ui)
        log("queued %s" % prompt_id)
    else:
        log("collecting %s" % prompt_id)
    t0 = time.time()
    entry = wait(client, prompt_id, timeout)
    elapsed = round(time.time() - t0, 1)
    failure = execution_error(entry)
    if failure:
        raise ComfyError("execution failed in node %s (%s): %s" % (failure["node_id"], failure["node_type"],
                                                                   failure["message"]), failure)
    files = download_outputs(client, entry, out_dir, name_fmt, dict(fields, prompt_id=prompt_id[:8]), include_temp)
    if not files:
        log("warning: %s finished but produced no output files (cached result, or no Save node?)" % prompt_id)
    params = dict(meta, prompt_id=prompt_id, status=(entry.get("status") or {}).get("status_str"),
                  seconds=elapsed, exec_seconds=exec_seconds(entry), parameters=summarize(wf))
    for f in files:
        with open(os.path.splitext(f["path"])[0] + ".params.json", "w") as fh:
            json.dump(dict(params, output=f), fh, indent=2, ensure_ascii=False)
    with open(os.path.join(out_dir, "runs.jsonl"), "a") as fh:
        fh.write(json.dumps(dict(params, files=[f["path"] for f in files]), ensure_ascii=False) + "\n")
    return dict(params, files=[f["path"] for f in files])


# ---------------------------------------------------------------- commands

def cmd_status(client, args):
    st = client.get("/system_stats")
    q = client.get("/queue")
    sysi = st.get("system", {})
    return {"ok": True, "url": client.url, "comfyui_version": sysi.get("comfyui_version"),
            "python": sysi.get("python_version", "").split(" ")[0], "os": sysi.get("os"),
            "ram_free_gb": round(sysi.get("ram_free", 0) / 2**30, 1),
            "ram_total_gb": round(sysi.get("ram_total", 0) / 2**30, 1),
            "devices": [{"name": d.get("name"), "type": d.get("type"),
                         "vram_free_gb": round(d.get("vram_free", 0) / 2**30, 1)} for d in st.get("devices", [])],
            "argv": sysi.get("argv"),
            "queue": {"running": [i[1] for i in q.get("queue_running", [])],
                      "pending": len(q.get("queue_pending", []))}}


def server_paths():
    os.makedirs(STATE_DIR, exist_ok=True)
    return os.path.join(STATE_DIR, "server.pid"), os.path.join(STATE_DIR, "server.log")


def cmd_server(args):
    pid_file, log_file = server_paths()
    port = args.port
    url = "http://127.0.0.1:%d" % port
    if args.action == "stop":
        if not os.path.exists(pid_file):
            raise ComfyError("no server started by this script (no %s); a server you started yourself "
                             "or Comfy Desktop is left alone" % pid_file)
        with open(pid_file) as f:
            pid = int(f.read().strip())
        try:
            os.kill(pid, signal.SIGTERM)
            for _ in range(30):
                time.sleep(0.5)
                os.kill(pid, 0)
            os.kill(pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        os.remove(pid_file)
        return {"ok": True, "stopped": pid}
    client = Client(url)
    try:
        st = client.get("/system_stats", timeout=2)
        return {"ok": True, "already_running": url, "comfyui_version": st["system"].get("comfyui_version")}
    except ComfyError:
        pass
    root = os.path.expanduser(args.root or os.environ.get("COMFYUI_ROOT") or "~/ComfyUI")
    if not os.path.exists(os.path.join(root, "main.py")):
        raise ComfyError("no ComfyUI checkout at %s (set --root or COMFYUI_ROOT)" % root)
    python = next((p for p in (os.path.join(root, d, "bin", "python") for d in (".venv", "venv"))
                   if os.path.exists(p)), sys.executable)
    cmd = [python, "main.py", "--listen", "127.0.0.1", "--port", str(port)]
    extra = list(args.extra or [])
    if extra[:1] == ["--"]:
        extra = extra[1:]
    if any(a.startswith("--listen") or a.startswith("--enable-cors") for a in extra):
        raise ComfyError("refusing --listen/--enable-cors-header: the API has no authentication")
    try:
        ram = os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES")
    except (ValueError, OSError):
        ram = 0
    if ram and ram <= 16 * 2**30 and "--cache-none" not in extra and not args.keep_cache:
        extra.append("--cache-none")  # 16 GB machines get OOM-killed a few images in otherwise
    cmd += extra
    env = dict(os.environ, PYTORCH_ENABLE_MPS_FALLBACK="1")
    with open(log_file, "ab") as lf:
        proc = subprocess.Popen(cmd, cwd=root, stdout=lf, stderr=subprocess.STDOUT, env=env,
                                start_new_session=True)
    with open(pid_file, "w") as f:
        f.write(str(proc.pid))
    deadline = time.time() + args.wait
    while time.time() < deadline:
        if proc.poll() is not None:
            os.remove(pid_file)
            with open(log_file, errors="replace") as f:
                tail = f.read()[-2000:]
            raise ComfyError("ComfyUI exited with code %s during startup" % proc.returncode, tail)
        try:
            st = client.get("/system_stats", timeout=2)
            return {"ok": True, "started": url, "pid": proc.pid, "cmd": cmd, "log": log_file,
                    "comfyui_version": st["system"].get("comfyui_version")}
        except ComfyError:
            time.sleep(2)
    raise ComfyError("server did not answer within %ds; see %s" % (args.wait, log_file))


def cmd_nodes(client, args):
    oi = client.object_info()
    if args.cls:
        info = oi.get(args.cls)
        if info is None:
            raise ComfyError("no node class %s; close: %s" % (args.cls, difflib.get_close_matches(args.cls, list(oi))))
        ins = {}
        for name, spec, sect in ordered_inputs(info):
            opts = spec_opts(spec)
            entry = {"type": spec_type(spec), "section": sect}
            opt_list = combo_options(spec)
            if opt_list is not None:
                entry["options"] = opt_list[:50]
            for k in ("default", "min", "max", "step", "multiline", "forceInput", "control_after_generate"):
                if k in opts:
                    entry[k] = opts[k]
            ins[name] = entry
        return {"class": args.cls, "display_name": info.get("display_name"), "category": info.get("category"),
                "module": info.get("python_module"), "output_node": info.get("output_node"),
                "inputs": ins, "outputs": list(zip(info.get("output_name") or [], info.get("output") or []))}
    rows = []
    term = (args.search or "").lower()
    for name, info in sorted(oi.items()):
        hay = " ".join(str(x) for x in (name, info.get("display_name"), info.get("category"))).lower()
        if term and term not in hay:
            continue
        rows.append({"class": name, "display_name": info.get("display_name"), "category": info.get("category"),
                     "custom": not str(info.get("python_module", "")).startswith(("nodes", "comfy_extras", "comfy_api"))})
    return {"count": len(rows), "nodes": rows}


def cmd_models(client, args):
    folders = client.get("/models")
    if args.folder:
        return {"folder": args.folder, "files": client.get("/models/" + urllib.parse.quote(args.folder))}
    if not args.all:
        return {"folders": folders}
    res = {}
    folders = [f for f in folders if f not in NON_MODEL_FOLDERS]
    for f in folders:
        try:
            files = client.get("/models/" + urllib.parse.quote(f))
        except ComfyError:
            continue
        if files:
            res[f] = files
    return {"non_empty_folders": res, "empty": [f for f in folders if f not in res]}


def cmd_convert(client, args):
    with open(args.workflow) as f:
        ui = json.load(f)
    if not is_ui_format(ui):
        raise ComfyError("%s is not a UI-format workflow" % args.workflow)
    api, warnings = convert_ui(ui, client.object_info(), keep_previews=args.keep_previews)
    report = validate(api, client.object_info())
    with open(args.output, "w") as f:
        json.dump(api, f, indent=2, ensure_ascii=False)
    return {"ok": True, "output": args.output, "nodes": len(api), "warnings": warnings,
            "valid": report["valid"], "errors": report["errors"]}


def cmd_inspect(client, args):
    wf, ui, warnings = load_workflow(args.workflow, client, args.keep_previews)
    rows = []
    for nid, node in wf.items():
        lits = {k: (v[:80] + "…" if isinstance(v, str) and len(v) > 80 else v)
                for k, v in node["inputs"].items() if not is_link(v)}
        links = {k: "%s[%s]" % (v[0], v[1]) for k, v in node["inputs"].items() if is_link(v)}
        row = {"id": nid, "class": node["class_type"], "title": (node.get("_meta") or {}).get("title"),
               "literals": lits, "links": links}
        if (node.get("_meta") or {}).get("params"):
            row["params"] = node["_meta"]["params"]
        rows.append(row)
    return {"format": "ui" if ui else "api", "conversion_warnings": warnings, "nodes": rows,
            "parameters": summarize(wf)}


def cmd_validate(client, args):
    wf, ui, warnings = load_workflow(args.workflow, client, args.keep_previews)
    wf, applied = apply_overrides(wf, args, client)
    report = validate(wf, client.object_info())
    report["warnings"] = warnings + report["warnings"]
    report["overrides"] = applied
    if args.save:
        with open(args.save, "w") as f:
            json.dump(wf, f, indent=2, ensure_ascii=False)
        report["saved"] = args.save
    if not report["valid"]:
        raise ComfyError("workflow is invalid", report)
    return report


def cmd_run(client, args):
    wf, ui, warnings = load_workflow(args.workflow, client, args.keep_previews)
    for w in warnings:
        log("convert: " + w)
    wf, applied = apply_overrides(wf, args, client)
    meta = {"workflow": os.path.abspath(args.workflow), "overrides": applied, "set": args.set or []}
    res = run_one(client, wf, ui, args.out, args.name or "{orig}", {}, args.timeout, meta, args.include_temp)
    return dict(ok=True, **res)


def cmd_collect(client, args):
    """Wait for an already queued prompt (e.g. after a timeout) and download its outputs."""
    hist = client.get("/history/" + args.prompt_id) or {}
    graph = None
    if args.prompt_id in hist:
        graph = hist[args.prompt_id]["prompt"][2]
    else:
        q = client.get("/queue")
        for item in q.get("queue_running", []) + q.get("queue_pending", []):
            if item[1] == args.prompt_id:
                graph = item[2]
        if graph is None:
            raise ComfyError("prompt %s is neither in /history nor in the queue" % args.prompt_id)
    res = run_one(client, graph, None, args.out, args.name or "{orig}", {}, args.timeout,
                  {"collected": True}, args.include_temp, prompt_id=args.prompt_id)
    return dict(ok=True, **res)


def parse_seeds(spec):
    if not spec:
        return [None]
    seeds = []
    for part in str(spec).split(","):
        if "-" in part.strip()[1:]:
            a, b = part.split("-", 1)
            seeds += list(range(int(a), int(b) + 1))
        else:
            seeds.append(int(part))
    return seeds


def cmd_batch(client, args):
    wf0, ui, warnings = load_workflow(args.workflow, client, args.keep_previews)
    for w in warnings:
        log("convert: " + w)
    seeds = parse_seeds(args.seeds)
    items = []
    if args.prompts:
        with open(args.prompts) as f:
            lines = [l.rstrip("\n") for l in f]
        for i, line in enumerate(l for l in lines if l.strip() and not l.lstrip().startswith("#")):
            extra = json.loads(line) if args.prompts.endswith(".jsonl") else {"prompt": line}
            items.append({"index": i, "stem": "%03d" % i, **extra})
    elif args.images:
        paths = sorted(p for p in os.listdir(args.images) if os.path.splitext(p)[1].lower() in IMAGE_EXT)
        if not paths:
            raise ComfyError("no images in %s" % args.images)
        for i, p in enumerate(paths):
            items.append({"index": i, "stem": os.path.splitext(p)[0], "image": os.path.join(args.images, p)})
    else:
        items.append({"index": 0, "stem": "000"})
    default_name = "{stem}" + ("_s{seed}" if len(seeds) > 1 or not args.images else "")
    name_fmt = args.name or default_name
    manifest = os.path.join(args.out, "batch.jsonl")
    done, pending_ids = set(), {}
    if args.resume and os.path.exists(manifest):
        with open(manifest) as f:
            for rec in (json.loads(l) for l in f if l.strip()):
                if rec.get("ok"):
                    done.add(rec["key"])
                elif rec.get("prompt_id"):  # timed out: still queued/running or finished since
                    pending_ids[rec["key"]] = rec["prompt_id"]
    os.makedirs(args.out, exist_ok=True)
    uploads, results, failures = {}, [], 0
    total = len(items) * len(seeds)
    k = 0
    for item in items:
        for seed in seeds:
            k += 1
            key = "%s|%s" % (item["stem"], seed)
            if key in done:
                log("[%d/%d] %s already done, skipped" % (k, total, key))
                continue
            ns = argparse.Namespace(**vars(args))
            ns.prompt = item.get("prompt", args.prompt)
            ns.image = item.get("image", args.image)
            ns.seed = seed if seed is not None else args.seed
            ns.set = list(args.set or []) + ["%s=%s" % (k2, json.dumps(v)) for k2, v in item.get("set", {}).items()]
            log("[%d/%d] %s" % (k, total, key))
            rec = {"key": key, "item": {x: y for x, y in item.items() if x != "set"}, "seed": ns.seed}
            try:
                wf, applied = apply_overrides(wf0, ns, client, uploads)
                fields = {"stem": item["stem"], "index": item["index"], "seed": ns.seed if ns.seed is not None else ""}
                res = run_one(client, wf, ui, args.out, name_fmt, fields, args.timeout,
                              {"workflow": os.path.abspath(args.workflow), "overrides": applied, "batch_item": rec["item"]},
                              args.include_temp, prompt_id=pending_ids.get(key))
                rec.update(ok=True, prompt_id=res["prompt_id"], files=res["files"], seconds=res["seconds"])
            except ComfyError as e:
                failures += 1
                rec.update(ok=False, error=str(e), detail=e.detail)
                if isinstance(e.detail, dict) and e.detail.get("timed_out"):
                    rec["prompt_id"] = e.detail["prompt_id"]  # lets --resume collect instead of re-render
                log("  failed: %s" % e)
                if args.stop_on_error:
                    with open(manifest, "a") as fh:
                        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
                    raise
            with open(manifest, "a") as fh:
                fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
            results.append(rec)
    out = {"ok": failures == 0, "total": total, "ran": len(results), "failed": failures,
           "manifest": manifest, "files": [f for r in results for f in r.get("files", [])]}
    if failures:
        raise ComfyError("%d of %d batch items failed (see %s; rerun with --resume)" % (failures, len(results), manifest), out)
    return out


def cmd_upload(client, args):
    ref, res = client.upload(args.file, subfolder=args.subfolder or "", overwrite=not args.no_overwrite,
                             kind="mask" if args.mask else "image")
    return {"ok": True, "input_name": ref, "server": res}


def queue_items(q, key, mine_only):
    out = []
    for item in q.get(key, []):
        extra = item[3] if len(item) > 3 and isinstance(item[3], dict) else {}
        if not mine_only or str(extra.get("client_id", "")).startswith(CLIENT_PREFIX):
            out.append(item[1])
    return out


def cmd_stop(client, args):
    """Cancel this script's prompts; the editor's (and other clients') only with --all."""
    q = client.get("/queue")
    mine = not args.all
    running = queue_items(q, "queue_running", mine)
    pending = [] if args.keep_queue else queue_items(q, "queue_pending", mine)
    if pending:
        client.post("/queue", {"delete": pending})
    for pid in running:
        client.post("/interrupt", {"prompt_id": pid})
    others = len(q.get("queue_running", [])) + len(q.get("queue_pending", [])) - len(running) - \
        len(queue_items(q, "queue_pending", mine))
    return {"ok": True, "interrupted": running, "removed_pending": pending,
            "left_alone": others if mine else 0}


def cmd_history(client, args):
    return client.get("/history/" + args.prompt_id)


# ---------------------------------------------------------------- CLI

def add_overrides(p):
    p.add_argument("--set", action="append", metavar="TARGET.input=VALUE")
    p.add_argument("--prompt", help="positive prompt text")
    p.add_argument("--negative", help="negative prompt text")
    p.add_argument("--seed", type=int)
    p.add_argument("--steps", type=int)
    p.add_argument("--width", type=int)
    p.add_argument("--height", type=int)
    p.add_argument("--image", help="local image uploaded into the single LoadImage node")
    p.add_argument("--mask", help="local mask uploaded into the single LoadImageMask node")
    p.add_argument("--keep-previews", action="store_true", help="keep Preview* nodes when converting UI format")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--url", help="server URL (default: $COMFYUI_URL, else 127.0.0.1:8188, then :8000)")
    ap.add_argument("--allow-remote", action="store_true")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("status")
    p = sub.add_parser("server")
    p.add_argument("action", choices=["start", "stop"])
    p.add_argument("--root", help="ComfyUI checkout (default $COMFYUI_ROOT or ~/ComfyUI)")
    p.add_argument("--port", type=int, default=8188)
    p.add_argument("--wait", type=int, default=180)
    p.add_argument("--keep-cache", action="store_true", help="do not add --cache-none on <=16 GB machines")
    p.add_argument("extra", nargs=argparse.REMAINDER, help="-- extra main.py arguments")
    p = sub.add_parser("nodes")
    p.add_argument("--search")
    p.add_argument("--class", dest="cls")
    p = sub.add_parser("models")
    p.add_argument("folder", nargs="?")
    p.add_argument("--all", action="store_true")
    p = sub.add_parser("convert")
    p.add_argument("workflow")
    p.add_argument("-o", "--output", required=True)
    p.add_argument("--keep-previews", action="store_true")
    p = sub.add_parser("inspect")
    p.add_argument("workflow")
    p.add_argument("--keep-previews", action="store_true")
    p = sub.add_parser("validate")
    p.add_argument("workflow")
    p.add_argument("--save", help="write the overridden API workflow here")
    add_overrides(p)
    for name in ("run", "batch"):
        p = sub.add_parser(name)
        p.add_argument("workflow")
        p.add_argument("--out", required=True, help="local directory for outputs and sidecars")
        p.add_argument("--name", help="local file name template: {orig} {n} {node} {prompt_id}"
                       + (" {stem} {index} {seed}" if name == "batch" else ""))
        p.add_argument("--timeout", type=int, default=1800, help="seconds per prompt")
        p.add_argument("--include-temp", action="store_true", help="also download temp/preview outputs")
        add_overrides(p)
        if name == "batch":
            g = p.add_mutually_exclusive_group()
            g.add_argument("--prompts", help="one prompt per line, or .jsonl objects {prompt, set: {K: V}}")
            g.add_argument("--images", help="folder of input images, one run each via the LoadImage node")
            p.add_argument("--seeds", help="e.g. 101-104 or 1,7,42 — each item runs once per seed")
            p.add_argument("--resume", action="store_true", help="skip items already ok in batch.jsonl")
            p.add_argument("--stop-on-error", action="store_true")
    p = sub.add_parser("collect")
    p.add_argument("prompt_id")
    p.add_argument("--out", required=True)
    p.add_argument("--name", help="local file name template: {orig} {n} {node} {prompt_id}")
    p.add_argument("--timeout", type=int, default=1800)
    p.add_argument("--include-temp", action="store_true")
    p = sub.add_parser("upload")
    p.add_argument("file")
    p.add_argument("--subfolder")
    p.add_argument("--no-overwrite", action="store_true")
    p.add_argument("--mask", action="store_true", help="POST /upload/mask instead of /upload/image")
    p = sub.add_parser("stop")
    p.add_argument("--keep-queue", action="store_true", help="interrupt only, keep pending prompts")
    p.add_argument("--all", action="store_true", help="also cancel prompts queued by the editor or other clients")
    p = sub.add_parser("history")
    p.add_argument("prompt_id")
    args = ap.parse_args(argv)
    try:
        if args.cmd == "server":
            result = cmd_server(args)
        else:
            client = find_server(args)
            result = globals()["cmd_" + args.cmd](client, args)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0
    except ComfyError as e:
        out = {"ok": False, "error": str(e)}
        if e.detail is not None:
            out["detail"] = e.detail
        print(json.dumps(out, indent=2, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    sys.exit(main())
