#!/usr/bin/env python3
"""Search, export, cite and add to a Zotero 10 library through Zotero's local API.

Talks to the running Zotero desktop app on http://127.0.0.1:23119 (stdlib only,
Python 3.9+). Reads need the local API switched on; writes also need a key the
user approves once in a Zotero dialog (`authorize`).

Exit codes: 0 ok, 1 setup problem (Zotero not running, local API off, no write
key), 2 Zotero or network error, 3 not found / ambiguous, 4 output failed
validation.
"""

import argparse
import html
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid

BASE = os.environ.get("ZOTERO_URL", "http://127.0.0.1:23119").rstrip("/")
API = BASE + "/api/users/0"
HOME = os.path.expanduser(os.environ.get("ZOTERO_SKILL_HOME", "~/.config/zotero-skill"))
KEY_FILE = os.path.join(HOME, "key")
JOURNAL = os.path.join(HOME, "journal.jsonl")
UA = "zotero-skill/1.0 (https://github.com/jablonkai/skills)"
BATCH = 50  # max itemKey values / objects per request, as in the web API

EXIT_SETUP, EXIT_ZOTERO, EXIT_NOTFOUND, EXIT_INVALID = 1, 2, 3, 4


class Fail(Exception):
    def __init__(self, code, message, **extra):
        super().__init__(message)
        self.code, self.message, self.extra = code, message, extra


def out(obj):
    print(json.dumps(obj, ensure_ascii=False, indent=2))


def warn(msg):
    print("zotero.py: " + msg, file=sys.stderr)


# ---------------------------------------------------------------- HTTP layer

class Zotero:
    def __init__(self, need_key=False):
        self.server_id = None
        self.key = None
        if need_key:
            self.key = read_key()
            if not self.key:
                raise Fail(EXIT_SETUP, "no write key stored — run `zotero.py authorize` "
                           "and approve the dialog in Zotero")

    def raw(self, method, url, body=None, headers=None, timeout=30):
        h = {"User-Agent": UA}
        if self.server_id:
            h["Zotero-Server-ID"] = self.server_id
        if self.key:
            h["Zotero-API-Key"] = self.key
        data = None
        if body is not None:
            data = body if isinstance(body, bytes) else json.dumps(body).encode()
            h["Content-Type"] = "application/json"
        h.update(headers or {})
        req = urllib.request.Request(url, data=data, method=method, headers=h)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                sid = r.headers.get("Zotero-Server-ID")
                if sid:
                    self.server_id = sid
                return r.status, r.headers, r.read().decode("utf-8")
        except urllib.error.HTTPError as e:
            return e.code, e.headers, e.read().decode("utf-8", "replace")
        except (urllib.error.URLError, OSError) as e:
            raise Fail(EXIT_SETUP, "Zotero is not reachable at %s (%s) — start it with "
                       "`open -a Zotero`" % (BASE, getattr(e, "reason", e)))

    def api(self, method, path, body=None, params=None, headers=None, ok=(200, 204)):
        url = API + path
        if params:
            url += ("&" if "?" in url else "?") + urllib.parse.urlencode(params, doseq=True)
        if method != "GET" and not self.server_id:
            self.api("GET", "/collections", params={"limit": 1})
        status, hdrs, text = self.raw(method, url, body, headers)
        if status == 403 and "not enabled" in text:
            raise Fail(EXIT_SETUP, "Zotero's local API is off — ask the user to enable "
                       "Settings › Advanced › 'Allow other applications on this computer "
                       "to communicate with Zotero'")
        if status == 401:
            raise Fail(EXIT_SETUP, "write key missing or revoked — run `zotero.py authorize`")
        if status not in ok:
            raise Fail(EXIT_NOTFOUND if status == 404 else EXIT_ZOTERO,
                       "%s %s -> HTTP %s: %s" % (method, path, status, text.strip()[:300]))
        return status, hdrs, text

    def get_json(self, path, params=None):
        """GET with pagination (the local API normally returns everything at once)."""
        params = dict(params or {})
        results, start = [], 0
        while True:
            p = dict(params, start=start) if start else params
            _, hdrs, text = self.api("GET", path, params=p)
            page = json.loads(text) if text.strip() else []
            if isinstance(page, dict):
                return page
            results.extend(page)
            if 'rel="next"' not in (hdrs.get("Link") or "") or not page:
                return results
            start += len(page)

    def get_text(self, path, params=None):
        return self.api("GET", path, params=params)[2]

    def write(self, method, path, body, version=None):
        headers = {"If-Unmodified-Since-Version": str(version)} if version is not None else None
        _, _, text = self.api(method, path, body=body, headers=headers)
        return json.loads(text) if text.strip() else {}


def read_key():
    try:
        with open(KEY_FILE) as f:
            return f.read().strip() or None
    except OSError:
        return None


def journal(entry):
    os.makedirs(HOME, exist_ok=True)
    entry = dict(entry, time=time.strftime("%Y-%m-%dT%H:%M:%S"))
    with open(JOURNAL, "a") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


# ------------------------------------------------------------ library model

def collections(z):
    cols = z.get_json("/collections")
    by_key = {c["key"]: c for c in cols}

    def path(c):
        parts, seen = [], set()
        while c and c["key"] not in seen:
            seen.add(c["key"])
            parts.append(c["data"]["name"])
            parent = c["data"].get("parentCollection")
            c = by_key.get(parent) if parent else None
        return "/".join(reversed(parts))

    rows = []
    for c in cols:
        rows.append({"key": c["key"], "name": c["data"]["name"], "path": path(c),
                     "parent": c["data"].get("parentCollection") or None,
                     "items": c.get("meta", {}).get("numItems", 0)})
    return sorted(rows, key=lambda r: r["path"].lower())


def resolve_collection(z, ref, rows=None):
    """Collection by key, by name or by path (A/B), case-insensitive."""
    rows = rows if rows is not None else collections(z)
    for r in rows:
        if r["key"] == ref:
            return r
    low = ref.strip().strip("/").lower()
    hits = [r for r in rows if r["path"].lower() == low] or \
           [r for r in rows if r["name"].lower() == low]
    if len(hits) == 1:
        return hits[0]
    if not hits:
        raise Fail(EXIT_NOTFOUND, "no collection named %r" % ref,
                   collections=[r["path"] for r in rows])
    raise Fail(EXIT_NOTFOUND, "collection name %r is ambiguous — pass the path or key" % ref,
               candidates=[{"key": r["key"], "path": r["path"]} for r in hits])


def descendants(rows, key):
    keys, frontier = [key], [key]
    while frontier:
        nxt = [r["key"] for r in rows if r["parent"] in frontier]
        keys.extend(nxt)
        frontier = nxt
    return keys


NON_BIB = ("note", "attachment", "annotation")


def item_keys(z, collection=None, recursive=False, tags=(), item_type=None, qs=(),
              everything=False, keys=(), include_all=False):
    """Top-level bibliographic item keys matching the selection, in library order."""
    if keys:
        return list(dict.fromkeys(keys))
    base = {"format": "keys"}
    if tags:
        base["tag"] = list(tags)
    if item_type:
        base["itemType"] = item_type
    if everything:
        base["qmode"] = "everything"
    paths = ["/items/top"]
    if collection:
        rows = collections(z)
        col = resolve_collection(z, collection, rows)
        ckeys = descendants(rows, col["key"]) if recursive else [col["key"]]
        paths = ["/collections/%s/items/top" % k for k in ckeys]
    elif not (tags or item_type or qs or include_all):
        raise Fail(EXIT_NOTFOUND, "select items with --collection, --tag, --type, a query, "
                   "--keys or --all")
    found = []
    for p in paths:
        for q in (qs or [None]):
            params = dict(base, q=q) if q else base
            found.extend(z.get_text(p, params).split())
    return list(dict.fromkeys(found))


def fetch_items(z, keys):
    items = []
    for i in range(0, len(keys), BATCH):
        chunk = keys[i:i + BATCH]
        items.extend(z.get_json("/items", {"itemKey": ",".join(chunk)}))
    order = {k: n for n, k in enumerate(keys)}
    items = [it for it in items if it["data"]["itemType"] not in NON_BIB]
    return sorted(items, key=lambda it: order.get(it["key"], 0))


VENUE_FIELDS = ("publicationTitle", "proceedingsTitle", "bookTitle", "websiteTitle",
                "university", "institution", "publisher")


def summarize(it, col_names=None):
    d = it["data"]
    creators = []
    for c in d.get("creators", []):
        name = c.get("name") or ", ".join(x for x in (c.get("lastName"), c.get("firstName")) if x)
        creators.append(name if c.get("creatorType") in ("author", None)
                        else "%s (%s)" % (name, c.get("creatorType")))
    year = (it.get("meta", {}).get("parsedDate") or d.get("date") or "")[:4]
    venue = next((d[f] for f in VENUE_FIELDS if d.get(f)), "")
    row = {"key": it["key"], "type": d["itemType"], "title": d.get("title", ""),
           "creators": creators, "year": year, "venue": venue,
           "citationKey": d.get("citationKey") or None,
           "DOI": d.get("DOI") or doi_from_extra(d.get("extra", "")) or None,
           "ISBN": d.get("ISBN") or None, "tags": [t["tag"] for t in d.get("tags", [])]}
    if col_names is not None:
        row["collections"] = [col_names.get(k, k) for k in d.get("collections", [])]
    return row


def doi_from_extra(extra):
    m = re.search(r"^DOI:\s*(\S+)", extra or "", re.M | re.I)
    return m.group(1) if m else None


def md_table(rows):
    def cell(v):
        v = "; ".join(v) if isinstance(v, list) else (v or "")
        return str(v).replace("|", "\\|").replace("\n", " ")
    cols = ["key", "creators", "year", "title", "venue", "DOI", "tags"]
    lines = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    lines += ["| " + " | ".join(cell(r.get(c)) for c in cols) + " |" for r in rows]
    return "\n".join(lines)


# ----------------------------------------------------------- export checks

ENTRY_RE = re.compile(r"@(\w+)\s*\{\s*([^,\s]+)\s*,", re.M)


def validate_bibtex(text):
    problems, keys = [], []
    starts = [m for m in ENTRY_RE.finditer(text) if m.group(1).lower() not in
              ("comment", "preamble", "string")]
    for n, m in enumerate(starts):
        end = starts[n + 1].start() if n + 1 < len(starts) else len(text)
        body = text[m.start():end]
        depth = 0
        for ch in body:
            depth += ch == "{"
            depth -= ch == "}"
            if depth < 0:
                break
        if depth != 0:
            problems.append("unbalanced braces in %s" % m.group(2))
        keys.append(m.group(2))
        for field in ("title",):
            if not re.search(r"^\s*%s\s*=" % field, body, re.M | re.I):
                problems.append("%s has no %s" % (m.group(2), field))
    dup = sorted({k for k in keys if keys.count(k) > 1})
    if dup:
        problems.append("duplicate citation keys: " + ", ".join(dup))
    return keys, problems


def validate_csljson(text):
    try:
        data = json.loads(text)
    except ValueError as e:
        return [], ["not valid JSON: %s" % e]
    if not isinstance(data, list):
        return [], ["CSL-JSON must be an array"]
    problems = ["entry %d lacks id/type" % n for n, e in enumerate(data)
                if not (isinstance(e, dict) and e.get("id") and e.get("type"))]
    ids = [e.get("id") for e in data if isinstance(e, dict)]
    dup = sorted({str(i) for i in ids if ids.count(i) > 1})
    if dup:
        problems.append("duplicate ids: " + ", ".join(dup))
    return [str(i) for i in ids], problems


def generated_keys(z, keys):
    """{itemKey: citation key}: the stored citationKey, else the key Zotero's BibTeX
    exporter generates (unique within this selection, a/b suffixes in order)."""
    out_keys, taken = {}, set()
    for it in fetch_items(z, keys):
        stored = it["data"].get("citationKey")
        if stored:
            out_keys[it["key"]] = stored
            taken.add(stored)
    for k in keys:
        if k in out_keys:
            continue
        m = ENTRY_RE.search(z.get_text("/items", {"itemKey": k, "format": "biblatex"}))
        if not m:
            continue
        base, n, key = m.group(2), 0, m.group(2)
        while key in taken:
            n += 1
            key = "%s%s" % (base, chr(96 + n))
        taken.add(key)
        out_keys[k] = key
    return out_keys


BBT_TRANSLATOR = {"bibtex": "Better BibTeX", "biblatex": "Better BibLaTeX",
                  "csljson": "Better CSL JSON"}


def bbt_call(z, method, params):
    status, _, text = z.raw("POST", BASE + "/better-bibtex/json-rpc",
                            {"jsonrpc": "2.0", "method": method, "params": params}, timeout=120)
    if status != 200 or "No endpoint" in text:
        raise Fail(EXIT_SETUP, "Better BibTeX is not installed or not answering")
    data = json.loads(text)
    if data.get("error"):
        raise Fail(EXIT_ZOTERO, "Better BibTeX: %s" % data["error"].get("message", data["error"]))
    return data["result"]


def export_bbt(z, keys, fmt):
    if fmt not in BBT_TRANSLATOR:
        raise Fail(EXIT_NOTFOUND, "--bbt supports bibtex, biblatex and csljson")
    cites = bbt_call(z, "item.citationkey", [keys])
    return bbt_call(z, "item.export", [[cites[k] for k in keys if k in cites],
                                       BBT_TRANSLATOR[fmt]])


def export_text(z, keys, fmt):
    """One request per 50 keys; Zotero de-duplicates citation keys within a request,
    so batches are rejoined and any cross-batch clash gets a letter suffix."""
    parts = [z.get_text("/items", {"itemKey": ",".join(keys[i:i + BATCH]), "format": fmt})
             for i in range(0, len(keys), BATCH)]
    if fmt == "csljson":
        merged = []
        for p in parts:
            merged.extend(json.loads(p) if p.strip() else [])
        # Zotero adds an item's child notes as extra "document" entries with URI ids
        wanted = set(keys)
        merged = [e for e in merged if not (
            re.search(r"/items/([A-Z0-9]{8})$", str(e.get("id", "")))
            and re.search(r"/items/([A-Z0-9]{8})$", str(e["id"])).group(1) not in wanted)]
        uri = [e for e in merged if re.search(r"/items/[A-Z0-9]{8}$", str(e.get("id", "")))]
        if uri:  # no stored citationKey (no Better BibTeX): use the BibTeX exporter's keys
            gen = generated_keys(z, [e["id"][-8:] for e in uri])
            for e in uri:
                if e["id"][-8:] in gen:
                    e["id"] = e["citation-key"] = gen[e["id"][-8:]]
        seen = set()
        for e in merged:
            base, n = e.get("id"), 0
            while e.get("id") in seen:
                n += 1
                e["id"] = "%s%s" % (base, chr(96 + n))
            seen.add(e["id"])
        return json.dumps(merged, ensure_ascii=False, indent=2) + "\n"
    if fmt in ("bibtex", "biblatex") and len(parts) > 1:
        seen, fixed = set(), []
        for p in parts:
            def rename(m):
                key, n = m.group(2), 0
                new = key
                while new in seen:
                    n += 1
                    new = "%s%s" % (key, chr(96 + n))
                seen.add(new)
                return "@%s{%s," % (m.group(1), new)
            fixed.append(ENTRY_RE.sub(rename, p))
        parts = fixed
    return "\n".join(p.strip("\n") for p in parts if p.strip()) + "\n"


# ----------------------------------------------------- citations / biblio

def html_to_text(s):
    """CSL HTML -> one line per entry (styles like IEEE nest margin divs in an entry)."""
    s = re.sub(r'<span class="Z3988"[^>]*></span>', "", s)
    chunks = re.split(r'<div class="csl-entry"[^>]*>', s)
    entries = chunks[1:] if len(chunks) > 1 else chunks
    lines = []
    for chunk in entries:
        t = html.unescape(re.sub(r"<[^>]+>", " ", chunk))
        t = re.sub(r"\s+", " ", t).strip()
        t = re.sub(r"\s+([.,;:)\]])", r"\1", t)
        if t:
            lines.append(t)
    return "\n".join(lines)


def html_to_markdown(s):
    s = re.sub(r"</?(i|em)>", "*", s)
    s = re.sub(r"</?(b|strong)>", "**", s)
    return html_to_text(s)


# --------------------------------------------------------- DOI / ISBN → item

CSL_TO_ZOTERO = {
    "journal-article": "journalArticle", "article-journal": "journalArticle",
    "proceedings-article": "conferencePaper", "paper-conference": "conferencePaper",
    "book-chapter": "bookSection", "chapter": "bookSection", "book": "book",
    "monograph": "book", "edited-book": "book", "reference-book": "book",
    "posted-content": "preprint", "article": "preprint", "report": "report",
    "dissertation": "thesis", "thesis": "thesis", "dataset": "dataset",
    "reference-entry": "encyclopediaArticle", "entry-encyclopedia": "encyclopediaArticle",
    "standard": "standard", "webpage": "webpage",
}
CONTAINER_FIELD = {"journalArticle": "publicationTitle", "conferencePaper": "proceedingsTitle",
                   "bookSection": "bookTitle", "preprint": "repository",
                   "encyclopediaArticle": "encyclopediaTitle"}


def http_get(url, accept, timeout=30):
    req = urllib.request.Request(url, headers={"Accept": accept, "User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        if e.code == 404:
            raise Fail(EXIT_NOTFOUND, "not found: %s" % url)
        raise Fail(EXIT_ZOTERO, "%s -> HTTP %s" % (url, e.code))
    except (urllib.error.URLError, OSError) as e:
        raise Fail(EXIT_ZOTERO, "network error for %s: %s" % (url, getattr(e, "reason", e)))


def norm_doi(doi):
    doi = doi.strip()
    doi = re.sub(r"^(https?://(dx\.)?doi\.org/|doi:\s*)", "", doi, flags=re.I)
    if not re.match(r"^10\.\d{4,9}/\S+$", doi):
        raise Fail(EXIT_NOTFOUND, "not a DOI: %r" % doi)
    return doi


def norm_isbn(isbn):
    s = re.sub(r"[^0-9Xx]", "", isbn).upper()
    if len(s) not in (10, 13):
        raise Fail(EXIT_NOTFOUND, "not an ISBN: %r" % isbn)
    return s


def first(v):
    return (v[0] if v else "") if isinstance(v, list) else (v or "")


def csl_date(issued):
    parts = (issued or {}).get("date-parts") or [[]]
    p = [x for x in parts[0] if x not in (None, "")]
    return "-".join(["%04d" % int(p[0])] + ["%02d" % int(x) for x in p[1:3]]) if p else ""


def item_from_doi(doi):
    csl = json.loads(http_get("https://doi.org/" + urllib.parse.quote(doi, safe="/:;()"),
                              "application/vnd.citationstyles.csl+json"))
    itype = CSL_TO_ZOTERO.get(csl.get("type"), "journalArticle")
    item = {"itemType": itype, "title": first(csl.get("title")), "DOI": doi,
            "date": csl_date(csl.get("issued") or csl.get("published-print")
                             or csl.get("published-online")),
            "url": "https://doi.org/" + doi, "creators": []}
    for role, ctype in (("author", "author"), ("editor", "editor")):
        for a in csl.get(role) or []:
            if a.get("family"):
                item["creators"].append({"creatorType": ctype, "lastName": a["family"],
                                         "firstName": a.get("given", "")})
            elif a.get("name") or a.get("literal"):
                item["creators"].append({"creatorType": ctype,
                                         "name": a.get("name") or a.get("literal")})
    container = first(csl.get("container-title"))
    if container and itype in CONTAINER_FIELD:
        item[CONTAINER_FIELD[itype]] = container
    simple = {"volume": "volume", "issue": "issue", "page": "pages", "publisher": "publisher",
              "language": "language"}
    for src, dst in simple.items():
        if csl.get(src):
            item[dst] = str(csl[src])
    if itype == "journalArticle":
        if csl.get("ISSN"):
            item["ISSN"] = ", ".join(csl["ISSN"]) if isinstance(csl["ISSN"], list) else csl["ISSN"]
        short = first(csl.get("container-title-short"))
        if short:
            item["journalAbbreviation"] = short
    if itype in ("book", "bookSection") and csl.get("ISBN"):
        item["ISBN"] = first(csl["ISBN"])
    if csl.get("abstract"):
        item["abstractNote"] = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", csl["abstract"])).strip()
        item["abstractNote"] = re.sub(r"^Abstract\s+", "", item["abstractNote"])
    return item


def item_from_isbn(isbn):
    data = json.loads(http_get("https://openlibrary.org/api/books?bibkeys=ISBN:%s&format=json"
                               "&jscmd=data" % isbn, "application/json"))
    b = data.get("ISBN:" + isbn)
    if not b:
        raise Fail(EXIT_NOTFOUND, "ISBN %s not found on Open Library" % isbn)
    title = b.get("title", "")
    if b.get("subtitle"):
        title += ": " + b["subtitle"]
    item = {"itemType": "book", "title": title, "ISBN": isbn, "creators": [],
            "date": b.get("publish_date", ""), "url": b.get("url", "")}
    for a in b.get("authors") or []:
        name = a.get("name", "").strip()
        if " " in name:
            given, family = name.rsplit(" ", 1)
            item["creators"].append({"creatorType": "author", "lastName": family,
                                     "firstName": given})
        elif name:
            item["creators"].append({"creatorType": "author", "name": name})
    if b.get("publishers"):
        item["publisher"] = b["publishers"][0].get("name", "")
    if b.get("publish_places"):
        item["place"] = b["publish_places"][0].get("name", "")
    if b.get("number_of_pages"):
        item["numPages"] = str(b["number_of_pages"])
    return item


def find_existing(z, field, value):
    """Keys of library items whose DOI/ISBN equals value (also DOI stored in Extra)."""
    keys = z.get_text("/items", {"q": value, "qmode": "everything", "format": "keys"}).split()
    hits = []
    for it in fetch_items(z, keys):
        d = it["data"]
        if field == "DOI":
            have = (d.get("DOI") or doi_from_extra(d.get("extra", "")) or "").lower()
            if have == value.lower():
                hits.append(it)
        else:
            isbns = [norm_digits(x) for x in re.split(r"[\s,;]+", d.get("ISBN", "")) if x]
            if norm_digits(value) in isbns:
                hits.append(it)
    return hits


def norm_digits(s):
    return re.sub(r"[^0-9X]", "", s.upper())


def create_objects(z, path, objs):
    created, failed = [], []
    for i in range(0, len(objs), BATCH):
        res = z.write("POST", path, objs[i:i + BATCH])
        for idx, v in sorted(res.get("successful", {}).items(), key=lambda kv: int(kv[0])):
            created.append(v["key"])
        for idx, v in res.get("failed", {}).items():
            failed.append({"index": i + int(idx), "error": v.get("message", v)})
    if failed:
        raise Fail(EXIT_ZOTERO, "Zotero rejected %d object(s)" % len(failed), failed=failed,
                   created=created)
    return created


# --------------------------------------------------------------- commands

def cmd_check(a):
    info = {"url": BASE, "running": False, "version": None, "localApi": False,
            "writeKey": bool(read_key()), "betterBibtex": False, "problems": []}
    z = Zotero()
    try:
        status, hdrs, _ = z.raw("GET", BASE + "/connector/ping", timeout=5)
    except Fail:
        info["problems"].append("Zotero is not running — `open -a Zotero` (install: "
                                "`brew install --cask zotero`)")
        out(info)
        return EXIT_SETUP
    info["running"] = True
    info["version"] = hdrs.get("X-Zotero-Version")
    status, _, text = z.raw("GET", API + "/collections?limit=1")
    info["localApi"] = status == 200
    if status == 403:
        info["problems"].append("local API off: ask the user to tick Settings › Advanced › "
                                "'Allow other applications on this computer to communicate "
                                "with Zotero'")
    bstatus, _, btext = z.raw("POST", BASE + "/better-bibtex/json-rpc",
                              {"jsonrpc": "2.0", "method": "api.ready", "params": []}, timeout=5)
    info["betterBibtex"] = bstatus == 200 and "No endpoint" not in btext
    if info["localApi"]:
        info["serverId"] = z.server_id
        info["items"] = len(z.get_text("/items/top", {"format": "keys"}).split())
        info["collections"] = len(z.get_json("/collections"))
    if not info["writeKey"]:
        info["notes"] = ["no write key: reads work; run `authorize` before add/undo"]
    out(info)
    return EXIT_SETUP if info["problems"] else 0


def cmd_authorize(a):
    z = Zotero()
    z.api("GET", "/collections", params={"limit": 1})
    warn("a dialog is now open in Zotero — the user must click Allow (or Always Allow)")
    status, _, text = z.raw("POST", BASE + "/api/local/authorize",
                            {"appName": a.app_name}, timeout=a.timeout)
    if status == 429:
        raise Fail(EXIT_ZOTERO, "too many authorization requests — wait a minute")
    if status != 200:
        raise Fail(EXIT_SETUP, "authorization not granted (HTTP %s): %s" % (status, text[:200]))
    data = json.loads(text)
    os.makedirs(HOME, mode=0o700, exist_ok=True)
    fd = os.open(KEY_FILE, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as f:
        f.write(data["key"])
    out({"authorized": True, "remember": data.get("remember"), "keyFile": KEY_FILE})
    return 0


def cmd_deauthorize(a):
    existed = os.path.exists(KEY_FILE)
    if existed:
        os.remove(KEY_FILE)
    out({"removed": existed, "next": "to revoke on Zotero's side too: Settings › Advanced › "
         "Clear Write Authorizations"})
    return 0


def cmd_collections(a):
    z = Zotero()
    rows = collections(z)
    if a.table:
        for r in rows:
            print("%s  %-8s  %4d  %s" % ("  " * r["path"].count("/"), r["key"], r["items"],
                                         r["name"]))
    else:
        out(rows)
    return 0


def selection(a, z):
    return item_keys(z, collection=getattr(a, "collection", None),
                     recursive=getattr(a, "recursive", False), tags=a.tag or (),
                     item_type=getattr(a, "type", None), qs=getattr(a, "query", None) or (),
                     everything=getattr(a, "everything", False), keys=split_keys(a.keys),
                     include_all=getattr(a, "all", False))


def split_keys(keys):
    return [k for part in (keys or []) for k in re.split(r"[\s,]+", part) if k]


def cmd_search(a):
    z = Zotero()
    keys = item_keys(z, collection=a.collection, recursive=a.recursive, tags=a.tag or (),
                     item_type=a.type, qs=a.query, everything=a.everything,
                     include_all=not (a.query or a.tag or a.type or a.collection))
    names = {r["key"]: r["path"] for r in collections(z)}
    rows = [summarize(it, names) for it in fetch_items(z, keys)]
    if a.table:
        print(md_table(rows))
    else:
        out({"count": len(rows), "items": rows})
    return 0


FORMAT_EXT = {"bibtex": ".bib", "biblatex": ".bib", "csljson": ".json", "ris": ".ris"}


def cmd_export(a):
    z = Zotero()
    keys = selection(a, z)
    items = fetch_items(z, keys)
    keys = [it["key"] for it in items]
    if not keys:
        raise Fail(EXIT_NOTFOUND, "selection is empty — nothing to export")
    text = export_bbt(z, keys, a.format) if a.bbt else export_text(z, keys, a.format)
    if a.format in ("bibtex", "biblatex"):
        cites, problems = validate_bibtex(text)
    elif a.format == "csljson":
        cites, problems = validate_csljson(text)
    else:
        cites = re.findall(r"^TY  - ", text, re.M)
        problems = [] if len(cites) == len(keys) else ["RIS has %d records for %d items"
                                                       % (len(cites), len(keys))]
    if len(cites) != len(keys):
        problems.append("%d entries for %d items" % (len(cites), len(keys)))
    if a.output == "-":
        sys.stdout.write(text)
        for p in problems:
            warn(p)
        return EXIT_INVALID if problems else 0
    with open(a.output, "w", encoding="utf-8") as f:
        f.write(text)
    out({"file": os.path.abspath(a.output), "format": a.format, "entries": len(cites),
         "citationKeys": cites if a.format != "ris" else None, "problems": problems})
    return EXIT_INVALID if problems else 0


def cmd_bib(a, citation=False):
    z = Zotero()
    keys = [it["key"] for it in fetch_items(z, selection(a, z))]
    if not keys:
        raise Fail(EXIT_NOTFOUND, "selection is empty")
    params = {"style": a.style, "locale": a.locale}
    if citation:
        entries = []
        for k in keys:
            it = z.get_json("/items/" + k, dict(params, include="citation", format="json"))
            c = it.get("citation", "")
            entries.append({"key": k, "html": c, "text": html_to_text(c)})
        if a.output_format == "json":
            out(entries)
        else:
            conv = html_to_markdown if a.output_format == "markdown" else (
                (lambda s: s) if a.output_format == "html" else html_to_text)
            for e in entries:
                print("%s\t%s" % (e["key"], conv(e["html"])))
        return 0
    chunks = [z.get_text("/items", dict(params, itemKey=",".join(keys[i:i + BATCH]),
                                        format="bib"))
              for i in range(0, len(keys), BATCH)]
    if len(chunks) > 1:
        warn("more than %d items: bibliography rendered in %d sorted chunks" % (BATCH, len(chunks)))
    body = "\n".join(chunks)
    if a.output_format == "html":
        print(body)
    elif a.output_format == "markdown":
        print("\n\n".join(html_to_markdown(body).splitlines()))
    elif a.output_format == "json":
        out({"style": a.style, "entries": html_to_text(body).splitlines()})
    else:
        print("\n\n".join(html_to_text(body).splitlines()))
    return 0


def cmd_add(a):
    z = Zotero(need_key=not a.dry_run)
    wanted = [("DOI", norm_doi(d)) for d in split_keys(a.doi)] + \
             [("ISBN", norm_isbn(i)) for i in split_keys(a.isbn)]
    if not wanted:
        raise Fail(EXIT_NOTFOUND, "give at least one --doi or --isbn")
    run = uuid.uuid4().hex[:8]
    col, col_created = None, False
    if a.collection:
        rows = collections(z)
        try:
            col = resolve_collection(z, a.collection, rows)
        except Fail as e:
            if not a.create_collection or "ambiguous" in e.message:
                raise
            parts = [p for p in a.collection.strip("/").split("/") if p]
            parent = None
            if len(parts) > 1:
                parent = resolve_collection(z, "/".join(parts[:-1]), rows)["key"]
            if a.dry_run:
                col = {"key": None, "path": a.collection}
            else:
                obj = {"name": parts[-1]}
                if parent:
                    obj["parentCollection"] = parent
                key = create_objects(z, "/collections", [obj])[0]
                journal({"run": run, "action": "createCollection", "key": key,
                         "name": a.collection})
                col = {"key": key, "path": a.collection}
            col_created = True
    report, new_items = [], []
    for field, value in wanted:
        existing = find_existing(z, field, value)
        if existing:
            report.append({field: value, "status": "exists", "key": existing[0]["key"],
                           "title": existing[0]["data"].get("title")})
            continue
        try:
            item = item_from_doi(value) if field == "DOI" else item_from_isbn(value)
        except Fail as e:
            report.append({field: value, "status": "failed", "error": e.message})
            continue
        if col and col.get("key"):
            item["collections"] = [col["key"]]
        if a.tag:
            item["tags"] = [{"tag": t} for t in a.tag]
        new_items.append((field, value, item))
    if a.dry_run:
        out({"dryRun": True, "collection": col and col["path"], "createCollection": col_created,
             "wouldCreate": [dict(i, _source="%s %s" % (f, v)) for f, v, i in new_items],
             "report": report})
        return 0
    if new_items:
        keys = create_objects(z, "/items", [i for _, _, i in new_items])
        journal({"run": run, "action": "createItems", "keys": keys})
        for (field, value, item), key in zip(new_items, keys):
            report.append({field: value, "status": "added", "key": key, "title": item["title"]})
    if col and col.get("key"):
        linked = []
        for r in report:
            if r["status"] != "exists":
                continue
            it = z.get_json("/items/" + r["key"])
            cols = it["data"].get("collections", [])
            if col["key"] not in cols:
                z.write("PATCH", "/items/" + r["key"], {"collections": cols + [col["key"]]},
                        it["version"])
                linked.append(r["key"])
                r["status"] = "exists, added to collection"
        if linked:
            journal({"run": run, "action": "addToCollection", "keys": linked,
                     "collection": col["key"]})
    out({"run": run, "collection": col and {"key": col["key"], "path": col["path"],
                                            "created": col_created}, "items": report})
    failed = [r for r in report if r["status"] == "failed"]
    return EXIT_NOTFOUND if failed and len(failed) == len(report) else 0


def cmd_pin_keys(a):
    """Store the key Zotero's exporter generates in each empty citationKey field."""
    z = Zotero(need_key=not a.dry_run)
    items = fetch_items(z, selection(a, z))
    if not items:
        raise Fail(EXIT_NOTFOUND, "selection is empty")
    gen = generated_keys(z, [it["key"] for it in items])
    plan = [(it, gen[it["key"]]) for it in items
            if not it["data"].get("citationKey") and it["key"] in gen]
    pinned_before = sum(1 for it in items if it["data"].get("citationKey"))
    if a.dry_run:
        out({"dryRun": True, "alreadyPinned": pinned_before,
             "wouldPin": [{"key": it["key"], "citationKey": k} for it, k in plan]})
        return 0
    run = uuid.uuid4().hex[:8]
    for it, key in plan:
        z.write("PATCH", "/items/" + it["key"], {"citationKey": key}, it["version"])
    if plan:
        journal({"run": run, "action": "pinKeys", "keys": [it["key"] for it, _ in plan]})
    out({"run": run, "alreadyPinned": pinned_before,
         "pinned": [{"key": it["key"], "citationKey": k} for it, k in plan]})
    return 0


def read_journal():
    try:
        with open(JOURNAL) as f:
            return [json.loads(line) for line in f if line.strip()]
    except OSError:
        return []


def cmd_undo(a):
    entries = read_journal()
    if not entries:
        raise Fail(EXIT_NOTFOUND, "journal is empty — nothing to undo")
    open_runs = [e["run"] for e in entries if not e.get("undone") and e["action"] != "undo"]
    run = a.run or (open_runs[-1] if open_runs else entries[-1]["run"])
    todo = [e for e in entries if e["run"] == run and not e.get("undone")]
    if not todo:
        raise Fail(EXIT_NOTFOUND, "run %s not found or already undone" % run)
    z = Zotero(need_key=True)
    done = []
    real_get = z.get_json

    def get_or_none(path, params=None):
        try:
            return real_get(path, params)
        except Fail as err:
            if err.code == EXIT_NOTFOUND:
                done.append({"gone": path})
                return None
            raise
    z.get_json = get_or_none
    for e in reversed(todo):
        if e["action"] == "createItems":
            for k in e["keys"]:
                it = z.get_json("/items/" + k)
                if it is None:
                    continue
                z.write("PATCH", "/items/" + k, {"deleted": 1}, it["version"])
                done.append({"trashed": k})
        elif e["action"] == "addToCollection":
            for k in e["keys"]:
                it = z.get_json("/items/" + k)
                if it is None:
                    continue
                cols = [c for c in it["data"].get("collections", []) if c != e["collection"]]
                z.write("PATCH", "/items/" + k, {"collections": cols}, it["version"])
                done.append({"removedFromCollection": k})
        elif e["action"] == "pinKeys":
            for k in e["keys"]:
                it = z.get_json("/items/" + k)
                if it is None:
                    continue
                z.write("PATCH", "/items/" + k, {"citationKey": ""}, it["version"])
                done.append({"unpinnedKey": k})
        elif e["action"] == "createCollection":
            c = z.get_json("/collections/" + e["key"])
            if c is None:
                continue
            z.write("PATCH", "/collections/" + e["key"], {"deleted": True}, c["version"])
            done.append({"trashedCollection": e["key"]})
    journal({"run": run, "action": "undo", "undone": True})
    with open(JOURNAL) as f:
        lines = [json.loads(line) for line in f if line.strip()]
    with open(JOURNAL, "w") as f:
        for e in lines:
            if e["run"] == run:
                e["undone"] = True
            f.write(json.dumps(e, ensure_ascii=False) + "\n")
    out({"run": run, "undone": done, "note": "items and collections are in Zotero's trash; "
         "empty it in the app to delete them for good"})
    return 0


def cmd_history(a):
    out(read_journal()[-a.limit:])
    return 0


# ------------------------------------------------------------------ CLI

def add_selection(p, query=False):
    p.add_argument("--collection", "-c", help="collection name, path (A/B) or key")
    p.add_argument("--recursive", "-r", action="store_true", help="include subcollections")
    p.add_argument("--tag", "-t", action="append", help="tag filter (repeat = AND; 'a || b' = OR)")
    p.add_argument("--keys", "-k", action="append", help="item keys, comma separated")
    p.add_argument("--all", action="store_true", help="the whole library")
    if query:
        p.add_argument("--query", "-q", action="append", help="quick-search text (repeat = OR)")
        p.add_argument("--everything", action="store_true", help="search all fields + full text")
        p.add_argument("--type", help="itemType filter, e.g. journalArticle or -book")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("check", help="is Zotero running, local API on, write key stored?")
    p = sub.add_parser("authorize", help="request a write key (user approves in Zotero)")
    p.add_argument("--app-name", default="Claude Code (zotero skill)")
    p.add_argument("--timeout", type=int, default=300)
    sub.add_parser("deauthorize", help="forget the stored write key")

    p = sub.add_parser("collections", help="list collections with paths and item counts")
    p.add_argument("--table", action="store_true")

    p = sub.add_parser("search", help="find top-level items; JSON or a Markdown table")
    p.add_argument("query", nargs="*", help="quick-search terms (each is OR'ed)")
    p.add_argument("--collection", "-c")
    p.add_argument("--recursive", "-r", action="store_true")
    p.add_argument("--tag", "-t", action="append")
    p.add_argument("--type")
    p.add_argument("--everything", action="store_true")
    p.add_argument("--table", action="store_true")

    p = sub.add_parser("export", help="BibTeX/BibLaTeX/CSL-JSON/RIS export with validation")
    add_selection(p, query=True)
    p.add_argument("--format", "-f", default="bibtex", choices=sorted(FORMAT_EXT))
    p.add_argument("--output", "-o", required=True, help="file path, or - for stdout")
    p.add_argument("--bbt", action="store_true",
                   help="export with Better BibTeX's translators (plugin must be installed)")

    for name, hlp in (("bib", "formatted bibliography in a CSL style"),
                      ("cite", "in-text citation per item in a CSL style")):
        p = sub.add_parser(name, help=hlp)
        add_selection(p, query=True)
        p.add_argument("--style", "-s", default="apa", help="CSL style id (apa, ieee, ...)")
        p.add_argument("--locale", "-l", default="en-US")
        p.add_argument("--output-format", default="text",
                       choices=["text", "markdown", "html", "json"])

    p = sub.add_parser("add", help="add papers by DOI / books by ISBN (needs write key)")
    p.add_argument("--doi", action="append", help="DOI(s), repeat or comma separate")
    p.add_argument("--isbn", action="append", help="ISBN(s)")
    p.add_argument("--collection", "-c", help="target collection (name, path or key)")
    p.add_argument("--create-collection", action="store_true",
                   help="create the collection if it does not exist")
    p.add_argument("--tag", "-t", action="append", help="tag(s) to put on new items")
    p.add_argument("--dry-run", action="store_true", help="resolve metadata, write nothing")

    p = sub.add_parser("pin-keys", help="store generated citation keys so they never change")
    add_selection(p, query=True)
    p.add_argument("--dry-run", action="store_true")

    p = sub.add_parser("undo", help="revert a previous add / pin-keys run")
    p.add_argument("--run", help="run id from add's output (default: last run)")
    p = sub.add_parser("history", help="show the write journal")
    p.add_argument("--limit", type=int, default=20)

    a = ap.parse_args(argv)
    try:
        if a.cmd == "check":
            return cmd_check(a)
        handlers = {"authorize": cmd_authorize, "deauthorize": cmd_deauthorize,
                    "collections": cmd_collections, "search": cmd_search, "export": cmd_export,
                    "bib": cmd_bib, "cite": lambda x: cmd_bib(x, citation=True),
                    "add": cmd_add, "pin-keys": cmd_pin_keys, "undo": cmd_undo, "history": cmd_history}
        return handlers[a.cmd](a)
    except Fail as e:
        print(json.dumps(dict({"error": e.message}, **e.extra), ensure_ascii=False, indent=2),
              file=sys.stderr)
        return e.code


if __name__ == "__main__":
    sys.exit(main())
