"""Generate a synthetic IBKR Activity Statement for the public demo.

The account is fictional, but trades are placed on real market days at prices
inside each day's real high-low range, so they line up with real candles on
the Chart tab. Daily prices are cached in data/sample/sample_prices.csv
(fetched once with --refresh), which keeps tests offline and reproducible.

The behaviour is shaped to exercise every page: a core position traded
around, an oversized swing, a zero-cost holding, a second market (SEK), many
minimum-commission orders, and USD cash held while the base currency moves.

Usage:  python scripts/make_sample.py [BASE] [OUT] [--refresh]
        default: AUD -> data/sample/sample_statement.csv
"""
from __future__ import annotations

import csv
import random
import sys
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src import costbasis as cb, fx, prices  # noqa: E402

OUT = ROOT / "data" / "sample" / "sample_statement.csv"
PRICES_CSV = ROOT / "data" / "sample" / "sample_prices.csv"
START, END = pd.Timestamp("2026-05-04"), pd.Timestamp("2026-10-09")

# symbol -> currency, IBKR listing exchange, exchange time zone
SYMBOLS = {
    "NVDA": ("USD", "NASDAQ", "America/New_York"),
    "MSFT": ("USD", "NASDAQ", "America/New_York"),
    "PLTR": ("USD", "NASDAQ", "America/New_York"),
    "RKLB": ("USD", "NASDAQ", "America/New_York"),
    "ERIC-B": ("SEK", "SFB", "Europe/Stockholm"),
}
# where a fictional holder of each base currency would live (statement clock)
HOME_TZ = {"AUD": "Australia/Sydney", "USD": "America/New_York", "EUR": "Europe/Berlin",
           "GBP": "Europe/London", "NZD": "Pacific/Auckland", "SGD": "Asia/Singapore", "HKD": "Asia/Hong_Kong"}


def load_prices(refresh: bool = False) -> pd.DataFrame:
    if refresh or not PRICES_CSV.exists():
        frames = []
        for sym, (_, exch, _) in SYMBOLS.items():
            bars, _ = prices.fetch_bars(prices.yahoo_symbol(sym, exch), "1Y")
            b = bars.reset_index(names="date")
            b["date"] = b["date"].dt.tz_localize(None).dt.normalize()
            b["symbol"] = sym
            frames.append(b[["symbol", "date", "open", "high", "low", "close"]])
        PRICES_CSV.parent.mkdir(parents=True, exist_ok=True)
        pd.concat(frames).round(4).to_csv(PRICES_CSV, index=False)
    df = pd.read_csv(PRICES_CSV, parse_dates=["date"])
    return df[(df["date"] >= START) & (df["date"] <= END)]


def ibkr_commission(ccy: str, qty: float, price: float) -> float:
    if ccy == "USD":
        return -min(max(1.0, 0.005 * abs(qty)), 0.01 * abs(qty) * price)
    return -max(49.0, 0.0005 * abs(qty) * price)  # SEK-style minimum


def main(base: str = "AUD", out: Path = OUT, refresh: bool = False) -> None:
    rng = random.Random(7)
    px = load_prices(refresh)
    ohlc = {s: g.set_index("date") for s, g in px.groupby("symbol")}
    DAYS = list(ohlc["NVDA"].index)
    home = ZoneInfo(HOME_TZ.get(base, "UTC"))
    rates = fx.Rates(fx.ecb_table(base), base)
    base_per = lambda ccy, d: rates(ccy, d)
    trades, fx_rows, deposits, interest = [], [], [], []

    def day_of(sym: str, day):
        idx = ohlc[sym].index
        return idx[idx.searchsorted(day, side="right") - 1]  # same day, or the last one before it

    def trade(sym: str, day, qty: float, at: str = "mid", hhmm: str = "11:00"):
        ccy, _, ex_tz = SYMBOLS[sym]
        d = day_of(sym, day)
        o, h, lo, c = ohlc[sym].loc[d, ["open", "high", "low", "close"]]
        frac = {"low": 0.12, "high": 0.88, "mid": rng.uniform(0.3, 0.7)}[at]
        price = round(lo + frac * (h - lo), 2)
        local = pd.Timestamp(f"{d:%Y-%m-%d} {hhmm}").tz_localize(ex_tz)
        when = local.tz_convert(home).tz_localize(None)  # IBKR writes the holder's local time
        trades.append({"time": when, "asset": "Stocks", "currency": ccy, "symbol": sym, "qty": qty,
                       "price": price, "proceeds": -qty * price, "commission": ibkr_commission(ccy, qty, price),
                       "close": c})

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

    # NVDA: core position traded around (sell into strength, buy back on dips), ends at zero cost
    trade("NVDA", DAYS[1], 150, "mid", "10:05")
    for i in range(3, len(DAYS) - 6, 4):
        q = rng.choice([20, 30, 40])
        trade("NVDA", DAYS[i], -q, "high", "14:30")
        trade("NVDA", DAYS[i + 1], q, "low", "10:40")
    trade("NVDA", DAYS[-6], -145, "high", "15:10")  # keeps 5 shares

    # MSFT: steady holding, small adds split into two orders (minimum commission twice)
    for i in range(2, min(100, len(DAYS)), 9):
        trade("MSFT", DAYS[i], rng.choice([1, 2, 3]), "mid", "10:30")
        trade("MSFT", DAYS[i], 1, "mid", "10:34")

    # PLTR: intraday scalps, many small orders
    for i in range(5, len(DAYS) - 3, 3):
        q = rng.choice([5, 8, 10])
        trade("PLTR", DAYS[i], q, "mid", "10:00")
        trade("PLTR", DAYS[i], -q, "mid", rng.choice(["11:20", "13:45", "15:30"]))

    # RKLB: oversized swing bought at the top, sold at the bottom
    trade("RKLB", DAYS[20], 20, "mid", "10:15")
    trade("RKLB", DAYS[25], 150, "high", "12:00")
    trade("RKLB", DAYS[40], -150, "low", "14:00")
    trade("RKLB", DAYS[45], -20, "mid", "11:00")

    # ERIC-B: a market the holder doesn't know well (Stockholm hours)
    for i in (32, 38, 50, 55):
        trade("ERIC-B", DAYS[i], 300, "high", "10:30")
        trade("ERIC-B", DAYS[i + 3], -300, "low", "15:00")

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

    generated = (END + pd.Timedelta(days=3, hours=9)).tz_localize(home)
    rows: list[list] = []
    w = rows.append
    w(["Statement", "Header", "Field Name", "Field Value"])
    w(["Statement", "Data", "Title", "Activity Statement (SAMPLE - synthetic data)"])
    w(["Statement", "Data", "Period", f"{START:%B %d, %Y} - {END:%B %d, %Y}"])
    w(["Statement", "Data", "WhenGenerated", f"{generated:%Y-%m-%d, %H:%M:%S} {generated.tzname()}"])
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
            close = float(ohlc[sym]["close"].iloc[-1])
            w(["Open Positions", "Data", "Summary", "Stocks", p.currency, sym, f"{p.shares:g}", "1",
               f"{p.lot_avg_cost:.4f}", f"{p.lot_avg_cost * p.shares:.2f}", f"{close}", f"{close * p.shares:.2f}",
               f"{(close - p.lot_avg_cost) * p.shares:.2f}", ""])

    w(["Forex Balances", "Header", "Asset Category", "Currency", "Description", "Quantity", "Cost Price",
       f"Cost Basis in {base}", "Close Price", f"Value in {base}", f"Unrealized P/L in {base}", "Code"])
    for ccy in ("USD", "SEK"):
        if ccy != base:
            w(["Forex Balances", "Data", "Forex", base, ccy, "0", "0", "0", f"{base_per(ccy, END):.6f}", "0", "0", ""])

    w(["Financial Instrument Information", "Header", "Asset Category", "Symbol", "Description", "Conid",
       "Security ID", "Underlying", "Listing Exch", "Multiplier", "Type", "Code"])
    for sym, (_, exch, _) in SYMBOLS.items():
        w(["Financial Instrument Information", "Data", "Stocks", sym, sym, "", "", sym, exch, "1", "COMMON", ""])

    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerows(rows)
    print(f"wrote {out} ({len(t)} stock trades, base {base})")


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if a != "--refresh"]
    main(args[0] if args else "AUD", Path(args[1]) if len(args) > 1 else OUT, "--refresh" in sys.argv)
