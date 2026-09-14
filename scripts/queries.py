#!/usr/bin/env python3
"""Reusable query helpers over the local tracker database.

Every function returns a pandas DataFrame. Import and call from a notebook,
or run this file directly for a quick console summary.

    from scripts.queries import summary, in_force_by_state
    summary()
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd

DB = Path(__file__).resolve().parent.parent / "data" / "tracker.db"


def _q(sql: str, params: tuple = ()) -> pd.DataFrame:
    if not DB.exists():
        raise SystemExit(f"Missing {DB}. Run: python scripts/build_db.py")
    con = sqlite3.connect(DB)
    try:
        return pd.read_sql_query(sql, con, params=params)
    finally:
        con.close()


def _scope(data_center_only: bool) -> str:
    return "v_data_center" if data_center_only else "moratoria"


def summary(data_center_only: bool = True) -> pd.DataFrame:
    """Headline counts. One row per enacted_status, plus a total."""
    t = _scope(data_center_only)
    df = _q(
        f"""
        SELECT enacted_status                AS status,
               COUNT(*)                      AS instruments,
               COUNT(DISTINCT state_abbrev)  AS states,
               COUNT(DISTINCT jurisdiction)  AS jurisdictions
        FROM {t}
        GROUP BY enacted_status
        ORDER BY instruments DESC
        """
    )
    total = _q(
        f"""
        SELECT 'TOTAL' AS status, COUNT(*) AS instruments,
               COUNT(DISTINCT state_abbrev) AS states,
               COUNT(DISTINCT jurisdiction) AS jurisdictions
        FROM {t}
        """
    )
    return pd.concat([df, total], ignore_index=True)


def in_force_by_state(data_center_only: bool = True) -> pd.DataFrame:
    """Currently in-force instruments (active or extended), ranked by state."""
    t = _scope(data_center_only)
    return _q(
        f"""
        SELECT state, state_abbrev,
               COUNT(*)                     AS in_force,
               COUNT(DISTINCT jurisdiction) AS jurisdictions,
               MIN(date_enacted_iso)        AS earliest,
               MAX(date_enacted_iso)        AS latest
        FROM {t}
        WHERE in_force = 1
        GROUP BY state, state_abbrev
        ORDER BY in_force DESC, state
        """
    )


def jurisdiction_history(name: str, state_abbrev: str | None = None) -> pd.DataFrame:
    """Every instrument for one jurisdiction, oldest first. Partial name match."""
    sql = """
        SELECT date_enacted_iso AS enacted, jurisdiction, jurisdiction_type,
               state_abbrev AS st, enacted_status AS status, duration_kind,
               duration_days, current_end_date_iso AS ends, sectors,
               legal_basis, trigger, outcome
        FROM moratoria
        WHERE jurisdiction LIKE ?
    """
    params: tuple = (f"%{name}%",)
    if state_abbrev:
        sql += " AND state_abbrev = ?"
        params += (state_abbrev.upper(),)
    sql += " ORDER BY date_enacted_iso"
    return _q(sql, params)


def flagged_for_verification(min_verify: int = 1) -> pd.DataFrame:
    """Rows the upstream dataset flagged as needing confirmation.

    These are the reconciliation candidates: anything you would not want to
    put in front of a client without checking the primary document.
    """
    return _q(
        """
        SELECT state_abbrev AS st, jurisdiction, jurisdiction_type,
               date_enacted_iso AS enacted, enacted_status AS status,
               verify_count, cite_count, moratorium_id
        FROM moratoria
        WHERE CAST(COALESCE(verify_count, 0) AS INT) >= ?
        ORDER BY verify_count DESC, cite_count ASC, state_abbrev, jurisdiction
        """,
        (min_verify,),
    )


def timeline_by_month(data_center_only: bool = True) -> pd.DataFrame:
    """Instruments enacted per month, with a running cumulative total."""
    t = _scope(data_center_only)
    df = _q(
        f"""
        SELECT enacted_month AS month, COUNT(*) AS enacted
        FROM {t}
        WHERE enacted_month IS NOT NULL AND enacted_month <> ''
        GROUP BY enacted_month
        ORDER BY enacted_month
        """
    )
    df["cumulative"] = df["enacted"].cumsum()
    return df


def no_end_date(data_center_only: bool = True) -> pd.DataFrame:
    """Instruments with no recorded end date.

    Relevant because the common claim that moratoria are all time-limited
    depends on this column being populated.
    """
    t = _scope(data_center_only)
    return _q(
        f"""
        SELECT state_abbrev AS st, jurisdiction, date_enacted_iso AS enacted,
               enacted_status AS status, duration_kind, duration
        FROM {t}
        WHERE current_end_date_iso IS NULL OR current_end_date_iso = ''
        ORDER BY state_abbrev, jurisdiction
        """
    )


if __name__ == "__main__":
    pd.set_option("display.width", 140)
    print("\n== summary (data center) ==")
    print(summary().to_string(index=False))
    print("\n== top 10 states, in force ==")
    print(in_force_by_state().head(10).to_string(index=False))
    print("\n== last 8 months ==")
    print(timeline_by_month().tail(8).to_string(index=False))
    print("\n== flagged for verification: %d rows ==" % len(flagged_for_verification()))
    print("== no recorded end date: %d rows ==" % len(no_end_date()))
