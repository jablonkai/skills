"""Shared helpers for the apple-reminders scripts (Python 3.9+ stdlib only).

Reads and writes go through `ek`, a small EventKit helper compiled from ek.swift on
first use and cached under ~/Library/Caches/apple-reminders/. EventKit answers a query
over thousands of reminders in milliseconds. When the terminal/IDE has no Reminders
access, reads fall back to the Reminders JXA dictionary, which takes tens of seconds per
query. JXA is also the only way to read or set `flagged`, which EventKit doesn't expose.
Nothing listens on a port and no process outlives its call.
"""
import csv
import datetime as dt
import hashlib
import io
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
CACHE = Path.home() / "Library" / "Caches" / "apple-reminders"
DEFAULT_TIMEOUT = 120
PRIORITY = {"none": 0, "high": 1, "medium": 5, "low": 9}


def die(msg, code=1):
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(code)


def warn(msg):
    print(f"warning: {msg}", file=sys.stderr)


def now():
    return dt.datetime.now().astimezone()


def today():
    return dt.date.today()


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
    # Without swiftc the interpreter still runs ek.swift, but it can't raise the
    # permission prompt: access must already be granted.
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
    """'fullAccess', 'denied', 'restricted' or 'notDetermined'."""
    return ek("status")["status"]


def can_use_ek():
    if os.environ.get("APPLE_REMINDERS_FORCE_JXA"):  # test the fallback on a machine with access
        return False
    return access() in ("fullAccess", "notDetermined")  # notDetermined: ek asks on first use


def require_ek():
    if not can_use_ek():
        die("writing needs EventKit access to Reminders: turn it on for this terminal/IDE in "
            "System Settings > Privacy & Security > Reminders", 3)


# ---- JXA ------------------------------------------------------------------------

JXA_PRELUDE = r"""
function run(argv) {
  const R = Application("Reminders");
  const P = JSON.parse(argv[0]);
  const iso = d => d ? d.toISOString() : null;
  return JSON.stringify(main(R, P, iso));
}
"""

JXA_SCRIPTS = {
    "lists": r"""
function main(R, P, iso) {
  const def = R.defaultList.id();
  return R.lists().map(l => ({id: l.id(), title: l.name(), source: l.container().name(),
                              writable: true, default: l.id() === def}));
}
""",
    # One list per call: a `whose` over the whole app scans every reminder of every account.
    "reminders": r"""
function main(R, P, iso) {
  const l = R.lists.byId(P.listId);
  const q = P.kind === "open" ? l.reminders.whose({completed: false})
          : P.kind === "completed" ? l.reminders.whose({completed: true}) : l.reminders;
  const ids = q.id(), n = q.name(), body = q.body(), due = q.dueDate(), ad = q.alldayDueDate(),
        pr = q.priority(), c = q.completed(), cd = q.completionDate(), fl = q.flagged();
  return ids.map((id, i) => ({id: id, title: n[i], notes: body[i] || "", due: iso(due[i]),
    allDayDue: iso(ad[i]), priority: pr[i], completed: c[i], completionDate: iso(cd[i]),
    flagged: fl[i]}));
}
""",
    "flagged": r"""
function main(R, P, iso) {
  const l = R.lists.byId(P.listId);
  const q = l.reminders.whose({completed: false});
  const ids = q.id(), fl = q.flagged();
  const out = {};
  ids.forEach((id, i) => { out[id.replace("x-apple-reminder://", "")] = fl[i]; });
  return out;
}
""",
    "setflag": r"""
function main(R, P, iso) {
  const l = R.lists.byId(P.listId);
  return P.ids.map(id => {
    const r = l.reminders.byId("x-apple-reminder://" + id);
    r.flagged = P.flagged;
    return {id: id, flagged: r.flagged()};
  });
}
""",
}


def jxa(name, payload=None, timeout=600):
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as fh:
        fh.write(JXA_PRELUDE + JXA_SCRIPTS[name])
        script = fh.name
    try:
        res = subprocess.run(["osascript", "-l", "JavaScript", script, json.dumps(payload or {})],
                             capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        die(f"Reminders did not answer within {timeout}s", 124)
    finally:
        os.unlink(script)
    if res.returncode != 0:
        if "-1743" in res.stderr:
            die("Automation permission denied: allow this terminal/IDE to control Reminders in "
                "System Settings > Privacy & Security > Automation", 3)
        if "-609" in res.stderr or "-600" in res.stderr:
            subprocess.run(["open", "-g", "-a", "Reminders"], check=False)
            die("Reminders wasn't running (launched it now): retry", 1)
        die(f"Reminders scripting failed: {res.stderr.strip()[-600:]}")
    return json.loads(res.stdout)


def _jxa_reminder(r, lst):
    """Normalise a JXA row to the ek shape. All-day items have due == allDayDue (midnight)."""
    out = {"id": r["id"].replace("x-apple-reminder://", ""), "title": r["title"],
           "list": lst["title"], "listId": lst["id"], "source": lst["source"],
           "completed": r["completed"], "priority": r["priority"],
           "notes": r["notes"], "url": "", "alarms": [], "repeat": "", "flagged": r["flagged"],
           "completionDate": _local_iso(r["completionDate"]), "due": None, "allDay": False}
    if r["due"]:
        due = _from_iso(r["due"])
        if r["allDayDue"] == r["due"]:
            out["due"], out["allDay"] = due.date().isoformat(), True
        else:
            out["due"] = due.isoformat(timespec="seconds")
    return out


def _from_iso(s):
    return dt.datetime.fromisoformat(s.replace("Z", "+00:00")).astimezone()


def _local_iso(s):
    return _from_iso(s).isoformat(timespec="seconds") if s else None


# ---- lists ----------------------------------------------------------------------

def lists():
    """[{id, title, source, writable, default}]; JXA fallback when EventKit can't be used."""
    if can_use_ek():
        out = ek("lists", check=False)
        if out is not None:
            return out
    return jxa("lists")


def label(lst):
    return f"{lst['source']}/{lst['title']}"


def resolve_lists(names, all_lists=None, writable=False):
    """Lists by title, 'Account/Title' or id (case-insensitive). Ambiguous names fail.
    Emoji prefixes are optional: 'Számlák' finds '🧾 Számlák'."""
    all_lists = all_lists if all_lists is not None else lists()
    out = []
    for name in names:
        want = name.strip().casefold()
        hits = [x for x in all_lists if x["id"].casefold() == want or label(x).casefold() == want]
        hits = hits or [x for x in all_lists if x["title"].casefold() == want]
        hits = hits or [x for x in all_lists if _bare(x["title"]) == _bare(name)]
        if not hits:
            die(f"no reminder list named {name!r}. Known: "
                + ", ".join(sorted(label(x) for x in all_lists)), 2)
        if len(hits) > 1:
            die(f"{name!r} is ambiguous, use one of: " + ", ".join(label(x) for x in hits), 2)
        if writable and not hits[0]["writable"]:
            die(f"list {label(hits[0])!r} is read-only", 2)
        out.append(hits[0])
    return out


def _bare(title):
    """Title without leading emoji/symbols, casefolded."""
    return re.sub(r"^[^\w]+", "", title, flags=re.UNICODE).strip().casefold()


def default_list(all_lists=None):
    all_lists = all_lists if all_lists is not None else lists()
    for x in all_lists:
        if x.get("default"):
            return x
    return all_lists[0] if all_lists else None


# ---- reminders ------------------------------------------------------------------

def reminders(kind="open", list_objs=None, completed_from=None, completed_to=None):
    """Reminders as dicts. kind: open | completed | all. list_objs None = every list."""
    if can_use_ek():
        ids = [x["id"] for x in list_objs] if list_objs else []
        if kind == "completed":
            args = ["query", "completed", completed_from or "-", completed_to or "-", *ids]
        else:
            args = ["query", kind, *ids]
        return ek(*args, timeout=300)
    warn("no EventKit access to Reminders: reading through AppleScript, which takes "
         "tens of seconds per list")
    out = []
    for lst in list_objs or lists():
        rows = jxa("reminders", {"listId": lst["id"], "kind": kind})
        out += [_jxa_reminder(r, lst) for r in rows]
    if kind == "completed" and (completed_from or completed_to):
        lo = _from_iso(completed_from) if completed_from else None
        hi = _from_iso(completed_to) if completed_to else None
        out = [r for r in out if r["completionDate"]
               and (lo is None or _from_iso(r["completionDate"]) >= lo)
               and (hi is None or _from_iso(r["completionDate"]) < hi)]
    return out


def get(ids, missing_ok=False):
    """Reminders by id; dies on an unknown id unless missing_ok."""
    out = ek("get", *ids)
    if not missing_ok and len(out) < len(ids):
        found = {r["id"] for r in out}
        die("no reminder with id " + ", ".join(i for i in ids if i.replace("x-apple-reminder://", "") not in found), 2)
    return out


def day_start(s):
    """Local midnight at the start of a user date, as ISO with offset."""
    kind, v = parse_when(s)
    d = dt.date.fromisoformat(v) if kind == "date" else v.date()
    return dt.datetime.combine(d, dt.time()).astimezone().isoformat(timespec="seconds")


def add_flagged(rems):
    """Fill r['flagged'] through JXA, one call per list (EventKit has no flag)."""
    by_list = {}
    for r in rems:
        if "flagged" not in r:
            by_list.setdefault(r["listId"], []).append(r)
    for list_id, group in by_list.items():
        flags = jxa("flagged", {"listId": list_id})
        for r in group:
            r["flagged"] = flags.get(r["id"], False)
    return rems


def set_flagged(rems, flagged):
    by_list = {}
    for r in rems:
        by_list.setdefault(r["listId"], []).append(r["id"])
    out = []
    for list_id, ids in by_list.items():
        out += jxa("setflag", {"listId": list_id, "ids": ids, "flagged": flagged})
    return out


# ---- dates ----------------------------------------------------------------------

WEEKDAYS = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
_TIME = r"(\d{1,2})[:.](\d{2})"


def parse_when(s):
    """A user date to ('date', 'YYYY-MM-DD') or ('time', aware datetime).

    Accepts 2026-10-20, 2026-10-20 14:30, 2026-10-20T14:30, ISO with offset, today,
    tomorrow, yesterday, weekday names (the next one, never today), +3d / -2w, each
    optionally followed by a time ('tomorrow 9:00', 'fri 14:30').
    """
    s = s.strip()
    try:
        d = dt.datetime.fromisoformat(s)
        if "T" in s or " " in s:
            return "time", (d if d.tzinfo else d.astimezone()).astimezone()
        return "date", d.date().isoformat()
    except ValueError:
        pass
    m = re.fullmatch(r"(.+?)(?:\s+(?:at\s+)?" + _TIME + r")?", s, re.I)
    word, hh, mm = m.group(1).strip().casefold(), m.group(2), m.group(3)
    base = None
    if word == "today":
        base = today()
    elif word == "tomorrow":
        base = today() + dt.timedelta(days=1)
    elif word == "yesterday":
        base = today() - dt.timedelta(days=1)
    elif re.fullmatch(r"[+-]\d+[dw]", word):
        n = int(word[:-1])
        base = today() + dt.timedelta(days=n * (7 if word.endswith("w") else 1))
    elif word[:3] in WEEKDAYS and word.isalpha():
        ahead = (WEEKDAYS.index(word[:3]) - today().weekday()) % 7 or 7
        base = today() + dt.timedelta(days=ahead)
    else:
        try:
            base = dt.date.fromisoformat(word)
        except ValueError:
            die(f"can't read the date {s!r} (want 2026-10-20, '2026-10-20 14:30', today, "
                "tomorrow, fri, +3d, -7d, optionally with a time)", 2)
    if hh is None:
        return "date", base.isoformat()
    return "time", dt.datetime.combine(base, dt.time(int(hh), int(mm))).astimezone()


def when_to_due(s):
    """parse_when result as the string ek save expects."""
    kind, v = parse_when(s)
    return v if kind == "date" else v.isoformat(timespec="seconds")


def due_key(r):
    """Sortable local datetime for a reminder's due date (all-day = start of that day)."""
    if not r.get("due"):
        return None
    if r.get("allDay"):
        return dt.datetime.combine(dt.date.fromisoformat(r["due"]), dt.time()).astimezone()
    return _from_iso(r["due"])


def state(r, at=None):
    """completed | overdue | today | upcoming | undated (the Reminders app's own split:
    an all-day reminder due today is not overdue until tomorrow)."""
    if r["completed"]:
        return "completed"
    if not r.get("due"):
        return "undated"
    at = at or now()
    if r.get("allDay"):
        day = dt.date.fromisoformat(r["due"])
        return "overdue" if day < at.date() else "today" if day == at.date() else "upcoming"
    due = _from_iso(r["due"])
    if due < at:
        return "overdue"
    return "today" if due.date() == at.date() else "upcoming"


def fmt_due(r):
    if not r.get("due"):
        return ""
    if r.get("allDay"):
        return r["due"]
    return _from_iso(r["due"]).strftime("%Y-%m-%d %H:%M")


def same_due(a, b):
    """True when two reminder dicts (or a dict and a parsed spec) have the same due."""
    if not a.get("due") or not b.get("due"):
        return not a.get("due") and not b.get("due")
    if bool(a.get("allDay")) != bool(b.get("allDay")):
        return False
    if a.get("allDay"):
        return a["due"] == b["due"]
    return _from_iso(a["due"]) == _from_iso(b["due"])


def priority_band(p):
    """EventKit stores 0 (none) or 1-9: 1-4 high, 5 medium, 6-9 low (Exchange uses 3 for high)."""
    return 0 if not p else 1 if p < 5 else 5 if p == 5 else 9


def priority_name(p):
    return {0: "none", 1: "high", 5: "medium", 9: "low"}[priority_band(p)]


# ---- selection and output ----------------------------------------------------------

def matcher(text, regex=False, in_notes=False):
    if regex:
        pat = re.compile(text, re.I)
        hit = pat.search
    else:
        needle = text.casefold()
        hit = lambda s: needle in s.casefold()  # noqa: E731
    return lambda r: bool(hit(r["title"]) or (in_notes and hit(r.get("notes") or "")))


def by_list(rems):
    groups = {}
    for r in rems:
        groups.setdefault((r["source"], r["list"]), []).append(r)
    return groups


def sort_key(r):
    k = due_key(r)
    return (k is None, k or now(), r["title"].casefold())


def render(rems, fmt="table", show_state=True):
    if fmt == "json":
        return json.dumps(rems, ensure_ascii=False, indent=2)
    if fmt == "csv":
        buf = io.StringIO()
        cols = ["list", "title", "due", "allDay", "state", "priorityName", "completed",
                "completionDate", "notes", "id"]
        w = csv.DictWriter(buf, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for r in rems:
            w.writerow({**r, "state": state(r), "priorityName": priority_name(r["priority"]), "notes": (r.get("notes") or "").replace("\n", " ")})
        return buf.getvalue()
    if not rems:
        return "(no reminders)\n"
    lines = []
    at = now()
    for (source, title), group in sorted(by_list(rems).items(), key=lambda kv: _bare(kv[0][1])):
        lines.append(f"## {title} ({source}) — {len(group)}")
        lines.append("")
        lines.append("| | Due | Title | Priority |" + (" State |" if show_state else ""))
        lines.append("|---|---|---|---|" + ("---|" if show_state else ""))
        for r in sorted(group, key=sort_key):
            st = state(r, at)
            box = "☑" if r["completed"] else "☐"
            flag = " ⚑" if r.get("flagged") else ""
            prio = priority_name(r["priority"])
            prio = "" if prio == "none" else prio
            title_cell = r["title"].replace("|", "\\|") + flag
            row = f"| {box} | {fmt_due(r)} | {title_cell} | {prio} |"
            if show_state:
                row += f" {_state_text(r, st, at)} |"
            lines.append(row)
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _state_text(r, st, at):
    if st == "overdue":
        days = (at.date() - due_key(r).date()).days
        return "overdue" + (f" {days}d" if days else "")
    return st


def add_list_args(p):
    p.add_argument("--list", action="append", default=[], metavar="NAME",
                   help="list title, Account/Title or id (repeatable; default: all lists)")
    p.add_argument("--exclude-list", action="append", default=[], metavar="NAME")


def lists_from_args(a, all_lists=None):
    all_lists = all_lists if all_lists is not None else lists()
    chosen = resolve_lists(a.list, all_lists) if a.list else list(all_lists)
    if a.exclude_list:
        drop = {x["id"] for x in resolve_lists(a.exclude_list, all_lists)}
        chosen = [x for x in chosen if x["id"] not in drop]
    return chosen


# ---- checklists -----------------------------------------------------------------

_ITEM = re.compile(r"^(?P<indent>[ \t]*)(?:[-*+]|\d+[.)])\s+(?:\[(?P<box>[ xX])\]\s*)?(?P<text>.*\S)\s*$")
_HEADING = re.compile(r"^#{1,6}\s+(?P<text>.+?)\s*#*\s*$")
_DATE = r"\d{4}-\d{2}-\d{2}(?:[ T]\d{1,2}[:.]\d{2})?"
_WORD_DATE = r"(?:today|tomorrow|(?:mon|tue|wed|thu|fri|sat|sun)[a-z]*|[+-]\d+[dw]|" + _DATE + r")(?:\s+" + _TIME + r")?"
# Explicit due markers, in the order they're tried. Each captures the date text.
_DUE_MARKERS = [
    re.compile(r"\(\s*(?:due|by|határidő)[:\s]\s*(" + _WORD_DATE + r")\s*\)", re.I),
    re.compile(r"\b(?:due|by|határidő):\s*(" + _WORD_DATE + r")", re.I),
    re.compile(r"(?:\s[-–—,]|^|\s)\s*(?:due|by|határidő)\s+(" + _DATE + r")(?=\s|$|[,.;)])", re.I),
    re.compile(r"(?:\s[-–—,]|^|\s)\s*due\s+(" + _WORD_DATE + r")(?=\s|$|[,.;)])", re.I),
    re.compile(r"@due\((" + _WORD_DATE + r")\)", re.I),        # TaskPaper
    re.compile(r"📅\s*(" + _DATE + r")"),                     # Obsidian Tasks
]
_BARE_DATE = re.compile(r"(?:^|\s)(?:[-–—]\s*)?(" + _DATE + r")\s*$")
_PRIORITY = [
    (re.compile(r"(?:^|\s)(?:!high|!!!|⏫|🔺)(?=\s|$)", re.I), "high"),
    (re.compile(r"(?:^|\s)(?:!medium|!med|!!|🔼)(?=\s|$)", re.I), "medium"),
    (re.compile(r"(?:^|\s)(?:!low|!|🔽|⏬)(?=\s|$)", re.I), "low"),
]
_DONE_MARK = re.compile(r"\s*✅\s*" + _DATE)                  # Obsidian Tasks completion stamp


def parse_checklist(text, bare_dates=True):
    """Markdown/plain checklist -> [{title, due, allDay, completed, priority, notes, heading, depth}].

    Items are `- [ ] text`, `- [x] text`, `- text`, `* text`, `1. text`. Due dates come from
    `(due 2026-10-20 14:00)`, `due: fri`, `@due(2026-10-20)`, `📅 2026-10-20` or, with
    bare_dates, a date at the end of the line. Priority from `!high/!medium/!low`, `!!!/!!/!`
    or the Obsidian Tasks emoji. Indented non-item lines become notes of the item above.
    Nested items are kept flat (Reminders subtasks aren't scriptable) with depth > 0.
    """
    items, heading, stack = [], None, []
    for raw in text.splitlines():
        if not raw.strip():
            continue
        h = _HEADING.match(raw)
        if h:
            heading = h.group("text").strip()
            continue
        m = _ITEM.match(raw)
        if not m:
            if items and raw[:1] in (" ", "\t"):
                items[-1]["notes"] = (items[-1]["notes"] + "\n" + raw.strip()).strip()
            continue
        indent = len(m.group("indent").expandtabs(4))
        while stack and stack[-1][0] >= indent:
            stack.pop()
        item = _parse_item(m.group("text"), bare_dates)
        item["completed"] = (m.group("box") or " ").lower() == "x"
        item["heading"] = heading
        item["depth"] = len(stack)
        item["parent"] = stack[-1][1]["title"] if stack else None
        stack.append((indent, item))
        items.append(item)
    return items


def _parse_item(text, bare_dates):
    due = None
    text = _DONE_MARK.sub("", text)
    for pat in _DUE_MARKERS:
        m = pat.search(text)
        if m:
            due = m.group(1)
            text = (text[:m.start()] + text[m.end():])
            break
    if due is None and bare_dates:
        m = _BARE_DATE.search(text)
        if m:
            due = m.group(1)
            text = text[:m.start()]
    priority = "none"
    for pat, name in _PRIORITY:
        m = pat.search(text)
        if m:
            priority = name
            text = text[:m.start()] + text[m.end():]
            break
    title = re.sub(r"\s{2,}", " ", text).strip(" \t-–—,;")
    out = {"title": title, "due": None, "allDay": False, "priority": PRIORITY[priority], "notes": ""}
    if due:
        kind, v = parse_when(due.replace(".", ":") if re.search(r"\d\.\d{2}$", due) else due)
        if kind == "date":
            out["due"], out["allDay"] = v, True
        else:
            out["due"] = v.isoformat(timespec="seconds")
    return out
