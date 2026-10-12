"""Cost-basis engine: tax lots, IBKR-style average cost and diluted cost.

Three views of "what did this position cost me":

* tax lots    - the lots that are still open after the broker's lot-matching
                method (FIFO / LIFO / ...) picked which lots each sell closed.
                This is what the tax office cares about.
* lot average - average unit cost of those open lots. This is the "average
                price" IBKR shows on the position screen.
* diluted     - (cash paid in - cash taken out) / shares held, since the
                position was last flat. What Chinese brokers call 摊薄成本:
                profits from trading around a core position (做T) lower it.

Amounts are tracked in the trade currency and, when an `fx` rate function
is given, also in the base currency at the rate on each trade's date.
Commissions are folded into cost.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

EPS = 1e-9


@dataclass
class Lot:
    time: pd.Timestamp
    qty: float
    unit_cost: float  # incl. buy commission
    unit_cost_base: float = 0.0  # same, converted at the opening date's rate


@dataclass
class Position:
    symbol: str
    currency: str
    lots: list[Lot] = field(default_factory=list)
    net_cash_in: float = 0.0  # since last flat; drives diluted cost
    net_cash_in_base: float = 0.0
    realized: float = 0.0

    @property
    def shares(self) -> float:
        return sum(l.qty for l in self.lots)

    @property
    def lot_avg_cost(self) -> float:
        s = self.shares
        return sum(l.qty * l.unit_cost for l in self.lots) / s if abs(s) > EPS else 0.0

    @property
    def diluted_cost(self) -> float:
        s = self.shares
        return self.net_cash_in / s if abs(s) > EPS else 0.0

    @property
    def lot_avg_cost_base(self) -> float:
        s = self.shares
        return sum(l.qty * l.unit_cost_base for l in self.lots) / s if abs(s) > EPS else 0.0

    @property
    def diluted_cost_base(self) -> float:
        s = self.shares
        return self.net_cash_in_base / s if abs(s) > EPS else 0.0


def _order_lots(lots: list[Lot], method: str, target_unit: float | None = None) -> list[Lot]:
    """Order in which a sell consumes open lots.

    SPECIFIC (the user picked lots by hand) can't be replayed from the
    statement, so we take the lots whose unit cost is closest to the basis
    IBKR reported for that sell.
    """
    if method == "SPECIFIC" and target_unit:
        return sorted(lots, key=lambda l: abs(l.unit_cost - target_unit))
    if method == "LIFO":
        return sorted(lots, key=lambda l: l.time, reverse=True)
    if method in ("HIFO", "MAX_LOSS", "MAX_ST_LOSS", "MAX_LT_LOSS"):
        return sorted(lots, key=lambda l: l.unit_cost, reverse=True)
    if method in ("MAX_ST_GAIN", "MAX_LT_GAIN"):
        return sorted(lots, key=lambda l: l.unit_cost)
    return sorted(lots, key=lambda l: l.time)  # FIFO and default


def _close(pos: Position, qty: float, method: str, target_unit: float | None = None):
    """Close `qty` shares (absolute) against open lots.

    Returns the pieces of lots consumed as [(lot, qty used)], each lot's
    value being cost for longs or proceeds received for shorts.
    """
    need, pieces = qty, []
    for lot in _order_lots(pos.lots, method, target_unit):
        if need <= EPS:
            break
        used = min(need, abs(lot.qty))
        pieces.append((Lot(lot.time, used, lot.unit_cost, lot.unit_cost_base), used))
        lot.qty -= used if lot.qty > 0 else -used
        need -= used
    pos.lots = [l for l in pos.lots if abs(l.qty) > EPS]
    return pieces


def run(trades: pd.DataFrame, method: str | None = None, fx=None):
    """Replay trades.

    `method` forces one lot-matching method for every sell (to compare "what
    if"); None uses the method IBKR recorded on each trade, falling back to
    FIFO (IBKR's default). `fx(ccy, time)` -> base-currency units per 1 ccy;
    without it base-currency columns equal the trade currency.

    Returns (positions dict, sells DataFrame).
    """
    positions: dict[str, Position] = {}
    sells = []
    for t in trades.itertuples(index=False):
        pos = positions.setdefault(t.symbol, Position(t.symbol, t.currency))
        cash = t.proceeds + t.commission  # negative when buying
        rate = fx(t.currency, t.time) if fx else 1.0
        held = pos.shares
        if abs(held) <= EPS:
            pos.net_cash_in = pos.net_cash_in_base = 0.0  # new holding cycle
        pos.net_cash_in -= cash
        pos.net_cash_in_base -= cash * rate
        # part of this trade that reduces the existing position
        closing = min(abs(t.qty), abs(held)) if held * t.qty < 0 else 0.0
        opening = abs(t.qty) - closing
        if closing > EPS:
            m = method or t.lot_method or "FIFO"
            target = abs(t.ibkr_basis) / abs(t.qty) if t.ibkr_basis else None
            pieces = _close(pos, closing, m, target)
            lot_value = sum(q * l.unit_cost for l, q in pieces)
            lot_value_base = sum(q * l.unit_cost_base for l, q in pieces)
            close_cash = cash * closing / abs(t.qty)
            # long: cash received - cost; short: proceeds kept - cash paid
            realized = close_cash - lot_value if held > 0 else lot_value + close_cash
            realized_base = (close_cash * rate - lot_value_base) if held > 0 else lot_value_base + close_cash * rate
            pos.realized += realized
            sells.append({
                "time": t.time, "symbol": t.symbol, "currency": t.currency,
                "side": "long" if held > 0 else "short",
                "qty": closing, "method": m, "basis": lot_value,
                "realized": realized, "mixed": opening > EPS,
                "rate": rate, "proceeds_base": close_cash * rate,
                "basis_base": lot_value_base, "realized_base": realized_base,
                "lots": [(l.time, q) for l, q in pieces],
                "ibkr_basis": abs(t.ibkr_basis), "ibkr_realized": t.ibkr_realized,
            })
        if opening > EPS:
            sign = 1 if t.qty > 0 else -1
            unit = abs(cash) / abs(t.qty)  # cost per share (long) or proceeds per share (short)
            pos.lots.append(Lot(t.time, sign * opening, unit, unit * rate))
    sells = pd.DataFrame(sells)
    if not sells.empty:
        sells["basis_diff"] = sells["basis"] - sells["ibkr_basis"]
    return positions, sells


def holdings(positions: dict[str, Position]) -> pd.DataFrame:
    rows = [{
        "symbol": p.symbol, "currency": p.currency, "shares": p.shares,
        "ibkr_avg_cost": p.lot_avg_cost, "diluted_cost": p.diluted_cost,
        "realized_this_cycle": p.lot_avg_cost * p.shares - p.net_cash_in,
        "ibkr_avg_cost_base": p.lot_avg_cost_base, "diluted_cost_base": p.diluted_cost_base,
    } for p in positions.values() if abs(p.shares) > EPS]
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows).sort_values("symbol").reset_index(drop=True)


def open_lots(positions: dict[str, Position]) -> pd.DataFrame:
    return pd.DataFrame([
        {"symbol": p.symbol, "currency": p.currency, "time": l.time, "qty": l.qty,
         "unit_cost": l.unit_cost, "unit_cost_base": l.unit_cost_base}
        for p in positions.values() for l in p.lots
    ])
