"""Minimal RFC 5545 writer and reader for the apple-calendar scripts (stdlib only).

Writer: VCALENDAR with VEVENTs (RRULE, EXDATE, RECURRENCE-ID overrides, VALARMs) and a
VTIMEZONE for every TZID used, so the file imports cleanly into Calendar, Google and
Outlook. Reader: unfolds lines and returns VEVENTs as dicts of (params, value) lists.
"""
import datetime as dt
import re

import cal_lib as L

PRODID = "-//apple-calendar skill//EN"


# ---- writing ------------------------------------------------------------------

def esc(text):
    return (str(text).replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,")
            .replace("\r\n", "\\n").replace("\n", "\\n"))


def fold(line):
    """Fold at 75 octets without splitting a UTF-8 character."""
    out, cur, size = [], "", 0
    for ch in line:
        n = len(ch.encode("utf-8"))
        if size + n > (75 if not out else 74):
            out.append(cur)
            cur, size = "", 0
        cur += ch
        size += n
    out.append(cur)
    return "\r\n ".join(out)


def utc(d):
    return d.astimezone(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def dt_prop(name, d, tzid, all_day=False):
    if all_day:
        return f"{name};VALUE=DATE:{d:%Y%m%d}"
    if tzid:
        return f"{name};TZID={tzid}:{d.astimezone(zone(tzid)):%Y%m%dT%H%M%S}"
    return f"{name}:{utc(d)}"


def zone(name):
    from zoneinfo import ZoneInfo
    return ZoneInfo(name)


def _rule_for(when):
    """RRULE:FREQ=YEARLY;BYMONTH=m;BYDAY=nSU-style rule matching one transition date."""
    last = (when + dt.timedelta(days=7)).month != when.month
    n = -1 if last else (when.day - 1) // 7 + 1
    return f"FREQ=YEARLY;BYMONTH={when.month};BYDAY={n}{L.WEEKDAYS[when.weekday()]}"


def vtimezone(tzid, year):
    """VTIMEZONE built from zoneinfo: the DST transitions of `year`, as yearly rules."""
    z = zone(tzid)

    def off(t):
        return z.utcoffset(t.replace(tzinfo=None))

    def fmt_off(o):
        m = int(o.total_seconds() // 60)
        sign = "+" if m >= 0 else "-"
        return f"{sign}{abs(m) // 60:02d}{abs(m) % 60:02d}"

    trans = []
    t = dt.datetime(year, 1, 1)
    prev = off(t)
    while t.year == year:
        nxt = t + dt.timedelta(hours=1)
        if off(nxt) != prev:
            trans.append((nxt, prev, off(nxt)))
            prev = off(nxt)
        t = nxt
    lines = ["BEGIN:VTIMEZONE", f"TZID:{tzid}"]
    if not trans:
        o = fmt_off(off(dt.datetime(year, 1, 1)))
        lines += ["BEGIN:STANDARD", f"DTSTART:{year}0101T000000", f"TZOFFSETFROM:{o}",
                  f"TZOFFSETTO:{o}", "END:STANDARD"]
    for when, before, after in trans:
        # `when` is the first wall-clock hour with the new offset. RFC 5545 wants the
        # local time at the change in the old offset: 02:00 for a spring-forward gap,
        # and the same 03:00 for a fall-back.
        start = when - (after - before) if after > before else when
        kind = "DAYLIGHT" if after > before else "STANDARD"
        lines += [f"BEGIN:{kind}", f"DTSTART:{start:%Y%m%dT%H%M%S}", f"RRULE:{_rule_for(start)}",
                  f"TZOFFSETFROM:{fmt_off(before)}", f"TZOFFSETTO:{fmt_off(after)}",
                  f"TZNAME:{z.tzname(when)}", f"END:{kind}"]
    lines.append("END:VTIMEZONE")
    return lines


def vevent(e, stamp, rrule=None, exdates=(), recurrence_id=None, uid=None):
    """One VEVENT from an ek event dict."""
    tzid = e.get("timeZone") if not e.get("allDay") else None
    start = L.ev_start(e)
    lines = ["BEGIN:VEVENT", f"UID:{esc(uid or e.get('externalId') or e['id'])}", f"DTSTAMP:{stamp}"]
    if e.get("allDay"):
        lines.append(dt_prop("DTSTART", start.date(), None, True))
        lines.append(dt_prop("DTEND", L.ev_last_day(e) + dt.timedelta(days=1), None, True))
    else:
        lines.append(dt_prop("DTSTART", start, tzid))
        lines.append(dt_prop("DTEND", L.ev_end(e), tzid))
    if recurrence_id:
        lines.append(dt_prop("RECURRENCE-ID", L.parse_when(recurrence_id), tzid, e.get("allDay")))
    lines.append(f"SUMMARY:{esc(e.get('title') or '')}")
    for key, prop in (("location", "LOCATION"), ("notes", "DESCRIPTION"), ("url", "URL")):
        if e.get(key):
            lines.append(f"{prop}:{esc(e[key]) if prop != 'URL' else e[key]}")
    if rrule:
        lines.append(f"RRULE:{rrule}")
    for x in exdates:
        lines.append(dt_prop("EXDATE", L.parse_when(x), tzid, e.get("allDay")))
    if e.get("availability") == "free":
        lines.append("TRANSP:TRANSPARENT")
    for att in e.get("attendees") or []:
        if att.get("email"):
            cn = f";CN={esc(att['name'])}" if att.get("name") else ""
            lines.append(f"ATTENDEE{cn};PARTSTAT={att.get('status', 'unknown').upper().replace('PENDING', 'NEEDS-ACTION')}"
                         f":mailto:{att['email']}")
    lines.append(f"X-APPLE-CALENDAR:{esc(e.get('calendar', ''))}")
    for al in e.get("alarms") or []:
        if "offsetMinutes" in al:
            m = al["offsetMinutes"]
            trig = f"TRIGGER:{'-' if m < 0 else ''}PT{abs(m)}M"
        else:
            trig = f"TRIGGER;VALUE=DATE-TIME:{utc(L.parse_when(al['absolute']))}"
        lines += ["BEGIN:VALARM", "ACTION:DISPLAY", f"DESCRIPTION:{esc(e.get('title') or 'Reminder')}",
                  trig, "END:VALARM"]
    lines.append("END:VEVENT")
    return lines


def calendar_text(vevents, tzids, year, name=None):
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0", f"PRODID:{PRODID}", "CALSCALE:GREGORIAN", "METHOD:PUBLISH"]
    if name:
        lines.append(f"X-WR-CALNAME:{esc(name)}")
    for tz in sorted(tzids):
        lines += vtimezone(tz, year)
    for ev in vevents:
        lines += ev
    lines.append("END:VCALENDAR")
    return "".join(fold(x) + "\r\n" for x in lines)


# ---- reading ------------------------------------------------------------------

def unesc(v):
    return re.sub(r"\\([\\;,nN])", lambda m: "\n" if m.group(1) in "nN" else m.group(1), v)


def parse(text):
    """[{'NAME': [(params, value), ...], '_alarms': [...]}] for every VEVENT."""
    text = re.sub(r"\r?\n[ \t]", "", text)
    events, stack = [], []
    for raw in text.splitlines():
        if not raw.strip():
            continue
        m = re.match(r"([A-Za-z0-9-]+)((?:;[^:;]+=(?:\"[^\"]*\"|[^:;]*))*):(.*)", raw)
        if not m:
            continue
        name, ptxt, value = m.group(1).upper(), m.group(2), m.group(3)
        params = dict((k.upper(), v.strip('"')) for k, v in re.findall(r";([^=;]+)=(\"[^\"]*\"|[^;]*)", ptxt))
        if name == "BEGIN":
            stack.append({"_type": value.upper(), "_alarms": []})
        elif name == "END":
            comp = stack.pop() if stack else None
            if comp and comp["_type"] == "VEVENT":
                events.append(comp)
            elif comp and comp["_type"] == "VALARM" and stack:
                stack[-1]["_alarms"].append(comp)
        elif stack:
            stack[-1].setdefault(name, []).append((params, value))
    return events


def first(comp, name, default=None):
    v = comp.get(name)
    return v[0] if v else (None, default) if default is not None else None


def parse_dt(params, value):
    """(datetime or date, is_date). TZID names that zoneinfo doesn't know fall back to local."""
    value = value.strip()
    if params.get("VALUE") == "DATE" or re.fullmatch(r"\d{8}", value):
        return dt.date(int(value[:4]), int(value[4:6]), int(value[6:8])), True
    t = dt.datetime.strptime(value.rstrip("Z")[:15], "%Y%m%dT%H%M%S")
    if value.endswith("Z"):
        return t.replace(tzinfo=dt.timezone.utc).astimezone(L.LOCAL_TZ), False
    tz = L.LOCAL_TZ
    if params.get("TZID"):
        try:
            tz = zone(params["TZID"])
        except Exception:  # noqa: BLE001 - Windows zone names etc.
            L.warn(f"unknown TZID {params['TZID']!r}, using local time")
    return t.replace(tzinfo=tz), False


def parse_duration(v):
    m = re.fullmatch(r"([+-])?P(?:(\d+)W)?(?:(\d+)D)?(?:T(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?)?", v.strip())
    if not m:
        return None
    sign = -1 if m.group(1) == "-" else 1
    w, d, h, mi, s = (int(x or 0) for x in m.groups()[1:])
    return sign * dt.timedelta(weeks=w, days=d, hours=h, minutes=mi, seconds=s)
