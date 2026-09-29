#!/usr/bin/env python3
"""Build, check and install OBS scene collection files (basic/scenes/<name>.json).

    obs_collection.py list                          collections on disk (* = the one OBS has open)
    obs_collection.py dump NAME                     summary: scenes, their items, inputs, filters
    obs_collection.py build SPEC.json OUT.json      compact spec → full collection file
    obs_collection.py validate FILE.json            structural check (exit 1 on problems)
    obs_collection.py install FILE.json [--force]   copy into OBS's scenes dir (backs up to .bak)
    obs_collection.py apply SPEC.json [--new-collection]
                                                    build the spec live in the running OBS

Two routes to the same result:
- OBS closed → build + install, then `obs-start.sh --collection NAME`. OBS reads the list of
  collection files only at startup, so a file installed while it runs is invisible until a
  restart (SetCurrentSceneCollection answers 600). install refuses while OBS is running.
- OBS running → apply. It creates or updates every scene, input, transform and filter over
  obs-websocket (re-runnable); with --new-collection it first creates and switches to an
  empty collection named after the spec. OBS then saves the collection file itself.

SPEC format (see references/scene-collection.md):
    {"name": "Stream",
     "scenes": [
       {"name": "Main", "items": [
          {"source": "BG", "kind": "color_source_v3",
           "settings": {"color": "#0b1f3a", "width": 1920, "height": 1080}},
          {"source": "Cam", "kind": "macos-avcapture", "pos": [960, 540], "align": 0,
           "scale": [0.5, 0.5], "filters": [{"name": "Tone", "kind": "color_filter_v2",
                                             "settings": {"saturation": 0.1}}]},
          {"source": "BRB"}  ← a scene name nests that scene; a known input name reuses it
       ]}]}
"#rrggbb[aa]" strings under keys containing "color" become OBS's ABGR integers.
"""

import json
import os
import re
import shutil
import sys
import uuid

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from obs_client import ObsClient, ObsNotReachable, config_dir, obs_color  # noqa: E402

SCENES_DIR = os.path.join(config_dir(), "basic", "scenes")


def _unversioned(kind):
    return re.sub(r"_v\d+$", "", kind)


def _colors(settings):
    out = {}
    for k, v in settings.items():
        if isinstance(v, dict):
            v = _colors(v)
        elif isinstance(v, str) and "color" in k.lower() and v.startswith("#"):
            v = obs_color(v)
        out[k] = v
    return out


def _source(name, kind, settings=None, filters=None):
    src = {"name": name, "uuid": str(uuid.uuid4()), "id": _unversioned(kind), "versioned_id": kind,
           "settings": _colors(settings or {}), "mixers": 0 if kind == "scene" else 255,
           "sync": 0, "flags": 0, "volume": 1.0, "balance": 0.5, "enabled": True, "muted": False,
           "hotkeys": {}, "private_settings": {}}
    if filters:
        src["filters"] = [{**_source(f["name"], f["kind"], f.get("settings")), "mixers": 0,
                           "enabled": f.get("enabled", True)} for f in filters]
    return src


def build(spec):
    scene_names = [s["name"] for s in spec["scenes"]]
    if len(set(scene_names)) != len(scene_names):
        raise ValueError("duplicate scene names in spec")
    inputs, scenes = {}, {n: _source(n, "scene", {"id_counter": 0, "custom_size": False, "items": []})
                          for n in scene_names}
    for s in spec["scenes"]:
        for it in s.get("items", []):
            n = it["source"]
            if n in scenes or n in inputs:
                if "kind" in it and n in inputs and inputs[n]["versioned_id"] != it["kind"]:
                    raise ValueError(f"input {n!r} redefined with another kind")
                continue
            if "kind" not in it:
                raise ValueError(f"item {n!r} in scene {s['name']!r} is neither a scene nor a defined input "
                                 "— give it a kind")
            inputs[n] = _source(n, it["kind"], it.get("settings"), it.get("filters"))
    by_name = {**inputs, **scenes}
    for s in spec["scenes"]:
        items = scenes[s["name"]]["settings"]["items"]
        for i, it in enumerate(s.get("items", []), 1):
            pos, scale = it.get("pos", [0, 0]), it.get("scale", [1, 1])
            items.append({
                "name": it["source"], "source_uuid": by_name[it["source"]]["uuid"],
                "visible": it.get("visible", True), "locked": it.get("locked", False),
                "rot": float(it.get("rot", 0)), "align": it.get("align", 5),  # 5 = top|left
                "bounds_type": 0, "bounds_align": 0, "bounds": {"x": 0.0, "y": 0.0},
                "crop_left": 0, "crop_top": 0, "crop_right": 0, "crop_bottom": 0,
                "id": i, "group_item_backup": False,
                "pos": {"x": float(pos[0]), "y": float(pos[1])},
                "scale": {"x": float(scale[0]), "y": float(scale[1])},
                "scale_filter": "disable", "blend_method": "default", "blend_type": "normal",
                "private_settings": {}})
        scenes[s["name"]]["settings"]["id_counter"] = len(items)
    first = spec.get("current_scene", scene_names[0])
    return {"name": spec["name"], "sources": list(inputs.values()) + list(scenes.values()), "groups": [],
            "scene_order": [{"name": n} for n in scene_names], "current_scene": first,
            "current_program_scene": first, "transitions": [], "quick_transitions": [],
            "saved_projectors": [], "modules": {}, "version": 2}


def validate(doc):
    problems = []
    for key in ("name", "sources", "scene_order", "current_scene"):
        if key not in doc:
            problems.append(f"missing top-level key {key!r}")
    sources = doc.get("sources", [])
    names = [s.get("name") for s in sources]
    for n in {n for n in names if names.count(n) > 1}:
        problems.append(f"duplicate source name {n!r} (OBS source names are global)")
    uuids = {s.get("uuid"): s for s in sources}
    scenes = {s["name"] for s in sources if s.get("id") == "scene"}
    for s in sources:
        for k in ("name", "uuid", "id", "versioned_id", "settings"):
            if k not in s:
                problems.append(f"source {s.get('name')!r} lacks {k!r}")
        if s.get("id") == "scene":
            ids = [it.get("id") for it in s["settings"].get("items", [])]
            if len(set(ids)) != len(ids):
                problems.append(f"scene {s['name']!r} has duplicate item ids")
            for it in s["settings"].get("items", []):
                ref = uuids.get(it.get("source_uuid"))
                if ref is None:
                    problems.append(f"scene {s['name']!r} item {it.get('name')!r}: source_uuid not in sources")
                elif ref["name"] != it.get("name"):
                    problems.append(f"scene {s['name']!r} item {it.get('name')!r}: uuid points at {ref['name']!r}")
    for o in doc.get("scene_order", []):
        if o.get("name") not in scenes:
            problems.append(f"scene_order lists unknown scene {o.get('name')!r}")
    if doc.get("current_scene") not in scenes:
        problems.append(f"current_scene {doc.get('current_scene')!r} is not a scene")
    return problems


def apply(spec, new_collection=False):
    """Create or update the spec's scenes, inputs, transforms and filters in the running OBS."""
    created = False
    with ObsClient() as obs:
        if new_collection:
            # Both requests block until OBS has finished switching collections.
            cols = obs.call("GetSceneCollectionList")
            if cols["currentSceneCollectionName"] == spec["name"]:
                pass
            elif spec["name"] in cols["sceneCollections"]:
                obs.call("SetCurrentSceneCollection", sceneCollectionName=spec["name"])
            else:
                obs.call("CreateSceneCollection", sceneCollectionName=spec["name"])
                created = True
        scene_names = [s["name"] for s in spec["scenes"]]
        for n in scene_names:
            obs.ensure_scene(n)
        for s in spec["scenes"]:
            for it in s.get("items", []):
                n = it["source"]
                if n in scene_names:
                    if obs.try_call("GetSceneItemId", sceneName=s["name"], sourceName=n) is None:
                        obs.call("CreateSceneItem", sceneName=s["name"], sourceName=n)
                elif "kind" in it:
                    obs.ensure_input(s["name"], n, it["kind"], _colors(it.get("settings", {})))
                elif obs.try_call("GetSceneItemId", sceneName=s["name"], sourceName=n) is None:
                    obs.call("CreateSceneItem", sceneName=s["name"], sourceName=n)  # reuse a defined input
                sid = obs.item_id(s["name"], n)
                pos, scale = it.get("pos", [0, 0]), it.get("scale", [1, 1])
                obs.call("SetSceneItemTransform", sceneName=s["name"], sceneItemId=sid, sceneItemTransform={
                    "positionX": pos[0], "positionY": pos[1], "scaleX": scale[0], "scaleY": scale[1],
                    "rotation": it.get("rot", 0), "alignment": it.get("align", 5)})
                obs.call("SetSceneItemEnabled", sceneName=s["name"], sceneItemId=sid,
                         sceneItemEnabled=it.get("visible", True))
                for f in it.get("filters", []):
                    obs.ensure_filter(n, f["name"], f["kind"], _colors(f.get("settings", {})))
            # Spec lists items bottom-to-top, like the file format; mirror that order.
            for idx, it in enumerate(s.get("items", [])):
                obs.call("SetSceneItemIndex", sceneName=s["name"], sceneItemId=obs.item_id(s["name"], it["source"]),
                         sceneItemIndex=idx)
        first = spec.get("current_scene", scene_names[0])
        obs.call("SetCurrentProgramScene", sceneName=first)
        if created:  # a fresh collection starts with one empty, localized default scene
            for n in obs.scene_names():
                if n not in scene_names and not obs.call("GetSceneItemList", sceneName=n)["sceneItems"]:
                    obs.call("RemoveScene", sceneName=n)
        return {"collection": obs.call("GetSceneCollectionList")["currentSceneCollectionName"],
                "scenes": scene_names, "program_scene": first}


def _current_collection():
    """Name of the collection OBS has open, or None when OBS is not reachable."""
    try:
        with ObsClient(timeout=5, events=0) as obs:
            return obs.call("GetSceneCollectionList")["currentSceneCollectionName"]
    except (ObsNotReachable, OSError):
        return None


def _path_for(name):
    for f in os.listdir(SCENES_DIR) if os.path.isdir(SCENES_DIR) else []:
        if f.endswith(".json"):
            try:
                with open(os.path.join(SCENES_DIR, f), encoding="utf-8") as fh:
                    if json.load(fh).get("name") == name:
                        return os.path.join(SCENES_DIR, f)
            except (OSError, ValueError):
                pass
    return None


def main(argv):
    if not argv:
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return 2
    cmd, rest = argv[0], argv[1:]
    if cmd == "list":
        cur = _current_collection()
        for f in sorted(os.listdir(SCENES_DIR)) if os.path.isdir(SCENES_DIR) else []:
            if f.endswith(".json"):
                with open(os.path.join(SCENES_DIR, f), encoding="utf-8") as fh:
                    n = json.load(fh).get("name")
                print(("* " if n == cur else "  ") + f"{n}\t{f}")
        return 0
    if cmd == "dump" and len(rest) == 1:
        path = rest[0] if os.path.isfile(rest[0]) else _path_for(rest[0])
        if not path:
            print(f"ERROR: no collection named {rest[0]!r} in {SCENES_DIR}", file=sys.stderr)
            return 2
        with open(path, encoding="utf-8") as fh:
            doc = json.load(fh)
        by_uuid = {s["uuid"]: s for s in doc["sources"]}
        print(json.dumps({
            "name": doc["name"], "file": path, "current_scene": doc.get("current_scene"),
            "scenes": [{"name": o["name"], "items": [
                {"source": it["name"], "kind": by_uuid.get(it["source_uuid"], {}).get("versioned_id"),
                 "visible": it.get("visible"), "pos": [it["pos"]["x"], it["pos"]["y"]]}
                for it in next(s for s in doc["sources"] if s["name"] == o["name"])["settings"]["items"]]}
                for o in doc["scene_order"]],
            "filters": {s["name"]: [f["name"] for f in s["filters"]] for s in doc["sources"] if s.get("filters")},
        }, indent=2, ensure_ascii=False))
        return 0
    if cmd == "build" and len(rest) == 2:
        with open(rest[0], encoding="utf-8") as fh:
            doc = build(json.load(fh))
        problems = validate(doc)
        if problems:
            print("ERROR: built collection is invalid:\n  " + "\n  ".join(problems), file=sys.stderr)
            return 1
        with open(rest[1], "w", encoding="utf-8") as fh:
            json.dump(doc, fh, indent=4, ensure_ascii=False)
        print(f"built {doc['name']!r}: {len(doc['scene_order'])} scenes, "
              f"{sum(s['id'] != 'scene' for s in doc['sources'])} inputs → {rest[1]}")
        return 0
    if cmd == "apply" and rest and rest[1:] in ([], ["--new-collection"]):
        with open(rest[0], encoding="utf-8") as fh:
            spec = json.load(fh)
        validate_problems = validate(build(spec))  # same checks as the file route
        if validate_problems:
            print("ERROR: spec is invalid:\n  " + "\n  ".join(validate_problems), file=sys.stderr)
            return 1
        try:
            print(json.dumps(apply(spec, "--new-collection" in rest), ensure_ascii=False))
        except ObsNotReachable as e:
            print(f"ERROR: {e}", file=sys.stderr)
            return 3
        return 0
    if cmd == "validate" and len(rest) == 1:
        with open(rest[0], encoding="utf-8") as fh:
            problems = validate(json.load(fh))
        print("ok" if not problems else "\n".join(problems))
        return 1 if problems else 0
    if cmd == "install" and rest and rest[1:] in ([], ["--force"]):
        with open(rest[0], encoding="utf-8") as fh:
            doc = json.load(fh)
        problems = validate(doc)
        if problems:
            print("ERROR: refusing to install an invalid collection:\n  " + "\n  ".join(problems), file=sys.stderr)
            return 1
        name = doc["name"]
        if _current_collection() is not None:
            print("ERROR: OBS is running. It reads collection files only at startup and rewrites the open\n"
                  "       one from memory, so an install now is either invisible or lost. Ask the user to\n"
                  "       quit OBS, then install and run obs-start.sh --collection NAME — or use\n"
                  "       'apply SPEC.json --new-collection' to build it live instead.", file=sys.stderr)
            return 1
        target = _path_for(name)
        if target and "--force" not in rest:
            print(f"ERROR: a collection named {name!r} exists ({target}); pass --force to replace it "
                  "(the old file is kept as .bak)", file=sys.stderr)
            return 1
        os.makedirs(SCENES_DIR, exist_ok=True)
        if target:
            shutil.copy2(target, target + ".bak")
        else:
            target = os.path.join(SCENES_DIR, re.sub(r"[^\w.-]+", "_", name) + ".json")
        shutil.copy2(rest[0], target)
        print(f"installed {name!r} → {target}")
        return 0
    print(__doc__.split("\n\n")[1], file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
