"""Runs inside `Nuke --nc -t nk_driver.py JOB.json` — never call it directly; nk.py does.

Loads one script and executes Write nodes by name. Everything is addressed by
name, because Non-commercial mode hands out at most 10 Node objects to Python.
Progress and results are printed as `NKJOB {json}` lines for nk.py to parse.
"""
import json
import os
import sys
import time
import traceback

import nuke


def emit(kind, **kw):
    kw["kind"] = kind
    sys.stdout.write("\nNKJOB " + json.dumps(kw) + "\n")
    sys.stdout.flush()


def main():
    job = json.load(open(sys.argv[1]))
    script = job["script"]
    try:
        if script.endswith(".nknc") or not job.get("read_as_text", True):
            nuke.scriptOpen(script)
        else:
            nuke.scriptReadFile(script)
            # Keeps [file dirname [value root.name]] style paths working.
            nuke.root()["name"].setValue(script)
    except Exception as e:  # noqa: BLE001 — report anything Nuke raises
        emit("load", ok=False, error=str(e).strip())
        return 3
    emit("load", ok=True, nuke=nuke.NUKE_VERSION_STRING, nc=bool(nuke.env.get("nc")))

    for hook in job.get("py", []):
        try:
            code = compile(open(hook).read(), hook, "exec")
            exec(code, {"nuke": nuke, "__name__": "__nk_hook__", "__file__": hook})
            emit("py", ok=True, file=hook)
        except Exception as e:  # noqa: BLE001
            emit("py", ok=False, file=hook, error=traceback.format_exc().strip().splitlines()[-1])
            return 4

    for spec in job.get("set", []):
        target, value = spec["target"], spec["value"]
        node_name, _, knob = target.rpartition(".")
        try:
            node = nuke.root() if node_name in ("root", "Root") else nuke.toNode(node_name)
            if node is None:
                raise ValueError("no node named %r (or the Non-commercial 10-node Python limit was hit)" % node_name)
            k = node.knob(knob)
            if k is None:
                raise ValueError("node %r has no knob %r" % (node_name, knob))
            k.fromScript(value)
            emit("set", ok=True, target=target, value=value)
        except Exception as e:  # noqa: BLE001
            emit("set", ok=False, target=target, error=str(e).strip())
            return 4

    root = nuke.root()
    r_first, r_last = int(root["first_frame"].value()), int(root["last_frame"].value())
    writes = job.get("writes")
    if writes is None:  # discover (encrypted .nknc cannot be parsed outside Nuke)
        writes = []
        for n in nuke.allNodes("Write", recurseGroups=True):
            if n["disable"].value():
                continue
            w = {"name": n.fullName(), "file": n["file"].value()}
            if n["use_limit"].value():
                w["first"], w["last"] = int(n["first"].value()), int(n["last"].value())
            writes.append(w)
    fr = job.get("frames")
    for w in writes:
        if fr:
            w["first"], w["last"], w["step"] = fr
        w.setdefault("first", r_first)
        w.setdefault("last", r_last)
        w.setdefault("step", 1)
        # Re-read the path: --set or a hook may have changed it since nk.py parsed the text.
        n = nuke.toNode(w["name"])
        if n is not None and n.knob("file"):
            w["file"] = n["file"].value()
        d = os.path.dirname(w["file"])
        if d and "[" not in d and not os.path.isdir(d):
            try:
                os.makedirs(d)
            except OSError:
                pass  # the Write reports the real error
    emit("plan", writes=writes)

    failed = 0
    for w in writes:
        t0 = time.time()
        try:
            nuke.execute(w["name"], int(w["first"]), int(w["last"]), int(w.get("step", 1)))
            emit("write", ok=True, name=w["name"], seconds=round(time.time() - t0, 2))
        except Exception as e:  # noqa: BLE001
            failed += 1
            msg = " ".join(str(e).split()) or traceback.format_exc().strip().splitlines()[-1]
            emit("write", ok=False, name=w["name"], error=msg, seconds=round(time.time() - t0, 2))
    return 1 if failed else 0


if __name__ == "__main__":
    code = main()
    emit("done", code=code)
    sys.exit(code)
