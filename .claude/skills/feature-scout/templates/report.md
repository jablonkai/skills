# Feature Scout Report — {{PRODUCT_NAME}}

- **Date:** {{YYYY-MM-DD}}
- **Subject:** {{repo path, app name or URL}}
- **Depth:** {{quick | deep}}
- **Focus:** {{focus area, or "whole product"}}
- **Competitors requested by user:** {{names, or "none"}}

> Evidence convention: every claim about a competitor carries a source link.
> Claims that could not be checked against a primary source are tagged
> **(unverified)**. Research that was skipped or failed is listed under
> [Research limits](#research-limits) instead of being filled in from memory.

## 1. Product profile

| | |
|---|---|
| **What it is** | {{one sentence}} |
| **Target users** | {{who, and in what situation}} |
| **Core use cases** | {{3-5 jobs the product is hired for}} |
| **Platforms** | {{…}} |
| **Monetization** | {{pricing / licence / none}} |
| **Recently shipped / in progress** | {{from its own changelog, roadmap, open issues — with links}} |

**Current features**

- {{feature}} — `{{path/to/evidence}}`

**Obvious gaps and rough edges**

- {{gap}} — {{where it shows: file, doc, issue; include rough edges seen in the code}}

## 2. Competitor overview

| Product | Type | Standout features | Users praise | Users complain about | Pricing | Direction of travel | Sources |
|---|---|---|---|---|---|---|---|
| {{name}} | direct / adjacent / best-in-class neighbour / open source | {{…}} | {{…}} | {{…}} | {{…}} | {{recent releases}} | [1](https://SOURCE-URL) |

## 3. Feature matrix

Legend: ✅ has it · 🟡 partial · ❌ missing · ❓ unverified

| Capability | {{Us}} | {{Comp A}} | {{Comp B}} | {{Comp C}} | Class |
|---|---|---|---|---|---|
| {{capability}} | ❌ | ✅ | ✅ | 🟡 | table stakes |

Class is one of: **table stakes** (we lack what most have) ·
**differentiator** (one or two others have it) · **unmet need** (nobody solves it
well) · **UX/quality** (we have it, but worse).

### Signals from our own repo

| Signal | Where | What it suggests |
|---|---|---|
| {{TODO / open issue / half-finished feature}} | `{{file:line}}` or {{#issue}} | {{…}} |

## 4. Top opportunities

Ranked (10 in deep mode; fewer if the evidence supports fewer). Value is 1–5; effort is S (≤ 2 days), M (≤ 2 weeks), L (more); fit is
high / medium / low against the product's core use cases.

| # | Opportunity | Class | Value | Effort | Fit | Evidence |
|---|---|---|---|---|---|---|
| 1 | {{title}} | {{class}} | {{1-5}} | {{S/M/L}} | {{fit}} | [source](https://SOURCE-URL) |

### 1. {{Opportunity title}}

- **Problem:** {{what users cannot do, or do painfully, today}}
- **Proposed solution:** {{concrete, scoped to this product}}
- **Evidence:** {{who does it, what users say}} — [source](https://SOURCE-URL), [source](https://SOURCE-URL)
- **Value:** {{1-5}} — {{why}}
- **Effort:** {{S/M/L}} — {{why, grounded in the current architecture}}
- **Strategic fit:** {{high/medium/low}} — {{why}}
- **Affected code:** `{{path}}`, `{{path}}`
- **Technical risks:** {{…}}

<!-- repeat for 2–10; in quick mode write up the top 5 and leave the rest as rows in the table above -->

## 5. Quick wins (under 1 day)

| Quick win | Why it matters | Where | Evidence |
|---|---|---|---|
| {{…}} | {{…}} | `{{path}}` | [source](https://SOURCE-URL) |

## 6. Rejected ideas

| Idea | Seen in | Why rejected |
|---|---|---|
| {{…}} | {{competitor}} | {{out of scope / low value / too costly / conflicts with positioning}} |

## Research limits

- {{sources that were unreachable, competitors researched only shallowly, claims left unverified, anything skipped because of depth}}

## Sources

1. {{url}} — {{what it supported}}
