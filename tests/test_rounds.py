import pytest

from src import rounds
from tests.test_costbasis import trades


def test_sell_first_round():
    # base 100 @10; sell 30 @12, buy back 30 @11 -> +30 minus 2 commissions
    c, r = rounds.cycles_and_rounds(trades((0, 100, 10), (1, -30, 12), (2, 30, 11)))
    assert len(r) == 1 and r.iloc[0].done and r.iloc[0].kind == rounds.SELL_FIRST
    assert r.iloc[0].result == pytest.approx(30 * 12 - 1 - (30 * 11 + 1))
    assert c.iloc[0].open


def test_buy_first_round_and_overshoot():
    # base 100; buy 50 @9, sell 80 @10 -> round closes on 50, extra 30 opens a 倒T
    c, r = rounds.cycles_and_rounds(trades((0, 100, 10), (1, 50, 9), (2, -80, 10)))
    first = r.iloc[0]
    assert first.kind == rounds.BUY_FIRST and first.done
    assert first.result == pytest.approx(-(450 + 1) + (800 - 1) * 50 / 80)
    assert not r.iloc[1].done and r.iloc[1].qty == pytest.approx(30)


def test_cycle_result_is_net_cash():
    c, r = rounds.cycles_and_rounds(trades((0, 10, 10), (1, -5, 12), (2, 5, 11), (3, -10, 13)))
    closed = c[~c.open]
    assert len(closed) == 1
    assert closed.iloc[0].cash == pytest.approx(-101 + 59 - 56 + 129)


def test_buying_more_than_base_is_a_swing_not_a_t():
    # base 20, buy 3000, sell 3000 -> position trade, not 做T
    _, r = rounds.cycles_and_rounds(trades((0, 20, 10), (1, 3000, 10), (2, -3000, 9)))
    assert r.iloc[0].kind == rounds.SWING
