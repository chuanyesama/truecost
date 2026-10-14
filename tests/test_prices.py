import pandas as pd
import pytest

from src import prices


@pytest.mark.parametrize("symbol, exch, underlying, expected", [
    ("MDB", "NASDAQ", "MDB", "MDB"),
    ("BRK B", "NYSE", "BRK", "BRK-B"),
    ("SIVE", "SFB", "SIVE", "SIVE.ST"),
    ("ERIC.B", "SFB", "ERIC", "ERIC-B.ST"),
    ("005930.KS", "KRX", "005930", "005930.KS"),
    ("3363", "TPEX", "3363", "3363.TWO"),
    ("700", "SEHK", "700", "0700.HK"),
    ("XYZ", "SOMEWHERE", "XYZ", None),
])
def test_yahoo_symbol(symbol, exch, underlying, expected):
    assert prices.yahoo_symbol(symbol, exch, underlying) == expected


def test_instruments_expands_renamed_symbols():
    fi = pd.DataFrame({"Asset Category": ["Stocks"], "Symbol": ["SKHYV, SKHY"], "Listing Exch": ["NASDAQ"],
                       "Underlying": ["SKHY"]})
    ins = prices.instruments({"Financial Instrument Information": fi}).set_index("symbol")
    assert set(ins.index) == {"SKHYV", "SKHY"} and ins.loc["SKHYV", "quote"] == "SKHY"
    row = ins.loc["SKHYV"]
    assert prices.yahoo_symbol(row["quote"], row["exchange"], row["underlying"]) == "SKHY"


def _us_trade_at(local: str):
    return pd.DataFrame({"symbol": ["MDB"], "time": [pd.Timestamp(local)]})


def test_statement_timezone_from_abbreviation():
    st = pd.DataFrame({"Field Name": ["WhenGenerated"], "Field Value": ["2026-10-12, 05:47:07 AEDT"]})
    tz = prices.statement_timezone({"Statement": st}, _us_trade_at("2026-10-10 04:35"), {"MDB": "NASDAQ"})
    assert tz == "Australia/Sydney"


def test_ambiguous_abbreviation_resolved_by_us_market_hours():
    # "CST" could be Chicago or Shanghai; 10:00 in Chicago is US market hours, 10:00 in Shanghai is not
    st = pd.DataFrame({"Field Name": ["WhenGenerated"], "Field Value": ["2026-10-12, 09:00:00 CST"]})
    trades = pd.DataFrame({"symbol": ["MDB"] * 3,
                           "time": pd.to_datetime(["2026-03-02 10:00", "2026-03-03 11:30", "2026-03-04 14:00"])})
    assert prices.statement_timezone({"Statement": st}, trades, {"MDB": "NASDAQ"}) == "America/Chicago"


def _bars(start: str, periods: int, freq: str, tz: str = "America/New_York"):
    idx = pd.date_range(start, periods=periods, freq=freq, tz=tz)
    return pd.DataFrame({"open": 10.0, "high": 11.0, "low": 9.0, "close": 10.5, "volume": 100}, index=idx)


def test_place_trades_intraday_converts_statement_time():
    bars = _bars("2026-10-09 09:30", 13, "30min")
    # 13:35 New York == 04:35 next day in Sydney (AEDT)
    trades = pd.DataFrame({"time": [pd.Timestamp("2026-10-10 04:35")], "qty": [30.0], "price": [10.2]})
    m = prices.place_trades(trades, bars, "Australia/Sydney", intraday=True)
    assert len(m) == 1 and m.iloc[0]["side"] == "B"
    assert m.iloc[0]["bar"] == pd.Timestamp("2026-10-09 13:30", tz="America/New_York")


def test_place_trades_daily_combines_same_bar_and_skips_out_of_range():
    bars = _bars("2026-10-05", 5, "D")
    trades = pd.DataFrame({
        "time": pd.to_datetime(["2026-10-07 01:00", "2026-10-07 03:00", "2026-09-01 01:00"]),  # Sydney
        "qty": [-10.0, -20.0, 5.0], "price": [10.0, 11.0, 9.5]})
    m = prices.place_trades(trades, bars, "Australia/Sydney", intraday=False)
    assert len(m) == 1
    row = m.iloc[0]
    assert row["side"] == "S" and row["count"] == 2 and row["qty"] == 30
    assert row["avg_price"] == pytest.approx((10 * 10 + 20 * 11) / 30)
    assert row["bar"].strftime("%Y-%m-%d") == "2026-10-06"  # 01:00 Sydney is the previous day in New York
