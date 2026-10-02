#!/usr/bin/env python3
"""Build a MusicXML 4.0 score from a compact JSON spec.

    musicxml-build.py spec.json out.musicxml

Spec (see references/musicxml.md for the full format):

    {"title": "Evening Walk", "composer": "T. J.", "key": "F", "time": "4/4",
     "tempo": 96, "bars_per_line": 4,
     "parts": [{"name": "Melody", "instrument": "flute",
                "measures": [{"notes": "A4/q C5/q F5/h", "chords": "F"},
                             {"notes": "E5/q. D5/e C5/h", "chords": "Dm7 Gm7@3"}]}]}

Note tokens: PITCH/DUR, PITCH = C4 F#4 Bb3 (C4 = middle C), r = rest,
[C4,E4,G4] = chord. DUR = w h q e s t (whole .. 32nd), "." dots, "3" makes a
triplet member (e.g. C5/e3), "~" ties into the next note, "|text" adds a lyric
syllable (end the syllable with "-" when the word continues).
Chord symbols: "F Dm7 Bb/D C7b9@3", "@beat" = 1-based beat in the measure.

Every measure is checked against the time signature; a mismatch is an error,
not a silently broken score. Notes are given at concert pitch unless the spec
says "pitch": "written"; transposing instruments get their written pitch and
key in the file. Exit status: 0 written, 1 spec error, 2 usage.
"""

import json
import re
import sys
from fractions import Fraction
from xml.sax.saxutils import escape

DIV = 24  # divisions per quarter: covers 32nds, dots and triplets down to 16th triplets
DUR = {"w": 4, "h": 2, "q": 1, "e": Fraction(1, 2), "s": Fraction(1, 4), "t": Fraction(1, 8)}
TYPE = {"w": "whole", "h": "half", "q": "quarter", "e": "eighth", "s": "16th", "t": "32nd"}
STEPS = "CDEFGAB"
NATURAL = [0, 2, 4, 5, 7, 9, 11]
MAJOR_FIFTHS = {"Cb": -7, "Gb": -6, "Db": -5, "Ab": -4, "Eb": -3, "Bb": -2, "F": -1, "C": 0,
                "G": 1, "D": 2, "A": 3, "E": 4, "B": 5, "F#": 6, "C#": 7}
MINOR_FIFTHS = {"Ab": -7, "Eb": -6, "Bb": -5, "F": -4, "C": -3, "G": -2, "D": -1, "A": 0,
                "E": 1, "B": 2, "F#": 3, "C#": 4, "G#": 5, "D#": 6, "A#": 7}
CLEFS = {"treble": ("G", 2, 0), "bass": ("F", 4, 0), "alto": ("C", 3, 0), "tenor": ("C", 4, 0),
         "treble8vb": ("G", 2, -1), "bass8vb": ("F", 4, -1), "percussion": ("percussion", None, 0)}

# name: (instrument-sound, MIDI program 1-128, clef, (diatonic, chromatic) written->sounding, staves)
INSTRUMENTS = {
    "piano": ("keyboard.piano", 1, "treble", None, 2),
    "voice": ("voice.vocals", 53, "treble", None, 1),
    "soprano": ("voice.soprano", 53, "treble", None, 1),
    "alto voice": ("voice.alto", 53, "treble", None, 1),
    "tenor voice": ("voice.tenor", 53, "treble8vb", (0, 0), 1),
    "bass voice": ("voice.bass", 53, "bass", None, 1),
    "flute": ("wind.flutes.flute", 74, "treble", None, 1),
    "oboe": ("wind.reed.oboe", 69, "treble", None, 1),
    "clarinet": ("wind.reed.clarinet.bflat", 72, "treble", (-1, -2), 1),
    "bassoon": ("wind.reed.bassoon", 71, "bass", None, 1),
    "alto sax": ("wind.reed.saxophone.alto", 66, "treble", (-5, -9), 1),
    "tenor sax": ("wind.reed.saxophone.tenor", 67, "treble", (-8, -14), 1),
    "trumpet": ("brass.trumpet.bflat", 57, "treble", (-1, -2), 1),
    "horn": ("brass.french-horn", 61, "treble", (-4, -7), 1),
    "trombone": ("brass.trombone", 58, "bass", None, 1),
    "violin": ("strings.violin", 41, "treble", None, 1),
    "viola": ("strings.viola", 42, "alto", None, 1),
    "cello": ("strings.cello", 43, "bass", None, 1),
    "double bass": ("strings.contrabass", 44, "bass", (0, 0), 1),
    "guitar": ("pluck.guitar", 25, "treble8vb", (0, 0), 1),
    "bass guitar": ("pluck.bass.electric", 34, "bass", (0, 0), 1),
}
ALIASES = {"clarinet in bb": "clarinet", "bb clarinet": "clarinet", "b-flat clarinet": "clarinet",
           "trumpet in bb": "trumpet", "bb trumpet": "trumpet", "french horn": "horn",
           "horn in f": "horn", "alto saxophone": "alto sax", "tenor saxophone": "tenor sax",
           "contrabass": "double bass", "upright bass": "double bass", "electric bass": "bass guitar",
           "acoustic guitar": "guitar", "vocals": "voice", "melody": "voice", "lead": "voice",
           "violoncello": "cello", "grand piano": "piano"}
OCTAVE_DOWN = {"tenor voice", "double bass", "guitar", "bass guitar"}  # written an octave above sounding

CHORD_KINDS = [  # longest suffix first
    ("maj13", "major-13th"), ("Maj7", "major-seventh"), ("maj11", "major-11th"), ("maj9", "major-ninth"), ("maj7", "major-seventh"),
    ("m7b5", "half-diminished"), ("min13", "minor-13th"), ("min11", "minor-11th"), ("min9", "minor-ninth"),
    ("min7", "minor-seventh"), ("min6", "minor-sixth"), ("mMaj7", "major-minor"), ("7sus4", "suspended-fourth+7"),
    ("dim7", "diminished-seventh"), ("aug7", "augmented-seventh"), ("sus2", "suspended-second"),
    ("sus4", "suspended-fourth"), ("m13", "minor-13th"), ("m11", "minor-11th"), ("m9", "minor-ninth"),
    ("m7", "minor-seventh"), ("m6", "minor-sixth"), ("M7", "major-seventh"), ("-7", "minor-seventh"),
    ("ø7", "half-diminished"), ("o7", "diminished-seventh"), ("+7", "augmented-seventh"), ("13", "dominant-13th"),
    ("11", "dominant-11th"), ("sus", "suspended-fourth"), ("dim", "diminished"), ("aug", "augmented"),
    ("min", "minor"), ("ø", "half-diminished"), ("9", "dominant-ninth"), ("7", "dominant"), ("6", "major-sixth"),
    ("5", "power"), ("m", "minor"), ("-", "minor"), ("o", "diminished"), ("+", "augmented"), ("", "major"),
]


class SpecError(ValueError):
    pass


def parse_pitch(tok):
    m = re.fullmatch(r"([A-Ga-g])(#{1,2}|b{1,2}|x)?(-?\d)", tok)
    if not m:
        raise SpecError(f"bad pitch {tok!r} (want e.g. C4, F#4, Bb3)")
    acc = m.group(2) or ""
    alter = {"": 0, "#": 1, "##": 2, "x": 2, "b": -1, "bb": -2}[acc]
    return STEPS.index(m.group(1).upper()), alter, int(m.group(3))


def shift_pitch(p, diatonic, chromatic):
    step, alter, octave = p
    semis = 12 * octave + NATURAL[step] + alter + chromatic
    idx = 7 * octave + step + diatonic
    nstep, noct = idx % 7, idx // 7
    nalter = semis - (12 * noct + NATURAL[nstep])
    if abs(nalter) > 2:
        raise SpecError("transposition produced a triple accidental")
    return nstep, nalter, noct


def fifths_shift(fifths, diatonic, chromatic):
    f = fifths + 7 * chromatic - 12 * diatonic
    while f > 7:
        f -= 12
    while f < -7:
        f += 12
    return f


def parse_key(key):
    if isinstance(key, int):
        return key, "major"
    m = re.fullmatch(r"\s*([A-G][#b]?)\s*(m|min|minor|maj|major)?\s*", str(key))
    if not m:
        raise SpecError(f"bad key {key!r} (want e.g. F, Bb, F#m, D minor)")
    minor = (m.group(2) or "").startswith("m") and not (m.group(2) or "").startswith("maj")
    table = MINOR_FIFTHS if minor else MAJOR_FIFTHS
    if m.group(1) not in table:
        raise SpecError(f"no key signature for {key!r}")
    return table[m.group(1)], "minor" if minor else "major"


def parse_time(t):
    m = re.fullmatch(r"\s*(\d+)\s*/\s*(\d+)\s*", str(t))
    if not m:
        raise SpecError(f"bad time signature {t!r}")
    beats, beat_type = int(m.group(1)), int(m.group(2))
    return beats, beat_type, Fraction(4 * beats, beat_type)


def parse_note(tok):
    m = re.fullmatch(r"(\[[^\]]+\]|[^/\s]+)/([whqest])(\.{0,2})(3?)(~?)(?:\|(.*))?", tok)
    if not m:
        raise SpecError(f"bad note token {tok!r} (want e.g. C5/q, r/h, [C4,E4]/e., D5/e3~)")
    head, base, dots, trip, tie, lyric = m.groups()
    dur = DUR[base] * (Fraction(1) + sum(Fraction(1, 2 ** (i + 1)) for i in range(len(dots))))
    if trip:
        dur = dur * Fraction(2, 3)
    if head == "r":
        pitches = None
    elif head.startswith("["):
        pitches = [parse_pitch(x.strip()) for x in head[1:-1].split(",") if x.strip()]
    else:
        pitches = [parse_pitch(head)]
    return {"pitches": pitches, "base": base, "dots": len(dots), "trip": bool(trip),
            "tie": bool(tie), "lyric": lyric, "dur": dur}


def tokenize_notes(text):
    toks, buf, depth = [], "", 0
    for ch in text:
        if ch == "[":
            depth += 1
        elif ch == "]":
            depth -= 1
        if ch.isspace() and depth == 0 and "|" not in buf:
            if buf:
                toks.append(buf)
            buf = ""
        elif ch.isspace() and "|" in buf:  # lyric text ends at whitespace too
            toks.append(buf)
            buf = ""
        else:
            buf += ch
    if buf:
        toks.append(buf)
    return toks


def parse_chord_symbol(sym):
    m = re.fullmatch(r"([A-G])([#b]?)(.*?)(?:/([A-G])([#b]?))?", sym)
    if not m:
        raise SpecError(f"bad chord symbol {sym!r}")
    root, racc, rest, bass, bacc = m.groups()
    for suffix, kind in CHORD_KINDS:
        if rest.startswith(suffix):
            tail_ = rest[len(suffix):]
            break
    degrees = []
    if kind == "suspended-fourth+7":  # MuseScore renders this encoding as "7sus4"
        kind = "dominant"
        degrees += [(4, 0, "add"), (3, 0, "subtract")]
    for alt, num in re.findall(r"(add|b|#)(\d+)", tail_):
        n = int(num)
        if alt == "add":
            degrees.append((n, 0, "add"))
        else:
            a = -1 if alt == "b" else 1
            degrees.append((n, a, "alter" if n == 5 else "add"))
    if re.sub(r"(add|b|#)\d+", "", tail_).strip("()"):
        raise SpecError(f"unsupported chord suffix in {sym!r}")
    return {"root": (root, {"": 0, "#": 1, "b": -1}[racc]), "kind": kind, "degrees": degrees,
            "bass": (bass, {"": 0, "#": 1, "b": -1}[bacc]) if bass else None}


def parse_chords(text):
    out = []
    for tok in str(text or "").split():
        sym, _, at = tok.partition("@")
        out.append((Fraction(at) - 1 if at else None, parse_chord_symbol(sym)))
    return out


def transpose_chord(ch, diatonic, chromatic):
    def tr(name_alter):
        step, alter, _ = shift_pitch((STEPS.index(name_alter[0]), name_alter[1], 4), diatonic, chromatic)
        return STEPS[step], alter
    return dict(ch, root=tr(ch["root"]), bass=tr(ch["bass"]) if ch["bass"] else None)


def harmony_xml(ch, offset):
    x = ["<harmony>", f"<root><root-step>{ch['root'][0]}</root-step>"]
    if ch["root"][1]:
        x.append(f"<root-alter>{ch['root'][1]}</root-alter>")
    x.append(f"</root><kind>{ch['kind']}</kind>")
    if ch["bass"]:
        x.append(f"<bass><bass-step>{ch['bass'][0]}</bass-step>")
        if ch["bass"][1]:
            x.append(f"<bass-alter>{ch['bass'][1]}</bass-alter>")
        x.append("</bass>")
    for val, alter, typ in ch["degrees"]:
        x.append(f"<degree><degree-value>{val}</degree-value><degree-alter>{alter}</degree-alter>"
                 f"<degree-type>{typ}</degree-type></degree>")
    if offset:
        x.append(f"<offset>{int(offset * DIV)}</offset>")
    x.append("</harmony>")
    return "".join(x)


def resolve_instrument(part):
    name = part.get("instrument") or part.get("name") or "voice"
    key = name.strip().lower()
    key = ALIASES.get(key, key)
    if key not in INSTRUMENTS:
        key = next((k for k in INSTRUMENTS if k in name.lower()), None)
    sound, program, clef, transp, staves = INSTRUMENTS.get(key, ("voice.vocals", 1, "treble", None, 1))
    d, c = transp or (0, 0)
    if key in OCTAVE_DOWN:
        d, c = d - 7, c - 12
    return {"key": key, "sound": sound, "program": part.get("program", program),
            "clef": part.get("clef", clef), "transpose": (d, c),
            "staves": int(part.get("staves", staves))}


class Builder:
    def __init__(self, spec):
        self.spec = spec
        self.fifths, self.mode = parse_key(spec.get("key", "C"))
        self.beats, self.beat_type, self.measure_len = parse_time(spec.get("time", "4/4"))
        self.written = spec.get("pitch", "concert") == "written"
        self.per_line = int(spec.get("bars_per_line") or 0)  # forced system breaks, e.g. 4 for lead sheets

    def note_xml(self, n, pitch, chord, staff, voice, transp, tie_start, tie_stop, tuplet, first):
        x = ["<note>"]
        if chord:
            x.append("<chord/>")
        if pitch is None:
            x.append("<rest/>")
        else:
            step, alter, octave = pitch
            x.append(f"<pitch><step>{STEPS[step]}</step>")
            if alter:
                x.append(f"<alter>{alter}</alter>")
            x.append(f"<octave>{octave}</octave></pitch>")
        x.append(f"<duration>{int(n['dur'] * DIV)}</duration>")
        if tie_stop:
            x.append('<tie type="stop"/>')
        if tie_start:
            x.append('<tie type="start"/>')
        x.append(f"<voice>{voice}</voice><type>{TYPE[n['base']]}</type>")
        x.extend("<dot/>" for _ in range(n["dots"]))
        if n["trip"]:
            x.append("<time-modification><actual-notes>3</actual-notes>"
                     "<normal-notes>2</normal-notes></time-modification>")
        if staff:
            x.append(f"<staff>{staff}</staff>")
        notations = []
        if tie_stop:
            notations.append('<tied type="stop"/>')
        if tie_start:
            notations.append('<tied type="start"/>')
        if tuplet and not chord:
            notations.append(f'<tuplet type="{tuplet}"/>')
        if notations:
            x.append("<notations>" + "".join(notations) + "</notations>")
        if n["lyric"] and first:
            text = n["lyric"]
            syll = "single"
            if text.endswith("-"):
                text = text[:-1]
                syll = "middle" if n.get("cont") else "begin"
            elif n.get("cont"):
                syll = "end"
            x.append(f'<lyric number="1"><syllabic>{syll}</syllabic><text>{escape(text)}</text></lyric>')
        x.append("</note>")
        return "".join(x)

    def voice_xml(self, text, mnum, staff, voice, transp, state, harmonies, allow_short):
        notes = [parse_note(t) for t in tokenize_notes(text)]
        total = sum(n["dur"] for n in notes)
        if total != self.measure_len and not (allow_short and total < self.measure_len):
            raise SpecError(f"measure {mnum}{' staff ' + str(staff) if staff else ''}: notes last "
                            f"{total} quarters, time signature needs {self.measure_len}")
        out, pos, trip_acc, trip_goal = [], Fraction(0), Fraction(0), None
        pending = sorted(harmonies, key=lambda h: h[0])
        for n in notes:
            n["cont"] = state.get("lyric_cont", False)
            if n["lyric"]:
                state["lyric_cont"] = n["lyric"].endswith("-")
            while pending and pending[0][0] < pos + n["dur"]:
                at, ch = pending.pop(0)
                out.append(harmony_xml(ch, max(Fraction(0), at - pos)))
            tuplet = None
            if n["trip"]:
                if trip_goal is None:
                    trip_goal, trip_acc, tuplet = DUR[n["base"]] * 2, Fraction(0), "start"
                trip_acc += n["dur"]
                if trip_acc >= trip_goal:
                    tuplet, trip_goal = "stop", None
            pitches = n["pitches"] or [None]
            tied_prev = state.get("tied", set())
            now_tied = set()
            for i, p in enumerate(pitches):
                if p is not None and not self.written:
                    p = shift_pitch(p, -transp[0], -transp[1])
                key = p and (p[0], p[1], p[2])
                stop = key in tied_prev
                if n["tie"] and p is not None:
                    now_tied.add(key)
                out.append(self.note_xml(n, p, i > 0, staff, voice, transp, n["tie"] and p is not None,
                                         stop, tuplet, i == 0))
            state["tied"] = now_tied
            pos += n["dur"]
        for at, ch in pending:  # chord after the last note start: anchor to the last note
            out.insert(len(out) - 1, harmony_xml(ch, at - (pos - notes[-1]["dur"])))
        return out, total

    def part_xml(self, pid, part):
        inst = resolve_instrument(part)
        d, c = inst["transpose"]
        transp = (d, c)  # written -> sounding, MusicXML <transpose> semantics
        staves = inst["staves"]
        measures = part.get("measures") or []
        if not measures:
            raise SpecError(f"part {part.get('name')!r} has no measures")
        out = [f'<part id="{pid}">']
        states = {1: {}, 2: {}}
        has_pickup = isinstance(measures[0], dict) and bool(measures[0].get("pickup"))
        fifths, beats, beat_type = self.fifths, self.beats, self.beat_type
        for i, m in enumerate(measures, start=1):
            if isinstance(m, str):
                m = {"notes": m}
            pickup = bool(m.get("pickup")) and i == 1
            number = i - 1 if has_pickup else i
            out.append(f'<measure number="{number}"' + (' implicit="yes"' if pickup else "") + ">")
            if m.get("page_break") and number > 1:
                out.append('<print new-page="yes"/>')
            elif m.get("break") or (self.per_line and number > 1 and (number - 1) % self.per_line == 0
                                    and m.get("break") is not False):
                out.append('<print new-system="yes"/>')
            if m.get("repeat_start"):
                out.append('<barline location="left"><bar-style>heavy-light</bar-style>'
                           '<repeat direction="forward"/></barline>')
            attrs = []
            if i == 1:
                attrs.append(f"<divisions>{DIV}</divisions>")
            if "key" in m:
                fifths, self.mode = parse_key(m["key"])
            if i == 1 or "key" in m:
                attrs.append(f"<key><fifths>{fifths_shift(fifths, -d, -c)}</fifths><mode>{self.mode}</mode></key>")
            if "time" in m:
                beats, beat_type, self.measure_len = parse_time(m["time"])
            if i == 1 or "time" in m:
                attrs.append(f"<time><beats>{beats}</beats><beat-type>{beat_type}</beat-type></time>")
            if i == 1:
                if staves > 1:
                    attrs.append(f"<staves>{staves}</staves>")
                clefs = [inst["clef"]] if staves == 1 else [part.get("clef", "treble"), part.get("clef2", "bass")]
                for sn, cname in enumerate(clefs, start=1):
                    if cname not in CLEFS:
                        raise SpecError(f"unknown clef {cname!r}")
                    sign, line, oct_ = CLEFS[cname]
                    num = f' number="{sn}"' if staves > 1 else ""
                    cx = f"<clef{num}><sign>{sign}</sign>" + (f"<line>{line}</line>" if line else "")
                    cx += f"<clef-octave-change>{oct_}</clef-octave-change>" if oct_ else ""
                    attrs.append(cx + "</clef>")
                if (d, c) != (0, 0):
                    tx = f"<transpose><diatonic>{d % 7 if d >= 0 else -((-d) % 7)}</diatonic>"
                    tx += f"<chromatic>{c % 12 if c >= 0 else -((-c) % 12)}</chromatic>"
                    octs = int(c / 12) if abs(c) >= 12 else 0
                    tx += f"<octave-change>{octs}</octave-change>" if octs else ""
                    attrs.append(tx + "</transpose>")
            if attrs:
                out.append("<attributes>" + "".join(attrs) + "</attributes>")
            if i == 1 and pid == "P1" and self.spec.get("tempo"):
                bpm = self.spec["tempo"]
                out.append('<direction placement="above"><direction-type><metronome>'
                           f"<beat-unit>quarter</beat-unit><per-minute>{bpm}</per-minute></metronome>"
                           f'</direction-type><sound tempo="{bpm}"/></direction>')
            if m.get("text"):
                out.append('<direction placement="above"><direction-type><words>'
                           f"{escape(m['text'])}</words></direction-type></direction>")
            if m.get("rehearsal"):
                out.append('<direction placement="above"><direction-type><rehearsal>'
                           f"{escape(m['rehearsal'])}</rehearsal></direction-type></direction>")
            harmonies = []
            for at, ch in parse_chords(m.get("chords")):
                harmonies.append((at, ch))
            harmonies = self.place_chords(harmonies, i)
            if not self.written and (d, c) != (0, 0):
                harmonies = [(at, transpose_chord(ch, -d, -c)) for at, ch in harmonies]
            if staves == 1:
                body, total = self.voice_xml(m.get("notes", ""), i, None, 1, transp, states[1], harmonies, pickup)
                out.extend(body)
            else:
                body, total = self.voice_xml(m.get("notes", ""), i, 1, 1, transp, states[1], harmonies, pickup)
                out.extend(body)
                out.append(f"<backup><duration>{int(total * DIV)}</duration></backup>")
                body2, _ = self.voice_xml(m.get("notes2") or f"r/{self.whole_rest()}", i, 2, 5, transp,
                                          states[2], [], pickup)
                out.extend(body2)
            last = i == len(measures)
            if m.get("repeat_end"):
                out.append('<barline location="right"><bar-style>light-heavy</bar-style>'
                           '<repeat direction="backward"/></barline>')
            elif last:
                out.append('<barline location="right"><bar-style>light-heavy</bar-style></barline>')
            elif m.get("double"):
                out.append('<barline location="right"><bar-style>light-light</bar-style></barline>')
            out.append("</measure>")
        out.append("</part>")
        return "".join(out), inst

    def whole_rest(self):
        for base, dur in DUR.items():
            for dots in ("", "."):
                if dur * (Fraction(3, 2) if dots else 1) == self.measure_len:
                    return base + dots
        raise SpecError("give notes2 explicitly: no single rest fills this time signature")

    def place_chords(self, harmonies, mnum):
        """Chords without @beat are spread evenly: 1 per measure, 2 = halves, 4 = beats."""
        n = len(harmonies)
        out = []
        beat = Fraction(4, self.beat_type)
        for idx, (at, ch) in enumerate(harmonies):
            if at is None:
                at = self.measure_len * idx / n if n else Fraction(0)
            else:
                at = at * beat
            if at >= self.measure_len:
                raise SpecError(f"measure {mnum}: chord {ch['root'][0]} placed past the barline")
            out.append((at, ch))
        return out

    def build(self):
        s = self.spec
        parts = s.get("parts") or []
        if not parts:
            raise SpecError("spec has no parts")
        lens = {len(p.get("measures") or []) for p in parts}
        if len(lens) > 1:
            raise SpecError(f"parts have different measure counts: {sorted(lens)}")
        part_list, bodies = [], []
        for i, p in enumerate(parts, start=1):
            pid = f"P{i}"
            body, inst = self.part_xml(pid, p)
            name = escape(p.get("name") or (inst["key"] or "Part").title())
            abbr = escape(p.get("abbreviation", ""))
            part_list.append(
                f'<score-part id="{pid}"><part-name>{name}</part-name>'
                + (f"<part-abbreviation>{abbr}</part-abbreviation>" if abbr else "")
                + f'<score-instrument id="{pid}-I1"><instrument-name>{name}</instrument-name>'
                f"<instrument-sound>{inst['sound']}</instrument-sound></score-instrument>"
                f'<midi-instrument id="{pid}-I1"><midi-channel>{i if i < 10 else min(i + 1, 16)}</midi-channel>'
                f"<midi-program>{inst['program']}</midi-program></midi-instrument></score-part>")
            bodies.append(body)
        title = escape(s.get("title", ""))
        head = ['<?xml version="1.0" encoding="UTF-8" standalone="no"?>',
                '<!DOCTYPE score-partwise PUBLIC "-//Recordare//DTD MusicXML 4.0 Partwise//EN" '
                '"http://www.musicxml.org/dtds/partwise.dtd">',
                '<score-partwise version="4.0">']
        if title:
            head.append(f"<work><work-title>{title}</work-title></work>")
        ident = []
        for role in ("composer", "lyricist", "arranger"):
            if s.get(role):
                ident.append(f'<creator type="{role}">{escape(s[role])}</creator>')
        ident.append("<encoding><software>musescore skill musicxml-build.py</software></encoding>")
        head.append("<identification>" + "".join(ident) + "</identification>")
        credits = []
        if title:
            credits.append(("title", title, "center", "top", 1600))
        if s.get("subtitle"):
            credits.append(("subtitle", escape(s["subtitle"]), "center", "top", 1530))
        if s.get("composer"):
            credits.append(("composer", escape(s["composer"]), "right", "top", 1480))
        for typ, text, just, valign, y in credits:
            size = {"title": 22, "subtitle": 14}.get(typ, 10)
            x = {"center": 600, "right": 1150}[just]
            head.append(f'<credit page="1"><credit-type>{typ}</credit-type>'
                        f'<credit-words default-x="{x}" default-y="{y}" font-size="{size}" '
                        f'justify="{just}" valign="{valign}">{text}</credit-words></credit>')
        head.append("<part-list>" + "".join(part_list) + "</part-list>")
        return "\n".join(head) + "\n" + "\n".join(bodies) + "\n</score-partwise>\n"


def main(argv):
    if len(argv) != 3 or argv[1] in ("-h", "--help"):
        print(__doc__.strip())
        return 0 if len(argv) == 2 and argv[1] in ("-h", "--help") else 2
    try:
        with open(argv[1], encoding="utf-8") as fh:
            spec = json.load(fh)
        xml = Builder(spec).build()
    except (SpecError, json.JSONDecodeError, OSError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1
    with open(argv[2], "w", encoding="utf-8") as fh:
        fh.write(xml)
    parts = len(spec["parts"])
    print(f"OK {argv[2]}: {parts} part(s), {len(spec['parts'][0]['measures'])} measure(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
