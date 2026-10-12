import pandas as pd
import pytest

from src import ledger


def test_cash_pool_fx_gain():
    # convert 1000 AUD -> 700 USD at 1.4286, hold, USD strengthens to 1.50
    t0, t1 = pd.Timestamp("2026-01-01"), pd.Timestamp("2026-02-01")
    rate = lambda c, t: 1.0 if c == "AUD" else (1 / 0.70 if t < t1 else 1.50)
    flows = pd.DataFrame([
        (t0, "AUD", -1000.0, "fx"), (t0, "USD", 700.0, "fx"),
        (t1, "USD", -350.0, "trade"),  # spend half later
    ], columns=["time", "currency", "amount", "kind"])
    c = ledger.cash_fx(flows, rate, t1, "AUD").iloc[0]
    assert c.balance == pytest.approx(350)
    assert c.realized_fx == pytest.approx(350 * (1.50 - 1 / 0.70))
    assert c.unrealized_fx == pytest.approx(350 * (1.50 - 1 / 0.70))
    # converted exactly at the reference rate -> no conversion gain/loss
    assert ledger.conversion_result(flows, rate) == pytest.approx(0)
