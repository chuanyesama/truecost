"""The web app engine (app/web.py) and its bundle for docs/app/."""
import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app"))
import web  # noqa: E402
from i18n import money  # noqa: E402

spec = importlib.util.spec_from_file_location("build_web", ROOT / "scripts" / "build_web.py")
build_web = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build_web)


def test_engine_bundle_is_current():
    built = build_web.build()
    assert (ROOT / "docs" / "app" / "engine.zip").read_bytes() == built, "run: python scripts/build_web.py"
    worker = (ROOT / "docs" / "app" / "py-worker.js").read_text(encoding="utf-8")
    assert f'ENGINE_VERSION = "{build_web.version(built)}"' in worker


@pytest.mark.parametrize("lang", ["en", "zh"])
def test_every_tab_renders(lang):
    info = json.loads(web.load(None))
    assert info["ok"] and info["demo"] and info["reconciles"]
    page = json.loads(web.page(lang, {}))
    assert sorted(k for k, _ in page["tabs"]) == sorted(web.TABS)
    for name in web.TABS:
        assert json.loads(web.tab(name, lang, {})), name


def test_round_trip_scorecard_is_pro_on_your_own_statement():
    web.load(None)
    sample = web.tab("rounds", "en", {})
    assert '"k": "locked"' not in sample and "rounds_stock" in sample  # the sample account shows it all
    web.load(web.DEMO.read_bytes())  # the same file, as a viewer's own upload
    own = json.loads(web.tab("rounds", "en", {}))
    assert own[-1]["k"] == "locked" and "rounds_stock" not in json.dumps(own)
    assert own[-1]["blocks"][-1]["where"] == "web_rounds"
    assert json.loads(web.tab("calc", "en", {}))  # the calculator stays free


def test_overview_matches_the_report():
    web.load(None)
    r = web.S["r"]
    first = json.loads(web.tab("overview", "en", {}))[0]
    assert first["items"][0]["value"] == money(r.total_pl, r.base)


def test_not_a_statement():
    assert json.loads(web.load(b"hello,world\n"))["ok"] is False


def test_entry_point_and_calculator_inputs():
    json.loads(web.call("load_file", "{}"))
    p = {"tc_pick": "__manual__", "tc___manual___n": 100, "tc___manual___c_None": 50, "tc___manual___q": 40,
         "tc___manual___s": 60, "tc___manual___fee": 1}
    out = json.dumps(json.loads(web.call("tab", json.dumps({"name": "calc", "lang": "en", "p": p}))))
    assert '"value": "59.95"' in out  # break-even: 60 - 2 * 1 / 40


def test_chart_without_live_prices():
    web.load(None)
    sample = json.dumps(json.loads(web.tab("chart", "en", {})))  # sample account: cached daily prices
    assert '"candlestick"' in sample
    target = json.loads(web.chart_target("en", {}))
    assert target["query"].startswith("/v8/finance/chart/")


def test_chart_from_a_yahoo_payload():
    web.load(None)
    payload = {"chart": {"error": None, "result": [{
        "meta": {"exchangeTimezoneName": "America/New_York"},
        "timestamp": [1780000000 + 86400 * i for i in range(5)],
        "indicators": {"quote": [{"open": [1, 2, 3, 4, 5], "high": [2, 3, 4, 5, 6], "low": [0.5, 1, 2, 3, 4],
                                  "close": [1.5, 2.5, 3.5, 4.5, 5.5], "volume": [10, 20, 30, 40, 50]}]}}]}}
    out = json.loads(web.tab("chart", "en", {}, json.dumps(payload)))
    fig = next(b for b in out if b["k"] == "chart")["fig"]
    assert fig["data"][0]["close"] == [1.5, 2.5, 3.5, 4.5, 5.5]
