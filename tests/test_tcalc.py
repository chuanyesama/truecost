import pytest

from src import tcalc


def test_plan_matches_the_site():
    p = tcalc.Plan(shares=1000, cost=100, qty=300, sell=110, fee=tcalc.ibkr_fixed_fee(300, 110))
    assert p.fee == pytest.approx(1.5)
    assert p.break_even == pytest.approx(109.99)
    assert p.gain(104.5) == pytest.approx(1647)
    assert p.new_cost(104.5) == pytest.approx(98.353)
    assert p.buy_back_for(97) == pytest.approx(99.99)
    assert p.new_cost(p.break_even) == pytest.approx(100)


def test_plan_caps_qty_and_flags_impossible_targets():
    assert tcalc.Plan(shares=100, cost=50, qty=500, sell=55, fee=1).qty == 100
    p = tcalc.Plan(shares=1000, cost=50, qty=100, sell=55, fee=1)
    assert p.buy_back_for(0) < 0          # selling a tenth can't reach zero cost in one round


def test_ibkr_fee_minimum_and_cap():
    assert tcalc.ibkr_fixed_fee(10, 100) == 1           # minimum
    assert tcalc.ibkr_fixed_fee(1000, 100) == 5         # per share
    assert tcalc.ibkr_fixed_fee(10, 5) == pytest.approx(0.5)   # 1% of a tiny trade


@pytest.mark.parametrize("rounds, ibkr, real", [
    ([(50, 120, 105), (50, 118, 102)], 103.5, 84.5),
    ([(50, 95, 104), (50, 98, 106)], 105, 108.5),
    ([(100, 150, 110), (100, 140, 100), (100, 130, 95)], 95, -15),
])
def test_review_presets_match_the_site(rounds, ibkr, real):
    r = tcalc.review(100, 100, rounds)
    assert r.ibkr_cost == pytest.approx(ibkr)
    assert r.real_cost == pytest.approx(real)
    assert r.rounds == len(rounds)
