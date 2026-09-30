#!/usr/bin/env python3
"""Rational-time math for FCPXML: times, frames, timecode, frame durations.

FCPXML times are exact rationals in seconds ("1001/30000s", "8s"). Every value in a
timeline must land on a frame boundary of the sequence (offsets, durations) or of the
source (start of a clip), so all math here uses fractions.Fraction, never floats.

Importable module and CLI:

  fcptime.py rate 29.97                      frameDuration and timebase facts
  fcptime.py frames 180180/30000s --rate 29.97   time -> frame count (exact or error)
  fcptime.py time 450 --rate 29.97           frames -> FCPXML time
  fcptime.py tc 3601s --rate 25              time -> timecode
  fcptime.py tc 00:59:58;28 --rate 29.97 --df --to-time   timecode -> time
  fcptime.py snap 1.234 --rate 25 [--mode floor|ceil|nearest]
  fcptime.py --selftest
"""
import argparse
import json
import re
import sys
from fractions import Fraction

# Nominal rate -> frame duration. NTSC rates are 1001-based.
RATES = {
    "23.976": Fraction(1001, 24000), "23.98": Fraction(1001, 24000),
    "24": Fraction(1, 24), "25": Fraction(1, 25),
    "29.97": Fraction(1001, 30000), "30": Fraction(1, 30),
    "47.952": Fraction(1001, 48000), "48": Fraction(1, 48), "50": Fraction(1, 50),
    "59.94": Fraction(1001, 60000), "60": Fraction(1, 60),
    "100": Fraction(1, 100), "119.88": Fraction(1001, 120000), "120": Fraction(1, 120),
}
# frameDuration as FCP writes it in <format> (timescale kept, not reduced).
FD_TEXT = {
    Fraction(1001, 24000): "1001/24000s", Fraction(1, 24): "100/2400s",
    Fraction(1, 25): "100/2500s", Fraction(1001, 30000): "1001/30000s",
    Fraction(1, 30): "100/3000s", Fraction(1001, 48000): "1001/48000s",
    Fraction(1, 48): "100/4800s", Fraction(1, 50): "100/5000s",
    Fraction(1001, 60000): "1001/60000s", Fraction(1, 60): "100/6000s",
    Fraction(1, 100): "100/10000s", Fraction(1001, 120000): "1001/120000s",
    Fraction(1, 120): "100/12000s",
}
# Suffix FCP uses in format names such as FFVideoFormat1080p2997.
RATE_NAME = {
    Fraction(1001, 24000): "2398", Fraction(1, 24): "24", Fraction(1, 25): "25",
    Fraction(1001, 30000): "2997", Fraction(1, 30): "30", Fraction(1, 50): "50",
    Fraction(1001, 60000): "5994", Fraction(1, 60): "60",
}

TIME_RE = re.compile(r"^\s*(-?\d+)(?:/(\d+))?s\s*$")
TC_RE = re.compile(r"^\s*(-)?(\d{1,2})[:;](\d{2})[:;](\d{2})([:;.,])(\d{2,3})\s*$")


class TimeError(ValueError):
    pass


def parse_time(text):
    """FCPXML time ("1001/30000s", "8s", "0s") -> Fraction seconds."""
    if isinstance(text, Fraction):
        return text
    m = TIME_RE.match(str(text))
    if not m:
        raise TimeError(f"not an FCPXML time: {text!r}")
    return Fraction(int(m.group(1)), int(m.group(2) or 1))


def frame_duration(rate):
    """'29.97', '30000/1001' (a rate), '1001/30000s' (a duration), 25 -> Fraction."""
    if isinstance(rate, Fraction):
        return rate if rate < 1 else 1 / rate
    s = str(rate).strip()
    if s.endswith("s"):
        return parse_time(s)
    if s in RATES:
        return RATES[s]
    if "/" in s:
        n, d = s.split("/", 1)
        fps = Fraction(int(n), int(d))
    else:
        fps = Fraction(s)
    if fps <= 0:
        raise TimeError(f"bad rate {rate!r}")
    # A decimal like 29.97 or 59.94 means the NTSC rate.
    for fd in RATES.values():
        if abs(float(1 / fd) - float(fps)) < 0.005:
            return fd
    return 1 / fps


def fmt_time(t, fd=None):
    """Fraction seconds -> FCPXML time, written the way FCP writes it: integer-rate
    values reduced ('137/25s'), NTSC values on the 1001 timescale (180 frames of
    1001/30000 -> '180180/30000s')."""
    t = Fraction(t)
    if t.denominator == 1:
        return f"{t.numerator}s"
    if fd is not None:
        fd = Fraction(fd)
        n = t / fd
        if n.denominator == 1 and fd.numerator == 1001:
            return f"{n.numerator * 1001}/{fd.denominator}s"
    return f"{t.numerator}/{t.denominator}s"


def is_aligned(t, fd):
    return (Fraction(t) / Fraction(fd)).denominator == 1


def to_frames(t, fd, exact=True):
    n = Fraction(t) / Fraction(fd)
    if n.denominator != 1:
        if exact:
            raise TimeError(f"{fmt_time(t)} is not on a {fmt_time(fd)} frame boundary "
                            f"({float(n):.3f} frames)")
        return n
    return n.numerator


def snap(t, fd, mode="nearest"):
    n = Fraction(t) / Fraction(fd)
    if mode == "floor":
        k = n.numerator // n.denominator
    elif mode == "ceil":
        k = -((-n.numerator) // n.denominator)
    else:
        k = int(n + Fraction(1, 2)) if n >= 0 else -int(-n + Fraction(1, 2))
    return k * Fraction(fd)


def nominal_fps(fd):
    """Timecode counts frames at the rounded rate: 29.97 -> 30, 23.976 -> 24."""
    return round(1 / Fraction(fd))


def is_drop_capable(fd):
    return Fraction(fd) in (Fraction(1001, 30000), Fraction(1001, 60000))


def tc_to_frames(tc, fd, drop=None):
    """'01:00:00:00' / '00:59:58;28' -> frame count. ';' before frames means DF."""
    m = TC_RE.match(tc)
    if not m:
        raise TimeError(f"not a timecode: {tc!r}")
    neg, hh, mm, ss, sep, ff = m.groups()
    hh, mm, ss, ff = int(hh), int(mm), int(ss), int(ff)
    fps = nominal_fps(fd)
    if drop is None:
        drop = sep == ";"
    if mm > 59 or ss > 59 or ff >= fps:
        raise TimeError(f"timecode out of range for {fps} fps: {tc!r}")
    if drop:
        if not is_drop_capable(fd):
            raise TimeError("drop-frame timecode only exists at 29.97 and 59.94")
        dropn = fps // 15  # 2 at 29.97, 4 at 59.94
        if ss == 0 and mm % 10 != 0 and ff < dropn:
            raise TimeError(f"{tc!r} does not exist in drop-frame timecode")
        total_min = hh * 60 + mm
        frames = (hh * 3600 + mm * 60 + ss) * fps + ff
        frames -= dropn * (total_min - total_min // 10)
    else:
        frames = (hh * 3600 + mm * 60 + ss) * fps + ff
    return -frames if neg else frames


def frames_to_tc(frames, fd, drop=False):
    fps = nominal_fps(fd)
    neg = frames < 0
    frames = abs(int(frames))
    if drop:
        if not is_drop_capable(fd):
            raise TimeError("drop-frame timecode only exists at 29.97 and 59.94")
        dropn = fps // 15
        per10 = fps * 600 - dropn * 9
        per1 = fps * 60 - dropn
        d, m = divmod(frames, per10)
        if m > dropn:
            frames += dropn * 9 * d + dropn * ((m - dropn) // per1)
        else:
            frames += dropn * 9 * d
    ff = frames % fps
    s = frames // fps
    sep = ";" if drop else ":"
    return f"{'-' if neg else ''}{s // 3600:02d}:{s // 60 % 60:02d}:{s % 60:02d}{sep}{ff:02d}"


def tc_to_time(tc, fd, drop=None):
    return tc_to_frames(tc, fd, drop) * Fraction(fd)


def time_to_tc(t, fd, drop=False, start=Fraction(0)):
    """Timeline time -> timecode; start is the sequence tcStart as a time.
    A time between frames gets the frame it falls in, marked with a trailing '~'."""
    total = Fraction(t) + Fraction(start)
    if is_aligned(total, fd):
        return frames_to_tc(to_frames(total, fd), fd, drop)
    return frames_to_tc(int(snap(total, fd, "floor") / Fraction(fd)), fd, drop) + "~"


def parse_user_time(value, fd, drop=None):
    """User-facing time: 12.5 / '12.5' (seconds), '300f' (frames), '1001/30000s',
    'HH:MM:SS:FF' (timecode) -> Fraction seconds."""
    if isinstance(value, Fraction):
        return value
    if isinstance(value, (int, float)):
        return Fraction(str(value))
    s = str(value).strip()
    if TC_RE.match(s):
        return tc_to_time(s, fd, drop)
    if s.endswith("f") and s[:-1].lstrip("-").isdigit():
        return int(s[:-1]) * Fraction(fd)
    if s.endswith("s"):
        return parse_time(s)
    try:
        return Fraction(s)
    except ValueError:
        raise TimeError(f"cannot read time {value!r}: use seconds, 'Nf', 'N/Ds' or HH:MM:SS:FF")


def _selftest():
    ok = 0

    def eq(a, b, what):
        nonlocal ok
        if a != b:
            raise AssertionError(f"{what}: {a!r} != {b!r}")
        ok += 1

    fd2997, fd25, fd2398, fd5994 = (frame_duration(r) for r in ("29.97", "25", "23.976", "59.94"))
    eq(fd2997, Fraction(1001, 30000), "29.97 fd")
    eq(frame_duration("30000/1001"), fd2997, "rational rate")
    eq(frame_duration("1001/30000s"), fd2997, "fd string")
    eq(frame_duration(29.97), fd2997, "float rate")
    eq(fd2398, Fraction(1001, 24000), "23.976 fd")
    eq(parse_time("180180/30000s"), Fraction(6006, 1000), "parse")
    eq(parse_time("8s"), Fraction(8), "parse int")
    eq(fmt_time(Fraction(6006, 1000), fd2997), "180180/30000s", "fmt keeps timescale")
    eq(fmt_time(Fraction(14)), "14s", "fmt int")
    eq(fmt_time(Fraction(137, 25), fd25), "137/25s", "fmt 25p")
    eq(to_frames(parse_time("180180/30000s"), fd2997), 180, "frames")
    try:
        to_frames(Fraction(1, 10), fd25)
        raise AssertionError("misaligned accepted")
    except TimeError:
        ok += 1
    eq(snap(Fraction(1234, 1000), fd25), Fraction(31, 25), "snap nearest")
    eq(snap(Fraction(1234, 1000), fd25, "floor"), Fraction(30, 25), "snap floor")
    eq(snap(Fraction(1201, 1000), fd25, "ceil"), Fraction(31, 25), "snap ceil")
    # NDF
    eq(tc_to_frames("01:00:00:00", fd25), 90000, "tc25")
    eq(frames_to_tc(90000 + 24, fd25), "01:00:00:24", "tc25 back")
    eq(tc_to_time("00:00:10:12", fd25), Fraction(262, 25), "tc->time")
    # 29.97 DF: known anchors
    eq(tc_to_frames("00:01:00;02", fd2997), 1800, "DF first frame after min 1")
    eq(frames_to_tc(1800, fd2997, True), "00:01:00;02", "DF back")
    eq(frames_to_tc(1799, fd2997, True), "00:00:59;29", "DF before drop")
    eq(tc_to_frames("00:10:00;00", fd2997), 17982, "DF 10 min")
    eq(frames_to_tc(17982, fd2997, True), "00:10:00;00", "DF 10 min back")
    eq(tc_to_frames("01:00:00;00", fd2997), 107892, "DF 1 hour")
    eq(frames_to_tc(107892, fd2997, True), "01:00:00;00", "DF 1 hour back")
    for n in (0, 1, 1799, 1800, 1801, 3597, 3598, 17981, 17982, 17983, 107891, 107893, 215784):
        eq(tc_to_frames(frames_to_tc(n, fd2997, True), fd2997), n, f"DF round trip {n}")
    for n in (0, 3599, 3600, 3601, 35963, 35964, 215783):
        eq(tc_to_frames(frames_to_tc(n, fd5994, True), fd5994), n, f"DF59.94 round trip {n}")
    try:
        tc_to_frames("00:01:00;00", fd2997)
        raise AssertionError("nonexistent DF tc accepted")
    except TimeError:
        ok += 1
    # 23.976 counts at 24 nominal
    eq(tc_to_frames("00:00:01:00", fd2398), 24, "23.976 nominal")
    eq(tc_to_time("00:00:01:00", fd2398), Fraction(1001, 1000), "23.976 1s tc is 1.001s")
    eq(time_to_tc(Fraction(3600), fd25), "01:00:00:00", "time_to_tc")
    eq(time_to_tc(Fraction(2), fd25, start=Fraction(3600)), "01:00:02:00", "time_to_tc start")
    eq(parse_user_time("300f", fd25), Fraction(12), "user frames")
    eq(parse_user_time(1.5, fd25), Fraction(3, 2), "user float")
    eq(parse_user_time("00:00:01:12", fd25), Fraction(37, 25), "user tc")
    print(json.dumps({"selftest": "ok", "checks": ok}))


def main():
    if "--selftest" in sys.argv:
        _selftest()
        return 0
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["rate", "frames", "time", "tc", "snap"])
    ap.add_argument("value")
    ap.add_argument("--rate", default="25", help="23.976, 25, 29.97, 30000/1001, 1001/30000s …")
    ap.add_argument("--df", action="store_true", help="drop-frame timecode (29.97/59.94)")
    ap.add_argument("--start", default="0s", help="sequence tcStart (FCPXML time or timecode)")
    ap.add_argument("--to-time", action="store_true", help="tc: convert timecode -> time")
    ap.add_argument("--mode", default="nearest", choices=["nearest", "floor", "ceil"])
    a = ap.parse_args()
    try:
        fd = frame_duration(a.rate if a.cmd != "rate" else a.value)
        out = {"frameDuration": FD_TEXT.get(fd, fmt_time(fd)), "fps": float(1 / fd)}
        if a.cmd == "rate":
            out.update(timecode_fps=nominal_fps(fd), drop_frame_capable=is_drop_capable(fd),
                       format_name_suffix=RATE_NAME.get(fd))
        elif a.cmd == "frames":
            t = parse_user_time(a.value, fd, a.df or None)
            out.update(time=fmt_time(t, fd), frames=to_frames(t, fd))
        elif a.cmd == "time":
            n = int(a.value)
            out.update(frames=n, time=fmt_time(n * fd, fd), seconds=float(n * fd))
        elif a.cmd == "tc":
            if a.to_time:
                t = tc_to_time(a.value, fd, True if a.df else None)
                start = parse_user_time(a.start, fd, a.df or None)
                out.update(timecode=a.value, time=fmt_time(t, fd), timeline_time=fmt_time(t - start, fd),
                           frames=to_frames(t, fd))
            else:
                t = parse_user_time(a.value, fd)
                start = parse_user_time(a.start, fd, a.df or None)
                out.update(time=fmt_time(t, fd), timecode=time_to_tc(t, fd, a.df, start))
        elif a.cmd == "snap":
            t = parse_user_time(a.value, fd)
            s = snap(t, fd, a.mode)
            out.update(input=fmt_time(t), snapped=fmt_time(s, fd), frames=to_frames(s, fd),
                       moved_by=fmt_time(s - t))
    except (TimeError, ValueError, ZeroDivisionError) as e:
        print(json.dumps({"error": str(e)}))
        return 1
    print(json.dumps(out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
