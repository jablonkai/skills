#!/usr/bin/env python3
"""Independent checks of what a MuseScore run produced; prints one JSON report.

    score-check.py [--xsd] [--no-meta] FILE...

Per file, by extension:
  .mscz .mscx .musicxml .mxl .xml .mid .midi .gp* -> MuseScore --score-meta summary
        (title, measures, keysig, timesig, tempo, pages, parts, harmony/lyric counts)
  .musicxml .xml .mxl -> also a parse of the file itself (parts, measures, notes,
        first pitches, chord symbols, lyrics), plus MusicXML 4.0 XSD validation with --xsd
  .pdf  -> page count          .png .svg -> pixel size / bytes
  .mp3 .wav .ogg .flac -> duration and peak/mean volume (silent renders are a real failure mode)

Exit status: 0 when every file exists and passed its checks, 1 otherwise.
The XSD (w3c/musicxml v4.0) is downloaded once into ~/.cache/musescore-skill/.
"""

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.request
import xml.etree.ElementTree as ET
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ms_lib  # noqa: E402

XSD_BASE = "https://raw.githubusercontent.com/w3c/musicxml/v4.0/schema/"
XSD_DIR = os.path.expanduser("~/.cache/musescore-skill/musicxml-4.0")
SCORE_EXT = {".mscz", ".mscx", ".musicxml", ".mxl", ".xml", ".mid", ".midi", ".kar",
             ".gp", ".gp3", ".gp4", ".gp5", ".gpx", ".cap", ".capx", ".mei"}
XML_EXT = {".musicxml", ".xml", ".mxl"}
AUDIO_EXT = {".mp3", ".wav", ".ogg", ".flac"}


def ensure_xsd():
    main = os.path.join(XSD_DIR, "musicxml.xsd")
    if os.path.exists(main):
        return main
    os.makedirs(XSD_DIR, exist_ok=True)
    for name in ("musicxml.xsd", "xlink.xsd", "xml.xsd"):
        with urllib.request.urlopen(XSD_BASE + name, timeout=30) as r:
            data = r.read().decode("utf-8")
        if name == "musicxml.xsd":  # point the imports at the local copies so xmllint works offline
            data = data.replace("http://www.musicxml.org/xsd/xml.xsd", "xml.xsd")
            data = data.replace("http://www.musicxml.org/xsd/xlink.xsd", "xlink.xsd")
        with open(os.path.join(XSD_DIR, name), "w", encoding="utf-8") as fh:
            fh.write(data)
    return main


def musicxml_text(path):
    """Return the score XML of a .musicxml/.xml or compressed .mxl file."""
    if path.lower().endswith(".mxl"):
        with zipfile.ZipFile(path) as z:
            root = ET.fromstring(z.read("META-INF/container.xml"))
            full = next(e.get("full-path") for e in root.iter() if e.tag.endswith("rootfile"))
            return z.read(full)
    with open(path, "rb") as fh:
        return fh.read()


def validate_xsd(path):
    if not shutil.which("xmllint"):
        return {"xsd": "skipped (no xmllint)"}
    try:
        xsd = ensure_xsd()
    except OSError as e:
        return {"xsd": f"skipped (download failed: {e})"}
    with tempfile.NamedTemporaryFile(suffix=".musicxml", delete=False) as tmp:
        tmp.write(musicxml_text(path))
    try:
        p = subprocess.run(["xmllint", "--noout", "--nonet", "--schema", xsd, tmp.name],
                           capture_output=True, text=True)
    finally:
        os.unlink(tmp.name)
    errors = [ln.replace(tmp.name, os.path.basename(path)) for ln in p.stderr.splitlines()
              if "validates" not in ln][:5]
    return {"xsd_valid": p.returncode == 0, **({"xsd_errors": errors} if errors else {})}


def parse_musicxml(path):
    root = ET.fromstring(musicxml_text(path))
    if root.tag != "score-partwise":
        return {"musicxml": f"root is <{root.tag}>, expected <score-partwise>"}
    names = {sp.get("id"): (sp.findtext("part-name") or "") for sp in root.iter("score-part")}
    parts = []
    for part in root.findall("part"):
        measures = part.findall("measure")
        pitches, chords, lyrics, notes = [], [], [], 0
        fifths = part.find("measure/attributes/key/fifths")
        for m in measures:
            for el in m:
                if el.tag == "note" and el.find("rest") is None and el.find("pitch") is not None:
                    notes += 1
                    if len(pitches) < 8 and el.find("chord") is None:
                        p = el.find("pitch")
                        alter = int(float(p.findtext("alter") or 0))
                        pitches.append(p.findtext("step") + {0: "", 1: "#", 2: "##", -1: "b", -2: "bb"}[alter]
                                       + p.findtext("octave"))
                    for ly in el.findall("lyric"):
                        lyrics.append(ly.findtext("text") or "")
                elif el.tag == "harmony":
                    r = el.find("root")
                    if r is not None:
                        alt = int(float(r.findtext("root-alter") or 0))
                        chords.append(r.findtext("root-step") + {0: "", 1: "#", -1: "b"}.get(alt, "?")
                                      + ":" + (el.findtext("kind") or ""))
        tr = part.find("measure/attributes/transpose")
        parts.append({
            "id": part.get("id"), "name": names.get(part.get("id"), ""), "measures": len(measures),
            "written_key_fifths": int(fifths.text) if fifths is not None else None,
            "transpose": None if tr is None else {
                "diatonic": int(tr.findtext("diatonic") or 0), "chromatic": int(tr.findtext("chromatic") or 0),
                "octave_change": int(tr.findtext("octave-change") or 0)},
            "notes": notes, "first_pitches": pitches, "chords": chords, "lyrics": lyrics[:16]})
    return {"title": root.findtext("work/work-title") or root.findtext("movement-title"), "parts": parts}


def meta(path):
    m = ms_lib.score_meta(path)
    return {
        "title": m.get("title"), "measures": m.get("measures"), "keysig": m.get("keysig"),
        "timesig": m.get("timesig"), "tempo": m.get("tempo"), "duration_s": m.get("duration"),
        "pages": m.get("pages"), "has_harmonies": m.get("hasHarmonies") == "true",
        "has_lyrics": m.get("hasLyrics") == "true",
        "parts": [{"name": p.get("name"), "instrument": p.get("instrumentId"),
                   "harmonies": p.get("harmonyCount"), "lyrics": p.get("lyricCount")}
                  for p in m.get("parts", [])],
    }


def pdf_pages(path):
    if shutil.which("pdfinfo"):
        p = subprocess.run(["pdfinfo", path], capture_output=True, text=True)
        m = re.search(r"^Pages:\s+(\d+)", p.stdout, re.M)
        if m:
            return int(m.group(1))
    with open(path, "rb") as fh:
        data = fh.read()
    if not data.startswith(b"%PDF"):
        return 0
    return len(re.findall(rb"/Type\s*/Page[^s]", data))


def audio(path):
    out = {}
    if shutil.which("ffprobe"):
        p = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=sample_rate,channels",
                            "-of", "json", path], capture_output=True, text=True)
        try:
            d = json.loads(p.stdout)
            out["duration_s"] = round(float(d["format"]["duration"]), 2)
            out["sample_rate"] = int(d["streams"][0]["sample_rate"])
        except (KeyError, IndexError, ValueError):
            out["error"] = "ffprobe could not read the file"
    elif shutil.which("afinfo"):
        p = subprocess.run(["afinfo", path], capture_output=True, text=True)
        m = re.search(r"estimated duration:\s*([\d.]+)", p.stdout)
        if m:
            out["duration_s"] = round(float(m.group(1)), 2)
    if shutil.which("ffmpeg"):
        p = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", path, "-af", "volumedetect",
                            "-f", "null", "-"], capture_output=True, text=True)
        for key in ("mean_volume", "max_volume"):
            m = re.search(key + r":\s*(-?[\d.]+|-inf) dB", p.stderr)
            if m:
                out[key + "_db"] = None if m.group(1) == "-inf" else float(m.group(1))
        mx = out.get("max_volume_db")
        out["silent"] = mx is None or mx < -60
    return out


def check(path, want_xsd, want_meta):
    rep = {"file": path}
    if not os.path.exists(path):
        rep.update(ok=False, error="missing")
        return rep
    size = os.path.getsize(path)
    rep["bytes"] = size
    if size == 0:
        rep.update(ok=False, error="empty")
        return rep
    ext = os.path.splitext(path)[1].lower()
    ok = True
    try:
        if ext == ".pdf":
            rep["pages"] = pdf_pages(path)
            ok = rep["pages"] > 0
        elif ext in AUDIO_EXT:
            rep.update(audio(path))
            ok = "error" not in rep and not rep.get("silent", False)
        elif ext == ".png" and shutil.which("sips"):
            p = subprocess.run(["sips", "-g", "pixelWidth", "-g", "pixelHeight", path], capture_output=True, text=True)
            rep["size_px"] = "x".join(re.findall(r"pixel\w+:\s*(\d+)", p.stdout))
        if ext in XML_EXT:
            rep["musicxml"] = parse_musicxml(path)
            if want_xsd:
                rep.update(validate_xsd(path))
                ok = ok and rep.get("xsd_valid", True)
        if ext in SCORE_EXT and want_meta:
            rep["meta"] = meta(path)
    except (ms_lib.MuseScoreError, ET.ParseError, zipfile.BadZipFile, KeyError, StopIteration) as e:
        rep["error"] = str(e) or type(e).__name__
        ok = False
    rep["ok"] = ok
    return rep


def main(argv):
    args = [a for a in argv[1:] if not a.startswith("--")]
    flags = {a for a in argv[1:] if a.startswith("--")}
    if not args or "--help" in flags:
        print(__doc__.strip())
        return 0 if "--help" in flags else 2
    reports = [check(a, "--xsd" in flags, "--no-meta" not in flags) for a in args]
    print(json.dumps(reports if len(reports) > 1 else reports[0], indent=1, ensure_ascii=False))
    return 0 if all(r["ok"] for r in reports) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
