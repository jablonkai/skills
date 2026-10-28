#!/usr/bin/env python3
"""Trim and join clips, stream-copying whenever that is lossless and correct.

  ff_cut.py SEG [SEG ...] -o OUT [--mode auto|copy|reencode] [--dry-run]

SEG is FILE, FILE@START-END, FILE@START- (to the end) or FILE@-END; times are
seconds or [h:]m:s, e.g.  a.mp4@4-10  b.mov@1:02.5-1:30  c.mp4

--mode auto (default): copy when every cut start sits on a keyframe and all
  segments share codec parameters; otherwise re-encode everything frame-accurately
  and say why.
--mode copy: never re-encode; starts that fall between keyframes are moved back to
  the previous keyframe (reported). Fails if the segments cannot be concatenated.
--mode reencode: frame-accurate cuts through the concat filter (libx264/AAC by
  default; segments are scaled/padded to --size/--fps, default the first one's).
"""
import argparse
import os
import re
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ff_lib as L  # noqa: E402

TIME = r"(\d+(?::\d+){0,2}(?:\.\d+)?)"


def parse_seg(s):
    m = re.match(rf"^(.*?)@{TIME}?-{TIME}?$", s)
    if m and (m.group(2) or m.group(3)) and not os.path.exists(s):
        path, a, b = m.groups()
        return path, L.parse_time(a) if a else 0.0, L.parse_time(b) if b else None
    return s, 0.0, None


def params(info):
    """The stream parameters that must match for the concat demuxer."""
    out = []
    for s in info["streams"]:
        k = s["codec_type"]
        if k == "video":
            out.append(("v", s.get("codec_name"), s.get("profile"), s.get("width"), s.get("height"),
                        s.get("pix_fmt"), s.get("avg_frame_rate"), s.get("sample_aspect_ratio", "1:1")))
        elif k == "audio":
            out.append(("a", s.get("codec_name"), s.get("sample_rate"), s.get("channels")))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("segments", nargs="+")
    ap.add_argument("-o", "--output", required=True)
    ap.add_argument("--mode", choices=("auto", "copy", "reencode"), default="auto")
    ap.add_argument("--crf", default="18", help="re-encode quality (libx264 CRF, default 18)")
    ap.add_argument("--preset", default="medium")
    ap.add_argument("--vcodec", default="libx264", help="re-encode video encoder (default libx264)")
    ap.add_argument("--abitrate", default="192k")
    ap.add_argument("--size", help="re-encode output size WxH (default: the first clip's); others are fitted with padding")
    ap.add_argument("--fps", help="re-encode output frame rate (default: the first clip's)")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    ffmpeg = L.find_ffmpeg()
    ffprobe = L.ffprobe_for(ffmpeg)
    out = args.output
    segs = []
    for raw in args.segments:
        path, start, end = parse_seg(raw)
        if not os.path.exists(path):
            L.die(f"no such file: {path}")
        if os.path.abspath(path) == os.path.abspath(out):
            L.die("output would overwrite a source")
        info = L.probe(path, ffprobe)
        total = L.duration(info)
        end = total if end is None else min(end, total)
        if end <= start:
            L.die(f"{raw}: end {end} is not after start {start}")
        v = L.streams(info, "video")
        fr = L.fps(v[0]) if v else 0
        kf = L.keyframes(path, ffprobe) if v else [0.0]
        on_kf = start == 0 or any(abs(k - start) <= (0.5 / fr if fr else 0.02) for k in kf)
        prev_kf = max([k for k in kf if k <= start + 1e-3] or [0.0])
        segs.append(dict(raw=raw, path=path, start=start, end=end, info=info, on_kf=on_kf, prev_kf=prev_kf,
                         has_a=bool(L.streams(info, "audio")), has_v=bool(v)))

    same = all(params(s["info"]) == params(segs[0]["info"]) for s in segs)
    off = [s for s in segs if not s["on_kf"]]
    mode = args.mode
    if mode == "auto":
        if off:
            print("re-encoding: cut start(s) between keyframes would not be frame-accurate with stream copy: "
                  + ", ".join(f"{s['raw']} (previous keyframe {s['prev_kf']:.3f}s)" for s in off), file=sys.stderr)
            mode = "reencode"
        elif not same and len(segs) > 1:
            print("re-encoding: segments differ in codec/size/rate, the concat demuxer would break", file=sys.stderr)
            mode = "reencode"
        else:
            mode = "copy"
    if mode == "copy" and not same and len(segs) > 1:
        L.die("segments have different codec parameters; stream-copy concat is impossible. Use --mode reencode.\n"
              + "\n".join(f"  {s['raw']}: {params(s['info'])}" for s in segs))

    expected = 0.0
    if mode == "copy":
        for s in off:
            print(f"snapping {s['raw']} start {s['start']:.3f}s back to keyframe {s['prev_kf']:.3f}s", file=sys.stderr)
            s["start"] = s["prev_kf"]
        tmp = tempfile.mkdtemp(prefix="ff_cut.", dir=os.path.dirname(os.path.abspath(out)) or ".")
        ext = os.path.splitext(out)[1] or ".mp4"
        parts = []
        for i, s in enumerate(segs):
            whole = s["start"] == 0 and s["end"] >= L.duration(s["info"]) - 1e-3
            expected += s["end"] - s["start"]
            if whole and len(segs) > 1:
                parts.append(os.path.abspath(s["path"]))
                continue
            p = os.path.join(tmp, f"seg{i:03d}{ext}") if len(segs) > 1 else out
            cmd = [ffmpeg]
            if s["start"]:
                cmd += ["-ss", f"{s['start']:.6f}"]
            if not whole:
                cmd += ["-to", f"{s['end']:.6f}"]
            cmd += ["-i", s["path"], "-map", "0:v?", "-map", "0:a?", "-map", "0:s?", "-c", "copy",
                    "-avoid_negative_ts", "make_zero"]
            vs = L.streams(s["info"], "video")
            if not whole and vs and L.fps(vs[0]):
                # -to alone keeps the B-frame packets that decode before the end point (+2-3 frames)
                cmd += ["-frames:v", str(int(round((s["end"] - s["start"]) * L.fps(vs[0]))))]
            if not whole:
                # audio overshoots too; the concat demuxer offsets the next file by the longest stream,
                # which would open a video gap at every join
                cmd += ["-t", f"{s['end'] - s['start']:.6f}"]
            if ext.lower() in (".mp4", ".mov", ".m4v"):
                cmd += ["-movflags", "+faststart"]
            L.run_ffmpeg(cmd + [p], p, dry_run=args.dry_run)
            parts.append(os.path.abspath(p))
        if len(segs) > 1:
            lst = os.path.join(tmp, "list.txt")
            # Without explicit durations the demuxer offsets each next file by its longest stream
            # (audio overshoot), leaving a video gap at every join. Make each file last exactly until
            # its last video frame ends, minus the next file's B-frame start delay.
            spans = []
            for p in parts:
                vs = L.streams(L.probe(p, ffprobe), "video") if not args.dry_run else []
                st = float(vs[0].get("start_time", 0)) if vs else 0.0
                spans.append((st, st + float(vs[0].get("duration", 0))) if vs else None)
            with open(lst, "w") as fh:
                for i, p in enumerate(parts):
                    fh.write("file '" + p.replace("'", "'\\''") + "'\n")
                    if i + 1 < len(parts) and spans[i] and spans[i + 1]:
                        fh.write(f"duration {spans[i][1] - spans[i + 1][0]:.6f}\n")
            if args.dry_run:
                print(f"# {lst}:\n" + "".join(f"#   file '{p}'\n" for p in parts))
            cmd = [ffmpeg, "-f", "concat", "-safe", "0", "-i", lst, "-map", "0", "-c", "copy"]
            if ext.lower() in (".mp4", ".mov", ".m4v"):
                cmd += ["-movflags", "+faststart"]
            L.run_ffmpeg(cmd + [out], out, dry_run=args.dry_run)
        if not args.dry_run:
            for name in os.listdir(tmp):
                os.remove(os.path.join(tmp, name))
            os.rmdir(tmp)
    else:
        ref = next(L.streams(s["info"], "video")[0] for s in segs if s["has_v"])
        W, H = (int(x) for x in args.size.lower().split("x")) if args.size else (ref["width"], ref["height"])
        R = args.fps or ref.get("avg_frame_rate", "25/1")
        any_a = any(s["has_a"] for s in segs)
        cmd, fg, labels = [ffmpeg], [], []
        for i, s in enumerate(segs):
            cmd += ["-ss", f"{s['start']:.6f}", "-to", f"{s['end']:.6f}", "-i", s["path"]]
            expected += s["end"] - s["start"]
        for i, s in enumerate(segs):
            d = s["end"] - s["start"]
            fg.append(f"[{i}:v:0]scale={W}:{H}:force_original_aspect_ratio=decrease,pad={W}:{H}:(ow-iw)/2:(oh-ih)/2,"
                      f"setsar=1,fps={R},format=yuv420p,trim=duration={d:.6f},setpts=PTS-STARTPTS[v{i}]")
            lab = f"[v{i}]"
            if any_a:
                if s["has_a"]:
                    fg.append(f"[{i}:a:0]aresample=48000,aformat=channel_layouts=stereo,"
                              f"atrim=duration={d:.6f},asetpts=PTS-STARTPTS,apad=whole_dur={d:.6f}[a{i}]")
                else:
                    fg.append(f"anullsrc=r=48000:cl=stereo,atrim=duration={d:.6f}[a{i}]")
                lab += f"[a{i}]"
            labels.append(lab)
        fg.append("".join(labels) + f"concat=n={len(segs)}:v=1:a={1 if any_a else 0}[v]" + ("[a]" if any_a else ""))
        cmd += ["-filter_complex", ";".join(fg), "-map", "[v]"]
        if any_a:
            cmd += ["-map", "[a]", "-c:a", "aac", "-b:a", args.abitrate]
        cmd += ["-c:v", args.vcodec]
        if args.vcodec == "libx264" or args.vcodec == "libx265":
            cmd += ["-crf", args.crf, "-preset", args.preset]
        if args.vcodec == "libx265":
            cmd += ["-tag:v", "hvc1"]
        cmd += ["-pix_fmt", "yuv420p", "-movflags", "+faststart", out]
        L.run_ffmpeg(cmd, out, total=expected, dry_run=args.dry_run)

    if not args.dry_run:
        info = L.probe(out, ffprobe)
        got = L.duration(info)
        print(f"{out}: mode={mode} duration={got:.3f}s (requested {expected:.3f}s) "
              + " ".join(s.get("codec_name", "?") for s in info["streams"]))


if __name__ == "__main__":
    main()
