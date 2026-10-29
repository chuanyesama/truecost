"""Candles for the chart tab, and trade markers placed on them.

Market data comes from Yahoo Finance's public chart endpoint. That is fine for
a free, non-commercial tool; a paid product needs a licensed feed. Everything
provider-specific lives in `yahoo_symbol` and `fetch_bars`, so swapping the
source means replacing those two functions.
"""
from __future__ import annotations

import json
import urllib.parse
import urllib.request
from zoneinfo import ZoneInfo

import pandas as pd

# IBKR-style ranges -> (Yahoo range, Yahoo interval, how to trim)
RANGES = {
    "2H": ("5d", "1m", "last_120_bars"),
    "1D": ("5d", "5m", "last_session"),
    "1W": ("5d", "30m", None),
    "1M": ("1mo", "60m", None),
    "3M": ("3mo", "1d", None),
    "6M": ("6mo", "1d", None),
    "1Y": ("1y", "1d", None),
    "2Y": ("2y", "1wk", None),
    "5Y": ("5y", "1wk", None),
}
INTRADAY = {"2H", "1D", "1W", "1M"}

# IBKR listing exchange -> Yahoo suffix
SUFFIX = {
    "NASDAQ": "", "NYSE": "", "ARCA": "", "BATS": "", "AMEX": "", "NYSEAMERICAN": "", "PINK": "", "IEX": "",
    "IBIS": ".DE", "IBIS2": ".DE", "FWB": ".F", "SBF": ".PA", "AEB": ".AS", "ENEXT.BE": ".BR", "BVL": ".LS",
    "SFB": ".ST", "OSE": ".OL", "CPH": ".CO", "HEX": ".HE", "EBS": ".SW", "VIRTX": ".SW", "BVME": ".MI",
    "BM": ".MC", "LSE": ".L", "LSEETF": ".L", "VSE": ".VI",
    "KRX": ".KS", "KOSDAQ": ".KQ", "TWSE": ".TW", "TPEX": ".TWO", "SEHK": ".HK", "TSEJ": ".T",
    "SGX": ".SI", "ASX": ".AX", "NZE": ".NZ", "TSE": ".TO", "VENTURE": ".V", "NSE": ".NS",
}

# statement timezone abbreviation -> candidate IANA zones
TZ_ABBR = {
    "AEDT": ["Australia/Sydney"], "AEST": ["Australia/Sydney", "Australia/Brisbane"],
    "ACDT": ["Australia/Adelaide"], "ACST": ["Australia/Adelaide", "Australia/Darwin"],
    "AWST": ["Australia/Perth"], "NZDT": ["Pacific/Auckland"], "NZST": ["Pacific/Auckland"],
    "EST": ["America/New_York"], "EDT": ["America/New_York"], "CST": ["America/Chicago", "Asia/Shanghai"],
    "CDT": ["America/Chicago"], "MST": ["America/Denver", "America/Phoenix"], "MDT": ["America/Denver"],
    "PST": ["America/Los_Angeles"], "PDT": ["America/Los_Angeles"],
    "GMT": ["Europe/London"], "BST": ["Europe/London"], "UTC": ["UTC"],
    "CET": ["Europe/Berlin"], "CEST": ["Europe/Berlin"], "EET": ["Europe/Helsinki"], "EEST": ["Europe/Helsinki"],
    "HKT": ["Asia/Hong_Kong"], "SGT": ["Asia/Singapore"], "JST": ["Asia/Tokyo"], "KST": ["Asia/Seoul"],
    "IST": ["Asia/Kolkata"],
}
FALLBACK_ZONES = ["America/New_York", "Europe/London", "Europe/Berlin", "Asia/Shanghai", "Asia/Hong_Kong",
                  "Asia/Singapore", "Asia/Tokyo", "Australia/Sydney", "Australia/Perth", "Pacific/Auckland",
                  "America/Los_Angeles", "America/Chicago", "Asia/Kolkata", "UTC"]
US_EXCHANGES = {k for k, v in SUFFIX.items() if v == ""}


# ---------- symbols ----------
def yahoo_symbol(symbol: str, exchange: str | None, underlying: str | None = None) -> str | None:
    """IBKR symbol + listing exchange -> Yahoo ticker; None when we can't map it."""
    if exchange not in SUFFIX:
        return None
    suffix = SUFFIX[exchange]
    # IBKR sometimes writes the market into the symbol ("005930.KS"); the Underlying column doesn't
    base = underlying if (underlying and suffix and symbol.endswith(suffix)) else symbol
    if exchange == "SEHK":
        base = base.zfill(4)
    # share classes: IBKR "BRK B" / "ERIC.B" -> Yahoo "BRK-B" / "ERIC-B"
    base = base.replace(" ", "-")
    if exchange in US_EXCHANGES or suffix in (".ST", ".CO", ".HE", ".OL"):
        base = base.replace(".", "-")
    return base + suffix


def instruments(sections: dict) -> pd.DataFrame:
    """symbol -> listing exchange, underlying, and the symbol to quote under
    (renamed tickers are listed as "OLD, NEW"; trades may use either name)."""
    fi = sections.get("Financial Instrument Information")
    if fi is None or fi.empty:
        return pd.DataFrame(columns=["symbol", "exchange", "underlying", "quote"])
    fi = fi[fi.get("Asset Category", "") == "Stocks"]
    rows = []
    for sym, exch, und in zip(fi["Symbol"], fi["Listing Exch"], fi.get("Underlying", fi["Symbol"])):
        aliases = [a.strip() for a in str(sym).split(",")]
        current = und if und in aliases else aliases[-1]
        for a in aliases:
            rows.append({"symbol": a, "exchange": exch, "underlying": und, "quote": current})
    return pd.DataFrame(rows, columns=["symbol", "exchange", "underlying", "quote"]).drop_duplicates("symbol")


# ---------- statement time zone ----------
def _in_us_session(local_times: pd.Series, zone: str) -> float:
    """Share of trades that fall inside US extended hours (04:00-20:00 New York) if the
    statement's clock is `zone`."""
    ny = local_times.dt.tz_localize(zone, ambiguous="NaT", nonexistent="NaT").dt.tz_convert("America/New_York")
    ny = ny.dropna()
    if ny.empty:
        return 0.0
    minutes = ny.dt.hour * 60 + ny.dt.minute
    return float(((minutes >= 240) & (minutes <= 1200) & (ny.dt.weekday < 5)).mean())


def statement_timezone(sections: dict, stock_trades: pd.DataFrame, exchanges: dict[str, str]) -> str:
    """IANA zone of the statement's Date/Time column.

    IBKR writes trade times in the account holder's local time and stamps the
    abbreviation on "WhenGenerated" (e.g. "... AEDT"). Abbreviations are
    ambiguous, so candidates are checked against US market hours."""
    candidates = FALLBACK_ZONES
    st = sections.get("Statement")
    if st is not None and "Field Name" in st:
        when = dict(zip(st["Field Name"], st["Field Value"])).get("WhenGenerated", "")
        abbr = when.split()[-1] if when else ""
        candidates = TZ_ABBR.get(abbr, FALLBACK_ZONES)
    us = stock_trades[stock_trades["symbol"].map(exchanges).isin(US_EXCHANGES)]["time"]
    if len(candidates) == 1 or us.empty:
        return candidates[0]
    return max(candidates, key=lambda z: _in_us_session(us, z))


# ---------- bars ----------
def chart_query(ticker: str, range_key: str) -> str:
    """Path and query of Yahoo's chart endpoint for one ticker and range (the web app sends it through a proxy)."""
    rng, interval, _ = RANGES[range_key]
    # include pre/post-market bars intraday: many users trade outside regular hours
    q = urllib.parse.urlencode({"range": rng, "interval": interval,
                                "includePrePost": "true" if range_key in INTRADAY else "false"})
    return f"/v8/finance/chart/{urllib.parse.quote(ticker)}?{q}"


def fetch_bars(ticker: str, range_key: str) -> tuple[pd.DataFrame, str]:
    """OHLCV bars indexed by bar start time in the exchange's time zone."""
    url = "https://query1.finance.yahoo.com" + chart_query(ticker, range_key)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (TrueCost)"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        return parse_bars(json.load(resp), ticker, range_key)


def parse_bars(payload: dict, ticker: str, range_key: str) -> tuple[pd.DataFrame, str]:
    """Yahoo's chart JSON -> (bars, exchange time zone)."""
    trim = RANGES[range_key][2]
    data = payload["chart"]
    if data.get("error") or not data.get("result"):
        raise LookupError(f"no data for {ticker}")
    res = data["result"][0]
    tz = res["meta"].get("exchangeTimezoneName", "UTC")
    if not res.get("timestamp"):
        raise LookupError(f"no bars for {ticker}")
    q = res["indicators"]["quote"][0]
    bars = pd.DataFrame({k: q.get(k) for k in ("open", "high", "low", "close", "volume")},
                        index=pd.to_datetime(res["timestamp"], unit="s", utc=True).tz_convert(tz))
    bars = bars.dropna(subset=["open", "high", "low", "close"])
    if trim == "last_120_bars":  # two hours of 1-minute bars that actually traded
        bars = bars.iloc[-120:]
    elif trim == "last_session" and not bars.empty:
        # today's session if it has really started, otherwise the previous full one
        days = bars.index.normalize()
        counts = pd.Series(1, index=days).groupby(level=0).sum()
        full = counts[counts >= counts.median() / 3]
        bars = bars[days == (full.index[-1] if len(full) else counts.index[-1])]
    return bars, tz


def latest_fx(ccy: str, base: str) -> float:
    """Latest exchange rate: base units per 1 unit of ccy."""
    bars, _ = fetch_bars(f"{ccy}{base}=X", "1D")
    return float(bars["close"].iloc[-1])


def place_trades(trades: pd.DataFrame, bars: pd.DataFrame, statement_tz: str, intraday: bool) -> pd.DataFrame:
    """Aggregate the user's trades into the bars they fall in, per side.

    trades: one symbol's rows from ingest (naive `time` in the statement's zone).
    Returns one row per (bar, side): bar label, side, count, qty, avg price."""
    if trades.empty or bars.empty:
        return pd.DataFrame(columns=["bar", "side", "count", "qty", "avg_price"])
    tz = bars.index.tz
    t = trades.copy()
    t["when"] = t["time"].dt.tz_localize(ZoneInfo(statement_tz), ambiguous="NaT", nonexistent="shift_forward")
    t["when"] = t["when"].dt.tz_convert(tz)
    starts = bars.index
    if intraday:
        step = (starts[1:] - starts[:-1]).min() if len(starts) > 1 else pd.Timedelta(minutes=1)
        pos = starts.searchsorted(t["when"], side="right") - 1
        ok = (pos >= 0) & (t["when"] < starts[pos.clip(0)] + step)
    else:  # daily / weekly bars are dated; match on the trade's exchange-local date
        day = t["when"].dt.tz_localize(None).dt.normalize()
        keys = starts.tz_localize(None).normalize()
        pos = keys.searchsorted(day, side="right") - 1
        span = pd.Timedelta(days=7 if len(keys) > 1 and (keys[1] - keys[0]).days >= 5 else 1)
        ok = (pos >= 0) & (day < keys[pos.clip(0)] + span)
    t = t[ok.values if hasattr(ok, "values") else ok].copy()
    t["bar"] = starts[pos[ok.values if hasattr(ok, "values") else ok]]
    if t.empty:
        return pd.DataFrame(columns=["bar", "side", "count", "qty", "avg_price"])
    t["side"] = t["qty"].map(lambda q: "B" if q > 0 else "S")
    t["notional"] = t["qty"].abs() * t["price"]
    g = t.groupby(["bar", "side"], as_index=False).agg(count=("qty", "size"), qty=("qty", lambda x: x.abs().sum()),
                                                        notional=("notional", "sum"))
    g["avg_price"] = g["notional"] / g["qty"]
    return g.drop(columns="notional")
