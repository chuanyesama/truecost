"""Parse an IBKR Activity Statement CSV into tidy tables.

The statement is a "multi-section" CSV: every row starts with the section name
and a row type (Header / Data / SubTotal / Total), and each section carries its
own header row. A section can change header mid-way (e.g. Trades), so we track
the latest header per section.
"""
from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path

import pandas as pd

# IBKR codes for the tax-lot election used on a closing trade
LOT_METHOD_CODES = {
    "FI": "FIFO",
    "LI": "LIFO",
    "HI": "HIFO",
    "SL": "SPECIFIC",
    "ML": "MAX_LOSS",
    "MLL": "MAX_LT_LOSS",
    "MLG": "MAX_LT_GAIN",
    "MSG": "MAX_ST_GAIN",
    "MSL": "MAX_ST_LOSS",
    "LT": None,  # long-term P/L marker, not an election
}


def read_sections(path: str | Path) -> dict[str, pd.DataFrame]:
    """Return {section name: DataFrame of its Data rows}."""
    headers: dict[str, list[str]] = {}
    rows: dict[str, list[dict]] = defaultdict(list)
    with open(path, encoding="utf-8-sig", newline="") as f:
        for rec in csv.reader(f):
            if len(rec) < 2:
                continue
            section, kind, *rest = rec
            if kind == "Header":
                headers[section] = rest
            elif kind == "Data" and section in headers:
                rows[section].append(dict(zip(headers[section], rest)))
    return {s: pd.DataFrame(r) for s, r in rows.items()}


def _num(s: pd.Series) -> pd.Series:
    return pd.to_numeric(s.astype(str).str.replace(",", ""), errors="coerce").fillna(0.0)


def _lot_method(code: str) -> str | None:
    for c in str(code).split(";"):
        if LOT_METHOD_CODES.get(c):
            return LOT_METHOD_CODES[c]
    return None


def load_trades(path: str | Path) -> pd.DataFrame:
    """Standard trade table: one row per execution, sorted by time.

    Columns: time, asset, currency, symbol, qty (+buy / -sell), price,
    proceeds, commission (negative = paid), ibkr_basis, ibkr_realized,
    code, lot_method.
    """
    t = read_sections(path)["Trades"]
    t = t[t["DataDiscriminator"] == "Order"].copy()
    out = pd.DataFrame({
        "time": pd.to_datetime(t["Date/Time"], format="%Y-%m-%d, %H:%M:%S"),
        "asset": t["Asset Category"],
        "currency": t["Currency"],
        "symbol": t["Symbol"],
        "qty": _num(t["Quantity"]),
        "price": _num(t["T. Price"]),
        "proceeds": _num(t["Proceeds"]),
        "commission": _num(t["Comm/Fee"]),
        "ibkr_basis": _num(t["Basis"]),
        "ibkr_realized": _num(t["Realized P/L"]),
        "code": t["Code"].fillna(""),
    })
    out["lot_method"] = out["code"].map(_lot_method)
    return out.sort_values("time", kind="stable").reset_index(drop=True)


def load_stock_trades(path: str | Path) -> pd.DataFrame:
    t = load_trades(path)
    t = t[t["asset"] == "Stocks"].reset_index(drop=True)
    return apply_commission_adjustments(t, read_sections(path).get("Commission Adjustments"))


def apply_commission_adjustments(trades: pd.DataFrame, adj: pd.DataFrame | None) -> pd.DataFrame:
    """IBKR sometimes computes commission after the trade is reported and books
    it separately ("Commission Computed After Trade Reported (SYM)"). Fold each
    one into the nearest-in-time trade of that symbol and currency."""
    if adj is None or adj.empty:
        return trades
    trades = trades.copy()
    sym = adj["Description"].str.extract(r"\(([^)]+)\)\s*$")[0]
    for s, ccy, date, amt in zip(sym, adj["Currency"], pd.to_datetime(adj["Date"]), _num(adj["Amount"])):
        cand = trades[(trades["symbol"] == s) & (trades["currency"] == ccy)]
        if cand.empty or amt == 0:
            continue
        i = (cand["time"] - date).abs().idxmin()
        trades.loc[i, "commission"] += amt
    return trades


def account_info(path: str | Path) -> dict[str, str]:
    a = read_sections(path).get("Account Information")
    return {} if a is None else dict(zip(a["Field Name"], a["Field Value"]))
