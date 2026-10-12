"""Where the trading costs went, and what could have been saved.

Costs counted: commissions on stock trades (including exchange/regulatory
fees and transaction taxes IBKR folds into Comm/Fee) and commissions on
currency conversions. All in the base currency at the trade-date rate.

Savings scenarios are estimates and are labelled as such in the UI:
* merge   - same symbol, same direction, within N minutes, executed as one
            order would pay one minimum instead of several.
* tiered  - IBKR Pro Tiered for US stocks: USD 0.0035/share (min 0.35,
            max 1% of value) plus approximate pass-through exchange and
            clearing fees. Fixed is USD 0.005/share, min 1.00.
"""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from . import ingest, ledger

SIZE_BUCKETS = [0, 500, 2000, 5000, 20000, float("inf")]
SIZE_LABELS = ["< 500", "500–2k", "2k–5k", "5k–20k", "> 20k"]  # in base currency

TIERED_PER_SHARE, TIERED_MIN = 0.0035, 0.35
TIERED_PASS_THROUGH = 0.0032  # exchange + clearing + regulatory, rough per-share average
FIXED_MIN = 1.0


@dataclass
class CostReport:
    total: float              # base currency, all trading costs
    stock: float
    fx_conversion: float
    trades: pd.DataFrame      # per stock trade: comm_base, notional_base, size bucket
    by_market: pd.DataFrame
    by_size: pd.DataFrame
    by_month: pd.DataFrame
    by_symbol: pd.DataFrame
    usd_min_share: float      # share of USD orders that paid the 1.00 minimum
    usd_per_share: float      # median commission per share, USD orders
    merge_orders: int         # orders that could have been merged away
    merge_saving: float       # base currency
    tiered_actual_usd: float
    tiered_estimate_usd: float
    tiered_saving: float      # base currency
    days: int


def _fx_conversion_commission(statement) -> float:
    t = ingest.read_sections(statement)["Trades"]
    fx = t[(t["DataDiscriminator"] == "Order") & (t["Asset Category"] == "Forex")]
    col = ledger.base_commission_column(fx.columns)
    if fx.empty or col is None:
        return 0.0
    return -float(ingest._num(fx[col]).sum())


def _mergeable(t: pd.DataFrame, minutes: int) -> pd.Series:
    """True for orders that follow another same-symbol, same-side order within
    `minutes` - they could have been one order."""
    t = t.sort_values("time")
    side = t["qty"].gt(0)
    prev_time = t.groupby([t["symbol"], side])["time"].shift()
    return ((t["time"] - prev_time) <= pd.Timedelta(minutes=minutes)).reindex(t.index, fill_value=False)


def analyse(r, statement, merge_minutes: int = 10) -> CostReport:
    t = r.stock_trades.copy()
    t["rate"] = [r.rates(c, x) for c, x in zip(t["currency"], t["time"])]
    t["comm_base"] = -t["commission"] * t["rate"]
    t["notional_base"] = t["qty"].abs() * t["price"] * t["rate"]
    t["bps"] = 1e4 * t["comm_base"] / t["notional_base"].where(t["notional_base"] > 0)
    t["size"] = pd.cut(t["notional_base"], SIZE_BUCKETS, labels=SIZE_LABELS, right=False)
    t["market"] = t["currency"]

    def summary(by, sort=True):
        g = t.groupby(by, observed=True)
        out = pd.DataFrame({
            "orders": g.size(), "commission": g["comm_base"].sum(),
            "per_order": g["comm_base"].mean(),
            "bps": 1e4 * g["comm_base"].sum() / g["notional_base"].sum(),
        }).reset_index()
        return out.sort_values("commission", ascending=False) if sort else out

    usd = t[t["currency"] == "USD"]
    usd_comm = -usd["commission"]
    q = usd["qty"].abs()
    tiered = ((TIERED_PER_SHARE * q).clip(lower=TIERED_MIN)
              .clip(upper=0.01 * q * usd["price"]) + TIERED_PASS_THROUGH * q)
    usd_rate = usd["rate"]

    mergeable = _mergeable(t, merge_minutes)
    # merging saves the minimum charge that each extra small order paid
    small_extra = t[mergeable & (t["comm_base"] <= t["rate"] * FIXED_MIN * 1.06)]

    stock = float(t["comm_base"].sum())
    fx_conv = _fx_conversion_commission(statement)
    return CostReport(
        total=stock + fx_conv, stock=stock, fx_conversion=fx_conv, trades=t,
        by_market=summary("market"), by_size=summary("size", sort=False),
        by_month=summary(t["time"].dt.to_period("M").astype(str).rename("month"), sort=False),
        by_symbol=summary("symbol"),
        usd_min_share=float(((usd_comm > 0.99) & (usd_comm < 1.06)).mean()) if len(usd) else 0.0,
        usd_per_share=float((usd_comm / q).median()) if len(usd) else 0.0,
        merge_orders=len(small_extra), merge_saving=float(small_extra["comm_base"].sum()),
        tiered_actual_usd=float(usd_comm.sum()), tiered_estimate_usd=float(tiered.sum()),
        tiered_saving=float(((usd_comm - tiered) * usd_rate).sum()),
        days=max((t["time"].max() - t["time"].min()).days, 1),
    )
