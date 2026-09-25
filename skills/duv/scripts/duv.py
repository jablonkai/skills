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


def fetch_text(url: str, delay: float) -> str:
    """GET a URL politely, returning the body with any UTF-8 BOM stripped.

    Some DUV JSON responses start with a BOM, which json.loads rejects, so the
    decode goes through 'utf-8-sig'. urllib is tried first; when the local
    Python has no CA bundle (a common macOS python.org install) the SSL
    verification fails, and curl — which uses the system trust store — takes
    over transparently.
    """
    global _last_request
    wait = delay - (time.monotonic() - _last_request)
    if wait > 0:
        time.sleep(wait)
    _last_request = time.monotonic()

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "duv-skill/1.0"})
        with urllib.request.urlopen(req, timeout=90) as resp:
            return resp.read().decode("utf-8-sig", errors="replace")
    except urllib.error.HTTPError as exc:
        return http_error_body(url, exc.code, exc.read().decode("utf-8-sig", errors="replace"))
    except urllib.error.URLError as exc:
        if not isinstance(exc.reason, ssl.SSLError) or not shutil.which("curl"):
            sys.exit(f"error: cannot reach {url}: {exc.reason}")
    proc = subprocess.run(["curl", "-sSL", "--max-time", "90", "-w", "\n%{http_code}", url],
                          capture_output=True)
    if proc.returncode:
        sys.exit(f"error: curl failed for {url}: {proc.stderr.decode(errors='replace').strip()}")
    body, _, code = proc.stdout.decode("utf-8-sig", errors="replace").rpartition("\n")
    return body if code.startswith("2") else http_error_body(url, int(code), body)


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


def to_csv(rows: list[dict]) -> str:
    if not rows:
        return ""
    import io
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    writer.writerows(rows)
    return buf.getvalue()


def to_markdown(rows: list[dict]) -> str:
    if not rows:
        return "(no rows)\n"
    cols = list(rows[0].keys())
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


def cmd_rankings(args) -> None:
    params = {"year": args.year, "dist": args.dist, "gender": args.gender,
              "nat": args.nat, "cat": args.cat, "label": args.label, "tt": args.tt}
    rows, raw, page = [], [], 1
    while True:
        payload = fetch_json("json/mgetintbestlist.php", {**params, "page": page}, args.delay)
        raw.append(payload)
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
                "age_grade_pct": r.get("AgeGradePct", ""),
            })
        pag = payload.get("Pagination", {})
        max_page = int(pag.get("MaxPage", 1) or 1)
        if page >= max_page or (args.pages != "all" and page >= int(args.pages)):
            if page < max_page:
                print(f"note: stopped after page {page} of {max_page} "
                      f"(use --pages all for the rest)", file=sys.stderr)
            break
        page += 1
    emit(rows, args.format, args.out, raw)


def resolve_runner(args) -> str:
    if args.id:
        return args.id
    hits = fetch_json("json/msearchrunner.php", {"sname": args.name}, args.delay)
    matches = hits.get("Hitlist", [])
    if not matches:
        sys.exit(f"error: no runner matches {args.name!r}; try without accents, or surname only")
    if len(matches) != 1:
        listing = "\n".join(f"  {h['PersonID']:>8}  {h['LastName']}, {h['FirstName']}  "
                            f"{h.get('Nationality', '')}  b.{h.get('YOB') if h.get('YOB') not in (None, '', '0') else '?'}  "
                            f"{h.get('Club', '')}  active {h.get('ActivRange', '')}"
                            for h in matches[:30])
        sys.exit(f"error: {len(matches)} runners match {args.name!r}; pass --id\n{listing}")
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
    payload = fetch_json("json/mcalendar.php", {
        "year": args.year, "country": args.country, "dist": args.dist,
        "cups": args.cups, "rproof": args.rproof}, args.delay)
    rows = [{"date": r.get("Startdate", ""), "event": r.get("EventName", "").strip(),
             "length": r.get("Length") or "", "duration": r.get("Duration") or "",
             "city": r.get("City", ""), "country": r.get("Country", ""),
             "event_type": r.get("EventType", ""), "results": r.get("Results", ""),
             "iau_label": r.get("IAULabel", ""), "record_proof": r.get("RecordProof", ""),
             "event_id": r.get("EventID", "")}
            for r in payload.get("Races", [])]
    hit = payload.get("HitCnt")
    if hit is not None and int(hit) > len(rows):
        print(f"note: DUV reports {hit} races but returned {len(rows)}; narrow the filters",
              file=sys.stderr)
    emit(rows, args.format, args.out, payload)


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
    p.add_argument("--year", default="futur", help="4-digit year, futur, past1, all")
    p.add_argument("--country", default="all", help="IOC-3 or continent 1-6")
    p.add_argument("--dist", help="100km, 24h, range code 1/2/4/8, or surface Road/Trail/...")
    p.add_argument("--cups", help="0 all, 1 DUV-Cup, 2 DUV-50km-Cup, 3 DUV-6h-Cup, "
                                  "4 IAU-50k-Trophy, 5 Championships, 6 ECU, 7 Anglo Celtic Plate")
    p.add_argument("--rproof", help="ranking-eligible: 0 all, 1 yes, 2 no")
    p.set_defaults(func=cmd_calendar)

    p = sub.add_parser("get", parents=[common], help="fetch any DUV json/ URL")
    p.add_argument("url", help="full URL or path such as json/msearchevent.php?sname=Sparta")
    p.add_argument("--keep-nls", dest="drop_nls", action="store_false",
                   help="keep the nlsText label dictionary (dropped by default)")
    p.set_defaults(func=cmd_get)
    return top


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
