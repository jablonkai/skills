#!/usr/bin/env python3
"""Compact read-back of an .anicraft document, in 1-based timeline frames.

  ac_inspect.py FILE                      stage, scenes, layers, keyframes, elements, library,
                                          actions and scripts
  ac_inspect.py FILE --at 1 15 30         plus camera, bones and every motion tween's
                                          values at those frames (1-based)

Reads the saved JSON for element detail (`info` only counts elements) and asks a
headless session for the rest; changes nothing. Prints JSON.
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import aclib  # noqa: E402


def describe_element(el, library_names, paths):
    kind, body = aclib.element_kind(el)
    out = {"id": el["id"], "kind": kind}
    if el.get("name"):
        out["name"] = el["name"]
    m = (el.get("transform") or {}).get("m")
    if m:
        out["at"] = [round(m[4], 2), round(m[5], 2)]
    if kind == "Text":
        out.update(text=body.get("text"), font=body.get("font"), size=body.get("size"))
    elif kind == "Symbol":
        out["symbol"] = library_names.get(body.get("symbol"), body.get("symbol"))
    elif kind == "Shape":
        fill = body.get("fill") or {}
        if isinstance(fill, dict) and "Bitmap" in fill:
            out["kind"] = "Bitmap"
            out["bitmap"] = library_names.get(fill["Bitmap"]["bitmap"], fill["Bitmap"]["bitmap"])
    return out


def describe_timeline(timeline, library_names, paths):
    layers = []
    for layer in aclib.walk_layers(timeline):
        entry = {"id": layer["id"], "name": layer["name"], "type": layer.get("kind")}
        if layer.get("armature"):
            entry["bones"] = [
                {"id": b["id"], "name": b.get("name", ""),
                 "limits": [round(v * 57.29578, 1) for v in (b["limits"]["min"], b["limits"]["max"])]
                 if b.get("limits") else None}
                for b in layer["armature"].get("bones", [])]
        keys = []
        for k in layer.get("keyframes", []):
            key = {"frames": "%d-%d" % (k["start"] + 1, k["start"] + k["duration"])}
            if k.get("label"):
                key["label"] = k["label"]
            tween = k.get("tween")
            if tween:
                key["tween"] = tween
            if k.get("motion"):
                key["motion"] = {t["property"]: [[x["frame"] + 1, round(x["value"], 2)]
                                                for x in t["keys"]]
                                 for t in k["motion"].get("tracks", [])}
                if k["motion"].get("path") is not None:
                    key["motion"]["path"] = True
            if k.get("pose"):
                key["pose"] = {p["bone"]: round(p["angle"] * 57.29578, 1) for p in k["pose"]}
            if k.get("hints"):
                key["hints"] = len(k["hints"])
            script = k.get("script") or {}
            if script.get("actions"):
                key["actions"] = [a.get("op") for a in script["actions"]]
            if script.get("source"):
                key["script"] = script["source"].get("language", True)
            if k.get("sound"):
                key["sound"] = True
            key["elements"] = [describe_element(e, library_names, paths) for e in k.get("elements", [])]
            keys.append(key)
        entry["keyframes"] = keys
        layers.append(entry)
    return layers


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("file")
    ap.add_argument("--at", nargs="*", type=int, default=[],
                    help="1-based frames to read camera, bones and motion values at")
    args = ap.parse_args()

    data = aclib.load_document(args.file)
    doc = data["document"]
    with aclib.Serve(args.file) as s:
        lib = s.call("library.items")
        actions = s.call("actions.list")
        scripts = s.call("script.list", {"text": True})
        info = s.call("doc.info")
        names = {}
        for item in lib.get("items", []):
            for key in ("symbol", "bitmap", "sound"):
                if key in item:
                    names[item[key]] = item["name"]
        report = {
            "file": os.path.abspath(args.file),
            "generator": data.get("generator"),
            "stage": info.get("stage"),
            "frames": info.get("frames"),
            "scenes": [sc.get("name") for sc in doc.get("scenes", [])],
            "layers": describe_timeline(doc["scenes"][0]["timeline"], names, data.get("paths")),
            "library": [{k: v for k, v in i.items() if k in ("symbol", "bitmap", "sound", "kind", "name", "uses")}
                        for i in lib.get("items", [])],
            "actions": [{"layer": a.get("layer_name"), "frame": a["frame"] + 1, "summary": a.get("summary")}
                        for a in actions.get("frames", [])],
            "scripts": scripts.get("scripts", scripts),
        }
        if len(doc.get("scenes", [])) > 1:
            report["note"] = "layers shown for the first scene only"
        if args.at:
            motion_layers = [l["id"] for l in info.get("layers", [])
                             if any(k.get("motion") for k in l.get("keyframes", []))]
            has_camera = any(l.get("kind") == "Camera" for l in doc["scenes"][0]["timeline"]["layers"])
            at = {}
            for n in args.at:
                f = n - 1
                row = {}
                if has_camera:
                    cam = s.call("camera.info", {"frame": f})
                    row["camera"] = {k: (round(cam[k], 2) if isinstance(cam[k], float) else cam[k])
                                     for k in ("x", "y", "zoom", "rotation", "tint", "tint_amount") if k in cam}
                bones = s.call("bone.info", {"frame": f}).get("armatures", [])
                if bones:
                    row["bones"] = {b["id"]: round(b["angle"], 1) for a in bones for b in a["bones"]}
                for lid in motion_layers:
                    try:
                        mi = s.call("motion.info", {"layer": lid, "frame": f})
                    except aclib.StepError:
                        continue
                    row.setdefault("motion", {})[lid] = {"position": mi.get("position"),
                                                         "path": mi.get("path") is not None}
                at[n] = row
            report["at"] = at
    print(json.dumps(report, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
