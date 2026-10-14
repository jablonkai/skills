#!/usr/bin/env python3
"""Create, derive and inspect Gyroflow presets (JSON, version 2).

  gf-preset.py create OUT.gyroflow [--smoothing 0.8 --fov 1.1 --horizon-lock 100 ...]
                      [--codec ProRes --profile HQ --bitrate 100 --size 1920x1080]
                      [--sync JSON] [--from PRESET_OR_PROJECT]
  gf-preset.py show FILE [--json]        summarize a preset or a .gyroflow project

`--from` starts from an existing preset or project and keeps only the reusable
parts (stabilization, output codec settings, synchronization): clip-specific
fields such as the video path, trims, offsets, gyro data and output folder are
dropped, so the result applies to any clip. Flags override what --from provides.

Apply a preset with gf-render.py/gf-export.py --preset FILE. Those lift the
output block into -p, because a codec set only inside a preset keeps the default
.mp4 extension (ProRes in .mp4 fails). Gyroflow reads a .json positional input
as a lens profile, which is why presets are saved as .gyroflow (or passed via
--preset, where .json is fine too).
"""

import argparse
import json
import os
import sys
import urllib.parse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gf_lib as gf  # noqa: E402

CLIP_SPECIFIC_STAB = {"frame_readout_time", "frame_readout_direction", "frame_offset",
                      "adaptive_zoom_center_offset"}
REUSABLE_OUTPUT = {"codec", "codec_options", "bitrate", "use_gpu", "audio", "audio_codec",
                   "pixel_format", "encoder_options", "keyframe_distance", "interpolation",
                   "preserve_other_tracks", "pad_with_black", "output_width", "output_height"}
REUSABLE_SYNC = {"search_size", "max_sync_points", "every_nth_frame", "time_per_syncpoint",
                 "of_method", "offset_method", "pose_method", "calc_initial_fast",
                 "auto_sync_points", "processing_resolution", "do_autosync"}


def reusable(doc):
    """Strip a preset or project down to settings that make sense for any clip."""
    out = {"version": 2}
    stab = {k: v for k, v in (doc.get("stabilization") or {}).items() if k not in CLIP_SPECIFIC_STAB}
    if stab:
        out["stabilization"] = stab
    output = {k: v for k, v in (doc.get("output") or {}).items() if k in REUSABLE_OUTPUT}
    if "videofile" in doc:  # a project: frame size and auto bitrate belong to that clip
        for key in ("output_width", "output_height", "bitrate"):
            output.pop(key, None)
    if output:
        out["output"] = output
    sync = {k: v for k, v in (doc.get("synchronization") or {}).items() if k in REUSABLE_SYNC}
    if sync:
        out["synchronization"] = sync
    return out


def summarize(doc):
    stab = doc.get("stabilization") or {}
    smooth = {p["name"]: p["value"] for p in stab.get("smoothing_params") or []}
    out = doc.get("output") or {}
    row = {"kind": "project" if "videofile" in doc else "preset",
           "method": stab.get("method"), "smoothing": smooth or None,
           "fov": stab.get("fov"), "max_zoom": stab.get("max_zoom"),
           "horizon_lock": [stab.get("horizon_lock_amount"), stab.get("horizon_lock_roll")]
           if "horizon_lock_amount" in stab else None,
           "lens_correction_amount": stab.get("lens_correction_amount"),
           "codec": out.get("codec"), "codec_options": out.get("codec_options") or None,
           "bitrate": out.get("bitrate"),
           "size": [out["output_width"], out["output_height"]] if out.get("output_width") else None,
           "synchronization": doc.get("synchronization") or None}
    if row["kind"] == "project":
        row["videofile"] = urllib.parse.unquote(doc["videofile"]).replace("file://", "")
        row["gyro_source"] = (doc.get("gyro_source") or {}).get("detected_source")
        row["lens_profile"] = bool(doc.get("calibration_data"))
    return {k: v for k, v in row.items() if v is not None}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("create", help="write a preset")
    c.add_argument("out")
    c.add_argument("--from", dest="base", help="preset or .gyroflow project to start from")
    gf.add_stab_args(c)
    c.add_argument("--codec")
    c.add_argument("--profile", help="codec_options, e.g. HQ for ProRes")
    c.add_argument("--bitrate", type=float)
    c.add_argument("--size", help="WIDTHxHEIGHT")
    c.add_argument("--no-audio", action="store_true")
    c.add_argument("--sync", help="synchronization params JSON")
    c.add_argument("--force", action="store_true")
    s = sub.add_parser("show", help="summarize a preset or project")
    s.add_argument("file")
    s.add_argument("--json", action="store_true")
    args = ap.parse_args()

    try:
        if args.cmd == "show":
            doc = gf.load_json_arg(args.file)
            info = summarize(doc)
            if args.json:
                print(json.dumps(info, indent=2))
            else:
                for k, v in info.items():
                    print(f"{k}: {json.dumps(v) if isinstance(v, (dict, list)) else v}")
            return 0

        if os.path.exists(args.out) and not args.force:
            raise gf.GFError(f"exists, not overwritten (use --force): {args.out}")
        if args.out.lower().endswith(".json"):
            print("note: a .json file passed to gyroflow as a positional input is read as a lens "
                  "profile; .gyroflow is the safer extension for presets", file=sys.stderr)
        if args.base:
            if args.preset:
                raise gf.GFError("use --from or --preset, not both")
            args.preset = json.dumps(reusable(gf.load_json_arg(args.base)))
        preset = gf.build_preset(args)
        output = dict(preset.get("output") or {})
        if args.codec:
            output["codec"] = gf.normalize_codec(args.codec)
        if args.profile:
            output["codec_options"] = args.profile
        if args.bitrate:
            output["bitrate"] = args.bitrate
        if args.size:
            w, _, h = args.size.lower().partition("x")
            output["output_width"], output["output_height"] = int(w), int(h)
        if args.no_audio:
            output["audio"] = False
        if output:
            preset["output"] = output
        if args.sync:
            preset["synchronization"] = gf.deep_merge(preset.get("synchronization") or {},
                                                      gf.load_json_arg(args.sync))
        if not (preset.get("stabilization") or preset.get("output") or preset.get("synchronization")):
            raise gf.GFError("nothing to save: give settings flags or --from")
        os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
        with open(args.out, "w", encoding="utf-8") as fh:
            json.dump(preset, fh, indent=2)
        print(f"wrote {args.out}")
        for k, v in summarize(preset).items():
            print(f"  {k}: {json.dumps(v) if isinstance(v, (dict, list)) else v}")
        return 0
    except (gf.GFError, OSError, ValueError, KeyError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
