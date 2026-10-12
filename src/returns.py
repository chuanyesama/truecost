"""Split a holding's base-currency gain into price, FX and cross effects.

For a lot bought at unit cost c when 1 unit of currency = F0 base units, now
worth price P when 1 unit = F1:

    base gain = P*F1 - c*F0
             = (P - c)*F0          price effect  (the stock moved)
             + c*(F1 - F0)         FX effect     (the currency moved)
             + (P - c)*(F1 - F0)   cross effect  (both at once)

This is why the % an app shows (P/c - 1, in USD) is not the change in an
investor's balance in their home currency.
"""
from __future__ import annotations

import pandas as pd


def decompose_open(lots: pd.DataFrame, prices: dict[str, float], rate_now) -> pd.DataFrame:
    """Per-symbol decomposition of unrealized gain on open lots.

    lots: costbasis.open_lots(...) output; prices: symbol -> current price in
    trade currency; rate_now(ccy) -> current base units per unit.
    """
    df = lots[lots["symbol"].isin(prices)].copy()
    df["price"] = df["symbol"].map(prices)
    df["f0"] = df["unit_cost_base"] / df["unit_cost"]
    df["f1"] = df["currency"].map(rate_now)
    q, c, p, f0, f1 = df["qty"], df["unit_cost"], df["price"], df["f0"], df["f1"]
    df["cost_base"] = q * c * f0
    df["value_base"] = q * p * f1
    df["price_effect"] = q * (p - c) * f0
    df["fx_effect"] = q * c * (f1 - f0)
    df["cross_effect"] = q * (p - c) * (f1 - f0)
    df["gain_local"] = q * (p - c)
    df["cost_local"] = q * c
    g = df.groupby(["symbol", "currency"], as_index=False)[[
        "cost_local", "gain_local", "cost_base", "value_base",
        "price_effect", "fx_effect", "cross_effect",
    ]].sum()
    g["gain_base"] = g["value_base"] - g["cost_base"]
    g["return_local_pct"] = 100 * g["gain_local"] / g["cost_local"]
    g["return_base_pct"] = 100 * g["gain_base"] / g["cost_base"]
    return g
