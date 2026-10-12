import pandas as pd
import pytest

from src import costbasis as cb


def trades(*rows, method="FIFO"):
    """rows: (day, qty, price). Commission 1 per trade."""
    return pd.DataFrame([{
        "time": pd.Timestamp("2026-01-01") + pd.Timedelta(days=d),
        "asset": "Stocks", "currency": "USD", "symbol": "X",
        "qty": q, "price": p, "proceeds": -q * p, "commission": -1.0,
        "ibkr_basis": 0.0, "ibkr_realized": 0.0, "code": "", "lot_method": method,
    } for d, q, p in rows])


def test_do_t_lowers_diluted_cost_not_lot_average():
    # buy 100 @10, sell 50 @12 (做T), buy 50 @10
    pos, s = cb.run(trades((0, 100, 10), (1, -50, 12), (2, 50, 10)))
    h = cb.holdings(pos).iloc[0]
    assert h.shares == 100
    # lots left: 50 @10.01 + 50 @10.02 -> avg 10.015
    assert h.ibkr_avg_cost == pytest.approx(10.015)
    # cash in: 1001 - 599 + 501 = 903 -> 9.03 per share
    assert h.diluted_cost == pytest.approx(9.03)
    assert s.realized.sum() == pytest.approx(599 - 500.5)


@pytest.mark.parametrize("method, realized", [
    ("FIFO", 1199 - 1001),  # sells the @10 lot
    ("LIFO", 1199 - 1101),  # sells the @11 lot
    ("HIFO", 1199 - 1101),
])
def test_lot_methods(method, realized):
    pos, s = cb.run(trades((0, 100, 10), (1, 100, 11), (2, -100, 12), method=method))
    assert s.realized.iloc[0] == pytest.approx(realized)


def test_method_override_beats_recorded_method():
    t = trades((0, 100, 10), (1, 100, 11), (2, -100, 12), method="LIFO")
    _, s = cb.run(t, method="FIFO")
    assert s.realized.iloc[0] == pytest.approx(198)


def test_flat_resets_diluted_cost():
    pos, _ = cb.run(trades((0, 10, 10), (1, -10, 20), (2, 10, 15)))
    assert cb.holdings(pos).iloc[0].diluted_cost == pytest.approx(15.1)


def test_sell_through_zero_opens_short():
    # long 5, sell 15 -> closes 5, short 10
    pos, s = cb.run(trades((0, 5, 10), (1, -15, 12), (2, 10, 11)))
    assert len(s) == 2 and s.iloc[0].mixed
    assert s.iloc[0].realized == pytest.approx((180 - 1) * 5 / 15 - 51)
    # short 10 opened at (179*10/15)/10 per share, covered for 111
    assert s.iloc[1].side == "short"
    assert s.iloc[1].realized == pytest.approx(179 * 10 / 15 - 111)
    assert cb.holdings(pos).empty


def test_zero_cost_holding():
    # buy 100 @10, sell 90 @20: everything paid back and more -> diluted cost < 0
    pos, _ = cb.run(trades((0, 100, 10), (1, -90, 20)))
    h = cb.holdings(pos).iloc[0]
    assert h.shares == 10
    assert h.diluted_cost == pytest.approx((1001 - 1799) / 10)  # -79.8: 798 already pocketed
    assert h.ibkr_avg_cost == pytest.approx(10.01)
