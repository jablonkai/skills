"""Shared helpers for the apple-contacts scripts (Python 3.9+ stdlib only).

Reads and writes go through `cn`, a small Contacts-framework helper compiled from
cn.swift on first use and cached under ~/Library/Caches/apple-contacts/. It answers a
whole address book in about a second, sees every account (iCloud, Exchange, Google,
On My Mac) and can create contacts and groups in a chosen one. Notes are the exception:
the framework hides them without an Apple entitlement, so notes go through Contacts'
JXA dictionary. When `cn` can't run (no Swift toolchain, no access), reads fall back to
JXA as well. Nothing listens on a port and no process outlives its call.
"""
import csv
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import unicodedata
from pathlib import Path

HERE = Path(__file__).resolve().parent
CN_SRC = HERE / "cn.swift"
CACHE = Path.home() / "Library" / "Caches" / "apple-contacts"
DEFAULT_TIMEOUT = 120


def die(msg, code=1):
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(code)


def warn(msg):
    print(f"warning: {msg}", file=sys.stderr)


# ---- the framework helper -------------------------------------------------------

def cn_binary():
    """Path to the compiled helper, rebuilt when cn.swift changed. None without swiftc."""
    digest = hashlib.sha256(CN_SRC.read_bytes()).hexdigest()[:12]
    exe = CACHE / f"cn-{digest}"
    if exe.exists():
        return exe
    if not shutil.which("swiftc"):
        return None
    CACHE.mkdir(parents=True, exist_ok=True)
    tmp = CACHE / f".cn-{digest}.{os.getpid()}"
    res = subprocess.run(["swiftc", "-O", str(CN_SRC), "-o", str(tmp)],
                         capture_output=True, text=True, timeout=600)
    if res.returncode != 0:
        die("compiling cn.swift failed (install the Xcode Command Line Tools: "
            f"xcode-select --install):\n{res.stderr[-1500:]}")
    tmp.replace(exe)
    for old in CACHE.glob("cn-*"):
        if old != exe:
            old.unlink(missing_ok=True)
    return exe


def cn(*args, spec=None, timeout=DEFAULT_TIMEOUT, check=True, raw=False):
    """Run `cn <args>` (JSON spec on stdin for `save`); parsed JSON, or text when raw."""
    exe = cn_binary()
    if exe is None:
        if not check:
            return None
        die("the Contacts helper needs the Swift toolchain: xcode-select --install", 3)
    try:
        res = subprocess.run([str(exe), *args], input=json.dumps(spec) if spec is not None else "",
                             capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        die(f"Contacts helper timed out after {timeout}s (a privacy prompt may be waiting "
            "on screen: answer it and retry)", 124)
    if res.returncode != 0:
        if not check:
            return None
        msg = res.stderr.strip()
        die(msg[len("error: "):] if msg.startswith("error: ") else msg or f"cn {args[0]} failed",
            res.returncode if res.returncode in (2, 3) else 1)
    if raw:
        return res.stdout
    return json.loads(res.stdout) if res.stdout.strip() else None


def access():
    """'authorized', 'limited', 'denied', 'restricted', 'notDetermined' or 'no-swift'."""
    if os.environ.get("APPLE_CONTACTS_FORCE_JXA"):  # test the fallback on a machine with access
        return "forced-jxa"
    if cn_binary() is None:
        return "no-swift"
    return cn("status")["status"]


def framework_ok():
    return access() in ("authorized", "limited", "notDetermined")  # notDetermined: cn asks


# ---- JXA (notes, and the read fallback) ------------------------------------------

JXA_READ = r"""
function run(argv) {
  const app = Application('Contacts');
  const want = argv[0] ? new Set(JSON.parse(argv[0])) : null;
  const src = argv[1] ? app.groups.byId(argv[1]).people : app.people;
  const p = src;
  const ids = p.id();
  const g = {
    given: p.firstName(), middle: p.middleName(), family: p.lastName(), nickname: p.nickname(),
    prefix: p.title(), suffix: p.suffix(), org: p.organization(), department: p.department(),
    jobTitle: p.jobTitle(), company: p.company(), birthDate: p.birthDate(), note: p.note(),
    el: p.emails.label(), ev: p.emails.value(), pl: p.phones.label(), pv: p.phones.value(),
    ul: p.urls.label(), uv: p.urls.value(),
    al: p.addresses.label(), as: p.addresses.street(), ac: p.addresses.city(),
    at: p.addresses.state(), az: p.addresses.zip(), ao: p.addresses.country(),
    ak: p.addresses.countryCode(),
  };
  const groups = {};
  app.groups().forEach(gr => gr.people.id().forEach(id => (groups[id] = groups[id] || []).push(gr.id())));
  const s = v => v || '';
  const out = [];
  ids.forEach((id, i) => {
    if (want && !want.has(id)) return;
    const b = g.birthDate[i];
    out.push({
      id, type: g.company[i] ? 'organization' : 'person',
      prefix: s(g.prefix[i]), given: s(g.given[i]), middle: s(g.middle[i]), family: s(g.family[i]),
      suffix: s(g.suffix[i]), nickname: s(g.nickname[i]), org: s(g.org[i]),
      department: s(g.department[i]), jobTitle: s(g.jobTitle[i]), note: s(g.note[i]),
      birthday: b ? b.getFullYear() + '-' + String(b.getMonth() + 1).padStart(2, '0') + '-' + String(b.getDate()).padStart(2, '0') : '',
      emails: g.ev[i].map((v, j) => ({label: s(g.el[i][j]), value: v})),
      phones: g.pv[i].map((v, j) => ({label: s(g.pl[i][j]), value: v})),
      urls: g.uv[i].map((v, j) => ({label: s(g.ul[i][j]), value: v})),
      addresses: g.as[i].map((v, j) => ({label: s(g.al[i][j]), street: s(v), city: s(g.ac[i][j]),
        state: s(g.at[i][j]), postalCode: s(g.az[i][j]), country: s(g.ao[i][j]), countryCode: s(g.ak[i][j])})),
      containers: [], groups: groups[id] || [],
    });
  });
  return JSON.stringify(out);
}
"""

JXA_GROUPS = r"""
function run() {
  const app = Application('Contacts');
  return JSON.stringify(app.groups().map(g => ({id: g.id(), name: g.name(), container: '', count: g.people.length})));
}
"""

JXA_NOTES_GET = r"""
function run(argv) {
  const p = Application('Contacts').people;
  const ids = p.id(), notes = p.note(), want = new Set(JSON.parse(argv[0]));
  const out = {};
  ids.forEach((id, i) => { if (want.has(id)) out[id] = notes[i] || ''; });
  return JSON.stringify(out);
}
"""

JXA_NOTES_SET = r"""
function run(argv) {
  const app = Application('Contacts');
  const notes = JSON.parse(argv[0]);
  Object.keys(notes).forEach(id => { app.people.byId(id).note = notes[id]; });
  app.save();
  return 'ok';
}
"""

JXA_VCARD = r"""
function run(argv) {
  const app = Application('Contacts');
  const want = new Set(JSON.parse(argv[0]));
  const p = app.people, ids = p.id(), cards = p.vcard();
  return ids.map((id, i) => want.has(id) ? cards[i] : null).filter(x => x).join('');
}
"""


def jxa(script, *args, timeout=DEFAULT_TIMEOUT):
    try:
        res = subprocess.run(["osascript", "-l", "JavaScript", "-", *args], input=script,
                             capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        die(f"Contacts did not answer within {timeout}s (an Automation or Contacts privacy "
            "prompt may be waiting on screen)", 124)
    if res.returncode != 0:
        err = res.stderr.strip()
        if "-1743" in err or "Not authorized" in err:
            die("osascript may not control Contacts: allow it in System Settings > Privacy & "
                "Security > Automation", 3)
        die(f"Contacts JXA failed: {err[-800:]}")
    return res.stdout.rstrip("\n")


def notes_get(ids):
    return json.loads(jxa(JXA_NOTES_GET, json.dumps(list(ids)))) if ids else {}


def notes_set(mapping):
    if mapping:
        jxa(JXA_NOTES_SET, json.dumps(mapping))


# Contacts' AppleScript stores labels in the same raw form as the framework constants.
JXA_LABELS = {"home": "_$!<Home>!$_", "work": "_$!<Work>!$_", "other": "_$!<Other>!$_",
              "school": "_$!<School>!$_", "mobile": "_$!<Mobile>!$_", "cell": "_$!<Mobile>!$_",
              "iphone": "iPhone", "main": "_$!<Main>!$_", "homefax": "_$!<HomeFAX>!$_",
              "workfax": "_$!<WorkFAX>!$_", "pager": "_$!<Pager>!$_", "homepage": "_$!<HomePage>!$_"}

JXA_APPLY = r"""
function run(argv) {
  const app = Application('Contacts');
  const ops = JSON.parse(argv[0]), labels = JSON.parse(argv[1]), notes = JSON.parse(argv[2] || '{}');
  const lab = l => (l ? (labels[l.toLowerCase()] || l) : '_$!<Other>!$_');
  const digits = s => (s || '').replace(/\D/g, '');
  const scalars = {prefix: 'title', given: 'firstName', middle: 'middleName', family: 'lastName',
    suffix: 'suffix', nickname: 'nickname', org: 'organization', department: 'department', jobTitle: 'jobTitle'};
  ops.forEach(op => {
    const p = app.people.byId(op.op === 'update' ? op.id : op.contact);
    if (op.op === 'addMember') { app.add(p, {to: app.groups.byId(op.group)}); return; }
    if (op.op === 'removeMember') { app.remove(p, {from: app.groups.byId(op.group)}); return; }
    const c = op.contact, merge = op.mode !== 'replace';
    Object.keys(scalars).forEach(k => { if (c[k] !== undefined && !(merge && c[k] === '')) p[scalars[k]] = c[k]; });
    if (c.type) p.company = c.type === 'organization';
    if (c.birthday && !c.birthday.startsWith('--')) {
      const [y, m, d] = c.birthday.split('-').map(Number);
      p.birthDate = new Date(y, m - 1, d, 12);
    }
    const lists = [['emails', app.Email, v => v.toLowerCase()], ['phones', app.Phone, digits], ['urls', app.Url, v => v]];
    lists.forEach(([key, Cls, norm]) => {
      if (!c[key]) return;
      if (!merge) p[key]().slice().reverse().forEach(x => x.delete());
      const have = new Set(merge ? p[key].value().map(norm) : []);
      c[key].forEach(e => { if (e.value && !have.has(norm(e.value))) p[key].push(Cls({label: lab(e.label), value: e.value})); });
    });
    if (c.addresses) {
      if (!merge) p.addresses().slice().reverse().forEach(x => x.delete());
      c.addresses.forEach(a => p.addresses.push(app.Address({label: lab(a.label), street: a.street || '',
        city: a.city || '', state: a.state || '', zip: a.postalCode || '', country: a.country || ''})));
    }
  });
  Object.keys(notes).forEach(id => { app.people.byId(id).note = notes[id]; });
  app.save();
  const back = {};
  Object.keys(notes).forEach(id => { back[id] = app.people.byId(id).note() || ''; });
  return JSON.stringify(back);
}
"""


def save(ops, notes=None):
    """Run cn save ops, routing around a framework limit: without Apple's notes entitlement
    the framework can't save a contact that has a note (CoreData error 134092), so updates
    and group-membership changes of noted contacts go through Contacts' AppleScript.
    notes ({id or ref: text}) are written in the same AppleScript call, which also reads
    them back: every AppleScript call right after a framework save waits ~8 s while
    Contacts reloads, so there is at most one.
    Returns ({ref: id} for created contacts and groups, {id: stored note})."""
    targets = set()
    for op in ops:
        if op["op"] == "update":
            targets.add(op["id"])
        elif op["op"] in ("addMember", "removeMember") and not op["contact"].startswith("new:"):
            targets.add(op["contact"])
    pre, post, cn_ops = [], [], []
    for op in ops:
        if op["op"] == "deleteGroup":
            members = contacts(group=op["id"])
            noted = {i for i, n in notes_get([c["id"] for c in members]).items() if n}
            pre += [{"op": "removeMember", "contact": i, "group": op["id"]} for i in sorted(noted)]
    noted = {i for i, n in notes_get(sorted(targets)).items() if n} if targets else set()
    for op in ops:
        cid = op.get("id") if op["op"] == "update" else op.get("contact")
        if op["op"] in ("update", "addMember", "removeMember") and cid in noted:
            post.append(op)
        else:
            cn_ops.append(op)
    if pre:
        jxa(JXA_APPLY, json.dumps(pre), json.dumps(JXA_LABELS))
    refs = cn("save", spec={"ops": cn_ops})["refs"] if cn_ops else {}
    notes = {refs.get(k, k): v for k, v in (notes or {}).items()}
    back = {}
    if post or notes:
        for op in post:
            if op.get("group") in refs:
                op["group"] = refs[op["group"]]
        back = json.loads(jxa(JXA_APPLY, json.dumps(post), json.dumps(JXA_LABELS), json.dumps(notes)))
    return refs, back


# ---- reading ------------------------------------------------------------------------

def containers():
    if framework_ok():
        return cn("containers")
    return []


def groups():
    """[{id, name, container, count}]."""
    if framework_ok():
        return cn("groups")
    return json.loads(jxa(JXA_GROUPS))


def contacts(group=None, container=None, ids=None, raw=False, notes=False):
    """Contacts as dicts (see references/contacts-api.md). Unified across linked cards
    unless raw. notes=True adds each contact's note (via JXA)."""
    if framework_ok():
        args = ["contacts"]
        if group:
            args += ["--group", group]
        elif container:
            args += ["--container", container]
        elif ids is not None:
            if not ids:
                return []
            args += ["--ids", ",".join(ids)]
        if raw:
            args.append("--raw")
        out = cn(*args)
        if notes:
            got = notes_get([c["id"] for c in out])
            for c in out:
                c["note"] = got.get(c["id"], "")
        return out
    if container:
        die("listing by account needs the Contacts framework (cn); JXA has no accounts", 3)
    warn("reading through AppleScript (no framework access): linked cards are not unified")
    out = json.loads(jxa(JXA_READ, json.dumps(ids) if ids is not None else "", group or ""))
    if not notes:
        for c in out:
            c.pop("note", None)
    return out


def vcard(group=None, container=None, ids=None, photos=False, notes=False):
    """vCard 3.0 text. PHOTO lines are dropped unless photos=True."""
    if framework_ok():
        args = ["vcard"]
        if group:
            args += ["--group", group]
        elif container:
            args += ["--container", container]
        elif ids is not None:
            if not ids:
                return ""
            args += ["--ids", ",".join(ids)]
        text = cn(*args, raw=True)
        if notes:
            text = add_vcard_notes(text, group=group, container=container, ids=ids)
    else:
        if ids is None:
            ids = [c["id"] for c in contacts(group=group, container=container)]
        text = jxa(JXA_VCARD, json.dumps(ids))
    return text if photos else strip_photos(text)


def unfold(text):
    return re.sub(r"\r?\n[ \t]", "", text)


def strip_photos(text):
    out, skip = [], False
    for line in re.split(r"\r?\n", text):
        if skip and line[:1] in (" ", "\t"):
            continue
        skip = line.upper().startswith("PHOTO")
        if not skip:
            out.append(line)
    return "\n".join(out)


def vcard_escape(s):
    return s.replace("\\", "\\\\").replace("\n", "\\n").replace(",", "\\,").replace(";", "\\;")


def add_vcard_notes(text, group=None, container=None, ids=None):
    """cn's vCards carry no NOTE (the framework hides notes), so splice them in, card by
    card: cn serializes in the same order as `contacts` with the same filter."""
    order = [c["id"] for c in contacts(group=group, container=container, ids=ids)]
    notes = notes_get(order)
    cards = re.split(r"(?<=END:VCARD)\r?\n", text.strip())
    if len(cards) != len(order):
        warn("could not match vCards to contacts; notes left out")
        return text
    out = []
    for cid, card in zip(order, cards):
        note = notes.get(cid, "")
        if note:
            card = card.replace("END:VCARD", f"NOTE:{vcard_escape(note)}\nEND:VCARD")
        out.append(card)
    return "\n".join(out) + "\n"


def parse_vcard_text(text):
    """Cards in a vCard string, parsed by the framework (or a minimal parser without it)."""
    if cn_binary() is not None:
        import tempfile
        with tempfile.NamedTemporaryFile("w", suffix=".vcf", delete=False) as f:
            f.write(text)
            tmp = f.name
        try:
            return cn("parse-vcard", tmp)
        finally:
            os.unlink(tmp)
    return parse_vcard_minimal(text)


def vcard_notes(text):
    """The NOTE of each card in order ('' when none), unescaped."""
    notes, cur = [], None
    for line in unfold(text).splitlines():
        key = line.partition(":")[0].split(";")[0].upper()
        if key == "BEGIN":
            cur = ""
        elif key == "END" and cur is not None:
            notes.append(cur)
            cur = None
        elif key == "NOTE" and cur is not None:
            v = line.partition(":")[2]
            cur = re.sub(r"\\([nN,;\\])", lambda m: "\n" if m[1] in "nN" else m[1], v)
    return notes


def parse_vcard_minimal(text):
    cards, cur = [], None
    for line in unfold(text).splitlines():
        name, _, value = line.partition(":")
        key = name.split(";")[0].upper()
        if key == "BEGIN":
            cur = {"given": "", "family": "", "org": "", "emails": [], "phones": []}
        elif key == "END" and cur is not None:
            cards.append(cur)
            cur = None
        elif cur is None:
            continue
        elif key == "N":
            parts = (value.split(";") + ["", ""])[:2]
            cur["family"], cur["given"] = parts
        elif key == "ORG":
            cur["org"] = value.split(";")[0]
        elif key == "EMAIL":
            cur["emails"].append({"label": "", "value": value})
        elif key == "TEL":
            cur["phones"].append({"label": "", "value": value})
    return cards


# ---- names, keys and resolution --------------------------------------------------

def display_name(c):
    parts = [c.get(k, "") for k in ("prefix", "given", "middle", "family", "suffix")]
    name = " ".join(p for p in parts if p).strip()
    if c.get("type") == "organization" or not name:
        return c.get("org") or name or (c["emails"][0]["value"] if c.get("emails") else "(no name)")
    return name


def fold(s):
    """Lowercase, accents removed, punctuation to spaces: 'Kovács-Tóth É.' -> 'kovacs toth e'."""
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(ch for ch in s if not unicodedata.combining(ch)).casefold()
    return " ".join(re.sub(r"[^\w]+", " ", s).split())


def name_key(c):
    """Order-insensitive person-name key ('Nagy Anna' == 'Anna Nagy'); '' when nameless."""
    toks = fold(" ".join(c.get(k, "") for k in ("given", "middle", "family"))).split()
    return " ".join(sorted(toks))


def email_key(e):
    return (e or "").strip().lower()


def phone_key(p):
    """Digits only, compared on the last 9 so +36 30 …, 06 30 … and 0036 30 … agree.
    Short numbers (extensions, service numbers) are kept whole."""
    d = re.sub(r"\D", "", p or "")
    return d[-9:] if len(d) >= 9 else d


def resolve_container(name, conts=None):
    conts = conts if conts is not None else containers()
    if not conts:
        die("accounts are only visible through the Contacts framework (cn)", 3)
    want = name.strip().lower()
    aliases = {"local": "on my mac", "mac": "on my mac", "onmymac": "on my mac"}
    want = aliases.get(want.replace(" ", ""), want)
    hits = [c for c in conts if c["id"].lower() == want or c["name"].lower() == want]
    if not hits:
        die(f"no account named {name!r}. Known: " + ", ".join(c["name"] for c in conts), 2)
    if len(hits) > 1:
        die(f"{name!r} is ambiguous: " + ", ".join(f"{c['name']} ({c['id']})" for c in hits), 2)
    return hits[0]


def default_container(conts=None):
    conts = conts if conts is not None else containers()
    for c in conts:
        if c["default"]:
            return c
    die("no default account found; pass --account", 2)


def container_name(cid, conts):
    for c in conts:
        if c["id"] == cid:
            return c["name"]
    return cid


def resolve_group(name, grps=None, container=None, missing_ok=False):
    """A group by name or id, optionally limited to one container. Ambiguous names fail."""
    grps = grps if grps is not None else groups()
    want = name.strip().lower()
    hits = [g for g in grps if g["id"].lower() == want or g["name"].lower() == want]
    if container:
        hits = [g for g in hits if not g["container"] or g["container"] == container]
    if not hits:
        if missing_ok:
            return None
        die(f"no group named {name!r}. Known: " + (", ".join(sorted(g["name"] for g in grps)) or "none"), 2)
    if len(hits) > 1:
        die(f"{name!r} matches {len(hits)} groups in different accounts; add --account", 2)
    return hits[0]


# ---- output ---------------------------------------------------------------------------

CSV_COLUMNS = ["id", "name", "given", "middle", "family", "nickname", "org", "department",
               "jobTitle", "emails", "phones", "addresses", "urls", "birthday", "note", "groups",
               "accounts"]


def joined(items, fmt):
    return "; ".join(fmt(x) for x in items)


def addr_text(a):
    parts = [a.get("street", ""), a.get("postalCode", ""), a.get("city", ""), a.get("state", ""), a.get("country", "")]
    return ", ".join(p.replace("\n", ", ") for p in parts if p)


def csv_row(c, group_names=None, cont_names=None):
    lab = lambda x: (f"{x['label']}: " if x.get("label") else "")  # noqa: E731
    return {
        "id": c["id"], "name": display_name(c), "given": c.get("given", ""),
        "middle": c.get("middle", ""), "family": c.get("family", ""),
        "nickname": c.get("nickname", ""), "org": c.get("org", ""),
        "department": c.get("department", ""), "jobTitle": c.get("jobTitle", ""),
        "emails": joined(c.get("emails", []), lambda e: lab(e) + e["value"]),
        "phones": joined(c.get("phones", []), lambda p: lab(p) + p["value"]),
        "addresses": joined(c.get("addresses", []), lambda a: lab(a) + addr_text(a)),
        "urls": joined(c.get("urls", []), lambda u: u["value"]),
        "birthday": c.get("birthday", ""), "note": c.get("note", ""),
        "groups": "; ".join((group_names or {}).get(g, g) for g in c.get("groups", [])),
        "accounts": "; ".join((cont_names or {}).get(x, x) for x in c.get("containers", [])),
    }


def write_csv(rows, path=None, columns=None):
    columns = columns or CSV_COLUMNS
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=columns, extrasaction="ignore", lineterminator="\n")
    w.writeheader()
    for r in rows:
        w.writerow(r)
    if path:
        Path(path).write_text(buf.getvalue(), encoding="utf-8")
    return buf.getvalue()


def md_escape(s):
    return str(s).replace("|", "\\|").replace("\n", " ")


def md_table(headers, rows):
    lines = ["| " + " | ".join(headers) + " |", "|" + "---|" * len(headers)]
    lines += ["| " + " | ".join(md_escape(x) for x in r) + " |" for r in rows]
    return "\n".join(lines)


# ---- CSV input -----------------------------------------------------------------------

def _norm_header(h):
    return re.sub(r"[^a-z0-9]", "", fold(h))


SCALAR_HEADERS = {
    "given": {"firstname", "givenname", "first", "keresztnev", "utonev"},
    "family": {"lastname", "familyname", "surname", "last", "vezeteknev", "csaladnev"},
    "middle": {"middlename", "middle", "additionalname"},
    "prefix": {"prefix", "nameprefix"},
    "suffix": {"suffix", "namesuffix"},
    "nickname": {"nickname", "becenev"},
    "org": {"company", "organization", "organisation", "org", "organizationname", "ceg", "cegnev"},
    "department": {"department", "osztaly", "organizationdepartment"},
    "jobTitle": {"jobtitle", "position", "role", "organizationtitle", "beosztas"},
    "birthday": {"birthday", "birthdate", "dob", "dateofbirth", "szuletesnap", "szuletesidatum"},
    "note": {"note", "notes", "megjegyzes"},
    "fullname": {"name", "fullname", "displayname", "nev", "teljesnev"},
    "groups": {"group", "groups", "groupmembership", "csoport"},
}
ADDRESS_HEADERS = {
    "street": {"street", "address", "streetaddress", "cim", "utca"},
    "city": {"city", "town", "varos", "telepules"},
    "state": {"state", "region", "province", "megye"},
    "postalCode": {"zip", "zipcode", "postalcode", "postcode", "iranyitoszam"},
    "country": {"country", "orszag"},
}


def _label_from_header(h):
    for word, label in (("mobile", "mobile"), ("cell", "mobile"), ("mobil", "mobile"),
                        ("iphone", "iphone"), ("home", "home"), ("otthon", "home"),
                        ("work", "work"), ("munka", "work"), ("main", "main"), ("other", "other")):
        if word in h:
            return label
    return ""


def classify_header(h):
    """('scalar', field) | ('email', label) | ('phone', label) | ('url', label) |
    ('address', part) | (None, None)."""
    n = _norm_header(h)
    for field, names in SCALAR_HEADERS.items():
        if n in names:
            return "scalar", field
    if n.endswith("type") or n.endswith("label"):  # Google's "Phone 1 - Type" etc.
        return None, None
    if "email" in n or n in ("mail", "emailcim"):
        return "email", _label_from_header(n)
    if any(w in n for w in ("phone", "mobile", "tel", "cell", "telefon", "mobil")):
        return "phone", _label_from_header(n)
    if n in ("url", "website", "web", "homepage", "honlap"):
        return "url", ""
    for part, names in ADDRESS_HEADERS.items():
        for name in names:
            if n == name or (name != "address" and n.endswith(name)):  # "Home Street", "Address 1 - City"
                return "address", part
    return None, None


def split_multi(v):
    return [x.strip() for x in re.split(r"\s*(?:;|:::|\n)\s*", v or "") if x.strip()]


def parse_birthday(v):
    v = (v or "").strip()
    if not v:
        return ""
    m = re.fullmatch(r"(\d{4})[-./](\d{1,2})[-./](\d{1,2})\.?", v)
    if m:
        return f"{int(m[1]):04d}-{int(m[2]):02d}-{int(m[3]):02d}"
    m = re.fullmatch(r"-{0,2}(\d{1,2})-(\d{1,2})", v)
    if m:
        return f"--{int(m[1]):02d}-{int(m[2]):02d}"
    m = re.fullmatch(r"(\d{1,2})[./](\d{1,2})[./](\d{4})", v)
    if m:
        return f"{int(m[3]):04d}-{int(m[2]):02d}-{int(m[1]):02d}"  # day-first, as in Europe
    die(f"can't read birthday {v!r} (use YYYY-MM-DD or --MM-DD)", 2)


def split_full_name(full):
    """'Nagy, Anna' -> (Anna, Nagy); 'Anna Nagy' -> (Anna, Nagy): last word is the family name."""
    full = full.strip()
    if "," in full:
        fam, giv = (x.strip() for x in full.split(",", 1))
        return giv, fam
    parts = full.split()
    if len(parts) == 1:
        return parts[0], ""
    return " ".join(parts[:-1]), parts[-1]


def read_csv_contacts(path):
    """Rows of a CSV as contact dicts plus ('groups', [names]) and ('_row', n)."""
    raw = Path(path).read_bytes()
    text = raw.decode("utf-8-sig") if not raw.startswith(b"\xff\xfe") else raw.decode("utf-16")
    sample = text[:4096]
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",;\t")
    except csv.Error:
        dialect = csv.excel
    reader = csv.reader(io.StringIO(text), dialect)
    rows = list(reader)
    if not rows:
        die(f"{path} is empty", 2)
    header = rows[0]
    kinds = [classify_header(h) for h in header]
    unknown = [h for h, k in zip(header, kinds) if k[0] is None and h.strip()]
    if unknown:
        warn("ignored CSV columns: " + ", ".join(unknown))
    out = []
    for n, row in enumerate(rows[1:], start=2):
        if not any(cell.strip() for cell in row):
            continue
        c = {"emails": [], "phones": [], "urls": [], "addresses": [], "groups": [], "_row": n}
        addr = {}
        for (kind, field), value in zip(kinds, row):
            value = value.strip()
            if not value or kind is None:
                continue
            if kind == "scalar" and field == "groups":
                c["groups"] += split_multi(value)
            elif kind == "scalar" and field == "fullname":
                c["_fullname"] = value
            elif kind == "scalar" and field == "birthday":
                c["birthday"] = parse_birthday(value)
            elif kind == "scalar":
                c[field] = value
            elif kind == "email":
                c["emails"] += [{"label": field or "", "value": v} for v in split_multi(value)]
            elif kind == "phone":
                c["phones"] += [{"label": field or "", "value": v} for v in split_multi(value)]
            elif kind == "url":
                c["urls"].append({"label": "", "value": value})
            elif kind == "address":
                addr[field] = value
        if addr:
            c["addresses"].append({"label": "", **addr})
        full = c.pop("_fullname", "")
        if full and not c.get("given") and not c.get("family"):
            c["given"], c["family"] = split_full_name(full)
        if not (c.get("given") or c.get("family") or c.get("org") or c["emails"] or c["phones"]):
            warn(f"row {n}: no name, company, email or phone; skipped")
            continue
        if not (c.get("given") or c.get("family")) and c.get("org"):
            c["type"] = "organization"
        out.append(c)
    return out


def emit_json(obj):
    print(json.dumps(obj, indent=2, ensure_ascii=False))
