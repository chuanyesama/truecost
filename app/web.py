"""TrueCost web app engine: the same analysis as app.py, for docs/app.html.

It runs inside the viewer's browser (Pyodide), so the statement never leaves their device. Every
function returns plain JSON-able data: the page is a list of blocks (headings, metrics, tables,
messages, Plotly figures, inputs) that docs/app.js draws. Inputs live in `p`, a dict of widget id ->
value kept by the page; changing one re-runs the tab, much like a Streamlit rerun.

The page calls everything through call(fn, args_json): load_file once per statement (reanalyse when
a setting changes), then page for the chrome and tab for whichever tab is open.
"""
from __future__ import annotations

import json
import math
import os
import sys
import tempfile
from contextlib import contextmanager
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "app"))
from i18n import Translator, money  # noqa: E402
from offers import FOUNDER_URL, PRICES  # noqa: E402
from src import costs, prices, report, rounds, style, tcalc  # noqa: E402

DEMO = ROOT / "data" / "sample" / "sample_statement.csv"
DEMO_PRICES = ROOT / "data" / "sample" / "sample_prices.csv"
METHODS = {"lot_ibkr": None, "lot_fifo": "FIFO", "lot_lifo": "LIFO", "lot_hifo": "HIFO"}
TABS = ["home", "overview", "cost", "chart", "rounds", "calc", "fees", "style", "fx", "trades"]  # i18n "tabs" order
WEB_TABS = ["home", "overview", "cost", "calc", "rounds", "chart", "fees", "style", "fx", "trades"]  # as shown
PRO_TABS = {"rounds"}  # complete on the sample account; a preview and the founder offer on a viewer's own statement
LANG_NAMES = {"en": "English", "zh": "中文"}
OFFLINE_RANGES = ["3M", "6M", "1Y"]  # what the sample account's cached daily prices cover

# colours are theme tokens; the page swaps them for the light or dark palette
POS, NEG, INK2 = "@pos", "@neg", "@ink2"

# where the web app differs from the Streamlit one: the file is read in the browser, there is no sidebar
WEB_TEXT = {
    "en": {
        "hero_private": "🔒 Read inside your browser — your statement never leaves your device. Free, no sign-up.",
        "guide_s2_body": "Drop the file into the upload box at the top of this page, or tap **Upload statement**. "
                         "Results appear in a few seconds.\n\n"
                         "🔒 Your statement is read inside your browser: it is never uploaded to a server, nothing "
                         "is stored, and no amounts, symbols or account numbers are ever sent anywhere.",
        "faq_safe_a": "Yes. TrueCost reads your statement inside your browser — the file is never uploaded to any "
                      "server and is gone when you close the tab. Anonymous usage counts (e.g. \"a statement was "
                      "uploaded\") never include amounts, symbols or account numbers. The code is open source on "
                      "GitHub.",
        "privacy_body": "- Your statement is read inside your browser and never uploaded; closing the tab clears "
                        "it.\n"
                        "- We count anonymous usage events to improve TrueCost: page opened, language, whether a "
                        "statement was uploaded, base currency, number of markets, a rough trade-count range, and "
                        "which buttons were clicked. **No amounts, symbols, account numbers or statement "
                        "contents.**\n"
                        "- A random id identifies one visit only; we don't track you across visits.\n"
                        "- Your email, feedback and survey answers are stored only if you send them, and used only "
                        "to improve TrueCost, reply or notify you.\n"
                        "- Analytics provider: PostHog (EU servers).",
        "sidebar_footer": "🔒 Your statement never leaves your browser · privacy notes at the bottom of 🏠 Home. "
                          "Not tax, financial or investment advice.",
        "chart_offline": "📈 Live price charts for your own stocks are coming to the web version soon — every other "
                         "tab already works.",
        "chart_offline_demo": "Sample account: daily prices only (3M–1Y).",
        "web_upload": "Upload statement", "web_upload_other": "Upload another statement",
        "web_settings": "Settings", "web_sample": "Back to the sample account",
        "web_loading": "Reading your statement…",
        # the round-trip scorecard is Pro; the calculator stays free
        "pro_demo_note": "⭐ **Pro feature — shown in full on the sample account.** On your own statement you'll see "
                         "how many round trips you made and their total; the full scorecard is part of Pro.",
        "swing_teaser": "We also found **{n} oversized swings** (adding beyond your core position, then selling "
                        "back). Pro breaks them down one by one, next to your round trips.",
        "lock_title": "⭐ The full round-trip scorecard is part of Pro",
        "lock_body": "- Win rate and average result per round\n"
                     "- Every round of every stock: when, how many shares, result per share\n"
                     "- Oversized swings vs round trips: where you really make and lose money\n"
                     "- Cost timeline: your real cost after every trade, next to IBKR's",
        "pro_pitch": "The full round-trip scorecard, plus today's trades and positions synced from IBKR with one-click "
                     "refresh, multi-year history, intraday charts and AI.",
        "guide_s3_table": "| Tab | The question it answers |\n|---|---|\n"
                          "| **Overview** | How much did I make in total, and how much came from trading vs currency? |\n"
                          "| **Real cost** | What did each position really cost after my round trips? Any zero-cost holdings? |\n"
                          "| **🧮 Calculator** | Before I sell: what buy-back price actually lowers my cost after commission? |\n"
                          "| **Round trips ⭐ Pro** | Does trading around a core position actually make me money? |\n"
                          "| **Chart** | Where exactly did I buy and sell on the price chart? |\n"
                          "| **Fees** | How much have commissions cost me, and how could I pay less? |\n"
                          "| **Trading style** | What kind of trader am I, and what do my habits cost me? |\n"
                          "| **Currency** | How much did exchange rates add to or take from my shares and cash? |\n"
                          "| **Trades** | Every closing trade, downloadable as CSV. |\n\n"
                          "Every page is checked against your account: the green ✅ bar at the top means TrueCost's "
                          "breakdown adds up exactly to *ending NAV − net deposits*.",
        "guide_s4_body": "Everything above is **free**, except the full round-trip scorecard (⭐). **Pro** is for active "
                         "traders:",
        "launch_status": "🚧 **What's live today:** every tab is free except the full **round-trip scorecard** (⭐ Pro — "
                         "see it in full on the sample account). **Pro, the annual report and the AI features are "
                         "still being built.** Founding members can already lock in Pro's first year for A$49, or one "
                         "month for A$12 (full refund if it isn't live by 31 Mar 2027); the report button only "
                         "registers interest. Your answers in the survey below decide what we build first.",
        "plans_table": "| | Free (live) | Pro (🚧 in development) |\n|---|---|---|\n"
                       "| Round-trip calculator, P/L split, real cost, fees, style | ✅ | ✅ |\n"
                       "| **Round-trip scorecard**: every round, win rate, swings | Count & total only | **✅ Full** |\n"
                       "| Getting your data | Download CSV & upload | **Auto-sync, today's trades, one-click refresh** |\n"
                       "| Account | None, nothing stored | Sign in; encrypted IBKR token |\n"
                       "| Chart with your trades | Daily & weekly | + intraday (2H–1M) |\n"
                       "| History | One statement at a time | Multi-year, merged |\n"
                       "| AI: ask your account, monthly review | — | ✅ |\n"
                       "| Annual report (PDF) | {report} each | Included |\n\n"
                       "**Pro: {month}/month or {year}/year. Presale: A$49 for the first year, or A$12 for one month.**",
    },
    "zh": {
        "hero_private": "🔒 在你的浏览器里读取，对账单不会离开你的设备。免费，不用注册。",
        "guide_s2_body": "把文件拖到本页顶部的上传框里，或者点「**上传对账单**」，几秒钟就出结果。\n\n"
                         "🔒 对账单只在你的浏览器里读取：不会上传到任何服务器，不保存任何内容，"
                         "也从不发送金额、股票代码或账户号码。",
        "faq_safe_a": "安全。TrueCost 在你的浏览器里读取对账单——文件不会上传到任何服务器，关掉页面就没了。匿名统计"
                      "（比如「有人上传了对账单」）从不包含金额、股票代码或账户号码。代码在 GitHub 上开源。",
        "privacy_body": "- 你的对账单只在浏览器里读取，不会上传；关掉页面就清除了。\n"
                        "- 为了改进 TrueCost，我们统计匿名使用情况：打开页面、语言、是否上传了对账单、本币、"
                        "市场数量、交易笔数的大致区间、点击了哪些按钮。**不记录任何金额、股票代码、账户号码或对账单内容。**\n"
                        "- 每次访问使用一个随机编号，不会跨访问追踪你。\n"
                        "- 只有你主动提交时才会保存邮箱、反馈和问卷回答，仅用于改进 TrueCost、回复或通知你。\n"
                        "- 统计服务商：PostHog（欧洲服务器）。",
        "sidebar_footer": "🔒 对账单不会离开你的浏览器 · 隐私说明在「🏠 首页」底部。仅供参考，不构成税务、财务或投资建议。",
        "chart_offline": "📈 网页版正在接入你自己股票的实时行情，K 线图很快上线——其他标签页都已经可以用了。",
        "chart_offline_demo": "示例账户：只有日线（3 个月到 1 年）。",
        "web_upload": "上传对账单", "web_upload_other": "换一份对账单",
        "web_settings": "设置", "web_sample": "回到示例账户",
        "web_loading": "正在读取对账单…",
        "pro_demo_note": "⭐ **专业版功能，示例账户完整展示。** 上传你自己的对账单后，可以看到做 T 的轮数和合计；"
                         "完整成绩单属于专业版。",
        "swing_teaser": "另外识别到 **{n} 次加仓波段**（加仓超过原底仓再卖回）。专业版会逐笔列出，和做 T 放在一起对比。",
        "lock_title": "⭐ 完整做 T 成绩单属于专业版",
        "lock_body": "- 胜率、平均每轮赚多少\n"
                     "- 每只股票的每一轮：什么时候、做了多少股、每股赚亏\n"
                     "- 加仓波段 vs 做 T：你到底在哪赚钱、在哪亏钱\n"
                     "- 成本走势图：每笔交易后的真实成本，和 IBKR 成本对比",
        "pro_pitch": "完整做 T 成绩单；打开网站就能看到今天的交易和持仓——自动从 IBKR 同步，点一下就刷新。"
                     "另有多年历史合并、分钟级 K 线和 AI 分析。",
        "guide_s3_table": "| 页面 | 回答什么问题 |\n|---|---|\n"
                          "| **总览** | 我一共赚了多少？其中交易赚的和汇率给的各是多少？ |\n"
                          "| **真实成本** | 做 T 之后，每只股票真实成本是多少？有没有零成本持股？ |\n"
                          "| **🧮 做T计算器** | 卖出之前：扣掉佣金后，买回价要低于多少才真的降成本？ |\n"
                          "| **做T记录 ⭐ 专业版** | 在底仓上做差价，到底有没有赚钱？ |\n"
                          "| **K线图** | 我在哪个价位、哪个时间买的卖的？ |\n"
                          "| **费用** | 佣金花了多少？怎样能少付？ |\n"
                          "| **交易风格** | 我是哪种交易者？哪些习惯在花我的钱？ |\n"
                          "| **汇率拆解** | 汇率给我的股票和现金加了多少、减了多少？ |\n"
                          "| **交易明细** | 每一笔平仓，可下载 CSV。 |\n\n"
                          "每个页面都和你的账户对过账：顶部的绿色 ✅ 表示 TrueCost 的拆分加起来"
                          "正好等于「期末净值 − 净入金」。",
        "guide_s4_body": "除了完整的做 T 成绩单（⭐），上面所有分析都是**免费**的。**专业版**适合活跃交易者：",
        "launch_status": "🚧 **目前上线的是免费版**：除了完整的**做 T 成绩单**（⭐ 专业版，示例账户可以看完整效果），"
                         "其他标签页都能直接用。**专业版、年度报告和 AI 功能都还在开发中。** 专业版现在可以 A$49 "
                         "锁定创始会员首年，或先买一个月 A$12（2027-03-31 前没上线全额退款）；年度报告的按钮只是登记兴趣，"
                         "不会扣款。先做哪个，由你在下面问卷里的回答决定。",
        "plans_table": "| | 免费版（已上线） | 专业版（🚧 开发中） |\n|---|---|---|\n"
                       "| 做T计算器、盈亏拆解、真实成本、费用、交易风格 | ✅ | ✅ |\n"
                       "| **做 T 成绩单**：每一轮明细、胜率、加仓波段 | 只看轮数和合计 | **✅ 完整** |\n"
                       "| 数据导入 | 自己下载 CSV 上传 | **自动同步、当天交易、一键刷新** |\n"
                       "| 账户 | 不用注册，不保存数据 | 登录；IBKR token 加密保存 |\n"
                       "| K线图 + 买卖点 | 日线、周线 | + 分钟级（2H–1M） |\n"
                       "| 历史范围 | 一次一份对账单 | 多年自动合并 |\n"
                       "| AI：问你的账户、每月复盘 | — | ✅ |\n"
                       "| 年度报告 PDF | 每份 {report} | 包含 |\n\n"
                       "**专业版：{month}/月，或 {year}/年。预售：首年 A$49，或单月 A$12。**",
    },
}


def translator(lang: str) -> Translator:
    t = Translator(LANG_NAMES.get(lang, "English"))
    t.d = {**t.d, **WEB_TEXT.get(lang, WEB_TEXT["en"])}
    return t


# ---------- blocks ----------
def h(text: str, level: int = 3) -> dict:
    return {"k": "h", "text": text, "level": level}


def md(text: str) -> dict:
    return {"k": "md", "md": text}


def cap(text: str) -> dict:
    return {"k": "cap", "md": text}


def msg(level: str, text: str) -> dict:
    """level: info / success / warning / error"""
    return {"k": "msg", "level": level, "md": text}


def metric(label: str, value: str, help: str | None = None, delta: str | None = None,
           delta_color: str = "normal") -> dict:
    return {"label": label, "value": value, "help": help, "delta": delta, "delta_color": delta_color}


def metrics(*items: dict) -> dict:
    return {"k": "metrics", "items": list(items)}


def cols(*columns: list, widths: list[float] | None = None) -> dict:
    return {"k": "cols", "cols": list(columns), "widths": widths or [1] * len(columns)}


def card(*blocks: dict) -> dict:
    return {"k": "card", "blocks": list(blocks)}


def expander(title: str, *blocks: dict) -> dict:
    return {"k": "expander", "title": title, "blocks": list(blocks)}


def chart(data: list, layout: dict) -> dict:
    return {"k": "chart", "fig": {"data": data, "layout": layout}}


def select(wid: str, label: str, options: list, value, labels: list | None = None, help: str | None = None) -> dict:
    return {"k": "select", "id": wid, "label": label, "value": value, "help": help,
            "options": [[o, str(l)] for o, l in zip(options, labels or options)]}


def seg(wid: str, label: str | None, options: list, value, labels: list | None = None) -> dict:
    """Segmented control / pills: one of a few options, always visible."""
    return {"k": "seg", "id": wid, "label": label, "value": value,
            "options": [[o, str(l)] for o, l in zip(options, labels or options)]}


def number(wid: str, label: str, value, decimals: int | None = 2, placeholder: str | None = None,
           help: str | None = None) -> dict:
    return {"k": "number", "id": wid, "label": label, "value": value, "decimals": decimals,
            "placeholder": placeholder, "help": help}


def slider(wid: str, label: str, lo: float, hi: float, value: float, step: float) -> dict:
    return {"k": "slider", "id": wid, "label": label, "min": lo, "max": hi, "value": value, "step": step}


def _blank(v) -> bool:
    try:
        return v is None or bool(pd.isna(v))
    except (TypeError, ValueError):
        return False


def _cell(v, f) -> str:
    if isinstance(v, str):
        return v
    if _blank(v):
        return "—"
    if f is not None:
        return f(v) if callable(f) else f.format(v)
    if isinstance(v, pd.Timestamp):
        return f"{v:%Y-%m-%d}" if v == v.normalize() else f"{v:%Y-%m-%d %H:%M:%S}"
    if isinstance(v, bool):
        return "✓" if v else ""
    if isinstance(v, int) or (hasattr(v, "dtype") and "int" in str(v.dtype)):
        return f"{int(v):,}"
    if isinstance(v, float) or hasattr(v, "dtype"):
        return f"{float(v):,.2f}"
    return str(v)


def table(df: pd.DataFrame, fmt: dict | None = None, max_rows: int | None = None) -> dict:
    """A formatted, read-only table. fmt: column -> format string or function, as in Styler.format."""
    fmt = fmt or {}
    right = [pd.api.types.is_numeric_dtype(df[c]) or c in fmt for c in df.columns]
    rows = [[_cell(v, fmt.get(c)) for c, v in zip(df.columns, rec)] for rec in df.itertuples(index=False)]
    return {"k": "table", "cols": [str(c) for c in df.columns], "rows": rows, "right": right, "max_rows": max_rows}


def txt(series: pd.Series, f: str, na: str = "—") -> pd.Series:
    return series.map(lambda v: na if pd.isna(v) else f.format(v))


def padded_range(values, pad: float = 0.18) -> list[float]:
    """y-range with room for labels above/below the bars (waterfall: cumulative values)."""
    lo, hi = min(0.0, *values), max(0.0, *values)
    span = (hi - lo) or 1.0
    return [lo - span * pad, hi + span * pad]


def clean(o):
    """Make numpy / pandas values JSON-safe; NaN becomes null."""
    if isinstance(o, dict):
        return {str(k): clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [clean(v) for v in o]
    if isinstance(o, (pd.Series, pd.Index)):
        return [clean(v) for v in o.tolist()]
    if isinstance(o, pd.Timestamp):
        return o.isoformat()
    if getattr(o, "ndim", 0) > 0:  # numpy array
        return [clean(v) for v in o.tolist()]
    if hasattr(o, "item") and not isinstance(o, (str, bytes)):
        o = o.item()
    if isinstance(o, float) and not math.isfinite(o):
        return None
    return o


def dumps(o) -> str:
    return json.dumps(clean(o), ensure_ascii=False)


# ---------- state ----------
@contextmanager
def _tmp(data: bytes):
    fd, path = tempfile.mkstemp(suffix=".csv")
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(data)
        yield path
    finally:
        os.unlink(path)


S: dict = {}


def load(data: bytes | None = None, method: str = "lot_ibkr", source: str = "ecb") -> str:
    """Analyse a statement (None: the sample account). Returns JSON: ok, demo, base, and the counts the
    page reports to analytics."""
    demo = data is None
    raw = DEMO.read_bytes() if demo else bytes(data)
    method = method if method in METHODS else "lot_ibkr"
    try:
        with _tmp(raw) as path:
            r = report.build(path, METHODS[method], source)
    except Exception as e:  # not an IBKR Activity Statement, or a format we don't handle yet
        return dumps({"ok": False, "error": type(e).__name__})
    S.clear()
    S.update(raw=raw, demo=demo, method=method, r=r)
    return dumps({"ok": True, "demo": demo, "base": r.base, "source": r.fx_source,
                  "markets": int(r.stock_trades["currency"].nunique()), "trades": len(r.stock_trades),
                  "reconciles": bool(r.reconciles)})


def load_file(path: str | None = None, method: str = "lot_ibkr", source: str = "ecb") -> str:
    """The page writes the chosen file into the browser's in-memory file system; read it and forget it."""
    if path is None:
        return load(None, method, source)
    try:
        data = Path(path).read_bytes()
    finally:
        Path(path).unlink(missing_ok=True)
    return load(data, method, source)


def reanalyse(method: str = "lot_ibkr", source: str = "ecb") -> str:
    """Same statement, another lot-matching method or exchange-rate source."""
    return load(None if S.get("demo", True) else S["raw"], method, source)


def call(fn: str, args_json: str = "{}") -> str:
    """The page's single entry point; arguments and result are JSON."""
    fns = {"load_file": load_file, "reanalyse": reanalyse, "page": page, "tab": tab, "chart_target": chart_target}
    return fns[fn](**json.loads(args_json))


def _costs():
    if "fc" not in S:
        with _tmp(S["raw"]) as path:
            S["fc"] = costs.analyse(S["r"], path)
    return S["fc"]


def _profile():
    if "prof" not in S:
        S["prof"] = style.profile(S["r"])
    return S["prof"]


class Ctx:
    """What every tab needs: the report, translator and money formatting in the base currency."""

    def __init__(self, lang: str, p: dict):
        self.lang, self.p = lang, p or {}
        self.t = translator(lang)
        self.r = S["r"]
        self.B = self.r.base
        self.demo = S["demo"]
        a = self.r.attribution
        self.a = a
        self.trading = a["stock_price"]
        self.currency = a["stock_fx"] + a["cash_fx"] + a["conversion"]
        self.other = a["income_fees"]
        self.TAB = dict(zip(TABS[1:], self.t("tabs")))

    def m(self, x, sign=True, d=0) -> str:
        return money(x, self.B, sign, d)

    def get(self, wid: str, default):
        v = self.p.get(wid)
        return default if v is None else v

    def price_of(self, item: str) -> str:
        table = PRICES[item]
        ccy = self.B if self.B in table else "USD"
        v = table[ccy]
        return money(v, ccy, sign=False, decimals=0 if float(v).is_integer() else 2)


# ---------- page chrome ----------
def page(lang: str, p: dict | None = None) -> str:
    c = Ctx(lang, p)
    t, r = c.t, c.r
    header = []
    if not c.demo:
        header.append(cap(t("as_of", date=f"{r.end:%Y-%m-%d}", base=c.B, source=t("fx_" + r.fx_source))))
        header.append(msg("success", t("reconciled_friendly", pl=c.m(r.total_pl))) if r.reconciles
                      else msg("error", t("not_reconciled", diff=c.m(r.total_pl - (r.nav_end - r.net_deposits)))))
    sources = ["rba", "ecb"] if c.B == "AUD" else ["ecb"]
    names = dict(zip(TABS, [t("tab_home")] + t("tabs")))
    keys = ["hero_title", "hero_sub", "hero_upload", "hero_private", "hero_or", "upload_label", "advanced",
            "lot_method", "lot_method_help", "fx_source", "parse_error", "disclaimer", "sidebar_footer",
            "pro_title", "pro_pitch", "web_upload", "web_upload_other", "web_settings", "web_sample", "web_loading"]
    return dumps({
        "demo": c.demo,
        "text": {k: t(k) for k in keys} | {"hero_pills": t("hero_pills")},
        "tabs": [[k, names[k] + (" ⭐" if k in PRO_TABS else "")] for k in WEB_TABS],
        "header": header,
        "settings": [
            select("method", t("lot_method"), list(METHODS), S["method"], [t(k) for k in METHODS],
                   help=t("lot_method_help")),
            select("source", t("fx_source"), sources, r.fx_source, [t("fx_" + s) for s in sources]),
        ],
        "pro": [msg("warning", t("pro_status")), founder_offer(c, "web_footer")],
    })


def tab(name: str, lang: str, p: dict | None = None, bars: str | None = None) -> str:
    c = Ctx(lang, p)
    fn = {"home": home, "overview": overview, "cost": real_cost, "rounds": round_trips, "calc": calculator,
          "fees": fees, "style": trading_style, "fx": currency_tab, "trades": trades}.get(name)
    blocks = chart_tab(c, bars) if name == "chart" else fn(c) if fn else []
    return dumps(blocks)


# ---------- offers, feedback, survey (handled in the page; analytics events go from there) ----------
def founder_offer(c: Ctx, where: str) -> dict:
    t = c.t
    return {"k": "founder", "where": where, "pay": t("founder_pay"), "demo": c.demo, "base": c.B,
            "plans": [{"plan": plan, "label": t(f"pro_button_{plan}"), "terms": t(f"founder_terms_{plan}"),
                       "url": url, "primary": plan == "year"} for plan, url in FOUNDER_URL.items()]}


def report_offer(c: Ctx, where: str) -> dict:
    t = c.t
    price = c.price_of("report")
    return {"k": "offer", "kind": "report", "where": where, "price": price, "label": t("report_button", price=price),
            "soon": t("offer_soon"), "email": t("offer_email"), "notify": t("offer_notify"),
            "thanks": t("offer_thanks"), "bad_email": t("offer_bad_email"), "base": c.B, "demo": c.demo}


def feedback_form(c: Ctx, where: str) -> dict:
    t = c.t
    return {"k": "feedback", "where": where, "label": t("feedback_label"), "placeholder": t("feedback_placeholder"),
            "email": t("offer_email"), "send": t("feedback_send"), "thanks": t("feedback_thanks")}


def survey(c: Ctx) -> dict:
    t = c.t
    ccy = c.B if c.B in PRICES["pro_month"] else "USD"
    scale = PRICES["pro_month"][ccy] / PRICES["pro_month"]["AUD"]
    opts = lambda keys, prefix: [[k, t(prefix + k)] for k in keys]  # noqa: E731
    return {"k": "survey", "send": t("sv_send"), "thanks": t("survey_thanks"), "base": c.B, "demo": c.demo,
            "questions": [
                {"id": "pay", "type": "radio", "label": t("sv_pay_q", price=c.price_of("pro_month")),
                 "options": opts(["yes", "cheaper", "maybe", "no"], "sv_pay_")},
                {"id": "price_aud", "type": "steps", "label": t("sv_price_q"), "value": 9,
                 "options": [[v, t("sv_price_free") if v == 0 else money(round(v * scale), ccy, sign=False)
                              + t("sv_per_month")] for v in [0, 3, 5, 9, 15]]},
                {"id": "report", "type": "radio", "label": t("sv_report_q", price=c.price_of("report")),
                 "options": opts(["yes", "maybe", "no"], "sv_report_"), "horizontal": True},
                {"id": "ai", "type": "multi", "label": t("sv_ai_q"),
                 "options": opts(["ask", "review", "coach", "import", "explain"], "sv_ai_")},
                {"id": "ai_text", "type": "text", "label": t("sv_ai_text")},
                {"id": "other", "type": "text", "label": t("sv_other"), "placeholder": t("feedback_placeholder")},
                {"id": "email", "type": "email", "label": t("sv_email")},
            ]}


# ---------- 🏠 home ----------
def finding_cards(c: Ctx) -> list:
    t, r, m = c.t, c.r, c.m
    fc = _costs()
    if r.total_pl > 0:
        line = t("card_money_fx") if c.currency > c.trading else t("card_money_trade", fx=m(c.currency))
    elif c.currency > 0:
        line = t("card_money_offset", trading=m(-c.trading, False), fx=m(c.currency, False))
    else:
        line = t("card_money_both")
    money_card = card(md(f"**{t('card_money')}**"),
                      metrics(metric(t("card_trading"), m(c.trading)), metric(t("card_fx"), m(c.currency)))
                      | {"stack": True},
                      md(line), cap(t("card_go", tab=c.TAB["overview"])))

    cost_blocks = [md(f"**{t('card_cost')}**")]
    hd = r.holdings.copy()
    if not hd.empty:
        hd["price"] = hd["symbol"].map(r.prices)
        zero = hd[hd["diluted_cost"] <= 0]
        if not zero.empty:
            z = zero.iloc[0]
            cost_blocks += [metrics(metric(z["symbol"], t("card_zero_value"))),
                            md(t("card_cost_zero", extra=money(-z["diluted_cost"] * z["shares"], z["currency"], False),
                                 ibkr=f"{z['ibkr_avg_cost']:,.2f}"))]
        else:
            hd["ibkr"] = 100 * (hd["price"] / hd["ibkr_avg_cost"] - 1)
            hd["real"] = 100 * (hd["price"] / hd["diluted_cost"] - 1)
            g = hd.loc[(hd["real"] - hd["ibkr"]).abs().idxmax()]
            cost_blocks += [metrics(metric(g["symbol"], f"{g['real']:+.1f}%", help=t("card_real_help"))),
                            md(t("card_cost_gap_line", ibkr=g["ibkr"], real=g["real"]))]
    else:
        done = r.rounds[r.rounds["done"]] if not r.rounds.empty else r.rounds
        cost_blocks += [metrics(metric(t("card_rounds_label"), m(done["result_base"].sum() if len(done) else 0))),
                        md(t("card_cost_rounds", n=len(done)))]
    cost_blocks.append(cap(t("card_go", tab=c.TAB["cost"])))

    gross = c.trading + fc.stock
    fee_line = (t("card_fees_share", share=fc.stock / gross) if gross > 0 and fc.stock > 0.3 * gross
                else t("card_fees_avg", n=f"{len(fc.trades):,}", avg=m(fc.stock / max(len(fc.trades), 1), False, 2)))
    fee_card = card(md(f"**{t('card_fees')}**"), metrics(metric(t("card_fees_label"), m(-fc.total))),
                    md(fee_line), cap(t("card_go", tab=c.TAB["fees"])))
    prof = _profile()
    return [cols([money_card], [card(*cost_blocks)], [fee_card]),
            md(t("style_line", style=t("style_" + prof.style), tab=c.TAB["style"]))]


def home(c: Ctx) -> list:
    t = c.t
    out = [h(t("findings_demo") if c.demo else t("findings_you"))]
    if c.demo:
        out.append(cap(t("demo_note")))
    out += finding_cards(c)
    out.append(msg("info", t("survey_callout")))
    if c.demo:
        out += [{"k": "hr"}, h(t("steps_title")),
                cols(*[[card(md(f"**{t(f'step{n}_t')}**"), md(t(f"step{n}_d")))] for n in (1, 2, 3)]),
                expander(t("steps_detail"), md(t("guide_s1_body")), md(f"**{t('guide_s1_mistakes')}**"),
                         md(t("guide_s1_mistakes_body")), md(t("guide_s2_body")))]
    out += [expander(t("tabs_explained"), md(t("guide_s3_table"))), {"k": "hr"},
            h(t("guide_s4")), msg("warning", t("launch_status")), md(t("guide_s4_body")),
            md(t("plans_table", month=c.price_of("pro_month"), year=c.price_of("pro_year"),
                 report=c.price_of("report"))),
            cols([founder_offer(c, "web_guide")], [report_offer(c, "web_guide")]),
            {"k": "hr"},
            card(h(t("survey_title")), cap(t("survey_sub")), survey(c)),
            h(t("guide_faq"), 4)]
    out += [expander(t(f"faq_{q}_q"), md(t(f"faq_{q}_a"))) for q in ("pro_setup", "safe", "diff", "brokers", "advice")]
    out += [{"k": "hr"},
            cols([card(h(t("privacy_title"), 4), md(t("privacy_body")))],
                 [card(h(t("feedback_title"), 4), feedback_form(c, "home"))]),
            cap(t("disclaimer"))]
    return out


# ---------- overview ----------
def overview(c: Ctx) -> list:
    t, r, m, B = c.t, c.r, c.m, c.B
    out = [metrics(metric(t("total_pl", base=B), m(r.total_pl)),
                   metric(t("from_trading"), m(c.trading), help=t("from_trading_help")),
                   metric(t("from_fx"), m(c.currency), help=t("from_fx_help")),
                   metric(t("other"), m(c.other), help=t("other_help")))]
    if r.total_pl > 0 and c.currency > 0 and c.trading < c.currency:
        out.append(msg("info", t("fx_driven", fx=m(c.currency), trading=m(c.trading))))
    out.append(cap(t("fees_note")))
    parts = [(t("wf_trading"), c.trading), (t("wf_fx"), c.currency), (t("wf_other"), c.other)]
    steps = [sum(v for _, v in parts[: i + 1]) for i in range(len(parts))] + [r.total_pl]
    out.append(chart([{
        "type": "waterfall", "x": [n for n, _ in parts] + [t("wf_total")], "y": [v for _, v in parts] + [0],
        "measure": ["relative"] * len(parts) + ["total"],
        "text": [m(v) for _, v in parts] + [m(r.total_pl)], "textposition": "outside",
        "increasing": {"marker": {"color": POS}}, "decreasing": {"marker": {"color": NEG}},
        "totals": {"marker": {"color": INK2}}, "connector": {"line": {"color": "@grid", "width": 1}},
        "hovertemplate": "%{x}<br>%{text}<extra></extra>"}],
        {"height": 460, "margin": {"t": 40, "b": 10, "l": 10, "r": 10}, "showlegend": False,
         "yaxis": {"title": {"text": B}, "range": padded_range(steps)}}))
    if not r.sells.empty:
        by = r.sells.groupby("currency", as_index=False)[["realized", "realized_base"]].sum()
        by.columns = [t("col_ccy"), t("col_realized_local"), t("col_realized_base", base=B)]
        out += [h(t("by_market")), cap(t("by_market_caption")),
                table(by, {by.columns[1]: "{:,.0f}", by.columns[2]: "{:+,.0f}"})]
    return out


# ---------- real cost ----------
def real_cost(c: Ctx) -> list:
    t, r, B = c.t, c.r, c.B
    out = [h(t("real_cost_title")), cap(t("real_cost_caption"))]
    hd = r.holdings.copy()
    if hd.empty:
        out.append(md(t("no_holdings")))
    else:
        hd["price"] = hd["symbol"].map(r.prices)
        hd["zero_cost"] = hd["diluted_cost"] <= 0
        hd["vs_ibkr"] = 100 * (hd["price"] / hd["ibkr_avg_cost"] - 1)
        hd["vs_diluted"] = (100 * (hd["price"] / hd["diluted_cost"] - 1)).where(~hd["zero_cost"])
        zero_label = t("zero_cost")
        extra = [t("already_up", amount=money(-d * n, ccy, sign=False)) for d, n, ccy in
                 zip(hd["diluted_cost"], hd["shares"], hd["currency"])]
        show = pd.DataFrame({
            t("c_symbol"): hd["symbol"], t("c_shares"): hd["shares"], t("c_price"): hd["price"],
            t("c_ibkr_cost"): hd["ibkr_avg_cost"],
            t("c_diluted"): txt(hd["diluted_cost"].where(~hd["zero_cost"]), "{:,.2f}", zero_label),
            t("c_vs_ibkr"): hd["vs_ibkr"],
            t("c_vs_diluted"): [e if z else f"{v:+.1f}%" for z, e, v in zip(hd["zero_cost"], extra, hd["vs_diluted"])],
            t("c_ibkr_cost_base", base=B): hd["ibkr_avg_cost_base"],
            t("c_diluted_base", base=B): txt(hd["diluted_cost_base"].where(~hd["zero_cost"]), "{:,.2f}", zero_label),
            t("c_cycle_realized"): hd["realized_this_cycle"],
        })
        cl = show.columns
        out.append(table(show, {cl[1]: "{:,.4g}", cl[2]: "{:,.2f}", cl[3]: "{:,.2f}", cl[5]: "{:+.1f}%",
                                cl[7]: "{:,.2f}", cl[9]: "{:+,.0f}"}))
        for row in hd.itertuples():
            if row.zero_cost:
                out.append(msg("success", t("zero_cost_msg", sym=row.symbol, ccy=row.currency,
                                            extra=-row.diluted_cost * row.shares, shares=row.shares,
                                            value=row.price * row.shares, ibkr=row.ibkr_avg_cost)))
                continue
            gap = row.vs_diluted - row.vs_ibkr
            if gap >= 5:
                out.append(msg("success", t("better_msg", sym=row.symbol, ibkr=row.vs_ibkr, real=row.vs_diluted)))
            elif gap <= -5:
                out.append(msg("warning", t("worse_msg", sym=row.symbol, ibkr=row.vs_ibkr, real=row.vs_diluted)))
        traces = []
        for col, name, color, sym in [("ibkr_avg_cost", t("s_ibkr_cost"), INK2, "circle-open"),
                                      ("diluted_cost", t("s_diluted"), POS, "circle"),
                                      ("price", t("s_price"), NEG, "diamond")]:
            vals = hd[col].where(~hd["zero_cost"]) if col == "diluted_cost" else hd[col]
            traces.append({"type": "scatter", "x": vals / hd["price"] * 100 - 100, "y": hd["symbol"],
                           "mode": "markers", "name": name,
                           "marker": {"size": 16, "color": color, "symbol": sym, "line": {"width": 2, "color": color}},
                           "customdata": hd[col], "hovertemplate": "%{y} " + name + ": %{customdata:,.2f}<extra></extra>"})
        out.append(chart(traces, {"height": 140 + 70 * len(hd), "margin": {"t": 20, "b": 10, "l": 10, "r": 10},
                                  "xaxis": {"title": {"text": t("rel_price")}, "ticksuffix": "%"},
                                  "yaxis": {"type": "category"},
                                  "legend": {"orientation": "h", "y": 1.15}}))

    out += [h(t("all_stocks")), cap(t("all_stocks_caption"))]
    cyc = r.cycles.copy()
    if not cyc.empty:
        cyc["result_base"] = cyc["cash_base"].where(~cyc["open"])
        per = cyc.groupby(["symbol", "currency"], as_index=False).agg(
            cycles=("start", "size"), trades=("trades", "sum"),
            closed_base=("result_base", "sum"), holding=("open", "any"))
        hold_cols = r.holdings[["symbol", "diluted_cost", "diluted_cost_base"]] if not r.holdings.empty else \
            pd.DataFrame(columns=["symbol", "diluted_cost", "diluted_cost_base"])
        per = per.merge(hold_cols, on="symbol", how="left")
        per["status"] = per["holding"].map({True: t("status_open"), False: t("status_closed")})
        per.loc[per["diluted_cost"] <= 0, "status"] = t("status_zero")
        per["last"] = per["symbol"].map(r.stock_trades.groupby("symbol")["time"].max())
        per["first"] = per["symbol"].map(cyc.groupby("symbol")["start"].min())
        sort_opts = {"sort_loss": ("closed_base", True), "sort_gain": ("closed_base", False),
                     "sort_recent": ("last", False), "sort_oldest": ("first", True),
                     "sort_trades": ("trades", False), "sort_symbol": ("symbol", True)}
        how = c.get("sort_by", "sort_loss")
        how = how if how in sort_opts else "sort_loss"
        col, asc = sort_opts[how]
        per = per.sort_values(col, ascending=asc, na_position="last")
        diluted = lambda s: [t("zero_cost") if d <= 0 else ("—" if pd.isna(d) else f"{d:,.2f}") for d in s]  # noqa: E731
        view = pd.DataFrame({
            t("c_symbol"): per["symbol"], t("col_ccy"): per["currency"], t("c_status"): per["status"],
            t("c_cycles"): per["cycles"], t("c_trades"): per["trades"],
            t("c_closed_pl", base=B): txt(per["closed_base"].where(per["closed_base"] != 0), "{:+,.0f}"),
            t("c_last_trade"): txt(per["last"], "{:%Y-%m-%d}"),
            t("c_cur_diluted"): diluted(per["diluted_cost"]),
            t("c_cur_diluted_base", base=B): diluted(per["diluted_cost_base"]),
        })
        out += [select("sort_by", t("sort_by"), list(sort_opts), how, [t(k) for k in sort_opts]),
                table(view, max_rows=25)]
    return out


# ---------- chart ----------
def chart_target(lang: str, p: dict | None = None) -> str:
    """Which candles the chart tab needs, so the page can fetch them before calling tab("chart")."""
    c = Ctx(lang, p)
    pick, rk, ticker = _chart_pick(c)
    return dumps({"ticker": ticker, "range": rk,
                  "query": prices.chart_query(ticker, rk) if ticker else None})


def _chart_pick(c: Ctx):
    st = c.r.stock_trades
    order = list(st.groupby("symbol")["time"].max().sort_values(ascending=False).index)
    pick = c.get("chart_stock", order[0] if order else None)
    pick = pick if pick in order else (order[0] if order else None)
    rk = c.get("chart_range", "6M")
    rk = rk if rk in prices.RANGES else "6M"
    ins = c.r.instruments.set_index("symbol") if not c.r.instruments.empty else None
    ticker = (prices.yahoo_symbol(ins["quote"][pick], ins["exchange"][pick], ins["underlying"][pick])
              if ins is not None and pick in ins.index else None)
    return pick, rk, ticker


def _sample_bars(pick: str, rk: str) -> tuple[pd.DataFrame, str] | None:
    """The sample account's cached daily prices, for when live prices can't be fetched."""
    if not c_demo() or rk not in OFFLINE_RANGES:
        return None
    px = pd.read_csv(DEMO_PRICES, parse_dates=["date"])
    px = px[px["symbol"] == pick]
    if px.empty:
        return None
    months = {"3M": 3, "6M": 6, "1Y": 12}[rk]
    px = px[px["date"] > px["date"].max() - pd.DateOffset(months=months)]
    tz = "Europe/Stockholm" if pick.endswith("-B") else "America/New_York"
    bars = px.set_index(pd.DatetimeIndex(px["date"]).tz_localize(tz))[["open", "high", "low", "close"]]
    bars["volume"] = 0.0
    return bars, tz


def c_demo() -> bool:
    return bool(S.get("demo"))


def chart_tab(c: Ctx, bars_json: str | None) -> list:
    t, r = c.t, c.r
    st = r.stock_trades
    if st.empty:
        return [h(t("chart_title")), md(t("rounds_none"))]
    last_trade = st.groupby("symbol")["time"].max().sort_values(ascending=False)
    ccy_of = st.groupby("symbol")["currency"].first()
    pick, rk, ticker = _chart_pick(c)
    offline = bars_json is None
    ranges = OFFLINE_RANGES if offline and c.demo else list(prices.RANGES)
    if rk not in ranges:
        rk = "6M"
    out = [h(t("chart_title")),
           cols([select("chart_stock", t("chart_stock"), list(last_trade.index), pick,
                        [f"{s} · {ccy_of[s]}" for s in last_trade.index])],
                [seg("chart_range", t("chart_range"), ranges, rk)], widths=[2, 5])]
    ins = r.instruments.set_index("symbol") if not r.instruments.empty else None
    exch = ins["exchange"].get(pick) if ins is not None and pick in ins.index else None
    if ticker is None:
        return out + [msg("info", t("chart_unmapped", sym=pick, exch=exch or "?"))]
    bars = ex_tz = None
    if not offline:
        try:
            bars, ex_tz = prices.parse_bars(json.loads(bars_json), ticker, rk)
        except Exception:
            bars = None
    if bars is None:
        sample = _sample_bars(pick, rk)
        if sample is not None:
            bars, ex_tz = sample
            out.append(cap(t("chart_offline_demo")))
        elif offline:
            return out + [msg("info", t("chart_offline"))]
        else:
            return out + [msg("warning", t("chart_no_data", ticker=ticker))]
    if bars.empty:
        return out + [msg("warning", t("chart_no_data", ticker=ticker))]

    up, down = ("#e34948", "#1baf7a") if c.lang == "zh" else ("#1baf7a", "#e34948")
    intraday = rk in prices.INTRADAY
    mine = st[st["symbol"] == pick]
    marks = prices.place_trades(mine, bars, r.statement_tz, intraday)
    label = pd.Series(bars.index.strftime("%m-%d %H:%M" if intraday else "%Y-%m-%d"), index=bars.index)
    rising = bars["close"] >= bars["open"]
    data = [
        {"type": "candlestick", "x": label, "open": bars["open"], "high": bars["high"], "low": bars["low"],
         "close": bars["close"], "name": ticker, "showlegend": False, "xaxis": "x", "yaxis": "y",
         "increasing": {"line": {"color": up}, "fillcolor": up},
         "decreasing": {"line": {"color": down}, "fillcolor": down}},
        {"type": "bar", "x": label, "y": bars["volume"], "xaxis": "x2", "yaxis": "y2", "showlegend": False,
         "marker": {"color": [up if v else down for v in rising], "opacity": 0.45}, "name": t("chart_volume"),
         "hovertemplate": "%{x}<br>" + t("chart_volume") + " %{y:,.0f}<extra></extra>"},
    ]
    pad = (bars["high"].max() - bars["low"].min()) * 0.035
    for side, color, edge, sign in [("B", POS, "low", -1), ("S", NEG, "high", 1)]:
        mk = marks[marks["side"] == side]
        if mk.empty:
            continue
        data.append({
            "type": "scatter", "x": label[mk["bar"]].to_numpy(), "y": bars.loc[mk["bar"], edge].to_numpy() + sign * pad,
            "mode": "markers+text", "text": [side] * len(mk), "textposition": "middle center",
            "textfont": {"color": "white", "size": 12}, "xaxis": "x", "yaxis": "y",
            "marker": {"size": 22, "color": color, "line": {"width": 1.5, "color": "white"}},
            "name": t("chart_" + side), "showlegend": True,
            "customdata": mk[["count", "qty", "avg_price"]].to_numpy(),
            "hovertemplate": "%{x}<br><b>" + t("chart_" + side) + "</b> · " + t("chart_hover") + "<extra></extra>"})
    out.append(chart(data, {
        "height": 640, "margin": {"t": 30, "b": 10, "l": 10, "r": 10}, "hovermode": "closest",
        "legend": {"orientation": "h", "y": 1.06, "x": 0},
        "xaxis": {"type": "category", "nticks": 8, "matches": "x2", "showticklabels": False, "anchor": "y",
                  "rangeslider": {"visible": False}, "showspikes": True, "spikethickness": 1},
        "xaxis2": {"type": "category", "nticks": 8, "anchor": "y2"},
        "yaxis": {"domain": [0.23, 1], "title": {"text": t("price_axis", ccy=ccy_of[pick])}},
        "yaxis2": {"domain": [0, 0.2], "showticklabels": False}}))
    n_in = int(marks["count"].sum()) if not marks.empty else 0
    out.append(cap(t("chart_caption", shown=n_in, total=len(mine), ticker=ticker, tz=ex_tz)))
    return out


# ---------- round trips ----------
def round_trips(c: Ctx) -> list:
    t, r, m, B = c.t, c.r, c.m, c.B
    rd = r.rounds
    if rd.empty:
        return [md(t("rounds_none"))]
    done_all = rd[rd["done"]]
    done = done_all[done_all["kind"] != rounds.SWING]
    swing = done_all[done_all["kind"] == rounds.SWING]
    if not c.demo:
        return rounds_preview(c, done, swing)
    out = [h(t("rounds_title")), msg("info", t("pro_demo_note")), cap(t("rounds_caption", base=B)),
           metrics(metric(t("m_rounds"), f"{len(done)}"),
                   metric(t("m_win"), f"{(done['result_base'] > 0).mean():.0%}" if len(done) else "—"),
                   metric(t("m_rounds_total"), m(done["result_base"].sum())),
                   metric(t("m_avg_round"), m(done["result_base"].mean()) if len(done) else "—"))]
    if not swing.empty:
        verdict = t("swing_verdict") if done["result_base"].sum() > 0 > swing["result_base"].sum() else ""
        out.append(msg("info", t("swing_msg", n=len(swing), total=m(swing["result_base"].sum()),
                                 win=(swing["result_base"] > 0).mean()) + verdict))
    by = done_all.groupby("kind", as_index=False).agg(n=("result_base", "size"),
                                                      win=("result_base", lambda x: (x > 0).mean()),
                                                      total=("result_base", "sum"))
    by["kind"] = by["kind"].map(lambda k: t("kind_" + k))
    by.columns = [t("c_kind"), t("c_n"), t("c_win"), t("c_total", base=B)]
    out.append(table(by, {by.columns[2]: "{:.0%}", by.columns[3]: "{:+,.0f}"}))

    per = done.groupby("symbol", as_index=False).agg(
        n=("result_base", "size"), win=("result_base", lambda x: (x > 0).mean()),
        total=("result_base", "sum")).sort_values("total", ascending=False)
    if not per.empty:
        out.append(chart([{
            "type": "bar", "x": per["total"], "y": per["symbol"], "orientation": "h",
            "marker": {"color": [POS if v >= 0 else NEG for v in per["total"]], "cornerradius": 4},
            "text": [m(v) for v in per["total"]], "textposition": "outside",
            "customdata": [t("rounds_hover", n=n, win=f"{w:.0%}") for n, w in zip(per["n"], per["win"])],
            "hovertemplate": "%{y}<br>%{text} · %{customdata}<extra></extra>"}],
            {"height": max(320, 36 * len(per)), "margin": {"t": 10, "b": 10, "l": 10, "r": 90},
             "xaxis": {"title": {"text": t("rounds_axis", base=B)}},
             "yaxis": {"autorange": "reversed", "type": "category"}}))

    symbols = per["symbol"].tolist() or sorted(rd["symbol"].unique())
    pick = c.get("rounds_stock", symbols[0])
    pick = pick if pick in symbols else symbols[0]
    one = rd[rd["symbol"] == pick]
    tv = pd.DataFrame({
        t("c_start"): one["start"], t("c_end"): txt(one["end"], "{:%Y-%m-%d %H:%M}"),
        t("c_kind"): one["kind"].map(lambda k: t("kind_" + k)),
        t("c_base_pos"): one["base"], t("c_round_qty"): one["qty"], t("c_round_trades"): one["trades"],
        t("c_result_local"): txt(one["result"], "{:+,.2f}"), t("c_per_share"): txt(one["per_share"], "{:+,.2f}"),
        t("c_result_base", base=B): txt(one["result_base"], "{:+,.0f}"),
        t("c_state"): one["done"].map({True: t("state_done"), False: t("state_open")}),
    }).sort_values(t("c_start"), ascending=False)
    out += [h(t("one_stock")), select("rounds_stock", t("pick_stock"), symbols, pick),
            table(tv, {tv.columns[0]: "{:%Y-%m-%d %H:%M}", tv.columns[3]: "{:,.4g}", tv.columns[4]: "{:,.4g}"})]

    tl = rounds.timeline(r.stock_trades, pick)
    data = [{"type": "scatter", "x": tl["time"], "y": tl["ibkr_avg_cost"], "name": t("s_ibkr_cost"), "mode": "lines",
             "line": {"color": INK2, "width": 2, "shape": "hv", "dash": "dot"}},
            {"type": "scatter", "x": tl["time"], "y": tl["diluted_cost"], "name": t("s_diluted"), "mode": "lines",
             "line": {"color": POS, "width": 2, "shape": "hv"}}]
    for side, color, sym in [("buy", POS, "triangle-up"), ("sell", NEG, "triangle-down")]:
        x = tl[tl["side"] == side]
        data.append({"type": "scatter", "x": x["time"], "y": x["price"], "name": t(side), "mode": "markers",
                     "marker": {"color": color, "size": 12, "symbol": sym},
                     "customdata": x[["qty", "shares"]].to_numpy(),
                     "hovertemplate": t(side) + " %{customdata[0]:,.4g} @ %{y:,.2f}<br>" + t("after_pos")
                     + " %{customdata[1]:,.4g}<extra></extra>"})
    lo, hi = tl["price"].min(), tl["price"].max()
    pad = (hi - lo) * 0.15 or hi * 0.05
    out += [cap(t("timeline_caption")),
            chart(data, {"height": 540, "margin": {"t": 40, "b": 10, "l": 10, "r": 10}, "hovermode": "closest",
                         "yaxis": {"title": {"text": t("price_axis", ccy=one["currency"].iloc[0])},
                                   "range": [lo - pad, hi + pad]},
                         "legend": {"orientation": "h", "y": 1.12}})]
    return out


def rounds_preview(c: Ctx, done: pd.DataFrame, swing: pd.DataFrame) -> list:
    """Pro preview on the viewer's own statement: how many rounds and their total; the rest is behind the offer."""
    t, m = c.t, c.m
    out = [h(t("rounds_title")), cap(t("rounds_caption", base=c.B)),
           metrics(metric(t("m_rounds"), f"{len(done)}"), metric(t("m_rounds_total"), m(done["result_base"].sum())),
                   metric(t("m_win"), "🔒"), metric(t("m_avg_round"), "🔒"))]
    if not swing.empty:
        out.append(msg("info", t("swing_teaser", n=len(swing))))
    out.append({"k": "locked", "blocks": [h(t("lock_title"), 4), md(t("lock_body")), cap(t("pro_status")),
                                          founder_offer(c, "web_rounds")]})
    return out


# ---------- round-trip calculator ----------
def fee_estimate(c: Ctx, sym: str | None, q: float, price: float) -> tuple[float, str]:
    """Commission per order: from the viewer's own trades in this stock when there are any, else IBKR's fixed rate."""
    if sym:
        st = c.r.stock_trades
        mine = st[(st["symbol"] == sym) & (st["commission"] < 0)]
        if len(mine) >= 3:
            paid = -mine["commission"]
            per_share = paid.sum() / mine["qty"].abs().sum()
            return max(paid.min(), per_share * q), "fee_mine"
    return tcalc.ibkr_fixed_fee(q, price), "fee_ibkr"


def _num(c: Ctx, wid: str, default: float, lo: float | None = 0.0) -> float:
    v = c.get(wid, default)
    try:
        v = float(v)
    except (TypeError, ValueError):
        v = default
    return max(lo, v) if lo is not None else v


def plan_calculator(c: Ctx) -> list:
    t, r = c.t, c.r
    held = r.holdings[r.holdings["shares"] > 0] if not r.holdings.empty else r.holdings
    manual = "__manual__"
    syms = (list(held["symbol"]) if not held.empty else []) + [manual]
    sym = c.get("tc_pick", syms[0])
    sym = sym if sym in syms else syms[0]
    row = None if sym == manual else held[held["symbol"] == sym].iloc[0]
    k = f"tc_{sym}"  # a different stock starts from its own numbers
    left = [select("tc_pick", t("tc_pick"), syms, sym, [s if s != manual else t("tc_manual") for s in syms],
                   help=t("tc_pick_help")),
            md(f"**① {t('tc_hold')}**")]
    n = _num(c, k + "_n", float(row.shares) if row is not None else 1000.0)
    hold_row = [[number(k + "_n", t("tc_shares"), n, None)]]
    if row is not None:
        basis = c.get(k + "_basis", "real")
        basis = basis if basis in ("real", "ibkr") else "real"
        hold_row.append([seg(k + "_basis", t("tc_basis"), ["real", "ibkr"], basis,
                             [t("tc_basis_" + v) for v in ("real", "ibkr")])])
        default_c = float(row.diluted_cost if basis == "real" else row.ibkr_avg_cost)
    else:
        basis, default_c = None, 100.0
    cost = _num(c, f"{k}_c_{basis}", round(default_c, 2), lo=None)
    left += [cols(*hold_row), number(f"{k}_c_{basis}", t("tc_cost"), cost)]
    if row is not None and row.diluted_cost <= 0 and basis == "real":
        left.append(cap(t("tc_zero_note")))
    q = _num(c, k + "_q", float(round(n * 0.3)) if n else 0.0)
    price_now = r.prices.get(sym) if row is not None else None
    price_now = float(price_now) if price_now is not None and pd.notna(price_now) else None
    s = _num(c, k + "_s", round(price_now or (cost * 1.1 if cost > 0 else 110.0), 2))
    left += [md(f"**② {t('tc_sell_title')}**"),
             cols([number(k + "_q", t("tc_qty"), q, None)], [number(k + "_s", t("tc_sell"), s)])]
    if price_now:
        left.append(cap(t("tc_price_now", price=price_now)))
    est, how = fee_estimate(c, None if row is None else sym, q, s)
    fee_in = c.p.get(k + "_fee")
    fee_in = max(0.0, float(fee_in)) if isinstance(fee_in, (int, float)) else None
    left += [md(f"**③ {t('tc_fee_title')}**"),
             number(k + "_fee", t("tc_fee"), fee_in, placeholder=f"{est:.2f}"),
             cap(t(how, fee=est) if fee_in is None else t("tc_fee_own", fees=2 * fee_in))]

    p = tcalc.Plan(shares=n, cost=cost, qty=q, sell=s, fee=est if fee_in is None else fee_in)
    if not p.ok:
        return [cols(left, [card(msg("info", t("tc_need")))], widths=[1, 1.15])]
    bb_id = f"{k}_bb_{s}"
    bb = _num(c, bb_id, round(s * 0.95, 2))
    bb = min(max(bb, round(s * 0.8, 2)), round(s * 1.1, 2))
    g, nc = p.gain(bb), p.new_cost(bb)
    right = [metrics(metric(t("tc_be"), f"{p.break_even:,.2f}")),
             cap(t("tc_be_say", q=p.qty, s=s, fees=p.fees, be=p.break_even, gap=s - p.break_even,
                   pct=(p.break_even / s - 1) * 100)),
             slider(bb_id, t("tc_if"), round(s * 0.8, 2), round(s * 1.1, 2), bb, 0.01),
             metrics(metric(t("tc_gain"), f"{g:+,.2f}", help=t("tc_gain_help", fees=p.fees)),
                     metric(t("tc_newcost"), t("zero_cost") if nc <= 0 else f"{nc:,.2f}",
                            delta=f"{(nc / cost - 1) * 100:+.1f}%" if cost > 0 else None, delta_color="inverse"))]
    levels = [(0.03, t("tc_up")), (None, t("tc_be_short")), (-0.01, ""), (-0.02, ""), (-0.03, ""),
              (-0.05, ""), (-0.08, ""), (-0.1, "")]
    rows = []
    for lvl, tag in levels:
        price = p.break_even if lvl is None else s * (1 + lvl)
        nc_ = p.new_cost(price)
        rows.append({t("tc_th_b"): f"{price:,.2f}" + (f"  ({lvl:+.0%})" if lvl is not None else "")
                     + (f"  {tag}" if tag else ""),
                     t("tc_th_gain"): f"{round(p.gain(price), 2) + 0:+,.2f}",  # no "-0.00" at break-even
                     t("tc_th_cost"): t("zero_cost") if nc_ <= 0 else f"{nc_:,.2f}"})
    tgt_id = f"{k}_tgt_{cost}"
    target = _num(c, tgt_id, round(cost * 0.97, 2) if cost > 0 else 0.0, lo=None)
    need = p.buy_back_for(target)
    if target >= cost:
        verdict = t("tc_tgt_above", be=p.break_even)
    elif need <= 0:
        verdict = t("tc_tgt_no", q=p.qty)
    else:
        verdict = t("tc_tgt_ok", b=need, pct=(need / s - 1) * 100)
    right += [md(f"**{t('tc_table')}**"), table(pd.DataFrame(rows)),
              number(tgt_id, t("tc_target"), target), md(verdict),
              msg("warning", t("tc_risk", up=s * 1.05, cost=p.new_cost(s * 1.05), left=n - p.qty)),
              cap(t("tc_fine"))]
    return [cols(left, [card(*right)], widths=[1, 1.15])]


REVIEW_PRESETS = {
    "good": (100, 100, 110, [(50, 120, 105), (50, 118, 102)]),
    "bad": (100, 100, 100, [(50, 95, 104), (50, 98, 106)]),
    "zero": (100, 100, 120, [(100, 150, 110), (100, 140, 100), (100, 130, 95)]),
}


def review_calculator(c: Ctx) -> list:
    t = c.t
    pick = c.get("tc_example", "good")
    pick = pick if pick in REVIEW_PRESETS else "good"
    n0, p0, now, rds = REVIEW_PRESETS[pick]
    k = "tcr_" + pick  # picking an example resets the inputs
    n0, p0, now = _num(c, k + "_n", float(n0)), _num(c, k + "_p", float(p0)), _num(c, k + "_now", float(now))
    grid = c.get(k + "_rounds", [list(x) for x in rds])
    clean_rows = []
    for row in grid if isinstance(grid, list) else []:
        vals = []
        for v in (list(row) + [None] * 3)[:3]:
            try:
                vals.append(max(0.0, float(v)))
            except (TypeError, ValueError):
                vals.append(0.0)
        clean_rows.append(tuple(vals))
    labels = [t("tc_qty"), t("tc_sell"), t("tc_buy")]
    left = [md(f"**① {t('tc_first')}**"),
            cols([number(k + "_n", t("tc_bought"), n0, None)], [number(k + "_p", t("tc_price"), p0)]),
            md(f"**② {t('tc_rounds')}**"), cap(t("tc_rounds_hint")),
            {"k": "grid", "id": k + "_rounds", "cols": labels, "rows": grid, "decimals": [0, 2, 2]},
            md(f"**③ {t('tc_now')}**"), number(k + "_now", t("tc_now"), now)]
    rv = tcalc.review(n0, p0, clean_rows)
    pct = lambda cost: f"{(now / cost - 1) * 100:+.1f}% @ {now:,.2f}" if cost > 0 else None  # noqa: E731
    right = [metrics(metric(t("tc_ibkr"), f"{rv.ibkr_cost:,.2f}", delta=pct(rv.ibkr_cost), delta_color="off"),
                     metric(t("tc_real"), t("zero_cost") if rv.real_cost <= 0 else f"{rv.real_cost:,.2f}",
                            delta=pct(rv.real_cost), delta_color="off"))]
    if not rv.rounds or abs(rv.real_cost - rv.ibkr_cost) < 0.005:
        right.append(msg("info", t("tc_say_same")))
    elif rv.real_cost <= 0:
        right.append(msg("success", t("tc_say_zero", extra=-rv.cash_in, ibkr=rv.ibkr_cost)))
    elif rv.real_cost < rv.ibkr_cost:
        right.append(msg("success", t("tc_say_lower", diff=p0 - rv.real_cost, pct=(rv.real_cost / p0 - 1) * 100)))
    else:
        right.append(msg("warning", t("tc_say_higher", diff=rv.real_cost - p0)))
    right.append(cap(t("tc_review_fine")))
    return [cap(t("tc_review_note", tab=c.TAB["cost"])),
            seg("tc_example", t("tc_examples"), list(REVIEW_PRESETS), pick,
                [t("tc_ex_" + v) for v in REVIEW_PRESETS]),
            cols(left, [card(*right)], widths=[1.4, 1])]


def calculator(c: Ctx) -> list:
    t = c.t
    mode = c.get("tc_mode", "plan")
    mode = mode if mode in ("plan", "review") else "plan"
    body = plan_calculator(c) if mode == "plan" else review_calculator(c)
    return [h(t("tc_title")), cap(t("tc_caption")),
            seg("tc_mode", None, ["plan", "review"], mode, [t("tc_mode_" + v) for v in ("plan", "review")]),
            *body, cap(t("tc_share"))]


# ---------- fees ----------
def fees(c: Ctx) -> list:
    t, m, B = c.t, c.m, c.B
    fc = _costs()
    gross = c.trading + fc.stock
    out = [h(t("fees_title")), cap(t("fees_caption")),
           metrics(metric(t("f_total"), m(-fc.total)),
                   metric(t("f_orders"), f"{len(fc.trades):,}",
                          help=t("f_orders_help", avg=m(fc.stock / max(len(fc.trades), 1), False, 2))),
                   metric(t("f_annual"), m(-fc.total * 365 / fc.days), help=t("f_annual_help", days=fc.days)),
                   metric(t("f_share"), f"{fc.stock / gross:.0%}" if gross > 0 else "—", help=t("f_share_help")))]
    if gross > 0:
        out.append(chart([{
            "type": "waterfall", "x": [t("wf_gross"), t("wf_fees"), t("wf_net")],
            "measure": ["absolute", "relative", "total"], "y": [gross, -fc.stock, 0],
            "text": [m(gross), m(-fc.stock), m(c.trading)], "textposition": "outside",
            "increasing": {"marker": {"color": POS}}, "decreasing": {"marker": {"color": NEG}},
            "totals": {"marker": {"color": INK2}}, "connector": {"line": {"color": "@grid", "width": 1}},
            "hovertemplate": "%{x}<br>%{text}<extra></extra>"}],
            {"height": 420, "margin": {"t": 40, "b": 10, "l": 10, "r": 10}, "showlegend": False,
             "yaxis": {"title": {"text": B}, "range": padded_range([gross, c.trading])}}))
    if fc.usd_min_share > 0.3:
        out.append(msg("warning", t("min_msg", share=fc.usd_min_share, ps=fc.usd_per_share,
                                    x=fc.usd_per_share / 0.005)))
    saving_l = [metrics(metric(t("merge"), m(fc.merge_saving, False), help=t("merge_help", n=fc.merge_orders))),
                cap(t("merge_caption", n=fc.merge_orders))]
    saving_r = ([metrics(metric(t("tiered"), m(fc.tiered_saving, False), help=t("tiered_help"))),
                 cap(t("tiered_caption", a=fc.tiered_actual_usd, e=fc.tiered_estimate_usd))]
                if fc.tiered_actual_usd > 0 else [])
    out += [h(t("savings"), 5), cols(saving_l, saving_r), cap(t("savings_warn"))]

    names = [t("c_orders"), t("c_comm"), t("c_per_order"), t("c_bps")]
    fmt = {t("c_comm"): lambda v: m(v, False), t("c_per_order"): lambda v: m(v, False, 2), t("c_bps"): "{:.1f}"}
    bs = fc.by_size.copy()
    bs.columns = [t("c_size")] + names
    bm = fc.by_market.copy()
    bm.columns = [t("col_ccy")] + names
    out += [h(t("where"), 5),
            cols([cap(t("by_size", base=B)), table(bs, fmt)], [cap(t("by_mkt")), table(bm, fmt)])]
    bym = fc.by_month
    out.append(chart([{
        "type": "bar", "x": bym["month"].astype(str), "y": bym["commission"],
        "marker": {"color": POS, "cornerradius": 4},
        "text": [m(v, False) for v in bym["commission"]], "textposition": "outside",
        "customdata": bym["orders"],
        "hovertemplate": "%{x}<br>%{text} · %{customdata} " + t("orders_word") + "<extra></extra>"}],
        {"title": {"text": t("monthly")}, "height": 380, "margin": {"t": 50, "b": 10, "l": 10, "r": 10},
         "xaxis": {"type": "category"},
         "yaxis": {"title": {"text": B}, "range": padded_range(bym["commission"].tolist(), 0.15)}}))
    top = fc.by_symbol.head(10).copy()
    top.columns = [t("c_symbol")] + names
    out += [cap(t("top_symbols")), table(top, fmt)]
    return out


# ---------- trading style ----------
MONEY_PARAMS = ("gross", "net", "total", "swing_total", "avg_win", "avg_loss", "pl", "best_pl", "fx")


def render_insight(c: Ctx, i: style.Insight) -> str:
    t, m = c.t, c.m
    p = dict(i.params)
    for k in MONEY_PARAMS:
        if k in p:
            p[k] = m(p[k])
    if "commission" in p:
        p["commission"] = m(-p["commission"])
    if "per_trade" in p:
        p["per_trade"] = m(p["per_trade"], False, 2)
    if "worst" in p:
        p["worst"] = ", ".join(f"{s} {m(v)}" for s, v in p["worst"])
    base_key = "fees_eat_profit" if i.key.startswith("fees_eat_profit") else i.key
    body = f"**{t(f'i_{i.key}_t', **p)}**\n\n{t(f'i_{base_key}_e', **p)}"
    if i.key == "cuts_losses" and i.params.get("but_big"):
        body += t("i_cuts_losses_but")
    if t.has(f"i_{base_key}_s"):
        body += f"\n\n💡 {t(f'i_{base_key}_s')}"
    return body


def trading_style(c: Ctx) -> list:
    t, m = c.t, c.m
    p = _profile()
    mt = p.metrics
    label = t("style_" + p.style)
    if p.tags:
        names = [t("tag_" + k, **kw) for k, kw in p.tags]
        label += f"（{'、'.join(names)}）" if c.lang == "zh" else f" ({', '.join(names)})"
    mix = p.holding_mix
    out = [h(t("style_title", style=label)),
           cap(t("style_detail", tpd=mt["trades_per_day"], intraday=mt["intraday_share"], hold=mt["median_hold_days"])),
           metrics(metric(t("k_win"), f"{mt['win_rate']:.0%}", help=t("k_win_help")),
                   metric(t("k_payoff"), f"{mt['payoff']:.2f}", help=t("k_payoff_help")),
                   metric(t("k_pf"), f"{mt['profit_factor']:.2f}", help=t("k_pf_help")),
                   metric(t("k_comm"), m(-mt["commission"]),
                          help=t("k_comm_help", avg=m(mt["commission_per_trade"], False, 2)))),
           chart([{"type": "bar", "x": mix["share"] * 100, "y": [t("hold_" + b) for b in mix["bucket"]],
                   "orientation": "h", "marker": {"color": POS, "cornerradius": 4},
                   "text": [f"{v:.0%}" for v in mix["share"]], "textposition": "outside",
                   "customdata": [t("hold_hover", share=f"{v:.0%}") for v in mix["share"]],
                   "hovertemplate": "%{y}: %{customdata}<extra></extra>"}],
                 {"title": {"text": t("hold_title")}, "height": 320, "margin": {"t": 50, "b": 10, "l": 10, "r": 40},
                  "xaxis": {"ticksuffix": "%", "range": [0, 100]},
                  "yaxis": {"autorange": "reversed", "type": "category"}}),
           h(t("insights"))]
    order = {"warn": 0, "info": 1, "good": 2}
    level = {"warn": "warning", "info": "info", "good": "success"}
    out += [msg(level[i.level], render_insight(c, i)) for i in sorted(p.insights, key=lambda x: order[x.level])]
    out.append(cap(t("style_disclaimer")))
    return out


# ---------- currency ----------
def currency_tab(c: Ctx) -> list:
    t, r, m, B, a = c.t, c.r, c.m, c.B, c.a
    out = [h(t("fx_title")), cap(t("fx_caption", base=B))]
    d = r.decomposition
    if not d.empty:
        dd = pd.DataFrame({
            t("c_symbol"): d["symbol"], t("col_ccy"): d["currency"],
            t("c_ret_local"): d["return_local_pct"], t("c_ret_base", base=B): d["return_base_pct"],
            t("c_price_eff"): d["price_effect"], t("c_fx_eff"): d["fx_effect"], t("c_cross"): d["cross_effect"],
            t("c_gain_base", base=B): d["gain_base"],
        })
        out.append(table(dd, {cl: "{:+.1f}%" for cl in dd.columns[2:4]} | {cl: "{:+,.0f}" for cl in dd.columns[4:]}))
    out += [h(t("fx_split_title")), cap(t("fx_split_caption")),
            metrics(metric(t("fx_on_shares"), m(a["stock_fx"])), metric(t("fx_on_cash"), m(a["cash_fx"])),
                    metric(t("fx_conversion"), m(a["conversion"]))),
            h(t("cash_title")), cap(t("cash_caption", base=B))]
    if not r.cash.empty:
        cc = r.cash
        cv = pd.DataFrame({
            t("col_ccy"): cc["currency"], t("c_balance"): cc["balance"], t("c_value_base", base=B): cc["value_base"],
            t("c_fx_realized"): cc["realized_fx"], t("c_fx_unrealized"): cc["unrealized_fx"],
            t("c_fx_total"): cc["realized_fx"] + cc["unrealized_fx"],
        })
        out.append(table(cv, {cv.columns[1]: "{:,.2f}", cv.columns[2]: "{:,.0f}"}
                         | {cl: "{:+,.0f}" for cl in cv.columns[3:]}))
    out.append(cap(t("fx_source_note", source=t("fx_" + r.fx_source))))
    return out


# ---------- trades ----------
def trades(c: Ctx) -> list:
    t, r, B = c.t, c.r, c.B
    out = [h(t("trades_title"))]
    s = r.sells.copy()
    if s.empty:
        return out
    s["holding_days"] = s.apply(lambda x: (x["time"] - min(tm for tm, _ in x["lots"])).days, axis=1)
    tt = pd.DataFrame({
        t("c_time"): s["time"], t("c_symbol"): s["symbol"], t("col_ccy"): s["currency"],
        t("c_side"): s["side"].map(lambda v: t("side_" + v)), t("c_qty"): s["qty"], t("c_method"): s["method"],
        t("col_realized_local"): s["realized"], t("col_realized_base", base=B): s["realized_base"],
        t("c_hold_days"): s["holding_days"],
    })
    symbols = sorted(s["symbol"].unique())
    picked = [x for x in c.get("trades_filter", []) if x in symbols]
    if picked:
        tt = tt[tt[t("c_symbol")].isin(picked)]
    tt = tt.sort_values(t("c_time"), ascending=False)
    out += [{"k": "multi", "id": "trades_filter", "label": t("filter"), "options": [[x, x] for x in symbols],
             "value": picked},
            table(tt, {t("c_time"): "{:%Y-%m-%d %H:%M:%S}", t("c_qty"): "{:,.4g}", tt.columns[6]: "{:+,.2f}",
                       tt.columns[7]: "{:+,.2f}"}, max_rows=20),
            {"k": "download", "label": t("download"), "filename": "truecost_trades.csv",
             "text": tt.to_csv(index=False)}]
    return out
