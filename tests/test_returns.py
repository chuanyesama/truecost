import pandas as pd
import pytest

from src import costbasis as cb, returns
from tests.test_costbasis import trades


def test_decomposition_adds_up():
    # buy 10 @100 USD when 1 USD = 1.40 AUD; now 120 USD and 1 USD = 1.50 AUD
    fx = lambda ccy, t: 1.40
    pos, _ = cb.run(trades((0, 10, 100)), fx=fx)
    d = returns.decompose_open(cb.open_lots(pos), {"X": 120.0}, lambda c: 1.50).iloc[0]
    cost = 1001 * 1.40
    assert d.cost_base == pytest.approx(cost)
    assert d.price_effect == pytest.approx((1200 - 1001) * 1.40)
    assert d.fx_effect == pytest.approx(1001 * 0.10)
    assert d.cross_effect == pytest.approx((1200 - 1001) * 0.10)
    assert d.price_effect + d.fx_effect + d.cross_effect == pytest.approx(d.gain_base)
    assert d.gain_base == pytest.approx(1200 * 1.50 - cost)


def test_realized_in_base_uses_rate_on_each_date():
    rates = {0: 1.40, 1: 1.50}
    fx = lambda ccy, t: rates[(t - pd.Timestamp("2026-01-01")).days]
    _, s = cb.run(trades((0, 10, 100), (1, -10, 100)), fx=fx)
    # flat in USD (-2 commissions) but AUD gain from the currency move
    assert s.realized.iloc[0] == pytest.approx(-2)
    assert s.realized_base.iloc[0] == pytest.approx(999 * 1.50 - 1001 * 1.40)
