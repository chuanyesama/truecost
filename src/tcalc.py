"""Round-trip (做 T) calculators, the same maths as docs/calculator.html.

Plan: before selling q of n shares at s, which buy-back price b lowers the cost? A round trip moves
q·(s − b) − 2·fee out of the position, so the cost per share becomes (n·c − gain) / n.

Review: given a first purchase and finished rounds, compare IBKR's first-in-first-out lot cost with
the real cost (money still in the position ÷ shares held). Fees are ignored here, as on the site.
"""
from __future__ import annotations

from dataclasses import dataclass


def ibkr_fixed_fee(q: float, price: float) -> float:
    """IBKR Pro fixed pricing for US stocks: 0.005 a share, min 1, max 1% of the trade value."""
    return min(max(1.0, 0.005 * q), 0.01 * q * price)


@dataclass
class Plan:
    shares: float          # n, held now
    cost: float            # c, cost per share now
    qty: float             # q, shares to sell (capped at n)
    sell: float            # s, sell price
    fee: float             # per order; a round trip pays it twice

    def __post_init__(self):
        self.qty = min(max(self.qty, 0.0), self.shares)

    @property
    def fees(self) -> float:
        return 2 * self.fee

    @property
    def ok(self) -> bool:
        return self.shares > 0 and self.qty > 0 and self.sell > 0

    @property
    def break_even(self) -> float:
        """Highest buy-back price at which the round trip doesn't lose money."""
        return self.sell - self.fees / self.qty

    def gain(self, buy_back: float) -> float:
        return self.qty * (self.sell - buy_back) - self.fees

    def new_cost(self, buy_back: float) -> float:
        return (self.shares * self.cost - self.gain(buy_back)) / self.shares

    def buy_back_for(self, target_cost: float) -> float:
        """Highest buy-back price that brings the cost down to target_cost (≤ 0: not possible in one round)."""
        return self.sell - (self.shares * (self.cost - target_cost) + self.fees) / self.qty


@dataclass
class Review:
    ibkr_cost: float       # first-in-first-out average of the lots still held
    real_cost: float       # money still in the position ÷ shares held (≤ 0: zero cost)
    cash_in: float         # money still in the position
    shares: float
    rounds: int            # rounds that actually sold something


def review(shares: float, price: float, rounds: list[tuple[float, float, float]]) -> Review:
    """rounds: (shares sold, sell price, buy-back price) in order."""
    lots = [[shares, price]] if shares > 0 else []
    cash = shares * price
    done = 0
    for q, s, b in rounds:
        sell = min(max(q, 0.0), sum(l[0] for l in lots))
        if sell <= 0:
            continue
        left = sell
        while left > 1e-9 and lots:
            take = min(left, lots[0][0])
            lots[0][0] -= take
            left -= take
            if lots[0][0] <= 1e-9:
                lots.pop(0)
        lots.append([sell, b])
        cash += sell * (b - s)
        done += 1
    held = sum(l[0] for l in lots)
    ibkr = sum(q * p for q, p in lots) / held if held else 0.0
    return Review(ibkr_cost=ibkr, real_cost=cash / held if held else 0.0, cash_in=cash, shares=held, rounds=done)
