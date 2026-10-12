"""One call from statement file to every number the app shows."""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from . import costbasis as cb, fx, ingest, ledger, returns, rounds


@dataclass
class Report:
    account: dict
    base: str
    fx_source: str
    end: pd.Timestamp
    holdings: pd.DataFrame      # per symbol: shares, IBKR avg cost, diluted cost (local + base)
    decomposition: pd.DataFrame  # per open symbol: price / FX / cross effects
    sells: pd.DataFrame          # every closing trade, local + base
    cash: pd.DataFrame           # foreign cash pools and their FX P/L
    attribution: dict            # headline split, base currency
    nav_end: float
    prices: dict
    stock_trades: pd.DataFrame
    rates: object
    cycles: pd.DataFrame         # flat-to-flat holding cycles per symbol
    rounds: pd.DataFrame         # 做T rounds inside cycles
    net_deposits: float

    @property
    def total_pl(self) -> float:
        return sum(self.attribution.values())

    @property
    def reconciles(self) -> bool:
        """Our split must add up to ending NAV - net deposits."""
        return abs(self.total_pl - (self.nav_end - self.net_deposits)) < 0.05


def build(statement, method: str | None = None, fx_source: str = "ecb") -> Report:
    """fx_source: "ecb" (any base currency) or "rba" (AUD base only)."""
    trades = ingest.load_trades(statement)
    sections = ingest.read_sections(statement)
    account = ingest.account_info(statement)
    base = account.get("Base Currency", "USD")
    if fx_source == "rba" and base != "AUD":
        fx_source = "ecb"
    rates = fx.build_rates(trades, base, fx_source)
    end_rates = ledger.end_rates_from_statement(statement, base)
    end = trades["time"].max().normalize()
    rate_end = lambda ccy: end_rates.get(ccy) or rates(ccy, end)

    stock_trades = ingest.load_stock_trades(statement)
    positions, sells = cb.run(stock_trades, method=method, fx=rates)
    cycles, t_rounds = rounds.cycles_and_rounds(stock_trades, fx=rates)
    op = sections.get("Open Positions", pd.DataFrame(columns=["Symbol", "Close Price"]))
    prices = dict(zip(op["Symbol"], ingest._num(op["Close Price"])))
    decomp = returns.decompose_open(cb.open_lots(positions), prices, rate_end)

    flows = ledger.cash_flows(statement, base)
    cash = ledger.cash_fx(flows, rates, end, base, end_rates)

    # realized stock P/L: price part = local P/L at the sell-date rate
    realized_price = float((sells["realized"] * sells["rate"]).sum()) if not sells.empty else 0.0
    realized_base = float(sells["realized_base"].sum()) if not sells.empty else 0.0
    attribution = {
        "stock_price": realized_price + float(decomp["price_effect"].sum()),
        "stock_fx": (realized_base - realized_price)
                    + float((decomp["fx_effect"] + decomp["cross_effect"]).sum()),
        "cash_fx": float((cash["realized_fx"] + cash["unrealized_fx"]).sum()) if not cash.empty else 0.0,
        "conversion": ledger.conversion_result(flows, rates),
        "income_fees": ledger.income_base(flows, rates),
    }
    base_cash = float(flows.loc[flows["currency"] == base, "amount"].sum())
    nav_end = base_cash + float(cash["value_base"].sum() if not cash.empty else 0) + float(decomp["value_base"].sum())

    return Report(
        account=account, base=base, fx_source=fx_source, end=end,
        holdings=cb.holdings(positions), decomposition=decomp, sells=sells, cash=cash,
        attribution=attribution, nav_end=nav_end, prices=prices,
        stock_trades=stock_trades, rates=rates, cycles=cycles, rounds=t_rounds,
        net_deposits=ledger.net_deposits_base(flows, rates),
    )
