# U.S. Data Center Policy Restriction Tracker

**Purpose document**
Laura R. Walter Consulting LLC
September 2026

---

## What this is

A reconciled, sourced database of state and local policy restrictions on data center
development in the United States, paired with a separate tracker for large load capacity.
The two are built independently and joined only where the geography allows it.

It exists to answer one question that nobody can currently answer well: **how much data
center capacity has policy actually stopped, and where?**

## Why it exists

Two reasons, and they pull in the same direction.

**A working tool.** Consulting questions about data center siting, moratoria, and
interconnection arrive constantly and answering them currently means re-searching from
scratch every time. A local database with query helpers turns a two-hour research task into
a two-minute lookup.

**A public credential.** Expert network work is intermediated: someone else owns the client
relationship and sets the rate. Direct clients need a reason to find Laura R. Walter
Consulting specifically. A public, sourced, well-reasoned tracker is that reason. It
demonstrates domain fluency and technical capability at the same time, and it is durable in
a way that a completed consulting engagement is not.

## What makes it different

Several data center moratorium trackers already exist. This project is explicitly
**curation and analysis layered on existing research**, not a from-scratch collection
effort. The value is in two things nobody else has done.

### 1. Cross-source reconciliation

Published counts of U.S. local data center moratoria diverge wildly: 225 in one source, 533
in another, 30 in another, across anywhere from 30 to 42 states depending on who is
counting. The divergence is not error. It is definitional. Sources disagree about whether a
zoning study counts, whether an expired ordinance counts, whether a county-level pause
counts separately from its municipalities.

Nobody has documented where the counts diverge or why. That reconciliation is the first
deliverable, and it is the part a client would pay for, because it is the difference
between a number and a defensible number.

### 2. Historical event chains

For roughly 15 to 20 flagship jurisdictions, the tracker links the full arc:
moratorium enacted, ordinance adopted, moratorium expired, permanent restriction in place.
Existing trackers show a snapshot. This shows the trajectory, which is what anyone trying to
forecast policy risk actually needs.

## The second tracker: large load capacity

Capacity is a separate build with different data properties, and conflating the two would
break both.

Restrictions are discrete legal events attached to a named jurisdiction. Capacity is a
moving, disputed, largely self-reported number, and the same project is routinely counted
three times under three definitions: announced nameplate, interconnection-requested,
under construction, and energized.

There is no demand-side equivalent of the generation interconnection queue. Large load does
not enter through it. The closest available sources are:

- LSE-submitted Large Load Adjustments under PJM Manual 19, which feed the load forecast
- The PJM Load Forecast Report and Load Forecast Supplement
- Utility special contracts and energy service agreements filed at state commissions
- Local zoning and permitting applications

**Working scope: zonal and state level.** That is a deliberate choice, not a limitation.
LLA data is zonal and aggregated, so per-project precision is not available from the
authoritative sources, and pretending otherwise would undermine the credibility the project
is meant to establish.

## The interesting problem

Restrictions are hyper-local: county and municipal. Capacity is zonal and utility-level.
There is no clean join key between them.

That gap is the finding. It is precisely why "how much capacity did the moratoria stop" has
no published answer, and documenting the gap honestly is more valuable than producing a
confident number that cannot be defended.

## Roadmap

| Phase | Scope | Status |
|---|---|---|
| 1 | Local SQLite database and personal query notebook | Complete |
| 2 | Cross-source reconciliation: document where and why counts diverge | Next |
| 3 | Historical event chains for 15 to 20 flagship jurisdictions | Planned |
| 4 | Public interactive map on GitHub Pages using MapLibre | Planned |
| 5 | Large load capacity tracker, zonal and state level | Scoping |

## Current state

Phase 1 is built. The repository contains:

- `scripts/build_db.py` — builds the SQLite database from source CSVs. Idempotent, rebuilds
  from scratch on each run.
- `scripts/queries.py` — reusable query helpers: `summary()`, `in_force_by_state()`,
  `jurisdiction_history()`, `flagged_for_verification()`, `timeline_by_month()`
- `notebooks/explore.ipynb` — exploration notebook with plain-English querying against the
  local dataframe

The repository is committed locally. Pushing it to GitHub is the outstanding item.

## Sources and licensing

Primary upstream source is the Moratorium Nation dataset (Bommarito, 2026), CC-BY-4.0, a
geocoded collection of local moratoria published on GitHub. Additional sources are brought
in for reconciliation. Project code is MIT licensed.

All upstream sources are credited. The project's claim is the reconciliation and the
analysis, not the underlying collection.

## What it feeds

- **RTO Insider column pitch.** The reconciliation work is a publishable article in its own
  right, and a recurring column is the highest-leverage way to turn the tracker into
  inbound.
- **Direct-client credibility.** A working public artifact is the evidence that supports the
  consulting positioning.
- **Practice efficiency.** Every data center policy question answered from the database
  instead of from scratch is billable time recovered.
