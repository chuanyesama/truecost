"""Flex XML -> Activity-Statement layout -> full report, offline."""
import pytest

from src import costbasis as cb, flex, ingest, report

FLEX_XML = """<FlexQueryResponse queryName="truecost" type="AF">
<FlexStatements count="1">
<FlexStatement accountId="U0000000" fromDate="20260504" toDate="20260930" whenGenerated="20261001;090000">
  <AccountInformation accountId="U0000000" currency="AUD" />
  <Trades>
    <Trade assetCategory="CASH" symbol="AUD.USD" currency="USD" dateTime="20260504;100000" quantity="-10000"
           tradePrice="0.65" proceeds="6500" ibCommission="-2" ibCommissionCurrency="AUD" levelOfDetail="EXECUTION"/>
    <Trade assetCategory="STK" symbol="MDB" currency="USD" listingExchange="NASDAQ" underlyingSymbol="MDB"
           dateTime="20260505;233000" quantity="10" tradePrice="300" closePrice="301" proceeds="-3000"
           ibCommission="-1" costBasis="3001" fifoPnlRealized="0" notes="O" levelOfDetail="EXECUTION"/>
    <Trade assetCategory="STK" symbol="MDB" currency="USD" listingExchange="NASDAQ" underlyingSymbol="MDB"
           dateTime="20260506;233000" quantity="10" tradePrice="290" closePrice="291" proceeds="-2900"
           ibCommission="-1" costBasis="2901" fifoPnlRealized="0" notes="O" levelOfDetail="EXECUTION"/>
    <Trade assetCategory="STK" symbol="MDB" currency="USD" listingExchange="NASDAQ" underlyingSymbol="MDB"
           dateTime="20260507;233000" quantity="-10" tradePrice="310" closePrice="309" proceeds="3100"
           ibCommission="-1" costBasis="-2901" fifoPnlRealized="198" notes="C" levelOfDetail="EXECUTION"/>
    <Trade assetCategory="STK" symbol="MDB" currency="USD" levelOfDetail="CLOSED_LOT"
           dateTime="20260507;233000" quantity="-10" tradePrice="310" proceeds="3100"/>
  </Trades>
  <CashTransactions>
    <CashTransaction type="Deposits/Withdrawals" currency="AUD" amount="10000" settleDate="20260504"
                     description="Electronic Fund Transfer" levelOfDetail="DETAIL"/>
    <CashTransaction type="Broker Interest Received" currency="USD" amount="1.5" dateTime="20260601"
                     description="USD Credit Interest" levelOfDetail="DETAIL"/>
  </CashTransactions>
  <OpenPositions>
    <OpenPosition assetCategory="STK" symbol="MDB" currency="USD" position="10" markPrice="320"
                  costBasisPrice="300.1" levelOfDetail="SUMMARY"/>
  </OpenPositions>
  <ConversionRates>
    <ConversionRate reportDate="20260929" fromCurrency="USD" toCurrency="AUD" rate="1.50"/>
    <ConversionRate reportDate="20260930" fromCurrency="USD" toCurrency="AUD" rate="1.52"/>
  </ConversionRates>
</FlexStatement>
</FlexStatements>
</FlexQueryResponse>"""


@pytest.fixture
def statement(tmp_path):
    return flex.save_statement(FLEX_XML, tmp_path / "flex.csv")


def test_conversion_keeps_executions_only(statement):
    t = ingest.load_stock_trades(statement)
    assert len(t) == 3  # the CLOSED_LOT detail row is not a trade
    assert t["time"].iloc[0].strftime("%Y-%m-%d %H:%M") == "2026-05-05 23:30"
    assert ingest.account_info(statement)["Base Currency"] == "AUD"


def test_report_from_flex_reconciles(statement):
    r = report.build(statement, fx_source="ecb")
    assert r.base == "AUD"
    assert r.reconciles
    assert r.holdings.iloc[0]["shares"] == 10
    assert r.instruments.set_index("symbol").loc["MDB", "exchange"] == "NASDAQ"


def test_missing_election_codes_fall_back_to_inference(statement):
    # IBKR realized +198 on selling 10 @310: matches LIFO (the @290 lot), not FIFO (the @300 lot)
    t = ingest.load_stock_trades(statement)
    assert t["lot_method"].isna().all()
    assert cb.infer_lot_method(t) == "LIFO"


def test_error_response_is_reported():
    err = "<FlexStatementResponse><Status>Fail</Status><ErrorCode>1012</ErrorCode>" \
          "<ErrorMessage>Token has expired.</ErrorMessage></FlexStatementResponse>"
    assert flex._status(err) == ("Fail", "1012", "Token has expired.")
    assert flex._status(FLEX_XML)[0] is None  # a real statement is data, not a status
