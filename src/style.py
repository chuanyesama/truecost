"""Trading-habit profile: measurable habits -> a style label -> evidence-based
observations.

Every observation carries the numbers it is based on, so the user can check
it. Suggestions are about process (costs, sizing, loss limits), never about
which security to buy or sell.

Output is language-neutral: a style code, tag codes and insight keys with
parameters. The UI renders them in the chosen language (app/i18n.py).
"""
from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from . import costbasis as cb
from .rounds import SWING

HOLD_BUCKETS = [(0, 1, "intraday"), (1, 5, "1_5d"), (5, 30, "5_30d"), (30, 1e9, "30d_plus")]


@dataclass
class Insight:
    level: str     # "good" | "warn" | "info"
    key: str       # i18n key: title / evidence / suggestion templates
    params: dict = field(default_factory=dict)


@dataclass
class Profile:
    style: str                 # intraday | short_term | swing | long_term
    tags: list[tuple[str, dict]]
    metrics: dict
    holding_mix: pd.DataFrame  # bucket code, share
    insights: list[Insight] = field(default_factory=list)


def _holding_days(sells: pd.DataFrame) -> pd.Series:
    """Quantity-weighted holding period (days) of the lots each sell closed."""
    def one(x):
        total = sum(q for _, q in x["lots"]) or 1
        return sum((x["time"] - t).total_seconds() / 86400 * q for t, q in x["lots"]) / total
    return sells.apply(one, axis=1)


def _buys_below_cost(trades: pd.DataFrame) -> tuple[int, int]:
    """(# buys that added to an open long, # of those below its average cost)."""
    adds = below = 0
    for sym, g in trades.groupby("symbol"):
        positions: dict = {}
        for i in range(len(g)):
            t = g.iloc[i]
            p = positions.get(sym)
            if t["qty"] > 0 and p is not None and p.shares > 0:
                adds += 1
                below += t["price"] < p.lot_avg_cost
            positions, _ = cb.run(g.iloc[: i + 1])
    return adds, below


def profile(r) -> Profile:
    """r: report.Report"""
    t = r.stock_trades
    rate = [r.rates(c, x) for c, x in zip(t["currency"], t["time"])]
    commission = -float((t["commission"] * rate).sum())
    notional = (t["qty"].abs() * t["price"] * rate)
    comm_rate = (-t["commission"] * rate) / notional.where(notional > 0)
    active_days = t["time"].dt.date.nunique()

    s = r.sells.copy()
    s["hold"] = _holding_days(s) if not s.empty else pd.Series(dtype=float)
    mix = pd.DataFrame([
        {"bucket": name, "share": float(((s["hold"] >= lo) & (s["hold"] < hi)).mean()) if len(s) else 0.0}
        for lo, hi, name in HOLD_BUCKETS
    ])
    intraday = float((s["hold"] < 1).mean()) if len(s) else 0.0
    median_hold = float(s["hold"].median()) if len(s) else 0.0

    c = r.cycles[~r.cycles["open"]].copy()
    c["days"] = (c["end"] - c["start"]).dt.total_seconds() / 86400
    wins, losses = c[c["cash_base"] > 0], c[c["cash_base"] <= 0]
    win_rate = len(wins) / len(c) if len(c) else 0.0
    avg_win = float(wins["cash_base"].mean()) if len(wins) else 0.0
    avg_loss = float(losses["cash_base"].mean()) if len(losses) else 0.0
    gross_loss = -float(losses["cash_base"].sum())
    profit_factor = float(wins["cash_base"].sum()) / gross_loss if gross_loss else float("inf")
    top3_loss_share = float(losses["cash_base"].nsmallest(3).sum() / losses["cash_base"].sum()) if len(losses) >= 3 else 0.0

    rd = r.rounds
    done = rd[rd["done"]] if not rd.empty else rd
    t_rounds = done[done["kind"] != SWING] if len(done) else done
    swings = done[done["kind"] == SWING] if len(done) else done
    t_total = float(t_rounds["result_base"].sum()) if len(t_rounds) else 0.0
    swing_total = float(swings["result_base"].sum()) if len(swings) else 0.0

    adds, below = _buys_below_cost(t)
    trading_net = r.attribution["stock_price"]
    trading_gross = trading_net + commission
    fx_total = r.attribution["stock_fx"] + r.attribution["cash_fx"] + r.attribution["conversion"]

    metrics = {
        "trades": len(t), "active_days": active_days, "trades_per_day": len(t) / max(active_days, 1),
        "intraday_share": intraday, "median_hold_days": median_hold,
        "cycles": len(c), "win_rate": win_rate, "avg_win": avg_win, "avg_loss": avg_loss,
        "payoff": avg_win / -avg_loss if avg_loss else float("inf"), "profit_factor": profit_factor,
        "win_hold_days": float(wins["days"].median()) if len(wins) else 0.0,
        "loss_hold_days": float(losses["days"].median()) if len(losses) else 0.0,
        "top3_loss_share": top3_loss_share,
        "commission": commission, "trading_gross": trading_gross, "trading_net": trading_net,
        "commission_per_trade": commission / max(len(t), 1),
        "costly_trade_share": float((comm_rate > 0.001).mean()),
        "t_rounds": len(t_rounds), "t_total": t_total, "swings": len(swings), "swing_total": swing_total,
        "adds": adds, "adds_below_cost": below / adds if adds else 0.0,
        "shorts": int((s["side"] == "short").sum()) if len(s) else 0,
        "fx_total": fx_total,
    }

    # ---- style ----
    if intraday >= 0.5:
        style = "intraday"
    elif median_hold <= 5:
        style = "short_term"
    elif median_hold <= 30:
        style = "swing"
    else:
        style = "long_term"
    tags: list[tuple[str, dict]] = []
    if len(t_rounds) >= 0.1 * max(len(s), 1):
        tags.append(("rounds", {}))
    if metrics["trades_per_day"] >= 8:
        tags.append(("high_freq", {}))
    if metrics["shorts"] >= 10:
        tags.append(("shorts", {}))
    n_mkts = r.sells["currency"].nunique() if not r.sells.empty else 0
    if n_mkts >= 3:
        tags.append(("markets", {"n": n_mkts}))

    # ---- insights ----
    ins: list[Insight] = []
    if trading_gross > 0 and commission > 0.5 * trading_gross:
        ins.append(Insight("warn", "fees_eat_profit_all" if commission > trading_gross else "fees_eat_profit", {
            "gross": trading_gross, "commission": commission, "net": trading_net,
            "share": commission / trading_gross, "per_trade": metrics["commission_per_trade"],
            "costly": metrics["costly_trade_share"]}))
    elif trading_gross < 0:
        ins.append(Insight("warn", "losing_before_fees", {"gross": trading_gross, "commission": commission}))

    if t_total > 0 > swing_total:
        ins.append(Insight("warn", "rounds_win_swings_lose", {
            "n": len(t_rounds), "total": t_total, "n_swing": len(swings), "swing_total": swing_total}))
    elif t_total < 0 and len(t_rounds) >= 10:
        ins.append(Insight("warn", "rounds_lose", {"n": len(t_rounds), "total": t_total}))
    elif t_total > 0:
        ins.append(Insight("good", "rounds_win", {"n": len(t_rounds), "total": t_total}))

    if top3_loss_share >= 0.4:
        worst = losses.nsmallest(3, "cash_base")
        ins.append(Insight("warn", "big_losses", {
            "worst": [(x.symbol, x.cash_base) for x in worst.itertuples()], "share": top3_loss_share}))

    # closed cycles miss profit still sitting in open positions, so only
    # flag this when trading is actually losing money
    if metrics["profit_factor"] < 1 and trading_net < 0:
        ins.append(Insight("warn", "profit_factor", {
            "win_rate": win_rate, "avg_win": avg_win, "avg_loss": avg_loss, "pf": profit_factor}))

    if metrics["loss_hold_days"] > 1.5 * max(metrics["win_hold_days"], 0.01):
        ins.append(Insight("warn", "disposition", {
            "loss_days": metrics["loss_hold_days"], "win_days": metrics["win_hold_days"]}))
    elif len(losses) and len(wins) and metrics["loss_hold_days"] < metrics["win_hold_days"]:
        ins.append(Insight("good", "cuts_losses", {
            "loss_days": metrics["loss_hold_days"], "win_days": metrics["win_hold_days"],
            "but_big": top3_loss_share >= 0.4}))

    if adds >= 20 and metrics["adds_below_cost"] >= 0.4:
        ins.append(Insight("info", "averaging_down", {"adds": adds, "share": metrics["adds_below_cost"]}))

    by_ccy = r.sells.groupby("currency")["realized_base"].sum() if not r.sells.empty else pd.Series(dtype=float)
    if len(by_ccy) >= 2:
        worst_ccy = by_ccy.idxmin()
        if by_ccy[worst_ccy] < 0 and by_ccy[worst_ccy] < -0.5 * abs(by_ccy.max()):
            ins.append(Insight("warn", "weak_market", {
                "ccy": worst_ccy, "pl": by_ccy[worst_ccy], "best": by_ccy.idxmax(), "best_pl": by_ccy.max()}))

    if fx_total > 0 and fx_total > abs(r.total_pl) * 0.5:
        ins.append(Insight("info", "fx_driven", {"fx": fx_total, "total": r.total_pl}))

    return Profile(style, tags, metrics, mix, ins)
