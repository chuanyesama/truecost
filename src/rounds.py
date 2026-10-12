"""Holding cycles and round trips around a core position (做T), independent of any lot-matching method.

* cycle   - from flat (0 shares) back to flat. Its result is simply all cash
            in minus all cash out; no lot method needed.
* round   - inside a cycle, the position leaves a base level and comes back:
              sell_first: 100 -> sell 30 -> buy 30 -> back to 100
              buy_first:  100 -> buy 30  -> sell 30 -> back to 100
            Result = cash from the round's trades. A trade that overshoots the
            base closes the round with part of its quantity and the rest
            starts the next round.
* timeline - after every trade: shares, IBKR-style lot average, diluted cost.

* swing   - a buy-first "round" larger than the base (e.g. hold 20, buy 3000,
            sell 3000) is really a position trade, not trading around a core
            position, and is labelled separately so it doesn't distort stats.

Long-only cycles are what most users do; a cycle that goes short is reported
as a cycle but not split into T rounds.
"""
from __future__ import annotations

import pandas as pd

from . import costbasis as cb

EPS = 1e-9
SELL_FIRST, BUY_FIRST, SWING = "sell_first", "buy_first", "swing"


def _cash(t) -> float:
    return t.proceeds + t.commission  # + received, - paid


def cycles_and_rounds(trades: pd.DataFrame, fx=None):
    """Return (cycles, rounds) DataFrames for every symbol in `trades`."""
    rate = fx or (lambda c, t: 1.0)
    cycles, rounds = [], []
    for sym, g in trades.groupby("symbol", sort=False):
        pos, cyc, rnd = 0.0, None, None
        for t in g.itertuples(index=False):
            cash, r = _cash(t), rate(t.currency, t.time)
            if cyc is None:
                cyc = {"symbol": sym, "currency": t.currency, "start": t.time, "trades": 0,
                       "max_shares": 0.0, "cash": 0.0, "cash_base": 0.0, "bought": 0.0}
            cyc["trades"] += 1
            cyc["cash"] += cash
            cyc["cash_base"] += cash * r
            cyc["bought"] += max(t.qty, 0)

            # --- T rounds (long positions only) ---
            remaining, new_pos = t.qty, pos + t.qty
            while abs(remaining) > EPS and pos > EPS and new_pos > -EPS:
                if rnd is None:
                    rnd = {"symbol": sym, "currency": t.currency, "start": t.time, "base": pos,
                           "kind": SELL_FIRST if remaining < 0 else BUY_FIRST,
                           "dir": -1 if remaining < 0 else 1, "qty": 0.0,
                           "cash": 0.0, "cash_base": 0.0, "trades": 0}
                # how far this trade can go before the position is back at base
                to_base = rnd["base"] - pos  # signed distance back to base
                back = rnd["dir"] * remaining < 0  # moving toward base
                use = remaining
                if back and abs(remaining) > abs(to_base):
                    use = to_base
                share = use / t.qty
                rnd["cash"] += cash * share
                rnd["cash_base"] += cash * share * r
                rnd["trades"] += 1
                if not back:
                    rnd["qty"] += abs(use)
                pos += use
                remaining -= use
                if back and abs(pos - rnd["base"]) <= EPS:
                    rnd.update(end=t.time, done=True)
                    rounds.append(rnd)
                    rnd = None
            pos += remaining  # opening from flat or going short: not a T
            cyc["max_shares"] = max(cyc["max_shares"], abs(pos))

            if abs(pos) <= EPS:
                if rnd is not None:  # cleared while a round was open: it ends with the cycle
                    rnd.update(end=t.time, done=False)
                    rounds.append(rnd)
                    rnd = None
                cyc.update(end=t.time, open=False, shares=0.0)
                cycles.append(cyc)
                cyc, pos = None, 0.0
        if cyc is not None:
            cyc.update(end=pd.NaT, open=True, shares=pos)
            cycles.append(cyc)
        if rnd is not None:
            rnd.update(end=pd.NaT, done=False)
            rounds.append(rnd)

    cycles = pd.DataFrame(cycles)
    rounds = pd.DataFrame(rounds)
    if not rounds.empty:
        rounds["result"] = rounds["cash"].where(rounds["done"])
        rounds["result_base"] = rounds["cash_base"].where(rounds["done"])
        rounds["per_share"] = rounds["result"] / rounds["qty"]
        # buying more than the base and selling it back is a position trade,
        # not trading around a core position
        swing = (rounds["kind"] == BUY_FIRST) & (rounds["qty"] > rounds["base"] + EPS)
        rounds.loc[swing, "kind"] = SWING
        rounds = rounds.drop(columns=["dir"])
    return cycles, rounds


def timeline(trades: pd.DataFrame, symbol: str, fx=None) -> pd.DataFrame:
    """Shares, lot-average cost and diluted cost after every trade of one symbol."""
    g = trades[trades["symbol"] == symbol]
    rows = []
    for i in range(len(g)):
        pos, _ = cb.run(g.iloc[: i + 1], fx=fx)
        p = pos[symbol]
        t = g.iloc[i]
        rows.append({
            "time": t["time"], "side": "buy" if t["qty"] > 0 else "sell", "qty": abs(t["qty"]),
            "price": t["price"], "shares": p.shares,
            "ibkr_avg_cost": p.lot_avg_cost if abs(p.shares) > EPS else None,
            "diluted_cost": p.diluted_cost if abs(p.shares) > EPS else None,
        })
    return pd.DataFrame(rows)
