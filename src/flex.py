"""Automatic sync from IBKR's Flex Web Service.

Flow: SendRequest (token + query id) -> reference code -> GetStatement (poll
until generated) -> Flex XML. The XML is converted into the same multi-section
CSV layout as the Activity Statement, so every downstream module is reused
unchanged and the reconciliation checks still apply.

The token only grants read access to Flex reports (no trading or transfers);
it can be IP-restricted and revoked in the IBKR portal. It is read from local
config and never written anywhere else.
"""
from __future__ import annotations

import csv
import io
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

BASE_URL = "https://ndcdyn.interactivebrokers.com/AccountManagement/FlexWebService"
RETRY_CODES = {"1001", "1004", "1018", "1019", "1021"}  # still generating / busy / paced: try again


class FlexError(RuntimeError):
    def __init__(self, code: str, message: str):
        super().__init__(f"{code}: {message}")
        self.code = code


# ---------- fetch ----------
def _get(endpoint: str, **params) -> str:
    url = f"{BASE_URL}/{endpoint}?" + urllib.parse.urlencode({**params, "v": 3})
    req = urllib.request.Request(url, headers={"User-Agent": "TrueCost/1.0"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read().decode("utf-8", errors="replace")


def _status(xml_text: str) -> tuple[str | None, str, str]:
    """(status, error code, message) of a FlexStatementResponse; status None if it's data."""
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return None, "", ""
    if root.tag != "FlexStatementResponse":
        return None, "", ""
    return root.findtext("Status"), root.findtext("ErrorCode") or "", root.findtext("ErrorMessage") or ""


def fetch(token: str, query_id: str, wait: float = 5, attempts: int = 24, on_wait=None) -> str:
    """Return the Flex statement (XML text) for this query."""
    sent = _get("SendRequest", t=token, q=query_id)
    status, code, msg = _status(sent)
    if status != "Success":
        raise FlexError(code or "?", msg or "SendRequest failed")
    ref = ET.fromstring(sent).findtext("ReferenceCode")
    for i in range(attempts):
        time.sleep(wait if i else 3)
        body = _get("GetStatement", t=token, q=ref)
        status, code, msg = _status(body)
        if status is None:
            return body
        if code not in RETRY_CODES:
            raise FlexError(code or "?", msg or "GetStatement failed")
        if on_wait:
            on_wait(i + 1)
    raise FlexError("timeout", "the statement was still being generated; try again in a minute")


# ---------- convert ----------
def _attr(el: ET.Element, *names: str, default: str = "") -> str:
    """First present attribute (Flex attribute names vary slightly by section/version)."""
    low = {k.lower(): v for k, v in el.attrib.items()}
    for n in names:
        if n.lower() in low and low[n.lower()] != "":
            return low[n.lower()]
    return default


def _num(s: str) -> float:
    try:
        return float(str(s).replace(",", ""))
    except ValueError:
        return 0.0


def _dt(s: str) -> str:
    """Flex date/time ("20261009;133500", "2026-10-09;13:35:00", "20261009 133500", ...)
    -> Activity Statement style "2026-10-09, 13:35:00"."""
    digits = "".join(ch for ch in s if ch.isdigit())
    if len(digits) < 8:
        return ""
    d = f"{digits[:4]}-{digits[4:6]}-{digits[6:8]}"
    t = digits[8:14].ljust(6, "0") if len(digits) > 8 else "000000"
    return f"{d}, {t[:2]}:{t[2:4]}:{t[4:6]}"


def _date(s: str) -> str:
    return _dt(s).split(",")[0]


ADDITIVE = ("quantity", "proceeds", "ibCommission", "taxes", "cost", "fifoPnlRealized", "mtmPnl", "netCash")


def _net_cancelled(trades: list[ET.Element]) -> list[ET.Element]:
    """Merge every row of a cancelled trade into one net row.

    IBKR records a correction as the original fill, a "TradeCancel" row reversing it and
    sometimes a re-booked copy, splitting commission and realized P/L between rows in
    different ways. Quantities, cash, commission, cost and realized P/L are additive, so
    summing all rows that share the cancelled trade id (and symbol) always gives the
    trade that actually stands - or nothing, when it was simply cancelled. Ids are only
    grouped when a cancel points at them: an auto FX conversion can share an id with an
    ordinary trade."""
    is_cancel = lambda t: _attr(t, "transactionType") == "TradeCancel" or "Ca" in _attr(t, "notes").split(";")
    groups = {(_attr(c, "origTradeID"), _attr(c, "symbol")) for c in trades if is_cancel(c)}
    key = lambda t: (_attr(t, "origTradeID") if is_cancel(t) else _attr(t, "tradeID"), _attr(t, "symbol"))
    members: dict[tuple, list[ET.Element]] = {}
    out = []
    for t in trades:
        k = key(t)
        if k in groups:
            members.setdefault(k, []).append(t)
        else:
            out.append(t)
    for rows in members.values():
        net_qty = sum(_num(_attr(r, "quantity")) for r in rows)
        if abs(net_qty) < 1e-9:
            continue  # cancelled outright
        kept = [r for r in rows if not is_cancel(r)] or rows
        lead = max(kept, key=lambda r: abs(_num(_attr(r, "fifoPnlRealized"))))
        merged = ET.Element("Trade", dict(lead.attrib))
        for f in ADDITIVE:
            merged.set(f, repr(sum(_num(_attr(r, f)) for r in rows)))
        proceeds = sum(_num(_attr(r, "proceeds")) for r in rows)
        merged.set("tradePrice", repr(abs(proceeds / net_qty)))
        codes = [c for r in kept for c in _attr(r, "notes").split(";") if c and c != "Ca"]
        merged.set("notes", ";".join(dict.fromkeys(codes)))
        merged.set("transactionType", "ExchTrade")
        out.append(merged)
    return out


CASH_SECTIONS = {  # Flex CashTransaction type -> Activity Statement section
    "deposits/withdrawals": "Deposits & Withdrawals", "deposits & withdrawals": "Deposits & Withdrawals",
    "dividends": "Dividends", "payment in lieu of dividends": "Dividends",
    "withholding tax": "Withholding Tax",
    "broker interest received": "Interest", "broker interest paid": "Interest", "bond interest received": "Interest",
    "other fees": "Fees", "commission adjustments": "Commission Adjustments",
}


def to_statement_rows(xml_text: str) -> list[list[str]]:
    root = ET.fromstring(xml_text)
    st = root.find(".//FlexStatement")
    if st is None:
        raise FlexError("format", "no FlexStatement in the response (is the query set to XML?)")
    acct = st.find("AccountInformation")
    base = _attr(acct, "currency") if acct is not None else ""
    if not base:
        raise FlexError("format", "the Flex query needs the Account Information section (base currency)")

    rows: list[list[str]] = []
    w = rows.append
    w(["Statement", "Header", "Field Name", "Field Value"])
    w(["Statement", "Data", "Title", "Flex statement (synced)"])
    w(["Statement", "Data", "Period", f"{_attr(st, 'fromDate')} - {_attr(st, 'toDate')}"])
    w(["Statement", "Data", "WhenGenerated", _dt(_attr(st, "whenGenerated"))])
    w(["Account Information", "Header", "Field Name", "Field Value"])
    w(["Account Information", "Data", "Base Currency", base])

    # trades: one row per execution; cancelled/re-booked trades netted (see _net_cancelled)
    trades = _net_cancelled([t for t in st.iter("Trade")
                             if _attr(t, "levelOfDetail", default="EXECUTION").upper() == "EXECUTION"])

    # Fills in the same second are processed in the order IBKR applied them: the piece that
    # closes a position before the piece that opens one ("C", then "C;O", then "O").
    rank = {"C": 0, "C;O": 1, "O": 2}
    trades.sort(key=lambda t: (_dt(_attr(t, "dateTime", "tradeDate")), _attr(t, "symbol"),
                               rank.get(_attr(t, "openCloseIndicator"), 1)))
    stocks = [t for t in trades if _attr(t, "assetCategory", "assetClass") == "STK"]
    forex = [t for t in trades if _attr(t, "assetCategory", "assetClass") == "CASH"]
    w(["Trades", "Header", "DataDiscriminator", "Asset Category", "Currency", "Symbol", "Date/Time", "Quantity",
       "T. Price", "C. Price", "Proceeds", "Comm/Fee", "Basis", "Realized P/L", "MTM P/L", "Code"])
    for t in stocks:
        comm = _num(_attr(t, "ibCommission", "commission")) + _num(_attr(t, "taxes"))
        w(["Trades", "Data", "Order", "Stocks", _attr(t, "currency"), _attr(t, "symbol"),
           _dt(_attr(t, "dateTime", "tradeDate")), _attr(t, "quantity"), _attr(t, "tradePrice"),
           _attr(t, "closePrice"), _attr(t, "proceeds"), str(comm), _attr(t, "costBasis", "cost", default="0"),
           _attr(t, "fifoPnlRealized", default="0"), _attr(t, "mtmPnl", default="0"),
           _attr(t, "notes", "code").replace(" ", "")])
    w(["Trades", "Header", "DataDiscriminator", "Asset Category", "Currency", "Symbol", "Date/Time", "Quantity",
       "T. Price", "", "Proceeds", f"Comm in {base}", "", "", f"MTM in {base}", "Code"])
    for t in forex:
        comm, comm_ccy = _num(_attr(t, "ibCommission", "commission")), _attr(t, "ibCommissionCurrency")
        if comm_ccy and comm_ccy != base:  # commission charged in the pair's currency: convert
            comm *= _num(_attr(t, "fxRateToBase", default="1"))
        w(["Trades", "Data", "Order", "Forex", _attr(t, "currency"), _attr(t, "symbol"),
           _dt(_attr(t, "dateTime", "tradeDate")), _attr(t, "quantity"), _attr(t, "tradePrice"), "",
           _attr(t, "proceeds"), str(comm), "", "", "0", _attr(t, "notes", "code")])

    # cash movements
    by_section: dict[str, list[ET.Element]] = {}
    for c in st.iter("CashTransaction"):
        if _attr(c, "levelOfDetail", default="DETAIL").upper() == "SUMMARY":
            continue
        sec = CASH_SECTIONS.get(_attr(c, "type").lower())
        if sec:
            by_section.setdefault(sec, []).append(c)
    for sec, items in by_section.items():
        date_col = "Settle Date" if sec == "Deposits & Withdrawals" else "Date"
        w([sec, "Header", "Currency", date_col, "Description", "Amount"])
        for c in items:
            when = _date(_attr(c, "settleDate", "dateTime", "reportDate"))
            w([sec, "Data", _attr(c, "currency"), when, _attr(c, "description"), _attr(c, "amount")])

    # open positions
    w(["Open Positions", "Header", "DataDiscriminator", "Asset Category", "Currency", "Symbol", "Quantity", "Mult",
       "Cost Price", "Cost Basis", "Close Price", "Value", "Unrealized P/L", "Code"])
    for p in st.iter("OpenPosition"):
        if _attr(p, "assetCategory", "assetClass") != "STK":
            continue
        w(["Open Positions", "Data", "Summary", "Stocks", _attr(p, "currency"), _attr(p, "symbol"),
           _attr(p, "position"), "1", _attr(p, "costBasisPrice"), _attr(p, "costBasisMoney"),
           _attr(p, "markPrice"), _attr(p, "positionValue"), _attr(p, "fifoPnlUnrealized"), ""])

    # closing exchange rates (to base) for end valuation
    latest: dict[str, tuple[str, float]] = {}
    for r in st.iter("ConversionRate"):
        if _attr(r, "toCurrency") != base:
            continue
        ccy, day = _attr(r, "fromCurrency"), _attr(r, "reportDate")
        if ccy != base and (ccy not in latest or day > latest[ccy][0]):
            latest[ccy] = (day, _num(_attr(r, "rate")))
    w(["Forex Balances", "Header", "Asset Category", "Currency", "Description", "Quantity", "Cost Price",
       f"Cost Basis in {base}", "Close Price", f"Value in {base}", f"Unrealized P/L in {base}", "Code"])
    for ccy, (_, rate) in latest.items():
        w(["Forex Balances", "Data", "Forex", base, ccy, "0", "0", "0", str(rate), "0", "0", ""])

    # listing exchanges (for charts)
    w(["Financial Instrument Information", "Header", "Asset Category", "Symbol", "Description", "Conid",
       "Security ID", "Underlying", "Listing Exch", "Multiplier", "Type", "Code"])
    seen = set()
    for t in [*stocks, *st.iter("SecurityInfo")]:
        sym = _attr(t, "symbol")
        if sym in seen or _attr(t, "assetCategory", "assetClass") != "STK":
            continue
        seen.add(sym)
        w(["Financial Instrument Information", "Data", "Stocks", sym, _attr(t, "description"), _attr(t, "conid"),
           _attr(t, "isin", "securityID"), _attr(t, "underlyingSymbol", default=sym), _attr(t, "listingExchange"),
           "1", "COMMON", ""])
    return rows


def save_statement(xml_text: str, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    buf = io.StringIO()
    csv.writer(buf).writerows(to_statement_rows(xml_text))
    path.write_text(buf.getvalue(), encoding="utf-8")
    return path
