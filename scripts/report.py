#!/usr/bin/env python3
"""Generate the findings report and charts from the local database.

Adds two things the upstream dataset does not provide:

  1. Computed expiration dates. Only 9 of 505 data-center rows carry a parsed
     end date, but 396 carry a duration in days. Enacted date plus duration
     gives a usable expiry for most of the inventory.
  2. An RTO footprint view. Moratoria are tracked by state; grid planning
     happens by RTO. Mapping states onto the PJM footprint is the join nobody
     else publishes.

Writes docs/findings.md, docs/expiry_calendar.png, docs/pjm_share.png.
Re-run after every build_db.py refresh.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "data" / "tracker.db"
DOCS = ROOT / "docs"

AS_OF = pd.Timestamp.today().normalize()

# States wholly or partly inside the PJM footprint.
PJM_STATES = ["PA", "NJ", "MD", "DE", "VA", "WV", "OH", "KY", "NC", "IN", "MI", "IL", "TN", "DC"]
PJM_PARTIAL = {"KY", "NC", "IN", "MI", "IL", "TN"}

NAVY = "#1F3864"
RUST = "#B45309"


def load() -> pd.DataFrame:
    con = sqlite3.connect(DB)
    try:
        df = pd.read_sql_query("SELECT * FROM v_data_center", con)
    finally:
        con.close()

    df["enacted"] = pd.to_datetime(df["date_enacted_iso"], errors="coerce")
    df["duration_days"] = pd.to_numeric(df["duration_days"], errors="coerce")
    df["expiry"] = df["enacted"] + pd.to_timedelta(df["duration_days"], unit="D")
    df["expiry_source"] = "computed"
    stated = pd.to_datetime(df["current_end_date_iso"], errors="coerce")
    df.loc[stated.notna(), "expiry"] = stated[stated.notna()]
    df.loc[stated.notna(), "expiry_source"] = "stated"
    df.loc[df["expiry"].isna(), "expiry_source"] = "none"
    df["in_pjm"] = df["state_abbrev"].isin(PJM_STATES)
    return df


def chart_expiry(inforce: pd.DataFrame) -> None:
    fut = inforce[inforce["expiry"].notna() & (inforce["expiry"] >= AS_OF)]
    by_month = fut.groupby(fut["expiry"].dt.to_period("M")).size()
    by_month = by_month[by_month.index <= pd.Period("2027-12")]

    fig, ax = plt.subplots(figsize=(11, 4.2))
    ax.bar([str(p) for p in by_month.index], by_month.values, color=NAVY)
    ax.set_title("When in-force data center moratoria are scheduled to lapse",
                 fontsize=13, color=NAVY, loc="left")
    ax.set_ylabel("instruments expiring")
    ax.tick_params(axis="x", rotation=60, labelsize=8)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    fig.text(0.01, -0.06,
             f"Expiry computed as enacted date plus stated duration. {len(fut)} of "
             f"{len(inforce)} in-force instruments have a computable date. "
             f"As of {AS_OF:%Y-%m-%d}.",
             fontsize=7.5, color="#595959")
    fig.tight_layout()
    fig.savefig(DOCS / "expiry_calendar.png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    return by_month


def chart_pjm(df: pd.DataFrame) -> None:
    d = df[df["in_pjm"]]
    counts = d.groupby("state_abbrev").size().sort_values(ascending=True)
    colors = [RUST if s in PJM_PARTIAL else NAVY for s in counts.index]

    fig, ax = plt.subplots(figsize=(7, 5))
    ax.barh(counts.index, counts.values, color=colors)
    ax.set_title("Data center moratoria in PJM footprint states",
                 fontsize=13, color=NAVY, loc="left")
    ax.set_xlabel("instruments")
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    fig.text(0.01, -0.04,
             "Navy: state wholly in PJM. Rust: state partly in PJM, so the count "
             "overstates the PJM-relevant share.",
             fontsize=7.5, color="#595959")
    fig.tight_layout()
    fig.savefig(DOCS / "pjm_share.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def write_report(df: pd.DataFrame, by_month: pd.Series) -> None:
    inforce = df[df["in_force"] == 1]
    pjm = df[df["in_pjm"]]
    pjm_core = df[df["state_abbrev"].isin([s for s in PJM_STATES if s not in PJM_PARTIAL])]
    stale = inforce[inforce["expiry"].notna() & (inforce["expiry"] < AS_OF)]
    nodate = inforce[inforce["expiry"].isna()]
    fut = inforce[inforce["expiry"].notna() & (inforce["expiry"] >= AS_OF)]
    peak = by_month.idxmax()

    top_stale = stale.sort_values("expiry")[
        ["state_abbrev", "jurisdiction", "date_enacted_iso", "duration_days", "expiry"]
    ].head(12)
    stale_tbl = "\n".join(
        f"| {r.state_abbrev} | {r.jurisdiction} | {r.date_enacted_iso} | "
        f"{int(r.duration_days)} | {r.expiry:%Y-%m-%d} |"
        for r in top_stale.itertuples()
    )

    pjm_tbl = "\n".join(
        f"| {st} | {int(g['in_force'].sum())} | {len(g)} | "
        f"{'partial' if st in PJM_PARTIAL else 'full'} |"
        for st, g in sorted(pjm.groupby("state_abbrev"),
                            key=lambda kv: -kv[1]["in_force"].sum())
    )

    md = f"""# Findings

Generated from `data/tracker.db` by `scripts/report.py`. As of {AS_OF:%B %-d, %Y}.

Underlying data: Moratorium Nation (Bommarito, 2026), CC-BY-4.0. The analysis and the
two derived columns below are this project's contribution.

---

## 1. Nearly half of U.S. data center moratoria sit in PJM footprint states

{len(pjm)} of {len(df)} data-center moratorium instruments ({100*len(pjm)/len(df):.0f}%) are in
states wholly or partly inside PJM. Restricting to states entirely within the footprint
still gives {len(pjm_core)} instruments.

This is not a coincidence and it is not published anywhere. Moratorium datasets are
organized by state because that is how local government works. Grid planning, load
forecasting, and capacity procurement are organized by RTO. Nobody has mapped one onto the
other, which means nobody has asked the obvious follow-up: what does the densest
concentration of local siting restrictions in the country do to the load forecast of the
RTO underneath it?

| State | In force | Total instruments | Footprint |
|---|---|---|---|
{pjm_tbl}

States marked partial have only part of their territory in PJM, so their counts overstate
the PJM-relevant share. Resolving that requires mapping jurisdictions to transmission
zones, which is Phase 3 work.

![PJM footprint](pjm_share.png)

---

## 2. The source dataset has almost no end dates. They are computable anyway.

Only **9 of {len(df)}** data-center rows carry a parsed end date in
`current_end_date_iso`. But **396** carry a duration in days.

Enacted date plus duration yields a usable expiry for **{int(inforce['expiry'].notna().sum())}
of {len(inforce)}** in-force instruments. That single derived column is the difference
between a dataset that describes the past and one that forecasts.

Anyone quoting duration claims straight from this dataset is quoting a column that is 98%
empty. That is worth knowing before it appears in a client deck.

---

## 3. A forward calendar of when pauses lift

{len(fut)} in-force moratoria have a computed expiry still ahead of them. They do not lapse
evenly.

| Period | Instruments scheduled to lapse |
|---|---|
{chr(10).join(f'| {p} | {v} |' for p, v in by_month.items())}

The peak is **{peak}**, when {int(by_month.max())} instruments are scheduled to expire at once.
That clustering follows mechanically from the mid-2026 adoption wave and standard 6 and
12 month terms, and it means a large block of jurisdictions face the same
renew-or-permanent decision in the same quarter.

For anyone modeling siting risk or load, that is a date to have on a calendar.

![Expiry calendar](expiry_calendar.png)

---

## 4. {len(stale)} instruments are listed as in force but their term has already run out

These carry `enacted_status` of active or extended, yet enacted date plus stated duration
puts expiry in the past. Each one is either an extension not yet captured, a permanent
ordinance that replaced the pause, or a stale row.

| State | Jurisdiction | Enacted | Days | Computed expiry |
|---|---|---|---|---|
{stale_tbl}

Showing the {len(top_stale)} earliest of {len(stale)}. This is the Phase 2 verification queue:
resolving these is exactly the cross-source reconciliation work, and it is the kind of
correction that makes a tracker citable rather than merely available.

A further **{len(nodate)}** in-force instruments have no computable expiry at all.

---

## What this supports

- A column pitch. Items 1 and 3 are the article: the PJM concentration, and a dated
  calendar of when the pauses lift.
- Client work. The expiry calendar answers siting-risk questions directly.
- Phase 2 scope. Item 4 is the verification queue, already enumerated.
"""
    (DOCS / "findings.md").write_text(md)


def main() -> None:
    DOCS.mkdir(exist_ok=True)
    df = load()
    inforce = df[df["in_force"] == 1]
    by_month = chart_expiry(inforce)
    chart_pjm(df)
    write_report(df, by_month)
    print(f"wrote {DOCS/'findings.md'}")
    print(f"wrote {DOCS/'expiry_calendar.png'}")
    print(f"wrote {DOCS/'pjm_share.png'}")


if __name__ == "__main__":
    main()
