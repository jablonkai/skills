"""Shared helpers for the apple-mail scripts (Python 3.9+ stdlib only).

Two read paths, one write path:

* JXA (`osascript -l JavaScript`): always available once Automation is allowed. Reads
  bulk property arrays per mailbox and filters in Python, because `whose` takes 20-40 s
  on a 15k-message inbox where a bulk fetch takes under one.
* Envelope Index (Mail's SQLite catalogue): milliseconds for any search, but only with
  Full Disk Access. Opened read-only; never written. Its message ROWID is the JXA `id`.
* Writes (move, flags, drafts) go through JXA only. Nothing here can send mail.

Messages are addressed as refs: "Account/mailbox/path#id", e.g. "Google/[Gmail]/All Mail#49674"
or "On My Mac/Skill-Eval#49681". Local mailboxes use the account name "On My Mac".
"""
import datetime as dt
import glob
import json
import os
import re
import sqlite3
import subprocess
import sys
import tempfile
import unicodedata
from pathlib import Path
from urllib.parse import unquote

JXA_DIR = Path(__file__).resolve().parent / "jxa"
DEFAULT_TIMEOUT = 300
LOCAL = "On My Mac"

# AppleScript error numbers; messages are localized, so match the number only.
ERRORS = {
    -1743: "Automation permission denied: allow this terminal/IDE to control Mail in "
           "System Settings > Privacy & Security > Automation, then retry.",
    -1712: "Mail did not answer in time (a modal dialog, a password prompt or a large "
           "mailbox still loading). Bring Mail to the front, dismiss any dialog, retry.",
    -600: "Mail is not running and could not be launched.",
    -1728: "Object not found (the message moved, or the mailbox/account no longer exists).",
    -1719: "Invalid index (the message is gone from that mailbox; search again).",
    -10000: "Mail refused the operation (for example deleting or renaming a special mailbox).",
}

# Mailboxes left out of searches unless --include-trash. Names are localized.
TRASH_JUNK = {"trash", "deleted items", "deleted messages", "kuka", "törölt elemek",
              "papierkorb", "corbeille", "papelera", "junk", "junk email", "junk e-mail",
              "spam", "bulk", "levélszemét", "werbung", "courrier indésirable"}
ARCHIVE_NAMES = ["archive", "archives", "archív", "archívum", "archiv", "archivio", "archivo"]


def die(msg, code=1):
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(code)


def warn(msg):
    print(f"warning: {msg}", file=sys.stderr)


def nfc(s):
    return unicodedata.normalize("NFC", s or "")


def fold(s):
    return "".join(c for c in unicodedata.normalize("NFKD", s or "").casefold()
                   if not unicodedata.combining(c))


def dump(obj):
    print(json.dumps(obj, ensure_ascii=False, indent=2))


# ---- JXA -----------------------------------------------------------------------

def jxa(name, payload=None, timeout=None):
    """Run jxa/<name>.js (with _common.js prepended) and return its parsed JSON result."""
    src = (JXA_DIR / "_common.js").read_text(encoding="utf-8") + "\n" + \
        (JXA_DIR / f"{name}.js").read_text(encoding="utf-8")
    tmp = tempfile.mkdtemp(prefix="apple-mail-")
    script, args = Path(tmp, f"{name}.js"), Path(tmp, "args.json")
    script.write_text(src, encoding="utf-8")
    args.write_text(json.dumps(payload or {}, ensure_ascii=False), encoding="utf-8")
    timeout = timeout or DEFAULT_TIMEOUT
    try:
        res = subprocess.run(["osascript", "-l", "JavaScript", str(script), str(args)],
                             capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        die(f"timed out after {timeout}s in {name}. " + ERRORS[-1712], 124)
    finally:
        script.unlink(missing_ok=True)
        args.unlink(missing_ok=True)
        os.rmdir(tmp)
    if res.returncode != 0:
        m = re.search(r"\((-?\d+)\)\s*$", res.stderr.strip())
        num = int(m.group(1)) if m else None
        hint = ERRORS.get(num, "")
        die(f"{name} failed{f' ({num})' if num else ''}: {hint or res.stderr.strip()[-800:]}",
            3 if num == -1743 else 1)
    out = res.stdout.strip()
    return json.loads(out) if out else None


_MAILBOXES = {}


def mailboxes(account=None, counts=False):
    """[{account, accountId, path, key, count?, unread?}] for every mailbox (cached per run)."""
    k = (account, counts)
    if k not in _MAILBOXES:
        _MAILBOXES[k] = jxa("mailboxes", {"account": account, "counts": counts})
    return _MAILBOXES[k]


def resolve_mailbox(spec, mbs=None):
    """A mailbox key from 'Account/Path', 'Path' or a bare unique name (case/accent-insensitive)."""
    mbs = mbs or mailboxes()
    want = fold(nfc(spec).strip("/"))
    for test in (lambda m: fold(m["key"]) == want,
                 lambda m: fold(m["path"]) == want,
                 lambda m: fold(m["path"].rsplit("/", 1)[-1]) == want):
        hits = [m for m in mbs if test(m)]
        if len(hits) == 1:
            return hits[0]
        if len(hits) > 1:
            die(f"mailbox {spec!r} is ambiguous: " + ", ".join(h["key"] for h in hits)
                + ". Pass 'Account/Path'.", 2)
    die(f"mailbox not found: {spec!r}. Run `mail.sh mailboxes` to list them.", 2)


def subtree(mb, mbs):
    return [m for m in mbs if m["key"] == mb["key"] or m["key"].startswith(mb["key"] + "/")]


def is_trash_or_junk(m):
    return fold(m["path"].rsplit("/", 1)[-1]) in {fold(x) for x in TRASH_JUNK}


def archive_mailbox(account, mbs=None):
    """The account's Archive mailbox (localized names), or None."""
    mbs = mbs or mailboxes()
    cands = [m for m in mbs if m["account"] == account
             and fold(m["path"].rsplit("/", 1)[-1]) in ARCHIVE_NAMES]
    cands.sort(key=lambda m: m["path"].count("/"))
    return cands[0] if cands else None


def split_ref(ref):
    key, _, mid = ref.rpartition("#")
    if not key or not mid.isdigit():
        die(f"bad message ref {ref!r}; expected 'Account/Mailbox#id' from search output", 2)
    return key, int(mid)


# ---- dates ---------------------------------------------------------------------

def parse_when(s):
    """'30d', '2w', '6m', '1y' (ago), 'today', 'yesterday', or an ISO date/datetime -> aware datetime."""
    s = s.strip().lower()
    now = dt.datetime.now().astimezone()
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    m = re.fullmatch(r"-?(\d+)\s*([dwmy])", s)
    if m:
        n, unit = int(m.group(1)), m.group(2)
        days = {"d": 1, "w": 7, "m": 30, "y": 365}[unit] * n
        return now - dt.timedelta(days=days)
    if s == "today":
        return today
    if s == "yesterday":
        return today - dt.timedelta(days=1)
    try:
        d = dt.datetime.fromisoformat(s)
    except ValueError:
        die(f"cannot parse date {s!r}; use 30d / 2w / 6m / 1y or YYYY-MM-DD[THH:MM]", 2)
    return d if d.tzinfo else d.astimezone()


def iso_local(ts):
    """Unix seconds or ISO string -> local ISO 8601 with offset, seconds precision."""
    if isinstance(ts, (int, float)):
        d = dt.datetime.fromtimestamp(ts).astimezone()
    else:
        d = dt.datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone()
    return d.isoformat(timespec="seconds")


# ---- Envelope Index ------------------------------------------------------------

def index_path():
    hits = sorted(glob.glob(os.path.expanduser("~/Library/Mail/V*/MailData/Envelope Index")),
                  key=lambda p: int(re.search(r"/V(\d+)/", p).group(1)))
    return hits[-1] if hits else None


def index_status():
    """('ok', path) | ('no-fda', None) | ('missing', None)."""
    try:
        os.listdir(os.path.expanduser("~/Library/Mail"))
    except PermissionError:
        return "no-fda", None
    except FileNotFoundError:
        return "missing", None
    p = index_path()
    if not p:
        return "missing", None
    try:
        con = sqlite3.connect(f"file:{p}?mode=ro", uri=True)
        con.execute("select count(*) from messages").fetchone()
        con.close()
    except sqlite3.Error:
        return "no-fda", None
    return "ok", p


def index_connect():
    st, p = index_status()
    if st != "ok":
        return None
    return sqlite3.connect(f"file:{p}?mode=ro", uri=True)


def url_to_key(url, acct_by_id, local_ids):
    """'imap://UUID/%5BGmail%5D/All%20Mail' -> 'Google/[Gmail]/All Mail' (None if unknown)."""
    m = re.match(r"^[a-z]+://([^/]+)/(.*)$", url or "")
    if not m:
        return None
    uid, path = m.group(1), nfc(unquote(m.group(2)))
    if uid in acct_by_id:
        return f"{acct_by_id[uid]}/{path}"
    if url.startswith("local://") or uid in local_ids:
        return f"{LOCAL}/{path}"
    return None


# ---- search --------------------------------------------------------------------

def add_filter_args(ap):
    """The selection flags shared by search, export and organize."""
    g = ap.add_argument_group("selection")
    g.add_argument("--from", dest="sender", action="append", default=[],
                   help="sender address or name contains (repeatable: any)")
    g.add_argument("--to", action="append", default=[], help="a To/Cc recipient contains (repeatable: any)")
    g.add_argument("--subject", action="append", default=[], help="subject contains (repeatable: all)")
    g.add_argument("--since", help="received on/after: 30d, 2w, 6m, 1y, today, YYYY-MM-DD")
    g.add_argument("--before", help="received before: same forms (e.g. 90d = older than 90 days)")
    g.add_argument("--mailbox", action="append", default=[],
                   help="'Account/Path' or a unique name; subfolders included (repeatable)")
    g.add_argument("--account", help="limit to one account (or 'On My Mac')")
    g.add_argument("--unread", action="store_true")
    g.add_argument("--flagged", action="store_true")
    g.add_argument("--has-attachment", action="store_true")
    g.add_argument("--newsletter", action="store_true",
                   help="only list mail (List-Unsubscribe / List-Id header)")
    g.add_argument("--not-newsletter", action="store_true")
    g.add_argument("--include-trash", action="store_true", help="also search Trash/Junk/Spam")
    g.add_argument("--engine", choices=["auto", "index", "jxa"], default="auto",
                   help="auto = Envelope Index when Full Disk Access allows, else JXA")
    g.add_argument("--limit", type=int, default=0, help="newest N after filtering (0 = all)")
    g.add_argument("--id", dest="refs", action="append", default=[],
                   help="explicit message ref(s) from search output, instead of filters")
    g.add_argument("--ids-from", help="JSON file from `search --json` (uses each item's ref)")
    ap.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT)


def has_filters(a):
    return any([a.sender, a.to, a.subject, a.since, a.before, a.mailbox, a.account, a.unread,
                a.flagged, a.has_attachment, a.newsletter, a.not_newsletter])


def scope(a, mbs):
    if a.mailbox:
        sel = []
        for spec in a.mailbox:
            sel += subtree(resolve_mailbox(spec, mbs), mbs)
    else:
        sel = [m for m in mbs if a.include_trash or not is_trash_or_junk(m)]
    if a.account:
        acc = LOCAL if fold(a.account) in (fold(LOCAL), "local") else a.account
        sel = [m for m in sel if fold(m["account"]) == fold(acc)]
        if not sel:
            die(f"no mailboxes in account {a.account!r}; known: "
                + ", ".join(sorted({m['account'] for m in mbs})), 2)
    seen, out = set(), []
    for m in sel:
        if m["key"] not in seen:
            seen.add(m["key"])
            out.append(m)
    return out


def _match_any(hay, needles):
    h = fold(hay)
    return any(fold(n) in h for n in needles)


def _search_index(con, a, keys, mbs):
    acct_by_id = {m["accountId"]: m["account"] for m in mbs if m["accountId"]}
    rows = con.execute("select ROWID, url from mailboxes").fetchall()
    local_ids = {re.match(r"local://([^/]+)/", u).group(1) for _, u in rows
                 if u and u.startswith("local://")}
    rowid_key = {r: url_to_key(u, acct_by_id, local_ids) for r, u in rows}
    want = [r for r, k in rowid_key.items() if k in keys]
    if not want:
        return []
    ph = ",".join("?" * len(want))
    sql = f"""
      select m.ROWID, m.mailbox, m.date_received, m.read, m.flagged, m.flag_color,
             coalesce(m.subject_prefix,'') || coalesce(s.subject,''), a.address, a.comment,
             g.message_id_header, m.list_id_hash, m.unsubscribe_type,
             exists(select 1 from attachments t where t.message = m.ROWID)
      from messages m
      left join subjects s on s.ROWID = m.subject
      left join addresses a on a.ROWID = m.sender
      left join message_global_data g on g.ROWID = m.global_message_id
      where m.deleted = 0
        and (m.mailbox in ({ph}) or m.ROWID in (select message_id from labels where mailbox_id in ({ph})))"""
    params = want + want
    if a.since:
        sql += " and m.date_received >= ?"
        params.append(int(parse_when(a.since).timestamp()))
    if a.before:
        sql += " and m.date_received < ?"
        params.append(int(parse_when(a.before).timestamp()))
    out = []
    for (rid, mbx, ts, read, flagged, color, subj, addr, name, mid, lhash, unsub,
         has_att) in con.execute(sql, params):
        key = rowid_key.get(mbx)
        if not key:
            continue
        frm = f"{name} <{addr}>" if name else (addr or "")
        out.append({"ref": f"{key}#{rid}", "id": rid, "mailbox": key,
                    "messageId": (mid or "").strip("<>") or None, "date": iso_local(ts),
                    "from": frm, "subject": subj, "read": bool(read), "flagged": bool(flagged),
                    "_list": True if (lhash or 0) != 0 or (unsub or 0) > 0
                    else (None if unsub is None else False),
                    "_att": bool(has_att)})
    if a.to:
        ids = [r["id"] for r in out]
        rec = {}
        for i in range(0, len(ids), 900):
            chunk = ids[i:i + 900]
            q = ("select r.message, a.address, coalesce(a.comment,'') from recipients r "
                 f"join addresses a on a.ROWID = r.address where r.message in ({','.join('?' * len(chunk))})")
            for mid, addr, nm in con.execute(q, chunk):
                rec.setdefault(mid, []).append(f"{nm} <{addr}>")
        for r in out:
            r["_to"] = rec.get(r["id"], [])
    return out


def _search_jxa(a, keys):
    since = parse_when(a.since) if a.since else None
    res = jxa("fetch", {"keys": keys, "since": since.isoformat() if since else None})
    for s in res["skipped"]:
        warn(f"skipped mailbox {s['key']} ({s['error']})")
    out = []
    for r in res["messages"]:
        r["date"] = iso_local(r["date"]) if r["date"] else None
        out.append(r)
    return out


def search(a):
    """Apply the selection flags; returns message dicts, newest first, de-duplicated."""
    refs = list(a.refs)
    if a.ids_from:
        data = json.loads(Path(a.ids_from).read_text(encoding="utf-8"))
        items = data.get("messages", data) if isinstance(data, dict) else data
        refs += [x["ref"] if isinstance(x, dict) else x for x in items]
    if refs:
        rows = jxa("details", {"refs": refs}, timeout=a.timeout)
        for r in rows:
            if r.get("error"):
                die(f"message {r['ref']} not found ({r['error']}); search again", 2)
            r["mailbox"] = split_ref(r["ref"])[0]
            r["date"] = iso_local(r["date"]) if r.get("date") else None
        return rows
    if not has_filters(a):
        die("give at least one filter (--from, --subject, --since, --mailbox, ...) or --id", 2)
    mbs = mailboxes()
    sel = scope(a, mbs)
    keys = [m["key"] for m in sel]
    engine = a.engine
    con = None
    if engine in ("auto", "index"):
        con = index_connect()
        if con is None and engine == "index":
            die("Envelope Index not readable (needs Full Disk Access); use --engine jxa", 3)
        engine = "index" if con else "jxa"
    rows = _search_index(con, a, set(keys), mbs) if engine == "index" else _search_jxa(a, keys)
    before = parse_when(a.before) if a.before else None
    since = parse_when(a.since) if a.since else None

    def keep(r):
        d = dt.datetime.fromisoformat(r["date"]) if r.get("date") else None
        if since and (d is None or d < since):
            return False
        if before and (d is None or d >= before):
            return False
        if a.sender and not _match_any(r.get("from", ""), a.sender):
            return False
        if a.subject and not all(fold(s) in fold(r.get("subject", "")) for s in a.subject):
            return False
        if a.unread and r.get("read"):
            return False
        if a.flagged and not r.get("flagged"):
            return False
        return True

    rows = [r for r in rows if keep(r)]
    # Gmail shows one message under several label mailboxes; keep one copy.
    seen, uniq = set(), []
    for r in sorted(rows, key=lambda r: ("All Mail" in r["mailbox"] or "Összes" in r["mailbox"],)):
        k = r.get("messageId") or r["ref"]
        if k in seen:
            continue
        seen.add(k)
        uniq.append(r)
    rows = sorted(uniq, key=lambda r: r.get("date") or "", reverse=True)

    # Filters that need per-message detail: confirm through JXA.
    need_detail = a.to and engine == "jxa" or a.has_attachment or a.newsletter or a.not_newsletter
    if a.to and engine == "index":
        rows = [r for r in rows if _match_any(" ".join(r.pop("_to", [])), a.to)]
    if need_detail and rows:
        if len(rows) > 2000:
            warn(f"checking {len(rows)} messages one by one; narrow with --mailbox/--since to speed up")
        unknown = rows
        if engine == "index" and (a.newsletter or a.not_newsletter) and not (a.has_attachment or a.to):
            unknown = [r for r in rows if r.get("_list") is None]
        if unknown:
            det = {d["ref"]: d for d in jxa("details", {"refs": [r["ref"] for r in unknown],
                                                         "headers": bool(a.newsletter or a.not_newsletter)},
                                            timeout=a.timeout)}
            for r in unknown:
                d = det.get(r["ref"], {})
                r["_att"] = bool(d.get("attachments"))
                r["attachments"] = d.get("attachments", [])
                r["_toall"] = (d.get("to") or []) + (d.get("cc") or [])
                if "headers" in d:
                    r["_list"] = bool(re.search(r"^(List-Unsubscribe|List-Id):", d["headers"], re.I | re.M))
        if a.to and engine == "jxa":
            rows = [r for r in rows if _match_any(" ".join(r.get("_toall", [])), a.to)]
        if a.has_attachment:
            rows = [r for r in rows if r.get("_att")]
        if a.newsletter:
            rows = [r for r in rows if r.get("_list")]
        if a.not_newsletter:
            rows = [r for r in rows if not r.get("_list")]
    if a.limit:
        rows = rows[:a.limit]
    for r in rows:
        for k in [k for k in r if k.startswith("_")]:
            del r[k]
        r["engine"] = engine
    return rows


# ---- files ---------------------------------------------------------------------

def slug(text, maxlen=80):
    s = re.sub(r"[\\/:*?\"<>|\x00-\x1f]+", "-", (text or "untitled").strip())
    s = re.sub(r"\s+", " ", s).strip(" .-")
    return (s or "untitled")[:maxlen]


def unique_path(path, taken):
    """path, or 'stem-2.ext', 'stem-3.ext'... not in `taken` (lower-cased strings) and not on disk."""
    stem, suffix, n = path.stem, path.suffix, 2
    cand = path
    while str(cand).lower() in taken or cand.exists():
        cand = path.with_name(f"{stem}-{n}{suffix}")
        n += 1
    taken.add(str(cand).lower())
    return cand
