#!/usr/bin/env python3
"""Inspect HandBrake presets: exported JSON files, built-ins, or one resolved preset.

    python3 hb-preset.py FILE.json...        presets in GUI/CLI exports, with key settings
    python3 hb-preset.py --builtin [GREP]    built-in preset names (optionally filtered)
    python3 hb-preset.py --resolve NAME [--preset-file FILE...] [--json]
                                             effective settings of one preset, as
                                             HandBrakeCLI will apply them

For each preset it prints the exact name to pass to -Z / hb-encode.py --preset.
Names are case-sensitive. Exits 1 if a file is not a HandBrake preset export or
the preset cannot be found.
"""

import argparse
import json
import subprocess
import sys

from hb_lib import HBError, find_cli, resolve_preset

QUALITY_TYPE = {0: "target size", 1: "avg bitrate", 2: "constant quality"}


def describe(p):
    q = p.get("VideoQualityType")
    if q == 2:
        rate = f"RF {p.get('VideoQualitySlider'):g}"
    elif q == 1:
        rate = f"{p.get('VideoAvgBitrate')} kbit/s" + (" 2-pass" if p.get("VideoMultiPass") else "")
    else:
        rate = QUALITY_TYPE.get(q, "?")
    w, h = p.get("PictureWidth") or 0, p.get("PictureHeight") or 0
    size = f"max {w or '∞'}x{h or '∞'}" if (w or h) else "source size"
    audio = ", ".join(f"{a.get('AudioEncoder')}"
                      + (f" {a.get('AudioBitrate')}k" if a.get("AudioBitrate") else "")
                      + f" {a.get('AudioMixdown', '')}".rstrip()
                      for a in p.get("AudioList", [])) or "none"
    langs = ",".join(p.get("AudioLanguageList") or []) or "any"
    sub_langs = ",".join(p.get("SubtitleLanguageList") or []) or "any"
    return {
        "container": p.get("FileFormat"),
        "video": f"{p.get('VideoEncoder')} {rate}"
                 + (f", preset {p['VideoPreset']}" if p.get("VideoPreset") else ""),
        "picture": size + (f", fps {p['VideoFramerate']}" if p.get("VideoFramerate") not in (None, "auto") else ""),
        "audio": f"{audio} (tracks: {p.get('AudioTrackSelectionBehavior', 'first')}, langs {langs})",
        "subtitles": f"{p.get('SubtitleTrackSelectionBehavior', 'none')} (langs {sub_langs})"
                     + (f", burn {p['SubtitleBurnBehavior']}" if p.get("SubtitleBurnBehavior") not in (None, "none") else ""),
    }


def walk(items, folder=""):
    for p in items:
        if p.get("Folder"):
            yield from walk(p.get("ChildrenArray", []), p.get("PresetName", ""))
        else:
            yield folder, p


def show_file(path):
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    if "PresetList" not in data:
        raise HBError(f"{path}: not a HandBrake preset export (no PresetList)")
    ver = ".".join(str(data.get(k, "?")) for k in ("VersionMajor", "VersionMinor", "VersionMicro"))
    print(f"{path}  (preset format {ver})")
    n = 0
    for folder, p in walk(data["PresetList"]):
        n += 1
        name = p.get("PresetName")
        print(f"  -Z {json.dumps(name, ensure_ascii=False)}"
              + (f"   (folder {folder!r})" if folder else "")
              + ("   [default]" if p.get("Default") else ""))
        if p.get("PresetDescription"):
            print(f"      {p['PresetDescription']}")
        for k, v in describe(p).items():
            print(f"      {k:<9} {v}")
    if not n:
        raise HBError(f"{path}: no presets inside")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("files", nargs="*")
    ap.add_argument("--builtin", nargs="?", const="", metavar="GREP")
    ap.add_argument("--resolve", metavar="NAME")
    ap.add_argument("--preset-file", action="append", default=[])
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    try:
        if args.builtin is not None:
            proc = subprocess.run([find_cli(), "-z"], capture_output=True, text=True,
                                  errors="replace")
            folder = ""
            for line in (proc.stdout + proc.stderr).splitlines():
                if line.startswith("[") or not line.strip():
                    continue
                if not line.startswith(" ") and line.endswith("/"):
                    folder = line[:-1]
                elif line.startswith("    ") and not line.startswith("        "):
                    name = line.strip()
                    if args.builtin.lower() in f"{folder}/{name}".lower():
                        print(f"{folder}/{name}")
            return 0
        if args.resolve:
            p = resolve_preset(find_cli(), args.resolve, args.preset_file)
            if args.json:
                json.dump(p, sys.stdout, indent=1, ensure_ascii=False)
                print()
            else:
                print(f"-Z {json.dumps(args.resolve, ensure_ascii=False)}")
                for k, v in describe(p).items():
                    print(f"    {k:<9} {v}")
            return 0
        if not args.files:
            ap.error("give preset FILEs, --builtin or --resolve NAME")
        for f in args.files:
            show_file(f)
    except (HBError, OSError, json.JSONDecodeError) as e:
        print(e, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
