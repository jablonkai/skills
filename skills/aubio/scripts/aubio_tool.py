#!/usr/bin/env python3
"""Audio analysis on top of the aubio CLI: beat grids, onsets, quiet regions, notes, pitch.

Every subcommand decodes the input with FFmpeg to 44.1 kHz mono 16-bit WAV first (any audio
or video file works), runs the aubio CLI on that, writes a CSV and prints a JSON summary on
stdout. Stdlib only — the aubio Python module lives in Homebrew's private interpreter, so
this shells out to `aubio`, `ffmpeg` and `ffprobe` instead of importing it.

  aubio_tool.py prep   IN -o out.wav
  aubio_tool.py beats  IN [--out beats.csv] [--bpm-hint 120] [--bpm-range 70 180] [--meter 4]
                          [--mode auto|grid|follow] [--first-downbeat SEC]
  aubio_tool.py onsets IN [--out onsets.csv] [--method hfc] [--threshold 0.3] [--minioi 0.05]
  aubio_tool.py quiet  IN [--out quiet.csv] [--min-duration 1.0] [--silence auto|-45]
                          [--pad 0.0] [--keep-csv keep.csv]
  aubio_tool.py notes  IN [--out notes.csv] [--midi notes.mid] [--midi-bpm 120]
  aubio_tool.py pitch  IN [--out pitch.csv] [--unit Hz|midi|cent] [--method yinfft]
                          [--min-hz 50] [--max-hz 2000]

Exit codes: 0 ok, 1 analysis found nothing usable, 2 usage/tool error.
"""
import argparse, array, cmath, csv, json, math, os, shutil, subprocess, sys, tempfile, wave

SR = 44100
NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]


class ToolError(Exception):
    pass


# ---------------------------------------------------------------- plumbing

def need_bin(name):
    path = shutil.which(name)
    if not path:
        hint = {"aubio": "brew install aubio", "ffmpeg": "brew install ffmpeg",
                "ffprobe": "brew install ffmpeg"}[name]
        raise ToolError(f"{name} not found on PATH ({hint})")
    return path


def run(cmd):
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode != 0:
        tail = (p.stderr or p.stdout).strip().splitlines()[-5:]
        raise ToolError(f"{os.path.basename(cmd[0])} failed (exit {p.returncode}): " + " | ".join(tail))
    return p.stdout


def prep(src, dst):
    """Decode any audio/video input to 44.1 kHz mono s16 WAV. aubio's own decoding and its
    -r resampling both change results, so analysis always runs on this normalised copy."""
    if not os.path.isfile(src):
        raise ToolError(f"input not found: {src}")
    run([need_bin("ffmpeg"), "-nostdin", "-loglevel", "error", "-y", "-i", src, "-vn", "-map", "0:a:0",
         "-ac", "1", "-ar", str(SR), "-c:a", "pcm_s16le", dst])
    with wave.open(dst) as w:
        dur = w.getnframes() / w.getframerate()
    if dur <= 0:
        raise ToolError(f"no audio decoded from {src}")
    return dur


def aubio(sub, wav, *opts):
    return run([need_bin("aubio"), sub, "-i", wav, "-T", "seconds", *map(str, opts)])


def floats(text):
    """Rows of floats from aubio output; ignores labels such as 'NOISY:' and blank lines."""
    rows = []
    for line in text.splitlines():
        vals = []
        for tok in line.replace(":", " ").split():
            try:
                vals.append(float(tok))
            except ValueError:
                pass
        if vals:
            rows.append(vals)
    return rows


def read_samples(wav):
    with wave.open(wav) as w:
        a = array.array("h")
        a.frombytes(w.readframes(w.getnframes()))
    if sys.byteorder == "big":
        a.byteswap()
    return a


def write_csv(path, header, rows):
    with open(path, "w", newline="") as f:
        cw = csv.writer(f)
        cw.writerow(header)
        cw.writerows(rows)


def default_out(src, kind):
    return f"{os.path.splitext(os.path.basename(src))[0]}.{kind}.csv"


def r(x, nd=3):
    return round(float(x), nd)


def pct(vals, p):
    s = sorted(vals)
    return s[min(len(s) - 1, max(0, int(round(p / 100 * (len(s) - 1)))))]


# ---------------------------------------------------------------- onsets

def detect_onsets(wav, method="default", threshold=None, minioi=None, silence=None):
    opts = ["-m", method]
    if threshold is not None:
        opts += ["-t", threshold]
    if minioi is not None:
        opts += ["-M", minioi]
    if silence is not None:
        opts += ["-s", silence]
    return [row[0] for row in floats(aubio("onset", wav, *opts))]


def onset_strengths(samples, times, win=0.05):
    """Peak amplitude (0..1) in the `win` seconds after each onset — the weight that lets a
    loud kick outvote a quiet off-beat hi-hat in the tempo search."""
    out = []
    n = len(samples)
    for t in times:
        a = int(t * SR)
        seg = samples[a:min(n, a + int(win * SR))]
        out.append(max(map(abs, seg)) / 32768 if seg else 0.0)
    return out


def cmd_onsets(a, wav, dur):
    times = detect_onsets(wav, a.method, a.threshold, a.minioi, a.silence)
    if not times:
        raise ToolError("no onsets detected — lower --threshold or --silence")
    w = onset_strengths(read_samples(wav), times)
    out = a.out or default_out(a.input, "onsets")
    write_csv(out, ["index", "time_s", "strength"], [[i + 1, r(t, 4), r(s)] for i, (t, s) in enumerate(zip(times, w))])
    return {"out": out, "count": len(times), "first_s": r(times[0]), "last_s": r(times[-1]),
            "method": a.method, "duration_s": r(dur)}


# ---------------------------------------------------------------- beats

def coherence(times, weights, bpm, win=8.0):
    """Windowed phase coherence of the onsets with a pulse at `bpm`, 0..1. Summing per-window
    magnitudes (not one global sum) tolerates slow tempo drift and keeps the peak broad
    enough to find on a coarse grid. Half tempo cancels itself (beats land at phase 0 and pi)."""
    T = 60.0 / bpm
    total = sum(weights) or 1.0
    acc, buckets = 0.0, {}
    for t, w in zip(times, weights):
        buckets.setdefault(int(t // win), []).append(w * cmath.exp(2j * math.pi * t / T))
    for vals in buckets.values():
        acc += abs(sum(vals))
    return acc / total


def pulse_score(times, weights, bpm):
    """Beat plus half its subdivision: off-beat hi-hats cancel the beat pulse on their own
    (they sit at phase pi) but reinforce the eighth-note pulse, so the pair stays stable."""
    return coherence(times, weights, bpm) + 0.5 * coherence(times, weights, 2 * bpm)


def search_tempo(times, weights, lo, hi):
    coarse = []
    b = lo
    while b <= hi:
        coarse.append((pulse_score(times, weights, b), b))
        b += 0.5
    coarse.sort(reverse=True)
    best = None
    for _, c in coarse[:4]:
        b = c - 0.6
        while b <= c + 0.6:
            s = pulse_score(times, weights, b)
            if best is None or s > best[0]:
                best = (s, b)
            b += 0.02
    return best


def match(times, weights, grid, tol):
    """For each grid beat, the strongest onset within tol (index or None)."""
    out, j, n = [], 0, len(times)
    for g in grid:
        while j < n and times[j] < g - tol:
            j += 1
        k, pick = j, None
        while k < n and times[k] <= g + tol:
            if pick is None or weights[k] > weights[pick]:
                pick = k
            k += 1
        out.append(pick)
    return out


def fit_grid(times, weights, bpm, start, end, tol):
    """Constant-tempo grid, refined by weighted least squares on the matched onsets."""
    T = 60.0 / bpm
    ph = cmath.phase(sum(w * cmath.exp(2j * math.pi * t / T) for t, w in zip(times, weights)))
    phi = (ph / (2 * math.pi)) * T
    for _ in range(3):
        k0 = math.ceil((start - tol - phi) / T)
        ks = list(range(k0, int((end + tol - phi) // T) + 1))
        grid = [phi + k * T for k in ks]
        m = match(times, weights, grid, tol)
        pts = [(k, times[i], weights[i]) for k, i in zip(ks, m) if i is not None]
        if len(pts) < 4:
            break
        sw = sum(p[2] for p in pts)
        mk = sum(p[0] * p[2] for p in pts) / sw
        mt = sum(p[1] * p[2] for p in pts) / sw
        var = sum(p[2] * (p[0] - mk) ** 2 for p in pts)
        if var <= 0:
            break
        T = sum(p[2] * (p[0] - mk) * (p[1] - mt) for p in pts) / var
        phi = mt - mk * T
    k0 = math.ceil((start - tol - phi) / T)
    ks = list(range(k0, int((end + tol - phi) // T) + 1))
    return [phi + k * T for k in ks], 60.0 / T


def follow_grid(times, weights, bpm, start, end, tol):
    """Beat-following walk for drifting tempo (live playing): each beat snaps to the strongest
    nearby onset and the local period is nudged toward the observed spacing."""
    T = 60.0 / bpm
    grid, _ = fit_grid(times, weights, bpm, start, start + 8 * T, tol)
    pos = grid[0] if grid else start
    beats, Tl = [], T
    while pos <= end + tol:
        m = match(times, weights, [pos], tol)[0]
        beat = times[m] if m is not None else pos
        if beats:
            Tl += 0.15 * ((beat - beats[-1]) - Tl)
            Tl = min(max(Tl, 0.8 * T), 1.25 * T)
        beats.append(beat)
        pos = beat + Tl
    span = beats[-1] - beats[0] if len(beats) > 1 else 0
    return beats, (60.0 * (len(beats) - 1) / span if span else bpm)


def grid_stats(times, weights, grid, tol=0.03):
    m = match(times, weights, grid, tol)
    errs = [times[i] - g for g, i in zip(grid, m) if i is not None]
    rate = len(errs) / len(grid) if grid else 0.0
    rms = math.sqrt(sum(e * e for e in errs) / len(errs)) if errs else None
    return m, rate, rms


def cmd_beats(a, wav, dur):
    samples = read_samples(wav)
    times = detect_onsets(wav, a.method)
    if len(times) < 8:
        raise ToolError(f"only {len(times)} onsets — too few for a beat grid (is the file mostly silent?)")
    weights = onset_strengths(samples, times)
    wmax = max(weights)
    strong = [t for t, w in zip(times, weights) if w >= 0.2 * wmax]
    start, end = strong[0], strong[-1]

    lo, hi = a.bpm_range
    if a.bpm_hint:
        lo, hi = a.bpm_hint * 0.92, a.bpm_hint * 1.08
    score, bpm0 = search_tempo(times, weights, lo, hi)
    alts = {}
    if bpm0 / 2 >= 40:
        alts["half"] = {"bpm": r(bpm0 / 2, 2),
                        "score_ratio": r(pulse_score(times, weights, bpm0 / 2) / score, 2)}

    tol = min(0.07, 0.15 * 60 / bpm0)
    cands = {}
    if a.mode in ("auto", "grid"):
        cands["grid"] = fit_grid(times, weights, bpm0, start, end, tol)
    if a.mode in ("auto", "follow"):
        cands["follow"] = follow_grid(times, weights, bpm0, start, end, tol)
    scored = {k: (grid_stats(times, weights, g), g, b) for k, (g, b) in cands.items()}
    # follow mode only wins when it explains clearly more beats than the steady grid
    mode = "grid" if "grid" in scored else "follow"
    if "follow" in scored and "grid" in scored and scored["follow"][0][1] > scored["grid"][0][1] + 0.1:
        mode = "follow"
    (m, rate, rms), grid, bpm = scored[mode]
    if bpm * 2 <= 260:
        # double time is plausible only when the off-beats hit about as hard as the beats
        T = 60.0 / bpm
        off = match(times, weights, [g + T / 2 for g in grid], tol / 2)
        on_w = [weights[i] for i in m if i is not None]
        off_w = [weights[i] for i in off if i is not None]
        ratio = (sum(off_w) / len(grid)) / (sum(on_w) / len(grid)) if on_w else 0.0
        alts["double"] = {"bpm": r(bpm * 2, 2), "offbeat_strength_ratio": r(ratio, 2)}

    meter = a.meter
    if a.first_downbeat is not None:
        k_down = min(range(len(grid)), key=lambda i: abs(grid[i] - a.first_downbeat)) % meter
        down_conf = None
    else:
        cls = [[] for _ in range(meter)]
        for i, (g, mi) in enumerate(zip(grid, m)):
            cls[i % meter].append(weights[mi] if mi is not None else 0.0)
        means = [sum(c) / len(c) if c else 0.0 for c in cls]
        order = sorted(range(meter), key=lambda c: means[c], reverse=True)
        k_down = order[0]
        down_conf = r((means[order[0]] - means[order[1]]) / means[order[0]], 2) if meter > 1 and means[order[0]] else None

    # bars count from the first downbeat; pickup beats before it are bar 0
    rows, bar = [], 0
    for i, (g, mi) in enumerate(zip(grid, m)):
        pos = (i - k_down) % meter
        if pos == 0:
            bar += 1
        rows.append([i + 1, r(g, 4), bar, pos + 1, int(mi is not None)])

    warnings = []
    if rate < 0.6:
        warnings.append(f"only {rate:.0%} of grid beats have an onset within 30 ms — tempo or phase may be wrong")
    if rms is not None and rms > 0.02:
        warnings.append(f"matched onsets scatter {rms * 1000:.0f} ms around the grid — try --mode follow")
    if alts.get("half", {}).get("score_ratio", 0) >= 0.85:
        warnings.append(f"half-time ({alts['half']['bpm']} bpm) fits almost as well — confirm with the user or pass --bpm-hint")
    if alts.get("double", {}).get("offbeat_strength_ratio", 0) >= 0.7:
        warnings.append(f"off-beats are nearly as strong as beats, so double-time ({alts['double']['bpm']} bpm) is plausible — confirm with the user or pass --bpm-hint")
    if down_conf is not None and down_conf < 0.15:
        warnings.append("downbeat is a guess (beat accents are flat) — pass --first-downbeat SEC if bars matter")
    try:
        aubio_tempo = aubio("tempo", wav).strip()
    except ToolError:
        aubio_tempo = None

    local = None
    if mode == "follow" and len(grid) > 16:
        # snapped beats sit on onsets, so a residual says nothing; the tempo range does
        local = [r(60 * 8 / (grid[8] - grid[0]), 1), r(60 * 8 / (grid[-1] - grid[-9]), 1)]
        rms = None

    out = a.out or default_out(a.input, "beats")
    write_csv(out, ["index", "time_s", "bar", "beat", "matched"], rows)
    return {"out": out, "bpm": r(bpm, 2), "bpm_rounded": int(round(bpm)), "beats": len(rows),
            "bars": max(row[2] for row in rows), "meter": meter, "mode": mode,
            "confidence": r(rate, 2), "residual_ms": r(rms * 1000, 1) if rms is not None else None,
            "bpm_start_end": local, "downbeat_confidence": down_conf, "first_beat_s": r(grid[0]), "last_beat_s": r(grid[-1]),
            "alternatives": alts, "aubio_tempo_raw": aubio_tempo, "uncertain": bool(warnings),
            "warnings": warnings, "duration_s": r(dur)}


# ---------------------------------------------------------------- quiet

def level_profile(wav, frame=0.05):
    """RMS level in dBFS per `frame` seconds, via FFmpeg astats (fast even for hour-long talks)."""
    n = int(8000 * frame)
    txt = run([need_bin("ffmpeg"), "-nostdin", "-hide_banner", "-nostats", "-i", wav, "-af",
               f"aresample=8000,asetnsamples=n={n}:p=0,astats=metadata=1:reset=1,"
               "ametadata=print:key=lavfi.astats.Overall.RMS_level:file=-", "-f", "null", "-"])
    lv = []
    for line in txt.splitlines():
        if "RMS_level=" in line:
            v = line.split("=", 1)[1].strip()
            lv.append(-120.0 if v in ("-inf", "inf", "nan") else float(v))
    return lv


def cmd_quiet(a, wav, dur):
    lv = level_profile(wav)
    floor = max(pct(lv, 3), -80.0) if lv else -70.0
    loud = pct(lv, 90) if lv else -20.0
    warnings = []
    if a.silence == "auto":
        thr = floor + min(max((loud - floor) * 0.3, 6.0), 15.0)
        if loud - floor < 12:
            warnings.append(f"little contrast between quiet ({floor:.0f} dB) and loud ({loud:.0f} dB) parts — results are shaky")
    else:
        thr = float(a.silence)
    rows = floats(aubio("quiet", wav, "-s", f"{thr:.1f}"))
    labels = [line.split(":")[0].strip() for line in aubio("quiet", wav, "-s", f"{thr:.1f}").splitlines() if ":" in line]
    regions = []
    for i, (lab, row) in enumerate(zip(labels, rows)):
        if lab == "QUIET":
            end = rows[i + 1][0] if i + 1 < len(rows) else dur
            regions.append((row[0], end))
    keep = [(s + a.pad, e - a.pad) for s, e in regions if e - s >= a.min_duration and e - s - 2 * a.pad > 0]
    out = a.out or default_out(a.input, "quiet")
    write_csv(out, ["index", "start_s", "end_s", "duration_s"], [[i + 1, r(s), r(e), r(e - s)] for i, (s, e) in enumerate(keep)])
    res = {"out": out, "count": len(keep), "total_quiet_s": r(sum(e - s for s, e in keep), 2),
           "threshold_db": r(thr, 1), "noise_floor_db": r(floor, 1), "loud_level_db": r(loud, 1),
           "min_duration_s": a.min_duration, "pad_s": a.pad, "shorter_regions_skipped": len(regions) - len(keep),
           "regions": [[r(s), r(e)] for s, e in keep], "warnings": warnings, "duration_s": r(dur)}
    if a.keep_csv:
        segs, cur = [], 0.0
        for s, e in keep:
            if s > cur:
                segs.append((cur, s))
            cur = e
        if cur < dur:
            segs.append((cur, dur))
        write_csv(a.keep_csv, ["index", "start_s", "end_s", "duration_s"], [[i + 1, r(s), r(e), r(e - s)] for i, (s, e) in enumerate(segs)])
        res["keep_csv"] = a.keep_csv
        res["kept_s"] = r(sum(e - s for s, e in segs), 2)
    return res


# ---------------------------------------------------------------- notes / pitch

def note_name(m):
    m = int(round(m))
    return f"{NOTE_NAMES[m % 12]}{m // 12 - 1}"


def write_midi(path, notes, bpm=120.0, ppq=480):
    """Type-0 SMF, one track, channel 1, velocity 90."""
    def vlq(n):
        b = [n & 0x7F]
        n >>= 7
        while n:
            b.append((n & 0x7F) | 0x80)
            n >>= 7
        return bytes(reversed(b))
    tick = lambda s: int(round(s * ppq * bpm / 60.0))
    ev = []
    for m, s, e in notes:
        ev.append((tick(s), 1, bytes([0x90, m, 90])))
        ev.append((max(tick(e), tick(s) + 1), 0, bytes([0x80, m, 0])))
    ev.sort(key=lambda x: (x[0], x[1]))
    us = int(round(60_000_000 / bpm))
    data, last = bytearray(b"\x00\xff\x51\x03" + us.to_bytes(3, "big")), 0
    for t, _, msg in ev:
        data += vlq(t - last) + msg
        last = t
    data += b"\x00\xff\x2f\x00"
    with open(path, "wb") as f:
        f.write(b"MThd" + (6).to_bytes(4, "big") + (0).to_bytes(2, "big") + (1).to_bytes(2, "big") + ppq.to_bytes(2, "big"))
        f.write(b"MTrk" + len(data).to_bytes(4, "big") + data)


def cmd_notes(a, wav, dur):
    raw = [row for row in floats(aubio("notes", wav)) if len(row) == 3]  # first/last lines are lone timestamps
    if not raw:
        raise ToolError("no notes detected — aubio notes is monophonic; is the input a single melodic line?")
    onsets = detect_onsets(wav)
    notes = []
    for m, s, e in raw:
        # aubio notes reports a start ~30-60 ms late (it waits for a stable pitch); the onset
        # detector is accurate to a few ms, so snap to the last onset just before it
        near = [t for t in onsets if s - 0.09 <= t <= s + 0.01]
        s2 = near[-1] if near else s
        notes.append((int(round(m)), s2, max(e, s2 + 0.01)))
    out = a.out or default_out(a.input, "notes")
    write_csv(out, ["index", "midi", "name", "start_s", "end_s", "duration_s", "freq_hz"],
              [[i + 1, m, note_name(m), r(s, 4), r(e, 4), r(e - s), r(440 * 2 ** ((m - 69) / 12), 2)]
               for i, (m, s, e) in enumerate(notes)])
    res = {"out": out, "count": len(notes), "sequence": [note_name(m) for m, _, _ in notes],
           "midi": [m for m, _, _ in notes], "first_s": r(notes[0][1]), "duration_s": r(dur)}
    if a.midi:
        write_midi(a.midi, notes, a.midi_bpm)
        res["midi_file"] = a.midi
    return res


def cmd_pitch(a, wav, dur):
    rows = floats(aubio("pitch", wav, "-m", a.method, "-u", "Hz"))
    pts = [(t, f) for t, f in rows if a.min_hz <= f <= a.max_hz]  # 0 = unvoiced frame
    if not pts:
        raise ToolError("no voiced frames in range — adjust --min-hz/--max-hz")
    conv = {"Hz": lambda f: f, "midi": lambda f: 69 + 12 * math.log2(f / 440),
            "cent": lambda f: 1200 * math.log2(f / 440) + 6900}[a.unit]
    out = a.out or default_out(a.input, "pitch")
    write_csv(out, ["time_s", a.unit.lower()], [[r(t, 4), r(conv(f), 3)] for t, f in pts])
    hz = [f for _, f in pts]
    return {"out": out, "frames": len(rows), "voiced_frames": len(pts), "voiced_share": r(len(pts) / len(rows), 2),
            "median_hz": r(pct(hz, 50), 1), "median_note": note_name(69 + 12 * math.log2(pct(hz, 50) / 440)),
            "range_hz": [r(pct(hz, 5), 1), r(pct(hz, 95), 1)], "unit": a.unit, "duration_s": r(dur)}


# ---------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)

    p = sp.add_parser("prep", help="decode to 44.1 kHz mono WAV")
    p.add_argument("input"); p.add_argument("-o", "--out", required=True)

    p = sp.add_parser("beats", help="BPM and a beat grid with bar/beat numbers")
    p.add_argument("input"); p.add_argument("--out")
    p.add_argument("--bpm-hint", type=float, help="expected BPM; searches only +-8%% around it")
    p.add_argument("--bpm-range", type=float, nargs=2, default=[70.0, 180.0], metavar=("LO", "HI"))
    p.add_argument("--meter", type=int, default=4, help="beats per bar")
    p.add_argument("--mode", choices=["auto", "grid", "follow"], default="auto",
                   help="grid = steady tempo, follow = drifting tempo, auto = pick the better fit")
    p.add_argument("--first-downbeat", type=float, metavar="SEC", help="time of a known bar start")
    p.add_argument("--method", default="default", help="aubio onset method (default, hfc, specflux, complex, ...)")

    p = sp.add_parser("onsets", help="onset times with strength")
    p.add_argument("input"); p.add_argument("--out")
    p.add_argument("--method", default="default")
    p.add_argument("--threshold", type=float, help="peak-picking threshold (aubio default 0.3); higher = fewer")
    p.add_argument("--minioi", type=float, help="minimum gap between onsets, seconds")
    p.add_argument("--silence", type=float, help="ignore onsets below this dB level (aubio default -70)")

    p = sp.add_parser("quiet", help="quiet regions (pauses, silences)")
    p.add_argument("input"); p.add_argument("--out")
    p.add_argument("--min-duration", type=float, default=1.0, help="shortest region to report, seconds")
    p.add_argument("--silence", default="auto", help="'auto' (from the noise floor) or a dBFS level such as -45")
    p.add_argument("--pad", type=float, default=0.0, help="shrink each region by this much on both sides")
    p.add_argument("--keep-csv", help="also write the non-quiet segments (for trimming)")

    p = sp.add_parser("notes", help="monophonic note events, optional MIDI file")
    p.add_argument("input"); p.add_argument("--out")
    p.add_argument("--midi", help="write a type-0 .mid file")
    p.add_argument("--midi-bpm", type=float, default=120.0, help="tempo stored in the MIDI file")

    p = sp.add_parser("pitch", help="monophonic pitch track, unvoiced frames removed")
    p.add_argument("input"); p.add_argument("--out")
    p.add_argument("--unit", choices=["Hz", "midi", "cent"], default="Hz")
    p.add_argument("--method", default="yinfft", help="yinfft, yin, mcomb, fcomb, schmitt")
    p.add_argument("--min-hz", type=float, default=40.0); p.add_argument("--max-hz", type=float, default=4000.0)

    a = ap.parse_args()
    try:
        if a.cmd == "prep":
            dur = prep(a.input, a.out)
            print(json.dumps({"out": a.out, "duration_s": r(dur), "samplerate": SR, "channels": 1}))
            return 0
        with tempfile.TemporaryDirectory(prefix="aubio-tool-") as tmp:
            wav = os.path.join(tmp, "in.wav")
            dur = prep(a.input, wav)
            res = {"beats": cmd_beats, "onsets": cmd_onsets, "quiet": cmd_quiet,
                   "notes": cmd_notes, "pitch": cmd_pitch}[a.cmd](a, wav, dur)
        res = {"input": a.input, **res}
        print(json.dumps(res, indent=1))
        return 0
    except ToolError as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        return 1 if "no " in str(e) or "too few" in str(e) else 2


if __name__ == "__main__":
    sys.exit(main())
