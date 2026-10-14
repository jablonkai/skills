#!/usr/bin/env python3
"""Render an Apple Motion template headless through Compressor and check frames.

  motn-render.py FILE --out DIR [--at 1,5] [--setting half|full|proxy|PATH]
                 [--expect "X,Y=#RRGGBB" ...] [--tolerance 8] [--timeout 300]

Compressor renders .moti/.motn/.moef/.motr directly (Motion must be installed; its
window never opens). Then ffmpeg grabs a PNG at each --at second and reports its luma
range (`blank` when the frame is flat). --expect samples a pixel (X,Y as pixels, or as
0..1 fractions of the frame) and compares it with the colour as written in the
template: Motion stores sRGB values and the render is BT.709-encoded, so mid-tones come
out a little darker (0.678 -> 0.640, 0.102 -> 0.094): the expected value is converted the same way (sRGB -> linear -> gamma 1/1.961, fitted to measured renders).

Settings: half (default) = H.264 half size, full = H.264 full size... both built in;
proxy = ProRes 422 Proxy full size; or a path to any .compressorsetting.
Titles render over their drop-zone placeholder (a grey box with an arrow) — FCP
replaces it with the clip underneath. On --timeout the batch is cancelled (-kill).
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time

APP = os.environ.get("COMPRESSOR_APP", "/Applications/Compressor.app")
CLI = os.path.join(APP, "Contents/MacOS/Compressor")
BUILTIN = ("Contents/PlugIns/Compressor/CompressorKit.bundle/Contents/Frameworks/Compressor.framework/"
           "Versions/A/Frameworks/StompUI.framework/Versions/A/Resources/BuiltInSettings/")
SETTINGS = {"half": "Proxy Settings/H264 Proxy half size.compressorsetting",
            "full": "Website Sharing/HD1080WebShareName.compressorsetting",
            "proxy": "ProRes/proRes422ProxyName.compressorsetting"}
ACTIVE = re.compile(r"(?i)process|pend|queue|prepar|submit|activ|wait")


def cli(args, timeout=120):
    p = subprocess.run([CLI] + args, capture_output=True, text=True, timeout=timeout)
    return p.stdout + p.stderr


def submit(src, setting, mov, name):
    last = ""
    for _ in range(3):  # "Unable to submit to queue" happens now and then; a retry clears it
        out = cli(["-batchname", name, "-jobpath", "file://" + os.path.abspath(src),
                   "-settingpath", setting, "-locationpath", mov, "-outputformat", "json"])
        m = re.search(r'"batchID"\s*:\s*"([^"]+)"', out)
        if m:
            return m.group(1)
        last = out
        time.sleep(5)
    msg = [line for line in last.splitlines() if "Compressor[" not in line] or last.splitlines()
    raise RuntimeError("Compressor rejected the job: " + " | ".join(msg[-3:]))


def wait(batch, mov, timeout):
    t0, status = time.time(), None
    while time.time() - t0 < timeout:
        time.sleep(2)
        try:
            out = cli(["-monitor", "-batchid", batch, "-outputformat", "json", "-once"], timeout=60)
        except subprocess.TimeoutExpired:  # a stuck -monitor call: poll again until --timeout
            continue
        found = re.findall(r'"status"\s*:\s*"([^"]+)"', out)
        if found:
            status = found[-1]
            if not ACTIVE.search(status):
                time.sleep(1)
                return status, round(time.time() - t0, 1)
    cli(["-kill", "-batchid", batch])
    raise TimeoutError(f"render still {status or 'queued'} after {timeout}s — batch {batch} cancelled")


def probe(mov):
    p = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                        "stream=codec_type,codec_name,width,height,nb_frames,avg_frame_rate:format=duration",
                        "-of", "json", mov], capture_output=True, text=True)
    j = json.loads(p.stdout or "{}")
    v = next((s for s in j.get("streams", []) if s.get("codec_type") == "video" and s.get("width")), None)
    if not v:
        return None
    n, d = (v.get("avg_frame_rate") or "0/1").split("/")
    return {"codec": v.get("codec_name"), "width": v["width"], "height": v["height"],
            "frames": int(v.get("nb_frames") or 0), "fps": round(float(n) / float(d), 3) if float(d) else None,
            "seconds": float(j.get("format", {}).get("duration") or 0)}


def grab(mov, t, png):
    if os.path.exists(png):
        os.remove(png)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(t), "-i", mov, "-frames:v", "1", png],
                   check=True)
    if not os.path.isfile(png):
        raise RuntimeError(f"no frame at {t}s in {mov}")
    p = subprocess.run(["ffmpeg", "-v", "error", "-i", png, "-vf", "signalstats,metadata=print:file=-",
                        "-f", "null", "-"], capture_output=True, text=True)
    st = {k: float(v) for k, v in re.findall(r"lavfi\.signalstats\.(YMIN|YMAX|YAVG)=([\d.]+)", p.stdout)}
    return {"t": t, "png": os.path.abspath(png), "luma_min": st.get("YMIN"), "luma_max": st.get("YMAX"),
            "luma_avg": st.get("YAVG"),
            "blank": (st.get("YMAX", 0) - st.get("YMIN", 0)) < 16 if st else None}


def pixel(png, x, y):
    p = subprocess.run(["ffmpeg", "-v", "error", "-i", png, "-vf", f"crop=3:3:{max(0, x - 1)}:{max(0, y - 1)},scale=1:1",
                        "-pix_fmt", "rgb24", "-f", "rawvideo", "-"], capture_output=True)
    return tuple(p.stdout[:3]) if len(p.stdout) >= 3 else None


def expected_709(hexcol):
    def lin(v):
        return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4

    def oetf(v):  # Apple's Rec. 709 encoding: pure gamma 1.961 (measured)
        return v ** (1 / 1.961)
    h = hexcol.lstrip("#")
    return tuple(round(oetf(lin(int(h[i:i + 2], 16) / 255)) * 255) for i in (0, 2, 4))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("file")
    ap.add_argument("--out", required=True, help="output folder for the movie and PNG frames")
    ap.add_argument("--at", default=None, help="seconds to grab, comma-separated (default: 1/3 and 2/3 in)")
    ap.add_argument("--setting", default="half")
    ap.add_argument("--expect", action="append", default=[], metavar="X,Y=#RRGGBB")
    ap.add_argument("--tolerance", type=int, default=4, help="max per-channel difference (0-255)")
    ap.add_argument("--timeout", type=int, default=300)
    a = ap.parse_args()

    res = {"ok": False, "file": os.path.abspath(a.file)}
    try:
        if not os.path.isfile(CLI):
            raise RuntimeError(f"Compressor not found at {APP} (set COMPRESSOR_APP)")
        for tool in ("ffmpeg", "ffprobe"):
            if not shutil.which(tool):
                raise RuntimeError(f"{tool} not found (brew install ffmpeg)")
        if not os.path.isfile(a.file):
            raise RuntimeError(f"{a.file} not found")
        setting = a.setting if os.path.isfile(a.setting) else os.path.join(APP, BUILTIN, SETTINGS.get(a.setting, ""))
        if not os.path.isfile(setting):
            raise RuntimeError(f"setting {a.setting!r} not found (half, full, proxy or a .compressorsetting path)")
        os.makedirs(a.out, exist_ok=True)
        stem = os.path.splitext(os.path.basename(a.file))[0]
        mov = os.path.join(os.path.abspath(a.out), stem + ".mov")
        if os.path.exists(mov):
            os.remove(mov)
        batch = submit(a.file, setting, mov, "motn-render " + stem)
        status, secs = wait(batch, mov, a.timeout)
        if re.search(r"(?i)controller down", status or ""):
            # transient Compressor failure ("Failed: 2x job controller down"): render once more
            res["retried"] = status
            if os.path.exists(mov):
                os.remove(mov)
            batch = submit(a.file, setting, mov, "motn-render " + stem)
            status, secs = wait(batch, mov, a.timeout)
        res.update(batch=batch, status=status, render_seconds=secs, mov=mov)
        info = probe(mov) if os.path.exists(mov) else None
        if not info or not info["frames"]:
            raise RuntimeError(f"Compressor finished ({status}) but {mov} has no video frames")
        res["video"] = info
        times = ([float(x) for x in a.at.split(",")] if a.at else
                 [round(info["seconds"] / 3, 2), round(info["seconds"] * 2 / 3, 2)])
        last = info["seconds"] - 2 / (info["fps"] or 25)
        clamped = [round(min(max(t, 0), last), 2) for t in times]
        if clamped != times:
            res["note"] = f"--at clamped to the template's {info['seconds']} s: {clamped}"
        res["frames"] = [grab(mov, t, os.path.join(a.out, f"{stem}@{t:g}s.png")) for t in clamped]
        checks = []
        for spec in a.expect:
            pos, _, col = spec.partition("=")
            x, y = (float(v) for v in pos.split(","))
            if x <= 1 and y <= 1:
                x, y = x * (info["width"] - 1), y * (info["height"] - 1)
            for fr in res["frames"]:
                got = pixel(fr["png"], int(x), int(y))
                want = expected_709(col)
                diff = max(abs(g - w) for g, w in zip(got, want)) if got else None
                checks.append({"t": fr["t"], "x": int(x), "y": int(y), "template_color": col,
                               "expected_rgb": want, "got_rgb": got,
                               "pass": diff is not None and diff <= a.tolerance})
        res["checks"] = checks
        res["ok"] = (status or "").lower().startswith("success") and all(c["pass"] for c in checks)
    except (RuntimeError, TimeoutError, subprocess.SubprocessError, ValueError, OSError) as e:
        res["error"] = str(e)
    print(json.dumps(res, indent=1))
    return 0 if res["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
