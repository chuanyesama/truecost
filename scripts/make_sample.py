"""Generate a synthetic IBKR Activity Statement for the public demo.

Nothing here comes from a real account: prices are random walks, trades are
simulated. The behaviour is shaped to exercise every page of the app - a core
position traded around (做T), an oversized swing, a zero-cost holding, a
second market (SEK), many minimum-commission orders, and USD cash held while
the AUD moves.

Usage:  python scripts/make_sample.py [BASE] [OUT]
        default: AUD -> data/sample/sample_statement.csv
"""
from __future__ import annotations

import csv
import random
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src import costbasis as cb, fx  # noqa: E402

OUT = ROOT / "data" / "sample" / "sample_statement.csv"
START, END = pd.Timestamp("2026-05-04"), pd.Timestamp("2026-10-09")
rng = random.Random(7)


def price_path(start: float, drift: float, vol: float) -> dict:
    days = pd.bdate_range(START, END)
    p, out = start, {}
    for d in days:
        p *= 1 + drift + rng.gauss(0, vol)
        out[d] = round(p, 2)
    return out


PATHS = {
    "NVDA": ("USD", price_path(135, 0.0012, 0.022)),
    "MSFT": ("USD", price_path(450, 0.0004, 0.012)),
    "PLTR": ("USD", price_path(120, 0.0025, 0.03)),
    "RKLB": ("USD", price_path(30, -0.002, 0.04)),
    "ERIC-B": ("SEK", price_path(85, -0.003, 0.025)),
}
DAYS = sorted(PATHS["NVDA"][1])


def ibkr_commission(ccy: str, qty: float, price: float) -> float:
    if ccy == "USD":
        return -min(max(1.0, 0.005 * abs(qty)), 0.01 * abs(qty) * price)
    return -max(49.0, 0.0005 * abs(qty) * price)  # SEK-style minimum


def main(base: str = "AUD", out: Path = OUT) -> None:
    rates = fx.Rates(fx.ecb_table(base), base)
    base_per = lambda ccy, d: rates(ccy, d)
    trades, fx_rows, deposits, interest = [], [], [], []

    def trade(sym: str, day, qty: float, hour: int = 15, minute: int = 0):
        ccy, path = PATHS[sym]
        px = round(path[day] * (1 + rng.uniform(-0.004, 0.004)), 2)
        t = day + pd.Timedelta(hours=hour, minutes=minute)
        trades.append({"time": t, "asset": "Stocks", "currency": ccy, "symbol": sym, "qty": qty,
                       "price": px, "proceeds": -qty * px, "commission": ibkr_commission(ccy, qty, px),
                       "close": path[day]})

    def convert(day, amount: float, ccy: str):
        if ccy == base:
            return
        rate = 1 / base_per(ccy, day) * (1 - 0.00002)  # small spread vs reference
        fx_rows.append((day + pd.Timedelta(hours=10), ccy, amount, rate))

    # money in
    scale = 1 / base_per("AUD", DAYS[0]) if base != "AUD" else 1.0  # same account size in any base
    for d, amt in [(DAYS[0], 30000), (DAYS[15], 20000), (DAYS[60], 10000)]:
        deposits.append((d, round(amt * scale)))
        convert(d, amt * scale * 0.95, "USD")
    convert(DAYS[30], 6000 * scale, "SEK")

    # NVDA: core position + frequent 做T, ends at zero cost
    trade("NVDA", DAYS[1], 150)
    for i in range(3, len(DAYS) - 5, 4):
        d = DAYS[i]
        q = rng.choice([20, 30, 40])
        trade("NVDA", d, -q, 14, 30)
        trade("NVDA", DAYS[i + 1], q, 15, 10)
    trade("NVDA", DAYS[-8], -145, 16)  # leaves 5 shares at zero cost

    # MSFT: steady holding, a few small averaging-down buys (min commission)
    for i in range(2, 100, 9):
        trade("MSFT", DAYS[i], rng.choice([1, 2, 3]))
        trade("MSFT", DAYS[i], 1, 15, 4)  # split order: mergeable

    # PLTR: intraday scalps, many small orders
    for i in range(5, len(DAYS) - 3, 3):
        d = DAYS[i]
        q = rng.choice([5, 8, 10])
        trade("PLTR", d, q, 14, 0)
        trade("PLTR", d, -q, 14 + rng.choice([1, 2]), 20)

    # RKLB: oversized swing that goes wrong (加仓波段)
    trade("RKLB", DAYS[20], 20)
    trade("RKLB", DAYS[25], 600)
    trade("RKLB", DAYS[40], -600)
    trade("RKLB", DAYS[45], -20)

    # ERIC-B: a market the user doesn't know well
    for i in (32, 38, 50, 55):
        trade("ERIC-B", DAYS[i], 300)
        trade("ERIC-B", DAYS[i + 3], -300)

    for m in range(6, 11):
        interest.append((pd.Timestamp(f"2026-{m:02d}-05"), round(rng.uniform(2, 9), 2)))

    t = pd.DataFrame(trades).sort_values("time").reset_index(drop=True)
    t["ibkr_basis"], t["ibkr_realized"], t["code"], t["lot_method"] = 0.0, 0.0, "", "LIFO"
    # fill Basis / Realized P/L the way IBKR would (LIFO)
    basis, realized = [], []
    for i in range(len(t)):
        _, s = cb.run(t.iloc[: i + 1])
        last = s.iloc[-1] if len(s) and s.iloc[-1]["time"] == t.loc[i, "time"] else None
        if t.loc[i, "qty"] > 0 or last is None:
            basis.append(-(t.loc[i, "proceeds"] + t.loc[i, "commission"]))
            realized.append(0.0)
        else:
            basis.append(-last["basis"])
            realized.append(last["realized"])
    t["basis"], t["realized"] = basis, realized
    positions, _ = cb.run(t)

    rows: list[list] = []
    w = rows.append
    w(["Statement", "Header", "Field Name", "Field Value"])
    w(["Statement", "Data", "Title", "Activity Statement (SAMPLE - synthetic data)"])
    w(["Account Information", "Header", "Field Name", "Field Value"])
    for k, v in [("Name", "Demo Investor"), ("Account", "U0000000"), ("Account Type", "Individual"),
                 ("Base Currency", base)]:
        w(["Account Information", "Data", k, v])

    w(["Trades", "Header", "DataDiscriminator", "Asset Category", "Currency", "Symbol", "Date/Time", "Quantity",
       "T. Price", "C. Price", "Proceeds", "Comm/Fee", "Basis", "Realized P/L", "MTM P/L", "Code"])
    for x in t.itertuples():
        code = "O" if x.qty > 0 else "C;LI"
        w(["Trades", "Data", "Order", "Stocks", x.currency, x.symbol, x.time.strftime("%Y-%m-%d, %H:%M:%S"),
           f"{x.qty:g}", f"{x.price:.2f}", f"{x.close:.2f}", f"{x.proceeds:.2f}", f"{x.commission:.4f}",
           f"{x.basis:.4f}", f"{x.realized:.4f}", "0", code])
    w(["Trades", "Header", "DataDiscriminator", "Asset Category", "Currency", "Symbol", "Date/Time", "Quantity",
       "T. Price", "", "Proceeds", f"Comm in {base}", "", "", f"MTM in {base}", "Code"])
    for day, ccy, amount, rate in fx_rows:
        w(["Trades", "Data", "Order", "Forex", ccy, f"{base}.{ccy}", day.strftime("%Y-%m-%d, %H:%M:%S"),
           f"{-amount:.2f}", f"{rate:.6f}", "", f"{amount * rate:.4f}", "-2.00", "", "", "0", ""])

    w(["Deposits & Withdrawals", "Header", "Currency", "Settle Date", "Description", "Amount"])
    for d, amt in deposits:
        w(["Deposits & Withdrawals", "Data", base, d.strftime("%Y-%m-%d"), "Electronic Fund Transfer", f"{amt}"])
    w(["Interest", "Header", "Currency", "Date", "Description", "Amount"])
    for d, amt in interest:
        w(["Interest", "Data", "USD", d.strftime("%Y-%m-%d"), "USD Credit Interest", f"{amt}"])

    w(["Open Positions", "Header", "DataDiscriminator", "Asset Category", "Currency", "Symbol", "Quantity", "Mult",
       "Cost Price", "Cost Basis", "Close Price", "Value", "Unrealized P/L", "Code"])
    for sym, p in positions.items():
        if abs(p.shares) > 1e-9:
            close = PATHS[sym][1][DAYS[-1]]
            w(["Open Positions", "Data", "Summary", "Stocks", p.currency, sym, f"{p.shares:g}", "1",
               f"{p.lot_avg_cost:.4f}", f"{p.lot_avg_cost * p.shares:.2f}", f"{close}", f"{close * p.shares:.2f}",
               f"{(close - p.lot_avg_cost) * p.shares:.2f}", ""])

    w(["Forex Balances", "Header", "Asset Category", "Currency", "Description", "Quantity", "Cost Price",
       f"Cost Basis in {base}", "Close Price", f"Value in {base}", f"Unrealized P/L in {base}", "Code"])
    for ccy in ("USD", "SEK"):
        if ccy != base:
            w(["Forex Balances", "Data", "Forex", base, ccy, "0", "0", "0", f"{base_per(ccy, END):.6f}", "0", "0", ""])

    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerows(rows)
    print(f"wrote {out} ({len(t)} stock trades, base {base})")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "AUD", Path(sys.argv[2]) if len(sys.argv) > 2 else OUT)
