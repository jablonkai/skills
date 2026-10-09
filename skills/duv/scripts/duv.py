#!/usr/bin/env python3
"""Command-line client for the DUV Ultramarathon Statistics JSON API.

Standard library only. Every subcommand fetches one of the `json/m*.php`
endpoints on statistik.d-u-v.org, flattens the interesting list into rows and
prints them as CSV (default), Markdown or the raw JSON:

    records        national / continental best performances per age group
    rankings       international best list for a year (or all-time), paginated
    runner         one runner: header, personal bests, every performance
    search-runner  find runner IDs by name ("Smith" or "Smith, John")
    search-event   find event IDs by name ("Spartathlon" or "York,100,USA")
    event          finisher list of one event (HTML page: its JSON twin needs a login)
    event-detail   metadata of one event (organizer, venue, limits, editions)
    calendar       races in a year (past or future) with optional filters
    event-history  every edition of a race, its winners and course records
    multiple-finishers  runners ranked by finishes of one race series
    event-list     past events with finisher counts, km bounds, surface filter
    champions      IAU (or German) championship medallists per edition
    stats          statistics pages: lifetime mileage, km per year, oldest
                   finishers, time spans, female overall winners, results
                   abroad, long-running races, 100x100 mi club, doping cases
    head-to-head   two runners' shared races and who finished ahead
    progression    best-so-far progression of a national/world best
    get            any DUV JSON URL, pretty-printed, for endpoints not wrapped here

`records` is the workhorse: `--nat` and `--dist` are repeatable, so one call can
pull a whole country's record table across every distance, or one distance
across several countries, into a single CSV. The site's own page shows one
country x one distance at a time, which is why this exists.

Examples:

    duv.py records --nat HUN --dist 100km --dist 24h
    duv.py records --nat HUN --dist all --gender W --overall-only --format md
    duv.py records --nat 1 --dist 24h --type track --cat YOB --out europe-24h-track.csv
    duv.py rankings --year 2024 --dist 100km --gender W --nat HUN
    duv.py rankings --year all --dist 24h --gender M --pages all --primary-only --out 24h-alltime.csv
    duv.py runner --name "Berces, Edit"
    duv.py event --id 100580 --format md
    duv.py calendar --year 2024 --country HUN --dist 100km
    duv.py event-history --id 100580 --format md
    duv.py progression --nat HUN --dist 24h --gender W
    duv.py head-to-head --runner 3510 --runner "Sipos, Istvan"
    duv.py stats lifetime-mileage --country HUN --gender W
    duv.py champions --dist 24hWC --cnt 3

Bad parameter values make DUV answer with an empty body instead of an error;
the client reports that as such rather than pretending the list is empty.
"""
from __future__ import annotations

import argparse
import csv
import html
import json
import re
import shutil
import ssl
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

BASE = "https://statistik.d-u-v.org/"

RECORD_DISTANCES = ["50km", "50mi", "100km", "100mi", "1000km", "1000mi",
                    "6h", "12h", "24h", "48h", "6d"]
RECORD_TYPES = {"overall": "0", "road": "1", "track": "2", "indoor": "3"}
SPLIT_FLAGS = {"S": "split", "T": "track", "I": "indoor"}


def describe_flags(code: str) -> str:
    """DUV marks a record with up to three letters: S(plit), T(rack), I(ndoor)."""
    return ",".join(SPLIT_FLAGS.get(ch, ch) for ch in code.strip())


# --------------------------------------------------------------------------- #
# HTTP
# --------------------------------------------------------------------------- #

_last_request = 0.0
_use_curl = False
RETRIES = 4


class Transient(Exception):
    """A failure worth retrying: refused/dropped connection, timeout, HTTP 5xx."""


def fetch_text(url: str, delay: float) -> str:
    """GET a URL politely, returning the body with any UTF-8 BOM stripped.

    Some DUV JSON responses start with a BOM, which json.loads rejects, so the
    decode goes through 'utf-8-sig'. urllib is tried first; when the local
    Python has no CA bundle (a common macOS python.org install) the SSL
    verification fails, and curl — which uses the system trust store — takes
    over transparently. The server refuses or drops connections in bursts,
    so transient failures are retried with a growing pause.
    """
    for attempt in range(RETRIES):
        try:
            return _fetch_once(url, delay)
        except Transient as exc:
            if attempt == RETRIES - 1:
                sys.exit(f"error: cannot reach {url} after {RETRIES} tries: {exc}")
            pause = 5 * 2 ** attempt
            print(f"note: {exc}; retrying in {pause}s", file=sys.stderr)
            time.sleep(pause)
    raise AssertionError("unreachable")


def _fetch_once(url: str, delay: float) -> str:
    global _last_request, _use_curl
    wait = delay - (time.monotonic() - _last_request)
    if wait > 0:
        time.sleep(wait)
    _last_request = time.monotonic()

    if not _use_curl:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "duv-skill/1.1"})
            with urllib.request.urlopen(req, timeout=90) as resp:
                return resp.read().decode("utf-8-sig", errors="replace")
        except urllib.error.HTTPError as exc:
            if exc.code >= 500:
                raise Transient(f"HTTP {exc.code}") from exc
            return http_error_body(url, exc.code, exc.read().decode("utf-8-sig", errors="replace"))
        except urllib.error.URLError as exc:
            if not isinstance(exc.reason, ssl.SSLError) or not shutil.which("curl"):
                raise Transient(str(exc.reason)) from exc
            _use_curl = True
        except (TimeoutError, ConnectionError) as exc:
            raise Transient(str(exc) or type(exc).__name__) from exc
    proc = subprocess.run(["curl", "-sSL", "--max-time", "90", "-w", "\n%{http_code}", url],
                          capture_output=True)
    if proc.returncode:
        raise Transient(f"curl: {proc.stderr.decode(errors='replace').strip()}")
    body, _, code = proc.stdout.decode("utf-8-sig", errors="replace").rpartition("\n")
    if code.startswith("2"):
        return body
    if code.startswith("5") or code == "000":
        raise Transient(f"HTTP {code}")
    return http_error_body(url, int(code), body)


def http_error_body(url: str, code: int, body: str) -> str:
    """Keep a JSON body that arrives with an error status, otherwise exit.

    meventdetail.php answers 404 for many events yet sends the complete JSON
    payload, so the status alone can't be trusted. A 401 is a real refusal:
    DUV now wants a login token for mgetresultevent.php.
    """
    if code != 401 and body.lstrip().startswith("{"):
        return body
    sys.exit(f"error: HTTP {code} for {url}"
             + ("\n       DUV now requires a login token for this endpoint; "
                "use its HTML twin instead." if code == 401 else ""))


def fetch_json(endpoint: str, params: dict, delay: float) -> dict:
    query = {k: v for k, v in params.items() if v not in (None, "")}
    query["language"] = "EN"
    url = BASE + endpoint + "?" + urllib.parse.urlencode(query)
    body = fetch_text(url, delay)
    if not body.strip():
        sys.exit(f"error: DUV returned an empty body for {url}\n"
                 "       That is how it signals an unrecognised parameter value "
                 "(check the dist/nat/type/cat tokens).")
    try:
        return json.loads(body)
    except json.JSONDecodeError:
        sys.exit(f"error: non-JSON response from {url}\n       {body[:200]!r}")


# --------------------------------------------------------------------------- #
# Output
# --------------------------------------------------------------------------- #

def emit(rows: list[dict], fmt: str, out: str | None, raw=None) -> None:
    """Write rows as csv/md, or `raw` (the untouched API payload) as json."""
    if fmt == "json":
        text = json.dumps(raw if raw is not None else rows, ensure_ascii=False, indent=1)
    elif fmt == "md":
        text = to_markdown(rows)
    else:
        text = to_csv(rows)
    if out:
        with open(out, "w", encoding="utf-8", newline="") as fh:
            fh.write(text)
        print(f"{len(rows)} rows -> {out}", file=sys.stderr)
    else:
        sys.stdout.write(text)


def columns(rows: list[dict]) -> list[str]:
    """Union of the rows' keys in first-seen order (scraped rows can differ)."""
    return list(dict.fromkeys(k for row in rows for k in row))


def to_csv(rows: list[dict]) -> str:
    if not rows:
        return ""
    import io
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=columns(rows), restval="")
    writer.writeheader()
    writer.writerows(rows)
    return buf.getvalue()


def to_markdown(rows: list[dict]) -> str:
    if not rows:
        return "(no rows)\n"
    cols = columns(rows)
    lines = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(c, "")).replace("|", "\\|") for c in cols) + " |")
    return "\n".join(lines) + "\n"


# --------------------------------------------------------------------------- #
# Subcommands
# --------------------------------------------------------------------------- #

def cmd_records(args) -> None:
    distances = RECORD_DISTANCES if "all" in args.dist else args.dist
    rows, raw = [], []
    for nat in args.nat:
        for dist in distances:
            payload = fetch_json("json/mbestperfcountry.php", {
                "nat": nat.upper() if nat.isalpha() else nat,
                "dist": dist,
                "type": RECORD_TYPES[args.type],
                "cat": args.cat,
            }, args.delay)
            raw.append({"nat": nat, "dist": dist, "type": args.type, "cat": args.cat,
                        "response": payload})
            for ak, rec in payload.get("Records", {}).items():
                gender = ak[0]
                if args.gender != "all" and gender != args.gender:
                    continue
                if args.overall_only and not ak.endswith("Overall"):
                    continue
                rows.append({
                    "nat": nat, "dist": dist, "type": args.type, "scheme": args.cat,
                    "gender": gender, "cat": ak,
                    "perf": rec.get("Perf", "").strip(),
                    "flag": describe_flags(rec.get("Split", "")),
                    "first_name": rec.get("FirstName", ""), "last_name": rec.get("LastName", ""),
                    "person_id": rec.get("PersonID", ""),
                    "dob": rec.get("DOB", ""), "club": rec.get("Club", ""),
                    "event_id": rec.get("EventID", ""), "event": rec.get("Eventname", ""),
                    "city": rec.get("City", ""), "country": rec.get("Country", ""),
                    "date": rec.get("Startdate", ""),
                    "end_date": "" if rec.get("Enddate", "").startswith("00.") else rec.get("Enddate", ""),
                })
    emit(rows, args.format, args.out, raw)


def fetch_rankings(params: dict, pages: str, delay: float) -> list[dict]:
    """Every page payload of mgetintbestlist.php, up to `pages` (a count or 'all')."""
    raw, page = [], 1
    while True:
        payload = fetch_json("json/mgetintbestlist.php", {**params, "page": page}, delay)
        raw.append(payload)
        max_page = int(payload.get("Pagination", {}).get("MaxPage", 1) or 1)
        if page >= max_page or (pages != "all" and page >= int(pages)):
            if page < max_page:
                print(f"note: stopped after page {page} of {max_page} "
                      f"(use --pages all for the rest)", file=sys.stderr)
            return raw
        page += 1


def cmd_rankings(args) -> None:
    params = {"year": args.year, "dist": args.dist, "gender": args.gender,
              "nat": args.nat, "cat": args.cat, "label": args.label, "tt": args.tt}
    raw = fetch_rankings(params, args.pages, args.delay)
    rows = []
    for payload in raw:
        for r in payload.get("RankingList", []):
            rank = str(r.get("Rank", ""))
            if args.primary_only and rank.startswith("("):
                continue
            rows.append({
                "rank": rank, "perf": r.get("Perf", "").strip(),
                "first_name": r.get("FirstName", ""), "last_name": r.get("LastName", ""),
                "nat": r.get("Nationality", ""), "dob": r.get("DOB_Display", ""),
                "cat": r.get("CatInt", ""), "cat_rank": r.get("CatRank", ""),
                "date": r.get("Startdate", ""), "city": r.get("City", ""),
                "country": r.get("Country", ""), "event_id": r.get("EventID", ""),
                "person_id": r.get("PersonID", ""), "iau_label": r.get("IAULabel", ""),
                "age_graded": r.get("AgeGradePerf", "").strip(),
            })
    emit(rows, args.format, args.out, raw)


def resolve_runner(args) -> str:
    return args.id or resolve_name(args.name, args.delay)


def resolve_name(name: str, delay: float) -> str:
    """Runner id for a name that must match exactly one DUV runner."""
    hits = fetch_json("json/msearchrunner.php", {"sname": name}, delay)
    matches = hits.get("Hitlist", [])
    if not matches:
        sys.exit(f"error: no runner matches {name!r}; try without accents, or surname only")
    if len(matches) != 1:
        listing = "\n".join(f"  {h['PersonID']:>8}  {h['LastName']}, {h['FirstName']}  "
                            f"{h.get('Nationality', '')}  b.{h.get('YOB') if h.get('YOB') not in (None, '', '0') else '?'}  "
                            f"{h.get('Club', '')}  active {h.get('ActivRange', '')}"
                            for h in matches[:30])
        sys.exit(f"error: {len(matches)} runners match {name!r}; pass the id instead\n{listing}")
    return matches[0]["PersonID"]


def cmd_runner(args) -> None:
    runner_id = resolve_runner(args)
    payload = fetch_json("json/mgetresultperson.php", {"runner": runner_id}, args.delay)
    header = payload.get("PersonHeader", {})
    rows = []
    for year in payload.get("AllPerfs", []):
        for p in year.get("PerfsPerYear", []):
            rows.append({
                "date": p.get("EvtDate", ""), "event": p.get("EvtName", ""),
                "city": p.get("EvtCity", ""), "country": p.get("EvtCountryCode", ""),
                "dist": p.get("EvtDist", ""), "perf": p.get("Perf", "").strip(),
                "rank_overall": p.get("RankOverall", ""), "rank_gender": p.get("RankMW", ""),
                "cat": p.get("Cat", ""), "rank_cat": p.get("RankCat", ""),
                "event_id": p.get("EvtID", ""),
            })
    if args.format == "json":
        emit(rows, "json", args.out, payload)
        return
    pbs = []
    for entry in payload.get("AllPBs", []):
        for dist, detail in entry.items():
            years = [y for y in detail if y != "PB"]
            pb_year = next((y for y in years if detail[y].get("Perf") == detail.get("PB")), "")
            pbs.append({"dist": dist, "pb": detail.get("PB", ""), "pb_year": pb_year,
                        "years_ranked": ", ".join(years)})
    summary = [
        f"# {header.get('PersonName', '')}  (DUV id {runner_id})",
        f"Nationality: {header.get('NationalityShort', '')}  DOB: {header.get('DOB', '')}  "
        f"Club: {header.get('Club', '')}  Residence: {header.get('Residence', '')}",
        f"Age groups: {header.get('CatINT', '')} (int) / {header.get('CatNAT', '')} (ger)  "
        f"Events: {header.get('TotalEvtCnt', '')}  Total: {header.get('TotalKm', '')}",
        "", "## Personal bests (ranking-eligible distances only)", "",
    ]
    text = "\n".join(summary) + to_markdown(pbs) + "\n## All performances\n\n"
    text += to_markdown(rows) if args.format == "md" else to_csv(rows)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(text)
        print(f"{len(rows)} performances -> {args.out}", file=sys.stderr)
    else:
        sys.stdout.write(text)


def cmd_search_runner(args) -> None:
    payload = fetch_json("json/msearchrunner.php", {"sname": args.name}, args.delay)
    rows = [{"person_id": h.get("PersonID", ""), "last_name": h.get("LastName", ""),
             "first_name": h.get("FirstName", ""), "nat": h.get("Nationality", ""),
             "yob": h.get("YOB", ""), "gender": h.get("Gender", ""), "club": h.get("Club", ""),
             "city": h.get("City", ""), "active": h.get("ActivRange", "")}
            for h in payload.get("Hitlist", [])]
    if not rows:
        print(f"note: no runner matches {args.name!r}; try without accents, "
              "or surname only", file=sys.stderr)
    emit(rows, args.format, args.out, payload)


def cmd_search_event(args) -> None:
    payload = fetch_json("json/msearchevent.php", {"sname": args.name}, args.delay)
    rows = [{"event_id": h.get("EventID", ""), "event": h.get("EventName", "").strip(),
             "date": (h.get("Startdate") or "")[:10], "length": h.get("Length", ""),
             "duration": h.get("Duration", ""), "city": h.get("City", ""),
             "country": h.get("Country", ""), "edition": h.get("Edition", ""),
             "iau_label": h.get("IAULabel", ""), "record_proof": h.get("RecordProof", "")}
            for h in payload.get("Hitlist", [])]
    emit(rows, args.format, args.out, payload)


def html_cells(row: str) -> list[str]:
    """Text of each <td> in one table row, tags and entities stripped."""
    return [html.unescape(re.sub(r"<[^>]+>", "", cell)).replace("\xa0", " ").strip()
            for cell in re.findall(r"<td[^>]*>(.*?)</td>", row, re.S)]


# Result-table headers of getresultevent.php (language=EN) -> output column.
EVENT_COLUMNS = {"Rank": "rank", "Performance": "perf", "Surname, first name": "name",
                 "Club": "club", "Nat.": "nat", "YOB": "yob", "M/F": "gender",
                 "Rank M/F": "rank_gender", "Cat": "cat", "Cat. Rank": "rank_cat",
                 "Avg.Speed km/h": "speed_kmh", "Age graded performance": "age_graded"}


def cmd_event(args) -> None:
    # json/mgetresultevent.php answers 401 (Bearer token) since 2026, so this
    # scrapes the HTML result page instead. It serves 2000 rows per `page`.
    rows, page = [], 1
    while True:
        text = fetch_text(f"{BASE}getresultevent.php?event={args.id}&language=EN&page={page}",
                          args.delay)
        if page == 1:
            info = dict(re.findall(r"<b>([^<:]+):\s*</b></td>\s*<td[^>]*>(.*?)</td>", text, re.S))
            info = {k: html.unescape(re.sub(r"<[^>]+>|\s+", " ", v)).strip() for k, v in info.items()}
            if "Event" not in info:
                sys.exit(f"error: no event {args.id!r} on DUV (check the id with search-event)")
            total = re.search(r"(\d+) search results", text)
            print(f"# {info.get('Event', '')}  {info.get('Date', '')}  {info.get('Distance', '')}  "
                  f"finishers: {info.get('Finishers', '')}  "
                  f"ranking-eligible: {info.get('Ranking eligible', '')}", file=sys.stderr)
            heads = [re.sub(r"<[^>]+>|\s+", " ", h).strip()
                     for h in re.findall(r"<th[^>]*>(.*?)</th>", text, re.S)]
            # the name header also carries an "Original name" toggle link
            cols = ["name" if h.endswith("first name") else EVENT_COLUMNS.get(h, h) for h in heads]
        for tr in re.findall(r"<tr class='(?:odd|even)'>(.*?)</tr>", text, re.S):
            rec = dict(zip(cols, html_cells(tr)))
            orig = re.search(r"class='hideSpan'>(.*?)</span>", tr, re.S)
            if orig:  # the name cell also holds the original-script name, hidden
                rec["name"] = rec.get("name", "").replace(
                    html.unescape(re.sub(r"<[^>]+>", "", orig.group(1))).replace("\xa0", " ").strip(), "").strip()
            last, _, first = rec.pop("name", "").partition(",")
            runner = re.search(r"getresultperson\.php\?runner=(\d+)", tr)
            rows.append({"rank": rec.get("rank", ""), "perf": rec.get("perf", ""),
                         "last_name": last.strip(), "first_name": first.strip(),
                         **{k: v for k, v in rec.items() if k not in ("rank", "perf")},
                         "person_id": runner.group(1) if runner else ""})
        more = f"page={page + 1}'" in text
        if not more or (args.pages != "all" and page >= int(args.pages)):
            if more:
                print(f"note: stopped after page {page} ({len(rows)} of "
                      f"{total.group(1) if total else '?'} rows; use --pages all)", file=sys.stderr)
            break
        page += 1
    emit(rows, args.format, args.out, rows)


def cmd_event_detail(args) -> None:
    payload = fetch_json("json/meventdetail.php", {"event": args.id}, args.delay)
    if args.format == "json":
        emit([], "json", args.out, payload)
        return
    det = payload.get("raceDetails", {})
    keep = ["EventID", "EventName", "Edition", "Startdate", "Enddate", "Length", "Duration",
            "EventType", "City", "Country", "CountryName", "PromOrg", "Contact", "Email", "URL",
            "TimeLimit", "FieldLimit", "Fee", "AltitudeDiff", "IAULabel", "RecordProof",
            "FinisherM", "FinisherW", "CourseDesc", "MoreInfo", "ResultSource"]
    rows = [{"field": k, "value": str(det.get(k) or "").strip()} for k in keep]
    editions = [{"event_id": e.get("EventID", ""), "date": e.get("SDate", ""),
                 "edition": e.get("Edition", ""), "length": e.get("Length", ""),
                 "duration": e.get("Duration", ""), "finishers_m": e.get("FinisherM", ""),
                 "finishers_w": e.get("FinisherW", ""), "results": e.get("Results", "")}
                for e in payload.get("editions", [])]
    render = to_markdown if args.format == "md" else to_csv
    text = render(rows) + "\n" + render(editions)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(text)
    else:
        sys.stdout.write(text)


def cmd_calendar(args) -> None:
    # mcalendar.php ignores cups= (checked 2026-10: same rows with and without), so the
    # cup/championship filter runs here on each race's Cupname ("NC 24h Hungary",
    # "IAU 24h WC", "DUV-Cup" ...), and so does ranking eligibility.
    if args.cups:
        print("note: DUV's JSON calendar ignores --cups; filter with --cupname instead",
              file=sys.stderr)
    payload = fetch_json("json/mcalendar.php", {
        "year": args.year, "country": args.country, "dist": args.dist,
        "cups": args.cups, "rproof": args.rproof}, args.delay)
    want_proof = {"1": "Y", "2": "N"}.get(args.rproof or "")
    rows = [{"date": r.get("Startdate", ""), "event": r.get("EventName", "").strip(),
             "length": r.get("Length") or "", "duration": r.get("Duration") or "",
             "city": r.get("City", ""), "country": r.get("Country", ""),
             "event_type": r.get("EventType", ""), "results": r.get("Results", ""),
             "iau_label": r.get("IAULabel", ""), "record_proof": r.get("RecordProof", ""),
             "cup": (r.get("Cupname") or "").strip(), "event_id": r.get("EventID", "")}
            for r in payload.get("Races", [])
            if (not want_proof or r.get("RecordProof") == want_proof)
            and (not args.cupname or args.cupname.lower() in (r.get("Cupname") or "").lower())]
    hit = payload.get("HitCnt")
    if hit is not None and int(hit) >= 4000:
        print(f"note: DUV caps the calendar at 4000 races; narrow by country or dist",
              file=sys.stderr)
    emit(rows, args.format, args.out, payload)


# --------------------------------------------------------------------------- #
# HTML list pages without a JSON twin
# --------------------------------------------------------------------------- #

ROW_RE = re.compile(r"<tr[^>]*>(.*?)</tr>", re.S)
CELL_RE = re.compile(r"<t([hd])[^>]*>(.*?)</t[hd]>", re.S)
RUNNER_LINK = re.compile(r"getresultperson\.php\?runner=(\d+)")
EVENT_LINK = re.compile(r"(?:getresultevent|eventdetail)\.php\?event=(\d+)")
COLUMN_NAMES = {"surname, first name": "name", "nat.": "nat", "nationality": "nat",
                "m/f": "gender", "rank m/f": "rank_gender", "cat. rank": "rank_cat",
                "year of birth": "yob", "event (country)": "event"}


def cell_text(raw: str) -> str:
    raw = re.sub(r"<span class='hideSpan'>.*?</span>", "", raw, flags=re.S)
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", raw)).replace("\xa0", " ").split())


def column_key(text: str, index: int) -> str:
    """Snake-case column name; "" for an unlabelled icon column (dropped)."""
    t = text.lower()
    if not t:
        return "rank" if index == 0 else ""
    if t.endswith("surname, first name"):  # header may carry an "Original name" toggle
        return "name"
    return COLUMN_NAMES.get(t) or re.sub(r"[^a-z0-9]+", "_", t).strip("_")


def scrape_table(text: str) -> list[dict]:
    """Rows of the result table(s) below a DUV page's filter form.

    Handles the page shapes the statistics, champions and list pages share: a
    <th> header row, one-cell group rows ("men", "10/2024") carried into a
    `group` column, "<b>Date: </b>" label rows that set context for the
    tables after them, and rowspan continuation rows (the second race of a
    time-span pair) folded into the previous row as `<column>_2`.
    """
    start = text.rfind("</form>")
    rows, cols, group, context = [], [], "", {}
    for tr in ROW_RE.findall(text[start:] if start != -1 else text):
        cells = CELL_RE.findall(tr)
        if not cells:
            continue
        texts = [cell_text(c[1]) for c in cells]
        if [c[0] for c in cells].count("h") >= 3:
            cols, group = [column_key(t, i) for i, t in enumerate(texts)], ""
            continue
        label = re.match(r"\s*<b>\s*([^<:]+):\s*</b>", cells[0][1])
        if label and len(cells) <= 3:
            key = column_key(label.group(1), 1)
            context[key] = texts[1] if len(texts) > 1 else ""
            event = EVENT_LINK.search(tr)
            if event:
                context["event_id"] = event.group(1)
            continue
        if not cols:
            continue
        runner, event = RUNNER_LINK.search(tr), EVENT_LINK.search(tr)
        if len(cells) == 1:
            group = texts[0]
        elif len(cells) == len(cols):
            rec = {**context, **({"group": group} if group else {}),
                   **{k: v for k, v in zip(cols, texts) if k}}
            if runner:
                rec["person_id"] = runner.group(1)
            if event:
                rec["event_id"] = event.group(1)
            rows.append(rec)
        elif rows and len(cells) < len(cols):
            # rowspan continuation: these cells fill the table's last columns
            for key, value in zip(cols[-len(cells):], texts):
                if key:
                    rows[-1][f"{key}_2"] = value
            if event:
                rows[-1]["event_id_2"] = event.group(1)
    count = re.search(r"\d+ to (\d+) of (\d+) search results", text)
    if count and int(count.group(1)) < int(count.group(2)):
        print(f"note: DUV shows {count.group(1)} of {count.group(2)} rows; narrow the filters",
              file=sys.stderr)
    return rows


def fetch_page(page: str, params: dict, delay: float) -> str:
    query = {k: v for k, v in params.items() if v not in (None, "")}
    query["language"] = "EN"
    return fetch_text(BASE + page + "?" + urllib.parse.urlencode(query), delay)


def emit_scraped(page: str, params: dict, args) -> None:
    rows = scrape_table(fetch_page(page, params, args.delay))
    if not rows:
        print(f"note: no rows on {page} for {params}; an unrecognised token often looks "
              "like this", file=sys.stderr)
    emit(rows, args.format, args.out, rows)


# stats <kind> -> page, and which filters that page understands
STATS_PAGES = {
    "lifetime-mileage": ("lifetimemileage.php", "country gender"),
    "year-km": ("yearkm.php", "country year gender"),
    "oldest-finishers": ("oldestfinishers.php", "country year gender"),
    "timespan": ("timespan.php", "country type years"),
    "female-winners": ("femalewinners.php", "country year dist"),
    "top-abroad": ("toprankabroad.php", "country year dist gender cnt"),
    "long-running-races": ("longrunningraces.php", "country dist"),
    "100x100mi": ("100x100miclub.php", "country gender"),
    "doping": ("doping.php", "country gender"),
}


def cmd_stats(args) -> None:
    page, allowed = STATS_PAGES[args.kind]
    params = {k: getattr(args, k) for k in allowed.split()}
    ignored = [k for k in ("country", "year", "gender", "dist", "type", "years", "cnt")
               if k not in allowed.split() and getattr(args, k) not in (None, "")]
    if ignored:
        print(f"note: {args.kind} has no {', '.join(ignored)} filter; ignored", file=sys.stderr)
    emit_scraped(page, params, args)


def cmd_champions(args) -> None:
    page = "championsGER.php" if args.ger else "championsIAU.php"
    emit_scraped(page, {"dist": args.dist, "cnt": args.cnt, "cat": args.cat or "all"}, args)


def cmd_multiple_finishers(args) -> None:
    emit_scraped("multiplefinish.php", {"event": args.id, "gender": args.gender}, args)


def cmd_event_list(args) -> None:
    emit_scraped("geteventlist.php", {
        "year": args.year, "country": args.country, "dist": args.dist, "surface": args.surface,
        "label": "Y" if args.iau else None, "from": args.km_from, "to": args.km_to,
        "sort": "2" if args.sort == "finishers" else None, "club": args.club}, args)


# --------------------------------------------------------------------------- #
# Derived views
# --------------------------------------------------------------------------- #

def perf_value(perf: str) -> float | None:
    """Comparable number for a DUV performance: seconds for a time, km for a distance.

    Times look like "7:25:21 h", "07:25:21" or "2d 03:04:05"; distances like
    "250.106 km" or "250.106". Lower is better for times, higher for distances.
    """
    p = perf.replace("h", "").replace("km", "").strip()
    if ":" not in p:
        try:
            return float(p)
        except ValueError:
            return None
    days = 0
    if "d" in p:
        d, _, p = p.partition("d")
        days = int(d.strip() or 0)
    parts = [int(x) for x in p.strip().split(":")]
    while len(parts) < 3:
        parts.insert(0, 0)
    return days * 86400 + parts[0] * 3600 + parts[1] * 60 + parts[2]


def is_timed(dist: str) -> bool:
    """True for fixed-time events (6h, 24h, 6d), where more km is better."""
    return bool(re.fullmatch(r"\d+\s*[hd]", dist.strip()))


def better(a: float, b: float, timed: bool) -> bool:
    return a > b if timed else a < b


def parse_winner(raw: str) -> dict:
    """'1#Miklos Ori 04:39:08' -> overall rank, name, performance."""
    rank, _, rest = (raw or "").partition("#")
    name, _, perf = rest.rpartition(" ")
    return {"rank": rank, "name": name.strip(), "perf": perf.strip()}


def cmd_event_history(args) -> None:
    payload = fetch_json("json/meventdetail.php", {"event": args.id}, args.delay)
    if args.format == "json":
        emit([], "json", args.out, payload)
        return
    winners = {w.get("EventID"): w for w in payload.get("winnerList", [])}
    rows, best = [], {}
    for e in payload.get("editions", []):
        w = winners.get(e.get("EventID"), {})
        m, f = parse_winner(w.get("Winner_M", "")), parse_winner(w.get("Winner_W", ""))
        length = e.get("Length") or e.get("Duration") or ""
        rows.append({"year": e.get("Year", ""), "date": e.get("SDate", ""),
                     "event_id": e.get("EventID", ""), "event": e.get("EventName", "").strip(),
                     "length": length, "finishers_m": e.get("FinisherM", ""),
                     "finishers_w": e.get("FinisherW", ""), "results": e.get("Results", ""),
                     "winner_m": m["name"], "perf_m": m["perf"],
                     "winner_w": f["name"], "perf_w": f["perf"]})
        for gender, win in (("M", m), ("W", f)):
            value = perf_value(win["perf"]) if win["perf"] else None
            if value is None:
                continue
            key = (length, gender)
            if key not in best or better(value, best[key][0], is_timed(length)):
                best[key] = (value, {"length": length, "gender": gender, "perf": win["perf"],
                                     "name": win["name"], "year": e.get("Year", ""),
                                     "event_id": e.get("EventID", "")})
    det = payload.get("raceDetails", {})
    render = to_markdown if args.format == "md" else to_csv
    text = (f"# {det.get('EventName', '').strip()} — {det.get('City', '')} "
            f"({det.get('Country', '')}), {len(rows)} editions\n\n" if args.format == "md" else "")
    text += render(rows)
    records = [rec for _, (_, rec) in sorted(best.items())]
    if records:
        text += ("\n## Course records (best winning performance per length)\n\n"
                 if args.format == "md" else "\n") + render(records)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(text)
        print(f"{len(rows)} editions -> {args.out}", file=sys.stderr)
    else:
        sys.stdout.write(text)


SPLIT_NAME = re.compile(r"\bsplit\b", re.I)


def runner_results(runner_id: str, delay: float, splits: bool) -> tuple[dict, dict]:
    """A runner's header and performances keyed by event id.

    DUV files an intermediate time (the 100 km split of a 24 h) as its own
    event named "... Split"; left in, one race would count twice.
    """
    payload = fetch_json("json/mgetresultperson.php", {"runner": runner_id}, delay)
    perfs = {p.get("EvtID"): p for y in payload.get("AllPerfs", [])
             for p in y.get("PerfsPerYear", [])
             if splits or not SPLIT_NAME.search(p.get("EvtName", ""))}
    return payload.get("PersonHeader", {}), perfs


def cmd_head_to_head(args) -> None:
    if len(args.runner) != 2:
        sys.exit("error: pass exactly two --runner values (DUV id or name)")
    ids = [r if r.isdigit() else resolve_name(r, args.delay) for r in args.runner]
    (head_a, perfs_a), (head_b, perfs_b) = (runner_results(i, args.delay, args.splits)
                                            for i in ids)
    name_a, name_b = head_a.get("PersonName", ids[0]), head_b.get("PersonName", ids[1])
    rows, score = [], {name_a: 0, name_b: 0}
    for evt in sorted(set(perfs_a) & set(perfs_b),
                      key=lambda e: perfs_a[e].get("EvtDateIso", ""), reverse=True):
        a, b = perfs_a[evt], perfs_b[evt]
        try:
            ra, rb = int(a.get("RankOverall")), int(b.get("RankOverall"))
            ahead = name_a if ra < rb else name_b
            score[ahead] += 1
        except (TypeError, ValueError):
            ahead = ""
        rows.append({"date": a.get("EvtDate", ""), "event": a.get("EvtName", ""),
                     "dist": a.get("EvtDist", ""), "event_id": evt,
                     "perf_a": a.get("Perf", "").strip(), "rank_a": a.get("RankOverall", ""),
                     "perf_b": b.get("Perf", "").strip(), "rank_b": b.get("RankOverall", ""),
                     "ahead": ahead})
    print(f"# {name_a} (a) vs {name_b} (b): {len(rows)} shared races, "
          f"{name_a} ahead {score[name_a]}x, {name_b} ahead {score[name_b]}x", file=sys.stderr)
    emit(rows, args.format, args.out, rows)


def cmd_progression(args) -> None:
    """Best-so-far progression from the all-time ranking, oldest first."""
    raw = fetch_rankings({"year": "all", "dist": args.dist, "gender": args.gender,
                          "nat": args.nat, "cat": args.cat, "tt": "brutto"}, "all", args.delay)
    perfs = [r for payload in raw for r in payload.get("RankingList", [])]
    perfs.sort(key=lambda r: r.get("Startdate", ""))
    timed, best, rows = is_timed(args.dist), None, []
    for r in perfs:
        value = perf_value(r.get("Distance", "") if timed else r.get("Time", ""))
        if value is None or value == 0:
            continue
        if best is None or better(value, best, timed):
            best = value
            rows.append({"date": r.get("Startdate", ""), "perf": r.get("Perf", "").strip(),
                         "first_name": r.get("FirstName", ""), "last_name": r.get("LastName", ""),
                         "nat": r.get("Nationality", ""), "cat": r.get("CatInt", ""),
                         "city": r.get("City", ""), "country": r.get("Country", ""),
                         "event_id": r.get("EventID", ""), "person_id": r.get("PersonID", "")})
    emit(rows, args.format, args.out, rows)


def cmd_get(args) -> None:
    url = args.url if args.url.startswith("http") else BASE + args.url.lstrip("/")
    sep = "&" if "?" in url else "?"
    if "language=" not in url:
        url += sep + "language=EN"
    body = fetch_text(url, args.delay)
    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        sys.exit(f"error: not JSON (empty body usually means a bad parameter): {body[:200]!r}")
    if args.drop_nls:
        payload.pop("nlsText", None)
    text = json.dumps(payload, ensure_ascii=False, indent=1)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(text)
    else:
        sys.stdout.write(text + "\n")


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #

def build_parser() -> argparse.ArgumentParser:
    top = argparse.ArgumentParser(description=__doc__.split("\n\n")[0],
                                  formatter_class=argparse.RawDescriptionHelpFormatter)
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--format", choices=["csv", "md", "json"], default="csv",
                        help="csv (default), md table, or the raw API json")
    common.add_argument("--out", help="write to this file instead of stdout")
    common.add_argument("--delay", type=float, default=0.5,
                        help="seconds between requests (site is volunteer-run; default 0.5)")
    sub = top.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("records", parents=[common],
                       help="national/continental best performances per age group")
    p.add_argument("--nat", action="append", required=True,
                   help="IOC-3 country (HUN) or continent 1-6; repeatable. No world scope exists.")
    p.add_argument("--dist", action="append", required=True,
                   help=f"{', '.join(RECORD_DISTANCES)} or all; repeatable")
    p.add_argument("--type", choices=list(RECORD_TYPES), default="overall",
                   help="surface: overall (default), road, track, indoor")
    p.add_argument("--cat", choices=["DOB", "YOB"], default="DOB",
                   help="age-group scheme: DOB = IAU (U23/23/35/40..., default), "
                        "YOB = German year-of-birth groups (U20/20/30/35...)")
    p.add_argument("--gender", choices=["M", "W", "all"], default="all")
    p.add_argument("--overall-only", action="store_true",
                   help="keep just the open (MOverall/WOverall) rows")
    p.set_defaults(func=cmd_records)

    p = sub.add_parser("rankings", parents=[common], help="international best list")
    p.add_argument("--year", required=True, help="4-digit year or all")
    p.add_argument("--dist", required=True, help="50km, 100km, 24h, 6d, 1000mi ...")
    p.add_argument("--gender", choices=["M", "W"], required=True)
    p.add_argument("--nat", default="all", help="athlete nationality: IOC-3, continent 1-6, all")
    p.add_argument("--cat", help="age group, gender-prefixed: M40, WU23 ...")
    p.add_argument("--label", choices=["IAU"], help="IAU-labelled events only")
    p.add_argument("--tt", choices=["netto", "brutto"],
                   help="time type; DUV defaults to netto, which can differ by seconds from the "
                        "brutto time shown on event results and records pages")
    p.add_argument("--pages", default="1", help="how many 400-row pages to fetch, or all")
    p.add_argument("--primary-only", action="store_true",
                   help="drop an athlete's secondary results (rows ranked '(2)', '(3)' ...)")
    p.set_defaults(func=cmd_rankings)

    p = sub.add_parser("runner", parents=[common], help="profile, PBs and all performances")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--id", help="DUV runner id")
    g.add_argument("--name", help='"Surname" or "Surname, Given" — must match exactly one runner')
    p.set_defaults(func=cmd_runner)

    p = sub.add_parser("search-runner", parents=[common], help="find runner ids")
    p.add_argument("name", help='"Smith" (prefix match) or "Smith, John"')
    p.set_defaults(func=cmd_search_runner)

    p = sub.add_parser("search-event", parents=[common], help="find event ids")
    p.add_argument("name", help='"Spartathlon" (name or town) or "York,100,USA"')
    p.set_defaults(func=cmd_search_event)

    p = sub.add_parser("event", parents=[common], help="finisher list (scraped from HTML)")
    p.add_argument("--id", required=True, help="DUV event id")
    p.add_argument("--pages", default="all", help="how many 2000-row pages to fetch (default all)")
    p.set_defaults(func=cmd_event)

    p = sub.add_parser("event-detail", parents=[common], help="event metadata + editions")
    p.add_argument("--id", required=True, help="DUV event id")
    p.set_defaults(func=cmd_event_detail)

    p = sub.add_parser("calendar", parents=[common], help="races in a year, past or future")
    p.add_argument("--year", default="futur",
                   help="4-digit year, futur, past1, all (all = from today on, like futur)")
    p.add_argument("--country", default="all", help="IOC-3 or continent 1-6")
    p.add_argument("--dist", help="100km, 24h, range code 1/2/4/8, or surface Road/Trail/...")
    p.add_argument("--cups", help="0 all, 1 DUV-Cup, 2 DUV-50km-Cup, 3 DUV-6h-Cup, "
                                  "4 IAU-50k-Trophy, 5 Championships, 6 ECU, 7 Anglo Celtic Plate")
    p.add_argument("--rproof", help="ranking-eligible: 0 all, 1 yes, 2 no")
    p.add_argument("--cupname", help="keep races whose cup/championship label contains this, "
                                     "e.g. 'NC 24h' (national championships), 'IAU', 'DUV-Cup'")
    p.set_defaults(func=cmd_calendar)

    p = sub.add_parser("event-history", parents=[common],
                       help="every edition of a race with its winners, plus course records")
    p.add_argument("--id", required=True, help="DUV event id of any edition")
    p.set_defaults(func=cmd_event_history)

    p = sub.add_parser("multiple-finishers", parents=[common],
                       help="runners ranked by number of finishes of one race series")
    p.add_argument("--id", required=True, help="DUV event id of any edition")
    p.add_argument("--gender", choices=["all", "M", "W"])
    p.set_defaults(func=cmd_multiple_finishers)

    p = sub.add_parser("event-list", parents=[common],
                       help="past events with finisher counts (geteventlist.php)")
    p.add_argument("--year", default="all", help="4-digit year or all")
    p.add_argument("--country", help="venue country: IOC-3 or continent 1-6")
    p.add_argument("--dist", help="100km, 24h, range code 1/2/4/8 ...")
    p.add_argument("--surface", choices=["Road", "Trail", "Stage", "Track", "Indoo", "Elim",
                                         "Backy", "Walk"])
    p.add_argument("--iau", action="store_true", help="IAU-labelled events only")
    p.add_argument("--from", dest="km_from", help="minimum length in km")
    p.add_argument("--to", dest="km_to", help="maximum length in km")
    p.add_argument("--sort", choices=["date", "finishers"], default="date")
    p.add_argument("--club", help="events with finishers from this club (partial name)")
    p.set_defaults(func=cmd_event_list)

    p = sub.add_parser("champions", parents=[common],
                       help="IAU (or German) championship medallists, every edition")
    p.add_argument("--dist", required=True,
                   help="IAU: 100kmWC 100kmEC 100kmAC 24hWC 24hEC 24hAC TrailWC 50kmWC; "
                        "German (--ger): 50km, '50km Track', 100km, '100km Track', 6h, 24h, "
                        "Ultratrail")
    p.add_argument("--cnt", choices=["1", "3", "10"], default="3", help="top N per gender")
    p.add_argument("--ger", action="store_true", help="German championships instead of IAU")
    p.add_argument("--cat", help="German only: age group (JUN, 20, 35 … 90), default all")
    p.set_defaults(func=cmd_champions)

    p = sub.add_parser("stats", parents=[common],
                       help="DUV statistics pages: mileage, longevity, oldest finishers ...")
    p.add_argument("kind", choices=list(STATS_PAGES))
    p.add_argument("--country", help="runner nationality: IOC-3, continent 1-6, or all")
    p.add_argument("--year", help="4-digit year or all")
    p.add_argument("--gender", help="M or W (all where the page allows it)")
    p.add_argument("--dist", help="distance token (female-winners, top-abroad, long-running-races)")
    p.add_argument("--type", help="timespan: 1 wins, 2 finishes >=160 km, 3 >=100 km, "
                                  "4 >=80 km, 5 >=45 km")
    p.add_argument("--years", help="timespan: minimum span 20/25/30/35/40/45 years")
    p.add_argument("--cnt", help="top-abroad: 1 wins, 3 podiums, 10 top tens, 10000 all")
    p.set_defaults(func=cmd_stats)

    p = sub.add_parser("head-to-head", parents=[common],
                       help="two runners' shared races and who finished ahead")
    p.add_argument("--runner", action="append", required=True,
                   help="DUV id or unambiguous name; pass twice")
    p.add_argument("--splits", action="store_true",
                   help="also count split results (intermediate times filed as own events)")
    p.set_defaults(func=cmd_head_to_head)

    p = sub.add_parser("progression", parents=[common],
                       help="best-performance progression over time (record history)")
    p.add_argument("--dist", required=True, help="50km, 100km, 24h, 6d ...")
    p.add_argument("--gender", choices=["M", "W"], required=True)
    p.add_argument("--nat", default="all", help="athlete nationality: IOC-3, continent 1-6, all")
    p.add_argument("--cat", help="age group, gender-prefixed: M40, W55 ...")
    p.set_defaults(func=cmd_progression)

    p = sub.add_parser("get", parents=[common], help="fetch any DUV json/ URL")
    p.add_argument("url", help="full URL or path such as json/msearchevent.php?sname=Sparta")
    p.add_argument("--keep-nls", dest="drop_nls", action="store_false",
                   help="keep the nlsText label dictionary (dropped by default)")
    p.set_defaults(func=cmd_get)
    return top


GLOBAL_FLAGS = ("--format", "--out", "--delay")


def hoist_global_flags(argv: list[str]) -> list[str]:
    """Move --format/--out/--delay given before the subcommand to after it.

    The shared flags live on each subcommand, so `duv.py --delay 2 runner …`
    would otherwise fail; both placements now work.
    """
    front, i = [], 0
    while i < len(argv) and argv[i].startswith("-") and argv[i] not in ("-h", "--help"):
        flag = argv[i].split("=", 1)[0]
        if flag not in GLOBAL_FLAGS:
            break
        take = 1 if "=" in argv[i] else 2
        front += argv[i:i + take]
        i += take
    if not front or i >= len(argv):
        return argv
    return [argv[i]] + front + argv[i + 1:]


def main(argv: list[str] | None = None) -> None:
    argv = hoist_global_flags(sys.argv[1:] if argv is None else argv)
    args = build_parser().parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
