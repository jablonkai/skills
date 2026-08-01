# DUV shared parameter vocabulary

Different endpoints use different names and different value vocabularies for conceptually similar
fields. Pick the right one for the endpoint you're calling.

Parameter names and values were verified against the live HTML forms — neither is always what the
on-screen label suggests. When in doubt, fetch the page and grep for `name='...'` inside
`<select>`/`<input>` elements, and pull `<option value='...'>` to see the exact tokens.

## Country / nation

One shared scheme, two param names. The same numeric continent codes and IOC-3 country codes work on
every country/nation filter — only the param name changes.

- `geteventlist.php`, `calendar.php`, `getresultclub.php` → `country=`
- `getintbestlist.php` → `nat=` (same value vocabulary, different param name)

Accepted values:

- `all` (or omit the param) → worldwide.
- Numeric continent codes: `1`=Europe, `2`=Asia, `3`=Africa, `4`=North America, `5`=South America,
  `6`=Oceania.
- IOC-3 country codes (e.g. `HUN`, `GER`, `USA`) — work on all four endpoints, including
  `getintbestlist.php`'s `nat=` even though the visible dropdown there only shows the seven
  continental options.

The labels shown in the dropdown (`World`, `Europe`, …) are **not** valid values — `nat=Europe`
silently returns 0 rows; use `nat=1`. Likewise the worldwide selector is `all`, not `World`.

## Distance (`dist`)

One shared vocabulary across `geteventlist.php`, `getintbestlist.php`, and `calendar.php`. Values are
**compact, no spaces, no `+`** — e.g. `100km`, not `100 km` or `100+km`. Bad distance tokens can
produce an explicit invalid-input page, 0 rows, or a broader/odd-looking page heading.

- Fixed distances: `50km`, `50mi`, `100km`, `100mi`
- Time-limited: `6h`, `12h`, `24h`, `48h`, `72h`, `6d`, `10d`
- Multi-day / long: `1000km`, `1000mi` (only `getintbestlist.php`)
- Distance-range codes (geteventlist + calendar only): `1` = 45–79 km, `2` = 80–119 km,
  `4` = 120–179 km, `8` = 180 km+
- `calendar.php` additionally accepts surface tokens in the `dist` slot (same values as `surface`,
  see below): `Road`, `Trail`, `Stage`, `Track`, `Indoo`, `Elim`, `Backy`, `Walk`

## Race surface (`surface` on `geteventlist.php`; `dist` slot on `calendar.php`)

Case-sensitive, truncated tokens exactly as they appear in the form dropdown. Common full-word
variants (`road`, `trail`, `indoor`, `elimination`, `backyard`, `walking`) are NOT recognised and may
return `Error - Invalid input`, be ignored, or return 0 rows. `getresultclub.php` has *no* surface
filter — its `racetype` param is something else entirely.

- `Road` — road race
- `Trail`
- `Stage` — stage race
- `Track`
- `Indoo` — indoor (yes, truncated at 5 chars)
- `Elim` — elimination race
- `Backy` — Backyard Ultra
- `Walk` — ultra-walking

Omit the param or pass `all` for no surface filter.

## Year

- Most endpoints: a 4-digit year (e.g. `2024`) or `all`. `geteventlist.php` years go back to 1798.
- `calendar.php` additionally: `futur` = all upcoming from today, `past1` = 1 year back from today.
  (Plain `past` is *not* recognised — use `past1`.)

## Gender (`getintbestlist.php` only)

`gender=M|W`. The form *label* for the female list renders as "F", but the posted *value* is `W` —
`gender=F` silently returns zero rows.

## Age category (`cat` on `getintbestlist.php`)

Gender-prefixed tokens, paired with the `gender` value:

- Male list (`gender=M`): `all`, `MU23`, `M23`, `M35`, `M40`, `M45`, `M50`, `M55`, `M60`, `M65`,
  `M70`, `M75`, `M80`, `M85`, `M90`
- Female list (`gender=W`): `all`, `WU23`, `W23`, `W35`, … `W90`

## IAU label (`label`)

Filters to IAU-labelled events only. The form *value* differs between the two endpoints — same
concept, different token:

- `geteventlist.php` → `label=Y`
- `getintbestlist.php` → `label=IAU`

Omit the param (or pass empty) for "all events". The dropdown label "IAU-Label" is the visible text,
not the value — passing `label=IAU-Label` silently drops the filter on both endpoints, and `label=Y`
silently drops it on `getintbestlist.php`.
