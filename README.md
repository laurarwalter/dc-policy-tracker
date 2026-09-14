# U.S. Data Center Policy Restriction Tracker

A reconciled, sourced database of state and local policy restrictions on data center
development in the United States.

Maintained by [Laura R. Walter Consulting LLC](https://laurarwalter.com). Full rationale in
[`docs/purpose.md`](docs/purpose.md).

## Why this exists

Published counts of U.S. local data center moratoria diverge wildly, and the divergence is
definitional rather than accidental. Sources disagree about whether a proposal counts,
whether an expired ordinance counts, whether a county pause counts separately from its
municipalities. Nobody has documented where the counts diverge or why.

That reconciliation is the product. This repository is the working substrate for it.

## Quick start

```bash
pip install -r requirements.txt

# fetch the upstream inventory
curl -L -o data/moratorium_inventory.csv \
  https://raw.githubusercontent.com/mjbommar/moratorium-data-2026/main/data/moratorium_inventory.csv

python scripts/build_db.py     # builds data/tracker.db
python scripts/queries.py      # console summary
jupyter notebook notebooks/explore.ipynb
```

`build_db.py` is idempotent. It drops and rebuilds every table, so re-run it any time the
upstream CSV is refreshed.

## What is in the database

One table, `moratoria`, one row per moratorium instrument, plus two views:

| Object | Contents |
|---|---|
| `moratoria` | All 533 instruments across every tracked sector |
| `v_data_center` | The 505 instruments naming data centers |
| `v_in_force` | Instruments whose `enacted_status` is active or extended |

Two derived columns are added at build time:

- `is_data_center` — 1 where the `sectors` list names data centers
- `in_force` — 1 where `enacted_status` is active or extended
- `enacted_month` — `YYYY-MM`, for timeline work

## Query helpers

From `scripts/queries.py`, all returning DataFrames:

| Function | Returns |
|---|---|
| `summary()` | Instrument counts by status, with states and jurisdictions |
| `in_force_by_state()` | In-force instruments ranked by state |
| `jurisdiction_history(name, state)` | Every instrument for one jurisdiction, oldest first |
| `flagged_for_verification()` | Rows upstream flagged as needing confirmation |
| `timeline_by_month()` | Instruments enacted per month, with cumulative total |
| `no_end_date()` | Instruments with no parsed end date |

Each takes `data_center_only=True` by default; pass `False` for the full inventory.

## Counting rules, stated plainly

The upstream dataset counts **moratorium instruments**, not moratoria currently in force,
on the reasoning that a publicly proposed moratorium is politically meaningful even if it
never passes. That choice is a large part of why published headline numbers differ.

This repository keeps that convention and exposes the filter rather than hiding it. Use
`v_in_force` or `in_force_by_state()` when the question is what is actually in effect today.

Two caveats worth carrying into any client-facing use:

- The most recent month in `timeline_by_month()` is almost always incomplete and should
  never be read as a trend.
- A large share of rows carry no parsed end date. Check `no_end_date()` before repeating the
  common claim that these pauses are uniformly short and self-expiring.

## Roadmap

| Phase | Scope | Status |
|---|---|---|
| 1 | Local SQLite database and query notebook | Complete |
| 2 | Cross-source reconciliation: document where and why counts diverge | Next |
| 3 | Historical event chains for 15 to 20 flagship jurisdictions | Planned |
| 4 | Public interactive map on GitHub Pages using MapLibre | Planned |
| 5 | Large load capacity tracker, zonal and state level | Scoping |

## Sources and licensing

Upstream data: **Moratorium Nation** (Bommarito, 2026), CC-BY-4.0.
<https://github.com/mjbommar/moratorium-data-2026>

Code in this repository is MIT licensed. The upstream dataset retains its own license and is
credited in full. The contribution here is the reconciliation and the analysis, not the
underlying collection.
