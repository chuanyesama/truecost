"""Whole-account P/L in the base currency, split into where it came from.

    total P/L = ending NAV - net deposits
              = stock trading P/L (realized + unrealized, in base currency)
              + FX P/L on foreign cash held
              + income and fees (interest, dividends, withholding, other fees)

The FX piece is what a broker app hides: while you hold USD (cash or shares),
its base-currency value moves with the exchange rate even if you never trade.

Foreign cash is tracked as a pool per currency at average base cost: money
coming in is booked at that day's rate, money going out releases cost at the
pool's average, and the difference is realized FX P/L. Whatever is still held
at the end is marked at the closing rate (unrealized FX P/L).
"""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from . import ingest

INCOME_SECTIONS = {
    "Dividends": "Date",
    "Withholding Tax": "Date",
    "Interest": "Date",
    "Fees": "Date",
}


def base_commission_column(columns) -> str | None:
    """IBKR names it after the base currency, e.g. "Comm in AUD"."""
    return next((c for c in columns if str(c).startswith("Comm in ")), None)


def cash_flows(path, base: str) -> pd.DataFrame:
    """Every movement of cash, one row per (time, currency, amount, kind)."""
    sec = ingest.read_sections(path)
    flows = []

    t = sec["Trades"]
    t = t[t["DataDiscriminator"] == "Order"]
    num = ingest._num
    time = pd.to_datetime(t["Date/Time"], format="%Y-%m-%d, %H:%M:%S")
    for when, asset, ccy, sym, qty, proceeds, comm, comm_base in zip(
        time, t["Asset Category"], t["Currency"], t["Symbol"], num(t["Quantity"]),
        num(t["Proceeds"]), num(t.get("Comm/Fee", pd.Series(dtype=str))).reindex(t.index, fill_value=0),
        num(t.get(base_commission_column(t.columns), pd.Series(dtype=str))).reindex(t.index, fill_value=0),
    ):
        if asset == "Forex":
            bought = sym.split(".")[0]
            flows += [(when, bought, qty, "fx"), (when, ccy, proceeds, "fx"), (when, base, comm_base, "fee")]
        else:
            flows.append((when, ccy, proceeds + comm, "trade"))

    ca = sec.get("Commission Adjustments")
    if ca is not None:
        ca = ca[ca["Currency"].str.len() == 3]
        for ccy, d, amt in zip(ca["Currency"], ca["Date"], num(ca["Amount"])):
            flows.append((pd.Timestamp(d), ccy, amt, "trade"))

    dw = sec.get("Deposits & Withdrawals")
    if dw is not None:
        dw = dw[dw["Currency"].str.len() == 3]
        for ccy, d, amt in zip(dw["Currency"], dw["Settle Date"], num(dw["Amount"])):
            flows.append((pd.Timestamp(d), ccy, amt, "deposit"))

    for name, date_col in INCOME_SECTIONS.items():
        s = sec.get(name)
        if s is None:
            continue
        s = s[s["Currency"].str.len() == 3]
        for ccy, d, amt in zip(s["Currency"], s[date_col], num(s["Amount"])):
            flows.append((pd.Timestamp(d), ccy, amt, "income"))

    df = pd.DataFrame(flows, columns=["time", "currency", "amount", "kind"])
    return df[df["amount"] != 0].sort_values("time", kind="stable").reset_index(drop=True)


@dataclass
class Pool:
    balance: float = 0.0
    cost_base: float = 0.0  # base-currency cost of the balance (negative balance = borrowed)


def cash_fx(flows: pd.DataFrame, rates, end: pd.Timestamp, base: str, end_rates: dict | None = None) -> pd.DataFrame:
    """Realized and unrealized FX P/L per foreign currency. Flows are booked at
    `rates`; what is left is marked at `end_rates` (e.g. the broker's close)
    when given, else at `rates` on `end`."""
    pools: dict[str, Pool] = {}
    realized: dict[str, float] = {}
    for f in flows[flows["currency"] != base].itertuples(index=False):
        p = pools.setdefault(f.currency, Pool())
        value = f.amount * rates(f.currency, f.time)
        same_direction = p.balance == 0 or (p.balance > 0) == (f.amount > 0)
        if same_direction:
            p.balance += f.amount
            p.cost_base += value
            continue
        # reducing the pool: release cost at average, book the difference
        used = min(abs(f.amount), abs(p.balance))
        avg = p.cost_base / p.balance
        sign = 1 if f.amount > 0 else -1
        realized[f.currency] = realized.get(f.currency, 0.0) + (
            -sign * used * rates(f.currency, f.time) + sign * used * avg)
        p.balance += sign * used
        p.cost_base += sign * used * avg
        rest = f.amount - sign * used
        if abs(rest) > 1e-9:  # flipped through zero
            p.balance += rest
            p.cost_base += rest * rates(f.currency, f.time)
    rows = []
    for ccy, p in pools.items():
        rate_end = (end_rates or {}).get(ccy) or rates(ccy, end)
        rows.append({
            "currency": ccy, "balance": p.balance, "rate_end": rate_end,
            "value_base": p.balance * rate_end,
            "realized_fx": realized.get(ccy, 0.0),
            "unrealized_fx": p.balance * rate_end - p.cost_base,
        })
    return pd.DataFrame(rows)


def income_base(flows: pd.DataFrame, rates) -> float:
    inc = flows[flows["kind"].isin(["income", "fee"])]
    return float(sum(a * rates(c, t) for t, c, a in zip(inc["time"], inc["currency"], inc["amount"])))


def net_deposits_base(flows: pd.DataFrame, rates) -> float:
    d = flows[flows["kind"] == "deposit"]
    return float(sum(a * rates(c, t) for t, c, a in zip(d["time"], d["currency"], d["amount"])))


def conversion_result(flows: pd.DataFrame, rates) -> float:
    """Gain (usually a small loss) from converting currencies at the broker's
    price instead of the reference rate: what you received minus what you gave
    up, both valued at that day's reference rate."""
    fx = flows[flows["kind"] == "fx"]
    return float(sum(a * rates(c, t) for t, c, a in zip(fx["time"], fx["currency"], fx["amount"])))


def end_rates_from_statement(path, base: str) -> dict[str, float]:
    """IBKR's own closing rates (base per unit), so end values match its NAV."""
    fb = ingest.read_sections(path).get("Forex Balances")
    if fb is None:
        return {}
    fb = fb[fb["Description"].str.len() == 3]
    return {d: float(p) for d, p in zip(fb["Description"], ingest._num(fb["Close Price"])) if d != base}
