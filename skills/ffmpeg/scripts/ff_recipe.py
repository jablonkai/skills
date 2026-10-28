#!/usr/bin/env python3
"""Ready-made ffmpeg jobs for the filtergraphs that are easy to get wrong.

Every subcommand probes its inputs, builds the command, writes the output atomically
and prints a one-line ffprobe summary. --dry-run prints the command instead.

  burnsubs  IN SUBS -o OUT [--style ASS_OVERRIDES] [--charenc CP1250]   (needs libass)
  burnsubs  IN --stream 0 -o OUT                                         (embedded text track)
  vertical  IN -o OUT [--size 1080x1920] [--fill blur|black|crop] [--blur 40]
  fit       IN -o OUT --size 1920x1080 [--color black]                   (scale + pad, no crop)
  watermark IN LOGO -o OUT [--pos br] [--margin 32] [--scale 0.15] [--opacity 0.85]
  xfade     IN IN [IN ...] -o OUT [--duration 1] [--transition fade] [--size WxH] [--fps 30]
  gif       IN -o OUT.gif|OUT.webm [--start S] [--duration D] [--fps 15] [--width 480]
  sheet     IN -o OUT.png [--grid 4x4] [--width 480] [--padding 6]       (contact sheet, evenly spaced)
  frames    IN -o OUT.png --at 12.5[,30,...]  |  IN -o DIR/f_%04d.png --every 10
  speed     IN -o OUT --factor 4 [--no-audio]                            (timelapse / slow motion)
  extract-audio IN -o OUT.m4a|.wav|.mp3|.flac [--stream 0]
  replace-audio VIDEO AUDIO -o OUT [--keep-length video|audio|shortest]
  mux-subs  VIDEO SUB [SUB ...] -o OUT [--lang eng,hun]                  (soft subtitle tracks)
"""
import argparse
import os
import shutil
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ff_lib as L  # noqa: E402

H264 = ["-c:v", "libx264", "-crf", "18", "-preset", "medium", "-pix_fmt", "yuv420p"]


def vstream(info, path):
    v = L.streams(info, "video")
    if not v:
        L.die(f"{path} has no video stream")
    return v[0]


def size(s):
    w, _, h = s.lower().partition("x")
    return int(w), int(h)


def even(n):
    return int(n) // 2 * 2


def video_codec(args):
    if getattr(args, "vcodec", None) and args.vcodec != "libx264":
        return ["-c:v", args.vcodec, "-pix_fmt", "yuv420p"] + (["-tag:v", "hvc1"] if "265" in args.vcodec or "hevc" in args.vcodec else [])
    return ["-c:v", "libx264", "-crf", str(getattr(args, "crf", 18)), "-preset", "medium", "-pix_fmt", "yuv420p"]


def mp4_flags(out):
    return ["-movflags", "+faststart"] if os.path.splitext(out)[1].lower() in (".mp4", ".mov", ".m4v", ".m4a") else []


def finish(args, cmd, total=None):
    L.run_ffmpeg(cmd, args.output, total=total, dry_run=args.dry_run)
    if not args.dry_run:
        info = L.probe(args.output)
        desc = []
        for s in info["streams"]:
            d = s.get("codec_name", "?")
            if s["codec_type"] == "video":
                d += f" {s.get('width')}x{s.get('height')}"
            desc.append(d)
        print(f"{args.output}: {L.duration(info):.3f}s  " + ", ".join(desc))


def safe_copy(path, tmp, name):
    """Filter arguments need escaping for ':' ',' quotes and backslashes; a plain temp name needs none."""
    dst = os.path.join(tmp, name + os.path.splitext(path)[1].lower())
    shutil.copyfile(path, dst)
    return dst


# ---------------------------------------------------------------------------

def burnsubs(a):
    ffmpeg = L.find_ffmpeg(("subtitles",))
    info = L.probe(a.input)
    vstream(info, a.input)
    tmp = tempfile.mkdtemp(prefix="ff_subs.")
    try:
        if a.subs:
            src = safe_copy(a.subs, tmp, "subs")
            vf = f"subtitles=filename={src}"
            if a.charenc:
                vf += f":charenc={a.charenc}"
        else:
            src = os.path.join(tmp, "input" + os.path.splitext(a.input)[1])
            os.symlink(os.path.abspath(a.input), src)
            vf = f"subtitles=filename={src}:si={a.stream}"
        if a.style:
            vf += ":force_style='" + a.style.replace("'", "") + "'"
        cmd = [ffmpeg, "-i", a.input, "-map", "0:v:0", "-map", "0:a?", "-vf", vf] + video_codec(a) + \
              ["-c:a", "copy"] + mp4_flags(a.output) + [a.output]
        finish(a, cmd, L.duration(info))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def vertical(a):
    ffmpeg = L.find_ffmpeg()
    info = L.probe(a.input)
    vstream(info, a.input)
    W, H = size(a.size)
    if a.fill == "crop":
        fg = f"[0:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1[v]"
    elif a.fill == "black":
        fg = f"[0:v]scale={W}:{H}:force_original_aspect_ratio=decrease,pad={W}:{H}:(ow-iw)/2:(oh-ih)/2:black,setsar=1[v]"
    else:
        # background: the same video zoomed to cover the frame and blurred; foreground: whole frame, centred
        fg = (f"[0:v]split=2[bg][fg];"
              f"[bg]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},gblur=sigma={a.blur},eq=brightness={a.dim}[bgb];"
              f"[fg]scale={W}:{H}:force_original_aspect_ratio=decrease[fgs];"
              f"[bgb][fgs]overlay=(W-w)/2:(H-h)/2,setsar=1,format=yuv420p[v]")
    cmd = [ffmpeg, "-i", a.input, "-filter_complex", fg, "-map", "[v]", "-map", "0:a?"] + video_codec(a) + \
          ["-c:a", "copy"] + mp4_flags(a.output) + [a.output]
    finish(a, cmd, L.duration(info))


def fit(a):
    ffmpeg = L.find_ffmpeg()
    info = L.probe(a.input)
    vstream(info, a.input)
    W, H = size(a.size)
    vf = f"scale={W}:{H}:force_original_aspect_ratio=decrease,pad={W}:{H}:(ow-iw)/2:(oh-ih)/2:{a.color},setsar=1"
    cmd = [ffmpeg, "-i", a.input, "-map", "0:v:0", "-map", "0:a?", "-vf", vf] + video_codec(a) + \
          ["-c:a", "copy"] + mp4_flags(a.output) + [a.output]
    finish(a, cmd, L.duration(info))


def watermark(a):
    ffmpeg = L.find_ffmpeg()
    info = L.probe(a.input)
    v = vstream(info, a.input)
    m = a.margin
    pos = {"tl": (f"{m}", f"{m}"), "tr": (f"W-w-{m}", f"{m}"), "bl": (f"{m}", f"H-h-{m}"),
           "br": (f"W-w-{m}", f"H-h-{m}"), "center": ("(W-w)/2", "(H-h)/2")}[a.pos]
    lw = even(v["width"] * a.scale)
    logo_in = ["-loop", "1", "-i", a.logo] if os.path.splitext(a.logo)[1].lower() in (".png", ".jpg", ".jpeg", ".webp") else ["-i", a.logo]
    fg = (f"[1:v]scale={lw}:-1,format=rgba,colorchannelmixer=aa={a.opacity}[logo];"
          f"[0:v][logo]overlay={pos[0]}:{pos[1]}:shortest=1,format=yuv420p[v]")
    cmd = [ffmpeg, "-i", a.input] + logo_in + ["-filter_complex", fg, "-map", "[v]", "-map", "0:a?"] + \
        video_codec(a) + ["-c:a", "copy"] + mp4_flags(a.output) + [a.output]
    finish(a, cmd, L.duration(info))


def xfade(a):
    ffmpeg = L.find_ffmpeg()
    if len(a.inputs) < 2:
        L.die("xfade needs at least two inputs")
    infos = [L.probe(p) for p in a.inputs]
    v0 = vstream(infos[0], a.inputs[0])
    W, H = size(a.size) if a.size else (v0["width"], v0["height"])
    R = a.fps or v0.get("avg_frame_rate", "30/1")
    D = a.duration
    durs = []
    for p, info in zip(a.inputs, infos):
        v = vstream(info, p)
        d = float(v.get("duration") or L.duration(info))
        if d <= 2 * D:
            L.die(f"{p} ({d:.2f}s) is too short for a {D}s transition on both sides")
        durs.append(d)
    with_audio = any(L.streams(i, "audio") for i in infos)
    fg = []
    for i, (info, d) in enumerate(zip(infos, durs)):
        # xfade needs identical size, frame rate, pixel format and timebase on both inputs
        fg.append(f"[{i}:v:0]scale={W}:{H}:force_original_aspect_ratio=decrease,pad={W}:{H}:(ow-iw)/2:(oh-ih)/2,"
                  f"setsar=1,fps={R},format=yuv420p,trim=duration={d:.6f},setpts=PTS-STARTPTS,settb=AVTB[v{i}]")
        if with_audio:
            if L.streams(info, "audio"):
                fg.append(f"[{i}:a:0]aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo,"
                          f"atrim=duration={d:.6f},apad=whole_dur={d:.6f},asetpts=PTS-STARTPTS[a{i}]")
            else:
                fg.append(f"anullsrc=r=48000:cl=stereo,atrim=duration={d:.6f}[a{i}]")
    prev_v, prev_a, t = "[v0]", "[a0]", durs[0]
    for i in range(1, len(durs)):
        off = t - D
        nv, na = ("[v]", "[a]") if i == len(durs) - 1 else (f"[vx{i}]", f"[ax{i}]")
        fg.append(f"{prev_v}[v{i}]xfade=transition={a.transition}:duration={D}:offset={off:.6f}{nv}")
        if with_audio:
            fg.append(f"{prev_a}[a{i}]acrossfade=d={D}:c1=tri:c2=tri{na}")
        prev_v, prev_a, t = nv, na, off + durs[i]
    cmd = [ffmpeg] + sum((["-i", p] for p in a.inputs), []) + ["-filter_complex", ";".join(fg), "-map", "[v]"]
    if with_audio:
        cmd += ["-map", "[a]", "-c:a", "aac", "-b:a", "192k"]
    cmd += video_codec(a) + mp4_flags(a.output) + [a.output]
    print(f"expected duration {t:.3f}s ({' + '.join(f'{d:.2f}' for d in durs)} - {len(durs) - 1}x{D})", file=sys.stderr)
    finish(a, cmd, t)


def gif(a):
    ffmpeg = L.find_ffmpeg()
    info = L.probe(a.input)
    vstream(info, a.input)
    seek = (["-ss", str(a.start)] if a.start else []) + (["-t", str(a.duration)] if a.duration else [])
    ext = os.path.splitext(a.output)[1].lower()
    if ext == ".webm":
        cmd = [ffmpeg] + seek + ["-i", a.input, "-an", "-vf", f"fps={a.fps},scale={a.width}:-2:flags=lanczos",
                                 "-c:v", "libvpx-vp9", "-crf", "32", "-b:v", "0", "-row-mt", "1", a.output]
    elif ext in (".mp4", ".mov"):
        cmd = [ffmpeg] + seek + ["-i", a.input, "-an", "-vf", f"fps={a.fps},scale={a.width}:-2:flags=lanczos"] + \
            H264 + mp4_flags(a.output) + [a.output]
    else:
        # one-pass palette: palettegen sees the whole clip, paletteuse maps every frame to it
        fg = (f"fps={a.fps},scale={a.width}:-1:flags=lanczos,split[s0][s1];"
              f"[s0]palettegen=max_colors={a.colors}:stats_mode={a.stats}[p];"
              f"[s1][p]paletteuse=dither={a.dither}" + (":diff_mode=rectangle" if a.stats == "diff" else ""))
        cmd = [ffmpeg] + seek + ["-i", a.input, "-filter_complex", fg, "-loop", "0" if a.loop else "-1", a.output]
    finish(a, cmd, a.duration or L.duration(info))


def sheet(a):
    ffmpeg = L.find_ffmpeg()
    info = L.probe(a.input)
    v = vstream(info, a.input)
    cols, rows = size(a.grid)
    n = cols * rows
    d = float(v.get("duration") or L.duration(info))
    times = [d * (k + 0.5) / n for k in range(n)]  # centre of each of n equal slices
    cmd = [ffmpeg]
    for t in times:
        cmd += ["-ss", f"{t:.3f}", "-i", a.input]  # input seek per tile: fast even on long files
    fg = [f"[{i}:v:0]trim=end_frame=1,setpts=PTS-STARTPTS,scale={a.width}:-2,setsar=1[t{i}]" for i in range(n)]
    fg.append("".join(f"[t{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=0,"
              f"tile={cols}x{rows}:padding={a.padding}:margin={a.padding}:color={a.color}[s]")
    cmd += ["-filter_complex", ";".join(fg), "-map", "[s]", "-frames:v", "1", "-update", "1", a.output]
    print("tile times: " + ", ".join(f"{t:.2f}" for t in times), file=sys.stderr)
    finish(a, cmd)


def frames(a):
    ffmpeg = L.find_ffmpeg()
    info = L.probe(a.input)
    vstream(info, a.input)
    if a.at:
        ts = [L.parse_time(t) for t in a.at.split(",")]
        if len(ts) == 1:
            finish(a, [ffmpeg, "-ss", f"{ts[0]:.3f}", "-i", a.input, "-frames:v", "1", "-update", "1", a.output])
            return
        if "%" not in a.output:
            L.die("several --at times need a numbered pattern, e.g. -o grabs/f_%02d.png")
        for i, t in enumerate(ts, 1):
            out = a.output % i
            L.run_ffmpeg([ffmpeg, "-ss", f"{t:.3f}", "-i", a.input, "-frames:v", "1", "-update", "1", out], out,
                         dry_run=a.dry_run)
            print(f"{out}: t={t:.3f}")
        return
    if not a.every or "%" not in a.output:
        L.die("use --at T[,T...] or --every SECONDS with a numbered pattern such as DIR/f_%04d.png")
    if a.dry_run:
        print(L.quote([ffmpeg, "-i", a.input, "-vf", f"fps=1/{a.every}", "-fps_mode", "vfr", a.output]))
        return
    os.makedirs(os.path.dirname(os.path.abspath(a.output)), exist_ok=True)
    # numbered patterns cannot be written atomically; ffmpeg writes them in place
    import subprocess
    r = subprocess.run([ffmpeg, "-hide_banner", "-nostdin", "-loglevel", "error", "-y", "-i", a.input,
                        "-vf", f"fps=1/{a.every}", "-fps_mode", "vfr", a.output])
    sys.exit(r.returncode)


def atempo_chain(f):
    parts = []
    while f > 2.0:
        parts.append(2.0)
        f /= 2.0
    while f < 0.5:
        parts.append(0.5)
        f /= 0.5
    parts.append(f)
    return ",".join(f"atempo={p:.6f}" for p in parts)


def speed(a):
    ffmpeg = L.find_ffmpeg()
    info = L.probe(a.input)
    v = vstream(info, a.input)
    R = v.get("avg_frame_rate", "30/1")
    vf = f"setpts=PTS/{a.factor},fps={R}"
    cmd = [ffmpeg, "-i", a.input, "-map", "0:v:0"]
    if a.no_audio or not L.streams(info, "audio"):
        cmd += ["-an", "-filter:v", vf]
    else:
        cmd += ["-map", "0:a:0", "-filter:v", vf, "-filter:a", atempo_chain(a.factor), "-c:a", "aac", "-b:a", "192k"]
    finish(a, cmd + video_codec(a) + mp4_flags(a.output) + [a.output], L.duration(info) / a.factor)


ACODEC = {".m4a": ["-c:a", "aac", "-b:a", "192k"], ".aac": ["-c:a", "aac", "-b:a", "192k"],
          ".mp3": ["-c:a", "libmp3lame", "-q:a", "2"], ".wav": ["-c:a", "pcm_s16le"], ".flac": ["-c:a", "flac"],
          ".opus": ["-c:a", "libopus", "-b:a", "128k"], ".ogg": ["-c:a", "libopus", "-b:a", "128k"]}
COPY_OK = {".m4a": {"aac", "alac"}, ".aac": {"aac"}, ".mp3": {"mp3"}, ".flac": {"flac"}, ".opus": {"opus"},
           ".mka": None, ".wav": {"pcm_s16le", "pcm_s24le"}}


def extract_audio(a):
    ffmpeg = L.find_ffmpeg()
    info = L.probe(a.input)
    au = L.streams(info, "audio")
    if len(au) <= a.stream:
        L.die(f"{a.input} has {len(au)} audio stream(s)")
    ext = os.path.splitext(a.output)[1].lower()
    codec = au[a.stream]["codec_name"]
    ok = COPY_OK.get(ext, set())
    copy = ok is None or codec in ok
    cmd = [ffmpeg, "-i", a.input, "-map", f"0:a:{a.stream}", "-vn", "-sn", "-dn"] + \
        (["-c:a", "copy"] if copy else ACODEC.get(ext, ["-c:a", "aac", "-b:a", "192k"])) + [a.output]
    print(("stream copy" if copy else f"re-encode ({codec} does not fit {ext})"), file=sys.stderr)
    finish(a, cmd, L.duration(info))


def replace_audio(a):
    ffmpeg = L.find_ffmpeg()
    vi, ai = L.probe(a.video), L.probe(a.audio)
    vstream(vi, a.video)
    if not L.streams(ai, "audio"):
        L.die(f"{a.audio} has no audio")
    acodec = L.streams(ai, "audio")[0]["codec_name"]
    ext = os.path.splitext(a.output)[1].lower()
    fits = acodec in ("aac", "alac", "mp3", "ac3", "eac3", "opus") if ext in (".mp4", ".mov", ".m4v") else True
    cmd = [ffmpeg, "-i", a.video, "-i", a.audio, "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy"]
    cmd += ["-c:a", "copy"] if fits else ["-c:a", "aac", "-b:a", "192k"]
    total = L.duration(vi)
    if a.keep_length == "video":
        cmd += ["-t", f"{total:.6f}"]
    elif a.keep_length == "shortest":
        cmd += ["-shortest"]
        total = min(total, L.duration(ai))
    else:
        total = L.duration(ai)
    finish(a, cmd + mp4_flags(a.output) + [a.output], total)


def mux_subs(a):
    ffmpeg = L.find_ffmpeg()
    info = L.probe(a.video)
    ext = os.path.splitext(a.output)[1].lower()
    scodec = "mov_text" if ext in (".mp4", ".m4v", ".mov") else ("webvtt" if ext == ".webm" else "copy")
    langs = a.lang.split(",") if a.lang else []
    cmd = [ffmpeg, "-i", a.video]
    for s in a.subs:
        cmd += (["-sub_charenc", a.charenc] if a.charenc else []) + ["-i", s]
    cmd += ["-map", "0:v", "-map", "0:a?"]
    for i in range(len(a.subs)):
        cmd += ["-map", f"{i + 1}:s:0"]
    cmd += ["-c:v", "copy", "-c:a", "copy", "-c:s", scodec]
    for i in range(len(a.subs)):
        if i < len(langs):
            cmd += [f"-metadata:s:s:{i}", f"language={langs[i]}"]
        cmd += [f"-disposition:s:{i}", "default" if i == 0 and a.default else "0"]
    finish(a, cmd + mp4_flags(a.output) + [a.output], L.duration(info))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    def add(name, fn, *pos):
        p = sub.add_parser(name)
        for x in pos:
            p.add_argument(x, **({"nargs": "+"} if x == "inputs" else {}))
        p.add_argument("-o", "--output", required=True)
        p.add_argument("--dry-run", action="store_true")
        p.add_argument("--crf", type=int, default=18, help="libx264 CRF for re-encoded video (default 18)")
        p.add_argument("--vcodec", default="libx264", help="video encoder, e.g. h264_videotoolbox")
        p.set_defaults(fn=fn)
        return p

    p = add("burnsubs", burnsubs, "input")
    p.add_argument("subs", nargs="?")
    p.add_argument("--stream", type=int, default=0, help="embedded subtitle index when no SUBS file is given")
    p.add_argument("--style", help="ASS overrides, e.g. 'FontName=Arial,FontSize=22,Outline=2,MarginV=40'")
    p.add_argument("--charenc", help="SRT encoding when not UTF-8, e.g. CP1250")
    p = add("vertical", vertical, "input")
    p.add_argument("--size", default="1080x1920")
    p.add_argument("--fill", choices=("blur", "black", "crop"), default="blur")
    p.add_argument("--blur", type=float, default=40)
    p.add_argument("--dim", type=float, default=-0.08, help="background brightness shift (eq), default -0.08")
    p = add("fit", fit, "input")
    p.add_argument("--size", required=True)
    p.add_argument("--color", default="black")
    p = add("watermark", watermark, "input", "logo")
    p.add_argument("--pos", choices=("tl", "tr", "bl", "br", "center"), default="br")
    p.add_argument("--margin", type=int, default=32)
    p.add_argument("--scale", type=float, default=0.15, help="logo width as a fraction of the video width")
    p.add_argument("--opacity", type=float, default=0.85)
    p = add("xfade", xfade, "inputs")
    p.add_argument("--duration", type=float, default=1.0)
    p.add_argument("--transition", default="fade", help="fade, dissolve, wipeleft, slideup, circleopen, fadeblack, ...")
    p.add_argument("--size", help="output WxH (default: the first input's); others are fitted with padding")
    p.add_argument("--fps", help="output frame rate (default: the first input's)")
    p = add("gif", gif, "input")
    p.add_argument("--start", type=float)
    p.add_argument("--duration", type=float)
    p.add_argument("--fps", type=float, default=15)
    p.add_argument("--width", type=int, default=480)
    p.add_argument("--colors", type=int, default=256)
    p.add_argument("--dither", default="sierra2_4a", help="sierra2_4a (default), bayer:bayer_scale=3, floyd_steinberg, none")
    p.add_argument("--stats", choices=("full", "diff"), default="full", help="diff: palette favours moving parts")
    p.add_argument("--no-loop", dest="loop", action="store_false")
    p = add("sheet", sheet, "input")
    p.add_argument("--grid", default="4x4")
    p.add_argument("--width", type=int, default=480, help="tile width in px")
    p.add_argument("--padding", type=int, default=6)
    p.add_argument("--color", default="black")
    p = add("frames", frames, "input")
    p.add_argument("--at")
    p.add_argument("--every", type=float)
    p = add("speed", speed, "input")
    p.add_argument("--factor", type=float, required=True, help=">1 faster (4 = 4x timelapse), <1 slower")
    p.add_argument("--no-audio", action="store_true")
    p = add("extract-audio", extract_audio, "input")
    p.add_argument("--stream", type=int, default=0)
    p = add("replace-audio", replace_audio, "video", "audio")
    p.add_argument("--keep-length", choices=("video", "audio", "shortest"), default="video")
    p = add("mux-subs", mux_subs, "video")
    p.add_argument("subs", nargs="+")
    p.add_argument("--lang", help="ISO 639-2 codes per subtitle file, e.g. eng,hun")
    p.add_argument("--charenc")
    p.add_argument("--no-default", dest="default", action="store_false")
    a = ap.parse_args()
    for attr in ("input", "video", "logo", "audio", "subs"):
        val = getattr(a, attr, None)
        for v in (val if isinstance(val, list) else [val] if val else []):
            if not os.path.exists(v):
                L.die(f"no such file: {v}")
    for v in getattr(a, "inputs", None) or []:
        if not os.path.exists(v):
            L.die(f"no such file: {v}")
    srcs = [getattr(a, k, None) for k in ("input", "video", "audio")] + list(getattr(a, "inputs", None) or [])
    if any(s and os.path.abspath(s) == os.path.abspath(a.output) for s in srcs):
        L.die("output would overwrite a source")
    a.fn(a)


if __name__ == "__main__":
    main()
