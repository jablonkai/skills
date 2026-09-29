"""Connect to the running OBS Studio over obs-websocket and run a job script against it.

Invoked by obs-run.sh. See that file for usage.

Injected into the job script: obs (a connected ObsClient), OUT, ARGS, ObsRequestError,
obs_color, and the client helpers as bare functions (call, batch, try_call, screenshot,
ensure_scene, ensure_input, ensure_filter, set_transform, item_id, input_kind,
text_settings, scene_names, input_names, wait_event).
"""

import json
import os
import sys
import traceback

sys.dont_write_bytecode = True  # keep __pycache__ out of the installed skill directory
sys.stdout.reconfigure(line_buffering=True)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from obs_client import ObsClient, ObsNotReachable, ObsRequestError, obs_color  # noqa: E402

USAGE = "usage: obs-run.sh <job.py> | -c '<code>' | --ping | --state  [--arg KEY=VALUE ...]"
HELPERS = ("call", "batch", "try_call", "screenshot", "ensure_scene", "ensure_input", "ensure_filter",
           "set_transform", "item_id", "input_kind", "text_settings", "scene_names", "input_names",
           "wait_event")


def ping(obs):
    v = obs.call("GetVersion")
    return {"ok": True, "obsVersion": v["obsVersion"], "obsWebSocketVersion": v["obsWebSocketVersion"],
            "rpcVersion": v["rpcVersion"], "platform": v.get("platformDescription"),
            "port": obs.port, "auth": bool(obs.hello.get("authentication"))}


def state(obs):
    """Scenes (with their items), inputs, outputs and settings — no secrets (stream key excluded)."""
    names = ("GetVersion", "GetSceneCollectionList", "GetProfileList", "GetSceneList", "GetInputList",
             "GetVideoSettings", "GetStudioModeEnabled", "GetRecordStatus", "GetStreamStatus",
             "GetVirtualCamStatus", "GetReplayBufferStatus", "GetRecordDirectory",
             "GetCurrentSceneTransition")
    r = dict(zip(names, obs.batch([(n,) for n in names], raise_on_error=False)))
    scenes = []
    for s in (r["GetSceneList"] or {}).get("scenes", [])[::-1]:  # reverse of the Scenes dock order
        items = obs.call("GetSceneItemList", sceneName=s["sceneName"])["sceneItems"]
        scenes.append({"name": s["sceneName"], "items": [
            {"id": i["sceneItemId"], "source": i["sourceName"], "kind": i.get("inputKind") or i["sourceType"],
             "enabled": i["sceneItemEnabled"],
             "pos": [round(i["sceneItemTransform"]["positionX"]), round(i["sceneItemTransform"]["positionY"])],
             "size": [round(i["sceneItemTransform"]["width"]), round(i["sceneItemTransform"]["height"])]}
            for i in items[::-1]]})  # top of the stack first, as in the Sources dock
    v, sl = r["GetVersion"] or {}, r["GetSceneList"] or {}
    status = lambda k, *f: {x: (r[k] or {}).get(x) for x in f} if r[k] is not None else None  # noqa: E731
    return {
        "obs": v.get("obsVersion"), "websocket": v.get("obsWebSocketVersion"),
        "collection": (r["GetSceneCollectionList"] or {}).get("currentSceneCollectionName"),
        "collections": (r["GetSceneCollectionList"] or {}).get("sceneCollections"),
        "profile": (r["GetProfileList"] or {}).get("currentProfileName"),
        "program_scene": sl.get("currentProgramSceneName"),
        "preview_scene": sl.get("currentPreviewSceneName"),
        "studio_mode": (r["GetStudioModeEnabled"] or {}).get("studioModeEnabled"),
        "video": r["GetVideoSettings"],
        "transition": (r["GetCurrentSceneTransition"] or {}).get("transitionName"),
        "scenes": scenes,
        "inputs": [{"name": i["inputName"], "kind": i["inputKind"]}
                   for i in (r["GetInputList"] or {}).get("inputs", [])],
        "record": status("GetRecordStatus", "outputActive", "outputPaused", "outputTimecode"),
        "record_directory": (r["GetRecordDirectory"] or {}).get("recordDirectory"),
        "stream": status("GetStreamStatus", "outputActive", "outputTimecode"),
        "virtualcam": status("GetVirtualCamStatus", "outputActive"),
        "replay_buffer": status("GetReplayBufferStatus", "outputActive"),  # None = not enabled
    }


def main(argv):
    if not argv or argv[0] == "-c" and len(argv) < 2:
        print(USAGE, file=sys.stderr)
        return 2
    if argv[0] in ("--ping", "--state"):
        mode, target, rest = argv[0], None, argv[1:]
    elif argv[0] == "-c":
        mode, target, rest = "code", argv[1], argv[2:]
    else:
        if not os.path.isfile(argv[0]):
            print(f"ERROR: script not found: {argv[0]}", file=sys.stderr)
            return 2
        mode, target, rest = "file", os.path.abspath(argv[0]), argv[1:]

    args = {}
    while rest:
        if rest[0] == "--arg" and len(rest) >= 2 and "=" in rest[1]:
            k, v = rest[1].split("=", 1)
            args[k] = v
            rest = rest[2:]
        else:
            print(f"ERROR: unexpected argument {rest[0]!r}\n{USAGE}", file=sys.stderr)
            return 2

    try:
        obs = ObsClient().connect()
    except ObsNotReachable as e:
        if mode == "--ping":
            print(json.dumps({"ok": False, "error": str(e)}))
        else:
            print(f"ERROR: {e}", file=sys.stderr)
        return 3

    try:
        if mode == "--ping":
            print(json.dumps(ping(obs)))
            return 0
        if mode == "--state":
            print(json.dumps(state(obs), indent=2, ensure_ascii=False))
            return 0
        ns = {"__name__": "__main__", "__file__": target if mode == "file" else "<inline>",
              "obs": obs, "OUT": os.environ.get("OUT", os.getcwd()), "ARGS": args,
              "ObsRequestError": ObsRequestError, "obs_color": obs_color}
        for name in HELPERS:
            ns[name] = getattr(obs, name)
        code = open(target, encoding="utf-8").read() if mode == "file" else target
        try:
            exec(compile(code, ns["__file__"], "exec"), ns)
        except SystemExit as e:
            return e.code if isinstance(e.code, int) else (0 if e.code is None else 1)
        except Exception:
            sys.stdout.flush()
            traceback.print_exc()
            return 1
        return 0
    finally:
        obs.close()


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
