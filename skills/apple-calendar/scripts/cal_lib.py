"""Shared helpers for the apple-calendar scripts (Python 3.9+ stdlib only).

Reads and writes go through `ek`, a small EventKit helper compiled from ek.swift on
first use and cached under ~/Library/Caches/apple-calendar/. EventKit expands recurring
events into occurrences and answers in well under a second. When the terminal/IDE has
no Full Access to Calendars, reads fall back to Calendar's JXA dictionary, which is far
slower and returns only series masters, so recurrences are expanded here (RRULE subset).
Nothing listens on a port and no process outlives its call.
"""
import calendar as _cal
import datetime as dt
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
EK_SRC = HERE / "ek.swift"
CACHE = Path.home() / "Library" / "Caches" / "apple-calendar"
DEFAULT_TIMEOUT = 120


def _local_tz():
    """The IANA zone (DST-aware) behind /etc/localtime; a fixed offset only as a last resort."""
    try:
        from zoneinfo import ZoneInfo
        name = os.environ.get("TZ") or os.path.realpath("/etc/localtime").split("zoneinfo/", 1)[1]
        return ZoneInfo(name)
    except Exception:  # noqa: BLE001 - any failure means "use the fixed offset"
        return dt.datetime.now().astimezone().tzinfo


LOCAL_TZ = _local_tz()


def die(msg, code=1):
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(code)


def warn(msg):
    print(f"warning: {msg}", file=sys.stderr)


# ---- the EventKit helper ------------------------------------------------------

def ek_binary():
    """Path to the compiled helper, building it when ek.swift changed. None if no swiftc."""
    digest = hashlib.sha256(EK_SRC.read_bytes()).hexdigest()[:12]
    exe = CACHE / f"ek-{digest}"
    if exe.exists():
        return exe
    if not shutil.which("swiftc"):
        return None
    CACHE.mkdir(parents=True, exist_ok=True)
    tmp = CACHE / f".ek-{digest}.{os.getpid()}"
    res = subprocess.run(["swiftc", "-O", str(EK_SRC), "-o", str(tmp)],
                         capture_output=True, text=True, timeout=600)
    if res.returncode != 0:
        die("compiling ek.swift failed (install the Xcode Command Line Tools: "
            f"xcode-select --install):\n{res.stderr[-1500:]}")
    tmp.replace(exe)
    for old in CACHE.glob("ek-*"):
        if old != exe:
            old.unlink(missing_ok=True)
    return exe


def ek(*args, spec=None, timeout=DEFAULT_TIMEOUT, check=True):
    """Run `ek <args>` (JSON spec on stdin for `save`) and return the parsed JSON output."""
    exe = ek_binary()
    cmd = [str(exe), *args] if exe else ["swift", str(EK_SRC), *args]
    try:
        res = subprocess.run(cmd, input=json.dumps(spec) if spec is not None else "",
                             capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        die(f"EventKit helper timed out after {timeout}s (a privacy prompt may be waiting "
            "on screen: answer it and retry)", 124)
    if res.returncode != 0:
        if not check:
            return None
        die(res.stderr.strip().removeprefix("error: ") or f"ek {args[0]} failed",
            res.returncode if res.returncode in (2, 3) else 1)
    return json.loads(res.stdout) if res.stdout.strip() else None


def access():
    """'fullAccess', 'writeOnly', 'denied', 'restricted' or 'notDetermined'."""
    return ek("status")["status"]


def can_read():
    if os.environ.get("APPLE_CALENDAR_FORCE_JXA"):  # test the fallback on a machine with access
        return False
    st = access()
    return st in ("fullAccess", "notDetermined")  # notDetermined: ek asks on first read


# ---- calendars ----------------------------------------------------------------

def calendars():
    """[{id, title, source, type, writable, default}]; JXA fallback when EventKit can't read."""
    if can_read():
        cals = ek("calendars", check=False)
        if cals is not None:
            return cals
    return jxa("calendars")


def label(cal):
    return f"{cal['source']}/{cal['title']}" if cal.get("source") else cal["title"]


def resolve_calendars(names, cals=None, writable=False):
    """Calendars by title, 'Source/Title' or id (case-insensitive). Ambiguous names fail."""
    cals = cals if cals is not None else calendars()
    out = []
    for name in names:
        want = name.strip().lower()
        hits = [c for c in cals if c["id"].lower() == want or label(c).lower() == want]
        if not hits:
            hits = [c for c in cals if c["title"].lower() == want]
        if not hits:
            die(f"no calendar named {name!r}. Known: " + ", ".join(sorted(label(c) for c in cals)), 2)
        if len(hits) > 1:
            die(f"{name!r} is ambiguous, use one of: " + ", ".join(label(c) for c in hits), 2)
        if writable and not hits[0]["writable"]:
            die(f"calendar {label(hits[0])!r} is read-only (subscribed, holidays or birthdays)", 2)
        out.append(hits[0])
    return out


def default_calendar(cals=None):
    cals = cals if cals is not None else calendars()
    for c in cals:
        if c.get("default"):
            return c
    die("no default calendar for new events; pass --calendar", 2)


# ---- dates --------------------------------------------------------------------

def now():
    return dt.datetime.now(LOCAL_TZ).replace(microsecond=0)


def start_of_day(d):
    return dt.datetime(d.year, d.month, d.day, tzinfo=LOCAL_TZ)


def parse_when(s, end_of_day=False):
    """Local datetime from 'today', 'tomorrow', '2026-10-20', '2026-10-20 14:30',
    '2026-10-20T14:30', or full ISO with an offset. A bare date means 00:00 (or the next
    midnight with end_of_day, so '--to 2026-10-25' includes the 25th)."""
    t = s.strip().lower()
    today = now().date()
    rel = {"today": today, "tomorrow": today + dt.timedelta(days=1),
           "yesterday": today - dt.timedelta(days=1)}
    if t in rel or re.fullmatch(r"\d{4}-\d{2}-\d{2}", t):
        d = rel.get(t) or dt.date.fromisoformat(t)
        return start_of_day(d + dt.timedelta(days=1 if end_of_day else 0))
    try:
        v = dt.datetime.fromisoformat(s.strip().replace("Z", "+00:00").replace(" ", "T", 1))
    except ValueError:
        die(f"can't read the date {s!r} (use 2026-10-20, 2026-10-20 14:30, today, tomorrow)", 2)
    return v.replace(tzinfo=LOCAL_TZ) if v.tzinfo is None else v.astimezone(LOCAL_TZ)


def iso(d):
    return d.isoformat(timespec="seconds")


def week_range(which):
    """Monday-to-Monday range: 'this', 'next', 'last' or any date inside the week."""
    base = now().date()
    if which in ("this", "next", "last"):
        base += dt.timedelta(weeks={"this": 0, "next": 1, "last": -1}[which])
    else:
        base = parse_when(which).date()
    mon = base - dt.timedelta(days=base.weekday())
    return start_of_day(mon), start_of_day(mon + dt.timedelta(days=7))


def month_range(which):
    """'this', 'next', 'last' or YYYY-MM."""
    today = now().date()
    if which in ("this", "next", "last"):
        m = today.year * 12 + today.month - 1 + {"this": 0, "next": 1, "last": -1}[which]
        y, mo = divmod(m, 12)
        mo += 1
    else:
        mt = re.fullmatch(r"(\d{4})-(\d{1,2})", which)
        if not mt:
            die(f"--month wants YYYY-MM, this, next or last, not {which!r}", 2)
        y, mo = int(mt.group(1)), int(mt.group(2))
    first = dt.date(y, mo, 1)
    nxt = dt.date(y + (mo == 12), mo % 12 + 1, 1)
    return start_of_day(first), start_of_day(nxt)


def add_range_args(p):
    g = p.add_argument_group("period (default: today plus the next 7 days)")
    g.add_argument("--from", dest="start", help="start date/time (inclusive)")
    g.add_argument("--to", dest="end", help="end date/time (a bare date includes that day)")
    g.add_argument("--week", help="this | next | last | a date inside the week (Monday start)")
    g.add_argument("--month", help="this | next | last | YYYY-MM")
    g.add_argument("--days", type=int, help="N days starting at --from (default today)")


def range_from_args(a):
    if a.week:
        return week_range(a.week)
    if a.month:
        return month_range(a.month)
    start = parse_when(a.start) if a.start else start_of_day(now().date())
    if a.end:
        end = parse_when(a.end, end_of_day=True)
    else:
        end = start + dt.timedelta(days=a.days or 7) if (a.days or not a.start) else \
            start_of_day(start.date()) + dt.timedelta(days=1)
    if end <= start:
        die("the period ends before it starts", 2)
    return start, end


# ---- reading events -------------------------------------------------------------

def events(start, end, cal_names=None, cals=None):
    """Occurrences overlapping [start, end), sorted by start. Each is a dict with id,
    title, start, end (ISO), allDay, calendar, source, rrule, alarms, location, notes …"""
    cals = cals if cals is not None else calendars()
    chosen = resolve_calendars(cal_names, cals) if cal_names else []
    if can_read():
        out = ek("range", iso(start), iso(end), *[c["id"] for c in chosen], check=False)
        if out is not None:
            return out
    warn("EventKit has no read access, using the slow AppleScript path "
         "(turn on Full Access in System Settings > Privacy & Security > Calendars)")
    return jxa_events(start, end, chosen or [c for c in cals])


def get_event(event_id, occurrence=None):
    return ek("get", event_id, *([iso(parse_when(occurrence))] if occurrence else []))


def ev_start(e):
    return parse_when(e["start"])


def ev_end(e):
    return parse_when(e["end"])


def series_key(e, field="id"):
    """A moved (detached) occurrence carries its series' id plus '/RID=<n>'; strip it."""
    return (e.get(field) or e["id"]).split("/RID=")[0]


def ev_last_day(e):
    """Last calendar day an all-day event covers. EventKit ends it at 23:59:59 that day;
    AppleScript (and .ics) end it at the next midnight."""
    t = ev_end(e)
    return (t - dt.timedelta(days=1)).date() if t.time() == dt.time(0) else t.date()


# ---- JXA fallback -------------------------------------------------------------

JXA_LIB = r"""
function fmt(d){ if(!d) return null; const p=n=>String(n).padStart(2,'0');
  const o=-d.getTimezoneOffset(), s=o>=0?'+':'-', a=Math.abs(o);
  return d.getFullYear()+'-'+p(d.getMonth()+1)+'-'+p(d.getDate())+'T'+p(d.getHours())+':'+
    p(d.getMinutes())+':'+p(d.getSeconds())+s+p(Math.floor(a/60))+':'+p(a%60); }
"""

# Calendar 27's dictionary can't return `calendarIdentifier` (a type-conversion error), so
# the fallback addresses calendars by index ("jxa:<n>"), stable within one session.
JXA_SCRIPTS = {
    "calendars": JXA_LIB + r"""
function run(argv){ const C=Application('Calendar'); const cs=C.calendars;
  const names=cs.name(), w=cs.writable();
  return JSON.stringify(names.map((n,i)=>({id:'jxa:'+i, title:n, source:'', type:'unknown',
    writable:w[i], default:false}))); }
""",
    "events": JXA_LIB + r"""
function run(argv){ const a=JSON.parse(argv[0]); const C=Application('Calendar');
  const from=new Date(a.from), to=new Date(a.to); const out=[];
  for (const cid of a.ids){ const c=C.calendars[Number(cid.split(':')[1])];
    const cname=c.name();
    const groups=[c.events.whose({_and:[{startDate:{_lessThan:to}},{endDate:{_greaterThan:from}}]}),
                  c.events.whose({_and:[{startDate:{_lessThan:to}},{recurrence:{_contains:'FREQ'}}]})];
    for (const g of groups){ const n=g.uid().length; if(!n) continue;
      const uid=g.uid(), sum=g.summary(), sd=g.startDate(), ed=g.endDate(), ad=g.alldayEvent(),
            rec=g.recurrence(), loc=g.location(), ex=g.excludedDates();
      for (let i=0;i<n;i++) out.push({id:uid[i], externalId:uid[i], title:sum[i]||'', start:fmt(sd[i]),
        end:fmt(ed[i]), allDay:ad[i], calendar:cname, calendarId:cid, source:'',
        rrule: rec[i]? [rec[i]]: [], excluded:(ex[i]||[]).map(fmt), location:loc[i]||undefined,
        alarms:[], recurring: !!rec[i], detached:false, availability:'busy'}); } }
  return JSON.stringify(out); }
""",
}


def jxa(name, payload=None, timeout=600):
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as fh:
        fh.write(JXA_SCRIPTS[name])
        script = fh.name
    try:
        res = subprocess.run(["osascript", "-l", "JavaScript", script, json.dumps(payload or {})],
                             capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        die(f"Calendar did not answer within {timeout}s (a dialog may be open in Calendar)", 124)
    finally:
        os.unlink(script)
    if res.returncode != 0:
        if "-1743" in res.stderr:
            die("Automation permission denied: allow this terminal/IDE to control Calendar in "
                "System Settings > Privacy & Security > Automation", 3)
        die(f"Calendar scripting failed: {res.stderr.strip()[-600:]}")
    return json.loads(res.stdout)


def jxa_events(start, end, cals):
    raw = jxa("events", {"from": iso(start), "to": iso(end), "ids": [c["id"] for c in cals]})
    seen, out, masters = set(), [], {}
    for e in raw:
        key = (e["id"], e["start"])
        if key not in seen:
            seen.add(key)
            if e["rrule"] and (e["id"] not in masters or e["start"] < masters[e["id"]]["start"]):
                masters[e["id"]] = e
    for e in sorted({(x["id"], x["start"]): x for x in raw}.values(), key=lambda x: x["start"]):
        if e["rrule"] and masters[e["id"]]["start"] == e["start"]:
            out.extend(expand(e, start, end))
            continue
        # A moved occurrence comes back as a copy of its series with the same uid and
        # RRULE; AppleScript doesn't say which slot it replaced, so it is listed once.
        if e["rrule"]:
            e = dict(e, detached=True, recurring=False, rrule=[])
        if parse_when(e["start"]) < end and parse_when(e["end"]) > start:
            out.append(e)
    return sorted(out, key=lambda e: (e["start"], e["title"]))


WEEKDAYS = ["MO", "TU", "WE", "TH", "FR", "SA", "SU"]


def parse_rrule(s):
    return dict(p.split("=", 1) for p in s.replace("RRULE:", "").upper().split(";") if "=" in p)


def rrule_until(v):
    if len(v) == 8:
        return start_of_day(dt.date(int(v[:4]), int(v[4:6]), int(v[6:]))) + dt.timedelta(days=1)
    t = dt.datetime.strptime(v.rstrip("Z"), "%Y%m%dT%H%M%S")
    return t.replace(tzinfo=dt.timezone.utc if v.endswith("Z") else LOCAL_TZ)


def expand(master, start, end, limit=5000):
    """Occurrences of a series master that overlap [start, end). Supports FREQ, INTERVAL,
    COUNT, UNTIL, BYDAY (weekly; or nth weekday for monthly), BYMONTHDAY and excluded dates."""
    r = parse_rrule(master["rrule"][0])
    freq, step = r.get("FREQ", "DAILY"), int(r.get("INTERVAL", "1"))
    count = int(r["COUNT"]) if "COUNT" in r else None
    until = rrule_until(r["UNTIL"]) if "UNTIL" in r else None
    s0, e0 = parse_when(master["start"]), parse_when(master["end"])
    dur = e0 - s0
    excluded = {x[:16] for x in master.get("excluded") or []}
    byday = [d for d in r.get("BYDAY", "").split(",") if d]

    def candidates():
        if freq == "WEEKLY":
            days = sorted(WEEKDAYS.index(d[-2:]) for d in byday) or [s0.weekday()]
            mon = s0 - dt.timedelta(days=s0.weekday())
            k = 0
            while True:
                for wd in days:
                    yield mon + dt.timedelta(weeks=k * step, days=wd)
                k += 1
        elif freq == "DAILY":
            k = 0
            while True:
                yield s0 + dt.timedelta(days=k * step)
                k += 1
        elif freq in ("MONTHLY", "YEARLY"):
            k = 0
            while True:
                months = k * step * (12 if freq == "YEARLY" else 1)
                y, m = divmod(s0.year * 12 + s0.month - 1 + months, 12)
                m += 1
                last = _cal.monthrange(y, m)[1]
                if byday and freq == "MONTHLY":
                    for tok in byday:
                        n, wd = int(tok[:-2] or 1), WEEKDAYS.index(tok[-2:])
                        days = [d for d in range(1, last + 1) if dt.date(y, m, d).weekday() == wd]
                        if -len(days) <= n <= len(days) and n != 0:
                            yield s0.replace(year=y, month=m, day=days[n - 1 if n > 0 else n])
                else:
                    for md in [int(x) for x in r.get("BYMONTHDAY", str(s0.day)).split(",")]:
                        d = md if md > 0 else last + 1 + md
                        if 1 <= d <= last:
                            yield s0.replace(year=y, month=m, day=d)
                k += 1

    out, n = [], 0
    for i, c in enumerate(candidates()):
        if i > limit or (until and c > until) or (count is not None and n >= count) or c >= end:
            break
        if c < s0:
            continue
        n += 1
        if iso(c)[:16] in excluded or c + dur <= start:
            continue
        occ = dict(master, start=iso(c), end=iso(c + dur), occurrence=iso(c))
        occ.pop("excluded", None)
        out.append(occ)
    return out


# ---- output -------------------------------------------------------------------

def when_text(e):
    s, t = ev_start(e), ev_end(e)
    if e.get("allDay"):
        last = ev_last_day(e)
        return ("all day" if last <= s.date() else f"all day, to {last:%a %d %b}")
    if t.date() != s.date():
        return f"{s:%H:%M} – {t:%a %d %b %H:%M}"
    return f"{s:%H:%M}–{t:%H:%M}"


def md_cell(v):
    return str(v or "").replace("|", "\\|").replace("\n", " ")


def write_json(obj):
    json.dump(obj, sys.stdout, ensure_ascii=False, indent=2)
    print()
