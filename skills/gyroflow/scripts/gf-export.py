#!/usr/bin/env python3
"""Export .gyroflow projects, STMaps or camera metadata for clips, without rendering.

  gf-export.py CLIP... --out-dir DIR --project [1|2|3]   .gyroflow project per clip
  gf-export.py CLIP... --out-dir DIR --stmap [frame|all] undistort/redistort EXR STMaps
  gf-export.py CLIP... --out-dir DIR --metadata camera.csv|.json|.usd|.jsx
                                     [--metadata-kind camera|parsed|full]

The stabilization flags of gf-render.py (--preset, --smoothing, --fov,
--horizon-lock, ...) and --gyro-file/--lens apply here too, so a project or STMap
carries the same settings a render would. Several export kinds can be combined in
one call; each runs as its own Gyroflow pass.

Project types: 1 = settings only (motion data stays in the clip; smallest; fine
for the Resolve/FCP/Premiere plugins when the clip has embedded gyro), 2 = with
gyro data (needed for external logs, synced clips, and handing the project to
someone without the clip's metadata), 3 = with processed data (adds the computed
camera orientations and FOVs).

Paths inside an exported project are rewritten from the sandbox staging copy back
to the original clip, so the project opens next to the real footage.
"""

import argparse
import glob
import json
import os
import sys
import urllib.parse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gf_lib as gf  # noqa: E402

PROJECT_TYPES = {"1": "default", "2": "with gyro data", "3": "with processed gyro data"}
META_KINDS = {"full": 1, "parsed": 2, "camera": 3}


def rewrite_paths(obj, mapping):
    """Replace staged paths/URLs with the originals everywhere in a JSON value."""
    if isinstance(obj, dict):
        return {k: rewrite_paths(v, mapping) for k, v in obj.items()
                if not k.endswith("_bookmark")}
    if isinstance(obj, list):
        return [rewrite_paths(v, mapping) for v in obj]
    if isinstance(obj, str):
        for old, new in mapping:
            if old in obj:
                obj = obj.replace(old, new)
        return obj
    return obj


def url_forms(path):
    return [urllib.parse.quote(path), path]


def project_readback(path):
    with open(path, encoding="utf-8") as fh:
        d = json.load(fh)
    stab = d.get("stabilization") or {}
    smooth = {p["name"]: p["value"] for p in stab.get("smoothing_params") or []}
    out = d.get("output") or {}
    gyro = d.get("gyro_source") or {}
    return {"videofile": urllib.parse.unquote(d.get("videofile", "")).replace("file://", ""),
            "method": stab.get("method"), "smoothness": smooth.get("smoothness"),
            "fov": stab.get("fov"), "max_zoom": stab.get("max_zoom"),
            "horizon_lock_amount": stab.get("horizon_lock_amount"),
            "horizon_lock_roll": stab.get("horizon_lock_roll"),
            "codec": out.get("codec"), "codec_options": out.get("codec_options"),
            "size": [out.get("output_width"), out.get("output_height")],
            "gyro_source": gyro.get("detected_source"),
            "gyro_file": urllib.parse.unquote(gyro.get("filepath", "")).replace("file://", ""),
            "gyro_data_in_project": _has_motion(gyro.get("file_metadata")),
            "sync_offsets": len(d.get("offsets") or {}),
            "lens_profile": bool(d.get("calibration_data"))}


def _has_motion(meta):
    """Type 2/3 projects carry the motion data (encoded string or raw_imu list)."""
    if isinstance(meta, str):
        return len(meta) > 64
    return bool(isinstance(meta, dict) and (meta.get("raw_imu") or meta.get("quaternions")))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("inputs", nargs="+", help="clips and/or folders")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--recursive", action="store_true")
    ap.add_argument("--project", nargs="?", const="2", choices=sorted(PROJECT_TYPES),
                    help="export a .gyroflow project (default type 2, with gyro data)")
    ap.add_argument("--stmap", nargs="?", const="frame", choices=["frame", "all"],
                    help="export STMaps: frame = one undistort+redistort pair, all = every frame")
    ap.add_argument("--metadata", metavar="NAME.EXT",
                    help="export metadata per clip as <clip>-NAME.EXT (camera kind: csv|json|usd|jsx)")
    ap.add_argument("--metadata-kind", default="camera", choices=sorted(META_KINDS))
    ap.add_argument("--codec", help="output codec stored in the project (e.g. ProRes)")
    ap.add_argument("--profile", help="codec_options stored in the project (e.g. HQ)")
    gf.add_stab_args(ap)
    ap.add_argument("-g", "--gyro-file")
    ap.add_argument("--lens")
    ap.add_argument("--sync", help="-s sync params JSON")
    ap.add_argument("--force", action="store_true", help="overwrite existing exports")
    ap.add_argument("--timeout", type=float, default=600)
    ap.add_argument("--json", action="store_true", help="print the read-back as JSON")
    args = ap.parse_args()
    if not (args.project or args.stmap or args.metadata):
        ap.error("choose at least one of --project, --stmap, --metadata")

    try:
        binary = gf.find_bin()
        sandboxed = gf.is_sandboxed(binary)
        clips = gf.collect_inputs(args.inputs, args.recursive)
        preset, preset_output = gf.split_output(gf.build_preset(args))
        params = dict(preset_output)
        if args.codec:
            params["codec"] = gf.normalize_codec(args.codec)
        if args.profile:
            params["codec_options"] = args.profile
        sync = gf.load_json_arg(args.sync) or {}
    except gf.GFError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    out_dir = os.path.abspath(args.out_dir)
    os.makedirs(out_dir, exist_ok=True)
    results, failed = [], 0
    for clip in clips:
        row = {"source": clip, "exports": {}}
        results.append(row)
        for kind in ("project", "stmap", "metadata"):
            if not getattr(args, kind):
                continue
            try:
                row["exports"][kind] = export_one(binary, sandboxed, clip, kind, args, preset,
                                                  params, sync, out_dir)
            except gf.GFError as exc:
                row["exports"][kind] = {"ok": False, "error": str(exc)}
                failed += 1
    if args.json:
        print(json.dumps(results, indent=2))
    else:
        for row in results:
            print(os.path.basename(row["source"]))
            for kind, r in row["exports"].items():
                if not r.get("ok"):
                    print(f"  {kind}: FAILED - {r.get('error')}")
                elif kind == "project":
                    rb = r["readback"]
                    print(f"  project: {r['files'][0]} (type {args.project}, {PROJECT_TYPES[args.project]})")
                    print(f"    method={rb['method']} smoothness={rb['smoothness']} fov={rb['fov']} "
                          f"horizon={rb['horizon_lock_amount']}/{rb['horizon_lock_roll']} "
                          f"codec={rb['codec']} {rb['codec_options'] or ''} gyro={rb['gyro_source']}")
                else:
                    extra = f" ({r['width']}x{r['height']})" if r.get("width") else ""
                    print(f"  {kind}: {len(r['files'])} file(s){extra}: "
                          + ", ".join(os.path.basename(f) for f in r["files"][:4])
                          + (" ..." if len(r["files"]) > 4 else ""))
    return 1 if failed else 0


def export_one(binary, sandboxed, clip, kind, args, preset, params, sync, out_dir):
    stage = gf.Stage(sandboxed)
    try:
        src = stage.add(clip) if sandboxed else clip
        argv = [src]
        mapping = [(u_old, u_new) for old, new in [(src, clip)]
                   for u_old, u_new in zip(url_forms(old), url_forms(new))]
        if args.lens:
            argv.append(stage.add(args.lens) if sandboxed else os.path.abspath(args.lens))
        p = dict(params)
        p["output_folder"] = stage.out + "/"
        argv += ["-f", "-p", gf.pjson(p)]
        if preset.get("stabilization") or len(preset) > 1:
            argv += ["--preset", gf.pjson(preset)]
        gyro_file = args.gyro_file
        sidecar = os.path.splitext(clip)[0] + ".gcsv"
        if not gyro_file and os.path.isfile(sidecar):  # the CLI does not pick sidecars up itself
            gyro_file = sidecar
        if gyro_file:
            sync = dict(sync)
            sync.setdefault("do_autosync", True)
        if sync:
            argv += ["-s", gf.pjson(sync)]
        if gyro_file:
            g = stage.add(gyro_file) if sandboxed else os.path.abspath(gyro_file)
            mapping += list(zip(url_forms(g), url_forms(os.path.abspath(gyro_file))))
            argv += ["-g", g]
        mapping.append((stage.out + "/", out_dir + "/"))
        mapping.append((urllib.parse.quote(stage.out + "/"), urllib.parse.quote(out_dir + "/")))
        stem = os.path.splitext(os.path.basename(clip))[0]
        if kind == "project":
            argv += ["--export-project", args.project]
        elif kind == "stmap":
            argv += ["--export-stmap", f"{1 if args.stmap == 'frame' else 2}:{stage.out}/"]
        else:
            argv += ["--export-metadata",
                     f"{META_KINDS[args.metadata_kind]}:{stage.out}/{stem}-{args.metadata}"]
        res = gf.run_gyroflow(binary, argv, stage, timeout=args.timeout, stall=60)
        produced = sorted(glob.glob(os.path.join(stage.out, "*")))
        if not produced:
            err = next((j.error for j in res.jobs.values() if j.error), None) \
                or (res.errors[-1] if res.errors else None) or res.killed or "nothing written"
            raise gf.GFError(err)
        files, result = [], {"ok": True}
        for f in produced:
            name = os.path.basename(f)
            if kind == "project":
                name = stem + ".gyroflow"
                with open(f, encoding="utf-8") as fh:
                    data = rewrite_paths(json.load(fh), mapping)
                with open(f, "w", encoding="utf-8") as fh:
                    json.dump(data, fh, indent=2)
            elif kind == "stmap":
                # "<clip.ext>-<brand>-<model>-<lens>-undistort-<n>.exr": drop the empty parts
                parts = [x for x in name.replace(os.path.basename(src), stem, 1).split("-") if x]
                name = "-".join(parts)
            dest = os.path.join(out_dir, name)
            if os.path.exists(dest) and not args.force:
                raise gf.GFError(f"exists, not overwritten (use --force): {dest}")
            os.replace(f, dest)
            files.append(dest)
        result["files"] = files
        if kind == "project":
            result["readback"] = project_readback(files[0])
        elif kind == "stmap":
            info = gf.video_info(next(f for f in files if "undistort" in f)) or {}
            result.update(width=info.get("width"), height=info.get("height"),
                          undistort=sum("undistort" in f for f in files),
                          redistort=sum("redistort" in f for f in files))
        return result
    finally:
        stage.cleanup()


if __name__ == "__main__":
    sys.exit(main())
