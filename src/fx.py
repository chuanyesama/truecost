"""Exchange rates: "how many units of the base currency is 1 unit of X worth
on a given day", for any base currency.

Sources
* ECB euro reference rates (default): ~30 currencies, daily. Any pair is
  derived through EUR: base per X = (base per EUR) / (X per EUR).
* RBA F11.1 (AUD base only): the rates the Australian Taxation Office accepts.

Currencies a source doesn't publish (e.g. TWD in ECB, SEK in RBA) are
derived from the user's own IBKR FX trades crossed with a known rate.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

FX_DIR = Path(__file__).resolve().parents[1] / "data" / "fx"
ECB_CSV = FX_DIR / "ecb-eurofxref-hist.csv"
RBA_CSV = FX_DIR / "f11.1-data.csv"

SOURCES = {"ecb": "ECB euro reference rates", "rba": "RBA F11.1 (AUD only)"}


def load_ecb(path: str | Path = ECB_CSV) -> pd.DataFrame:
    """Daily table, columns = currency, values = units of that currency per 1 EUR."""
    df = pd.read_csv(path, na_values=["N/A"])
    df = df.loc[:, ~df.columns.str.startswith("Unnamed")]
    df["Date"] = pd.to_datetime(df["Date"])
    df = df.set_index("Date").sort_index().dropna(axis=1, how="all")
    df["EUR"] = 1.0
    return df


def ecb_table(base: str, path: str | Path = ECB_CSV) -> pd.DataFrame:
    """Base-currency units per 1 unit of each currency."""
    ecb = load_ecb(path)
    if base not in ecb:
        raise KeyError(f"ECB does not publish {base}")
    return ecb.rdiv(ecb[base], axis=0)  # (base per EUR) / (X per EUR)


def load_rba(path: str | Path = RBA_CSV) -> pd.DataFrame:
    """Daily table indexed by date, columns = currency, values = AUD per 1 unit."""
    raw = pd.read_csv(path, header=None, skiprows=1, encoding="utf-8-sig", dtype=str)
    units = raw[raw[0] == "Units"].iloc[0]
    data = raw[pd.to_datetime(raw[0], format="%d-%b-%Y", errors="coerce").notna()]
    df = pd.DataFrame({"date": pd.to_datetime(data[0], format="%d-%b-%Y")})
    for col, ccy in units.items():
        if col == 0 or not isinstance(ccy, str) or len(ccy) != 3:
            continue
        foreign_per_aud = pd.to_numeric(data[col], errors="coerce")
        df[ccy] = 1 / foreign_per_aud
    return df.set_index("date").sort_index()


def base_table(base: str, source: str = "ecb") -> pd.DataFrame:
    if source == "rba":
        if base != "AUD":
            raise ValueError("RBA rates are only available for an AUD base")
        return load_rba()
    return ecb_table(base)


def implied_rates(trades: pd.DataFrame, table: pd.DataFrame, base: str) -> pd.DataFrame:
    """Daily base-per-unit rates for currencies missing from `table`, from the
    user's FX trades (symbol "X.Y", price = Y per X)."""
    fx = trades[trades["asset"] == "Forex"]
    out = {}
    for t in fx.itertuples(index=False):
        a, b = t.symbol.split(".")
        day = t.time.normalize()
        for known, missing, base_per_missing in (
            (a, b, lambda r: r / t.price),   # 1 b = 1/price a
            (b, a, lambda r: r * t.price),   # 1 a = price b
        ):
            if missing in table.columns or missing == base or t.price <= 0:
                continue
            if known == base:
                r = 1.0
            elif known in table.columns:
                r = table[known].asof(day)
            else:
                continue
            out.setdefault(missing, {})[day] = base_per_missing(r)
    return pd.DataFrame(out).sort_index()


class Rates:
    """rate(ccy, time) -> base units per 1 unit of ccy, using the last known
    rate on or before that day (weekends/holidays roll back)."""

    def __init__(self, table: pd.DataFrame, base: str, extra: pd.DataFrame | None = None):
        self.base = base
        self.table = table if extra is None or extra.empty else table.join(extra, how="outer")
        self.table = self.table.sort_index()
        self._series = {}

    def __call__(self, ccy: str, time: pd.Timestamp) -> float:
        if ccy == self.base:
            return 1.0
        series = self._series.get(ccy)
        if series is None:
            if ccy not in self.table:
                raise KeyError(f"no exchange rate for {ccy}")
            series = self._series[ccy] = self.table[ccy].dropna()
        v = series.asof(pd.Timestamp(time).normalize())
        if pd.isna(v):  # before first known rate: use the earliest
            v = series.iloc[0]
        return float(v)


def build_rates(trades: pd.DataFrame, base: str, source: str = "ecb") -> Rates:
    table = base_table(base, source)
    return Rates(table, base, implied_rates(trades, table, base))
