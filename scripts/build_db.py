#!/usr/bin/env python3
"""Build the local SQLite database from the Moratorium Nation inventory.

Idempotent: drops and rebuilds every table on each run, so it is always safe
to re-run after refreshing the source CSV.

Source: Moratorium Nation (Bommarito, 2026), CC-BY-4.0
        https://github.com/mjbommar/moratorium-data-2026
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
CSV = ROOT / "data" / "moratorium_inventory.csv"
DB = ROOT / "data" / "tracker.db"

DATE_COLS = ["date_enacted_iso", "current_end_date_iso"]
NUM_COLS = ["latitude", "longitude", "duration_days", "verify_count", "cite_count"]

# Sector strings we treat as data-center relevant.
DC_TOKENS = ("data_center", "data center", "datacenter", "data-center")


def load() -> pd.DataFrame:
    if not CSV.exists():
        raise SystemExit(
            f"Missing {CSV}.\n"
            "Fetch it with:\n"
            "  curl -L -o data/moratorium_inventory.csv \\\n"
            "    https://raw.githubusercontent.com/mjbommar/moratorium-data-2026/main/"
            "data/moratorium_inventory.csv"
        )
    df = pd.read_csv(CSV, dtype=str, keep_default_na=False, na_values=[""])
    df.columns = [c.strip() for c in df.columns]

    for c in NUM_COLS:
        if c in df:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    for c in DATE_COLS:
        if c in df:
            df[c] = pd.to_datetime(df[c], errors="coerce").dt.strftime("%Y-%m-%d")

    sectors = df.get("sectors", pd.Series([""] * len(df))).fillna("").str.lower()
    df["is_data_center"] = sectors.apply(
        lambda s: int(any(tok in s for tok in DC_TOKENS))
    )

    status = df.get("enacted_status", pd.Series([""] * len(df))).fillna("").str.lower()
    df["in_force"] = status.isin(["active", "extended"]).astype(int)

    df["enacted_month"] = df["date_enacted_iso"].str.slice(0, 7)
    return df


def build() -> None:
    df = load()
    DB.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB)
    try:
        con.execute("DROP TABLE IF EXISTS moratoria")
        df.to_sql("moratoria", con, index=False)
        con.executescript(
            """
            CREATE INDEX IF NOT EXISTS ix_state    ON moratoria(state_abbrev);
            CREATE INDEX IF NOT EXISTS ix_juris    ON moratoria(jurisdiction);
            CREATE INDEX IF NOT EXISTS ix_status   ON moratoria(enacted_status);
            CREATE INDEX IF NOT EXISTS ix_month    ON moratoria(enacted_month);
            CREATE INDEX IF NOT EXISTS ix_dc       ON moratoria(is_data_center);

            DROP VIEW IF EXISTS v_data_center;
            CREATE VIEW v_data_center AS
                SELECT * FROM moratoria WHERE is_data_center = 1;

            DROP VIEW IF EXISTS v_in_force;
            CREATE VIEW v_in_force AS
                SELECT * FROM moratoria WHERE in_force = 1;
            """
        )
        con.commit()
    finally:
        con.close()

    total = len(df)
    dc = int(df["is_data_center"].sum())
    force = int(df["in_force"].sum())
    states = df["state_abbrev"].nunique()
    print(f"built {DB}")
    print(f"  {total} instruments | {dc} data-center | {force} in force | {states} states")


if __name__ == "__main__":
    build()
