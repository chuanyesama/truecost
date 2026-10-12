"""TrueCost - Streamlit front end.

Run:  streamlit run app/app.py
"""
from __future__ import annotations

import os
import sys
import tempfile
from contextlib import contextmanager
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "app"))
from i18n import Translator, money  # noqa: E402
from src import costs, report, rounds, style  # noqa: E402

LOCAL_FILES = [] if os.environ.get("TRUECOST_DEMO") else sorted((ROOT / "data" / "raw").glob("*.csv"))  # never committed
DEMO = ROOT / "data" / "sample" / "sample_statement.csv"     # synthetic, safe to publish

# reference palette (dataviz skill): gain / loss poles, recessive ink
POS, NEG = "#2a78d6", "#eb6834"
INK2, GRID = "#52514e", "#e7e6e2"
CLEAR = dict(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font=dict(size=15))
TITLE = dict(size=18)
FONT = 16


def plot(fig: go.Figure) -> None:
    """Readable text on every chart, in both themes."""
    fig.update_layout(font=dict(size=FONT), legend=dict(font=dict(size=FONT)), hoverlabel=dict(font_size=FONT))
    fig.update_xaxes(tickfont=dict(size=FONT - 1), title_font=dict(size=FONT))
    fig.update_yaxes(tickfont=dict(size=FONT - 1), title_font=dict(size=FONT))
    fig.update_traces(textfont=dict(size=FONT), selector=lambda tr: hasattr(tr, "textfont"))
    fig.update_traces(cliponaxis=False, selector=lambda tr: hasattr(tr, "cliponaxis"))
    st.plotly_chart(fig, use_container_width=True)


def padded_range(values, pad: float = 0.18) -> list[float]:
    """y-range with room for labels above/below the bars (waterfall: cumulative values)."""
    lo, hi = min(0.0, *values), max(0.0, *values)
    span = (hi - lo) or 1.0
    return [lo - span * pad, hi + span * pad]

METHODS = {"lot_ibkr": None, "lot_fifo": "FIFO", "lot_lifo": "LIFO", "lot_hifo": "HIFO"}

st.set_page_config(page_title="TrueCost", page_icon="💱", layout="wide")
# larger base text in both light and dark themes (Streamlit sizes everything in rem)
st.markdown("<style>html { font-size: 18px; }</style>", unsafe_allow_html=True)
if (st.context.theme.type or "light") == "light":
    # Streamlit's light warning box is pale yellow text on pale yellow; darken it
    st.markdown("""<style>
      [data-testid="stAlertContentWarning"] { color: #4a3600; }
      [data-testid="stAlertContentWarning"] strong { color: #3a2a00; }
      [data-testid="stAlertContainer"]:has([data-testid="stAlertContentWarning"]) {
        background: #fff4d6; border: 1px solid #e3b33d; }
    </style>""", unsafe_allow_html=True)


def txt(series: pd.Series, fmt: str, na: str = "—") -> pd.Series:
    """Pre-format a column; st.dataframe shows None for missing values otherwise."""
    return series.map(lambda v: na if pd.isna(v) else fmt.format(v))


def md(text: str) -> str:
    """Escape $ so Streamlit markdown doesn't render $..$ as LaTeX."""
    return text.replace("$", r"\$")


@contextmanager
def _tmp(data: bytes):
    """Statement bytes on disk only for as long as parsing takes."""
    fd, path = tempfile.mkstemp(suffix=".csv")
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(data)
        yield path
    finally:
        os.unlink(path)


@st.cache_data(show_spinner=False, ttl=3600, max_entries=20)
def load(data: bytes, method: str | None, source: str):
    with _tmp(data) as path:
        return report.build(path, method, source)


@st.cache_data(show_spinner=False, ttl=3600, max_entries=20)
def load_costs(data: bytes, method: str | None, source: str):
    r = load(data, method, source)
    with _tmp(data) as path:
        return costs.analyse(r, path)


@st.cache_data(show_spinner=False, ttl=3600, max_entries=20)
def load_profile(data: bytes, method: str | None, source: str):
    return style.profile(load(data, method, source))


def set_theme(name: str) -> None:
    """Save the viewer's choice where Streamlit keeps it (this browser only) and reload."""
    components.html(f"""<script>
      const w = window.parent;
      const tabs = [...w.document.querySelectorAll('button[role="tab"]')];
      const open = tabs.findIndex(b => b.getAttribute("aria-selected") === "true");
      const url = new URL(w.location.href);
      if (open >= 0) url.searchParams.set("tab", open);
      w.history.replaceState(null, "", url);
      w.localStorage.setItem(`stActiveTheme-${{w.location.pathname}}-v1`, JSON.stringify({{name: "{name}"}}));
      w.location.reload();
    </script>""", height=0)


# ---------- sidebar ----------
with st.sidebar:
    top_l, top_r = st.columns([3, 2])
    # language lives in the URL (?lang=zh) so it survives the reload a theme switch causes
    langs = {"en": "English", "zh": "中文"}
    current = langs.get(st.query_params.get("lang", "en"), "English")
    lang = top_l.radio("Language / 语言", list(langs.values()), index=list(langs.values()).index(current),
                       horizontal=True, label_visibility="collapsed")
    st.query_params["lang"] = next(k for k, v in langs.items() if v == lang)
    t = Translator(lang)
    dark = (st.context.theme.type or "light") == "dark"
    if top_r.toggle("🌙", value=dark, help=t("theme_help")) != dark:
        set_theme("Light" if dark else "Dark")
    st.header(t("upload_header"))
    up = st.file_uploader(t("upload_label"), type="csv")
    with st.expander(t("how_to")):
        st.markdown(t("how_to_steps"))
    method_key = st.selectbox(t("lot_method"), list(METHODS), format_func=t, help=t("lot_method_help"))

demo = False
if up is not None:
    raw = up.getvalue()
elif LOCAL_FILES:
    raw = LOCAL_FILES[0].read_bytes()
    st.sidebar.info(t("local_file", name=LOCAL_FILES[0].name))
else:
    raw, demo = DEMO.read_bytes(), True

with st.spinner(t("parsing")):
    probe = load(raw, None, "ecb")
with st.sidebar:
    sources = ["rba", "ecb"] if probe.base == "AUD" else ["ecb"]
    source = st.selectbox(t("fx_source"), sources, format_func=lambda s: t("fx_" + s))
    st.caption(t("disclaimer"))

with st.spinner(t("parsing")):
    r = load(raw, METHODS[method_key], source)
B = r.base
m_ = lambda x, sign=True, d=0: money(x, B, sign, d)  # noqa: E731
a = r.attribution
trading = a["stock_price"]
currency = a["stock_fx"] + a["cash_fx"] + a["conversion"]
other = a["income_fees"]

# ---------- header ----------
st.title("TrueCost")
st.caption(t("tagline"))
st.caption(t("as_of", date=f"{r.end:%Y-%m-%d}", base=B, source=t("fx_" + r.fx_source)))
if demo:
    st.info(t("demo_banner"))
if r.reconciles:
    st.success(md(t("reconciled", nav=m_(r.nav_end, False), dep=m_(r.net_deposits, False), pl=m_(r.total_pl))))
else:
    st.error(md(t("not_reconciled", diff=m_(r.total_pl - (r.nav_end - r.net_deposits)))))

tab_names = t("tabs")
try:  # the theme switch reloads the page; reopen the tab the viewer was on
    open_tab = tab_names[int(st.query_params.get("tab", 0))]
except (ValueError, IndexError):
    open_tab = tab_names[0]
tab_overview, tab_cost, tab_t, tab_fees, tab_style, tab_fx, tab_trades = st.tabs(tab_names, default=open_tab)

# ---------- overview ----------
with tab_overview:
    c0, c1, c2, c3 = st.columns(4)
    c0.metric(t("total_pl", base=B), m_(r.total_pl))
    c1.metric(t("from_trading"), m_(trading), help=t("from_trading_help"))
    c2.metric(t("from_fx"), m_(currency), help=t("from_fx_help"))
    c3.metric(t("other"), m_(other), help=t("other_help"))
    if r.total_pl > 0 and currency > 0 and trading < currency:
        st.info(md(t("fx_driven", fx=m_(currency), trading=m_(trading))))
    st.caption(t("fees_note"))

    parts = [(t("wf_trading"), trading), (t("wf_fx"), currency), (t("wf_other"), other)]
    fig = go.Figure(go.Waterfall(
        x=[p[0] for p in parts] + [t("wf_total")], y=[p[1] for p in parts] + [0],
        measure=["relative"] * len(parts) + ["total"],
        text=[m_(p[1]) for p in parts] + [m_(r.total_pl)], textposition="outside",
        increasing={"marker": {"color": POS}}, decreasing={"marker": {"color": NEG}},
        totals={"marker": {"color": INK2}}, connector={"line": {"color": GRID, "width": 1}},
        hovertemplate="%{x}<br>%{text}<extra></extra>",
    ))
    steps = [sum(p[1] for p in parts[: i + 1]) for i in range(len(parts))] + [r.total_pl]
    fig.update_layout(height=460, margin=dict(t=40, b=10, l=10, r=10), showlegend=False,
                      yaxis=dict(title=B, gridcolor=GRID, zerolinecolor=INK2, range=padded_range(steps)), **CLEAR)
    plot(fig)

    if not r.sells.empty:
        by_ccy = r.sells.groupby("currency", as_index=False)[["realized", "realized_base"]].sum()
        by_ccy.columns = [t("col_ccy"), t("col_realized_local"), t("col_realized_base", base=B)]
        st.subheader(t("by_market"))
        st.caption(t("by_market_caption"))
        st.dataframe(by_ccy.style.format({by_ccy.columns[1]: "{:,.0f}", by_ccy.columns[2]: "{:+,.0f}"}),
                     hide_index=True, use_container_width=True)

# ---------- real cost ----------
with tab_cost:
    st.subheader(t("real_cost_title"))
    st.caption(t("real_cost_caption"))
    h = r.holdings.copy()
    if h.empty:
        st.write(t("no_holdings"))
    else:
        h["price"] = h["symbol"].map(r.prices)
        h["zero_cost"] = h["diluted_cost"] <= 0
        h["vs_ibkr"] = 100 * (h["price"] / h["ibkr_avg_cost"] - 1)
        h["vs_diluted"] = (100 * (h["price"] / h["diluted_cost"] - 1)).where(~h["zero_cost"])
        show = pd.DataFrame({
            t("c_symbol"): h["symbol"], t("c_shares"): h["shares"], t("c_price"): h["price"],
            t("c_ibkr_cost"): h["ibkr_avg_cost"], t("c_diluted"): h["diluted_cost"],
            t("c_zero"): h["zero_cost"].map({True: t("zero_cost"), False: ""}),
            t("c_vs_ibkr"): h["vs_ibkr"], t("c_vs_diluted"): txt(h["vs_diluted"], "{:+.1f}%", t("c_zero")),
            t("c_ibkr_cost_base", base=B): h["ibkr_avg_cost_base"], t("c_diluted_base", base=B): h["diluted_cost_base"],
            t("c_cycle_realized"): h["realized_this_cycle"],
        })
        cols = show.columns
        num = {cols[1]: "{:,.4g}", cols[2]: "{:,.2f}", cols[3]: "{:,.2f}", cols[4]: "{:,.2f}",
               cols[6]: "{:+.1f}%", cols[8]: "{:,.2f}", cols[9]: "{:,.2f}", cols[10]: "{:+,.0f}"}
        st.dataframe(show.style.format(num, na_rep="—"), hide_index=True, use_container_width=True)

        for row in h.itertuples():
            if row.zero_cost:
                st.success(md(t("zero_cost_msg", sym=row.symbol, ccy=row.currency, extra=-row.diluted_cost * row.shares,
                                shares=row.shares, value=row.price * row.shares, ibkr=row.ibkr_avg_cost)))
                continue
            gap = row.vs_diluted - row.vs_ibkr
            if gap >= 5:
                st.success(md(t("better_msg", sym=row.symbol, ibkr=row.vs_ibkr, real=row.vs_diluted)))
            elif gap <= -5:
                st.warning(md(t("worse_msg", sym=row.symbol, ibkr=row.vs_ibkr, real=row.vs_diluted)))

        fig = go.Figure()
        for col, name, color, sym in [("ibkr_avg_cost", t("s_ibkr_cost"), INK2, "circle-open"),
                                      ("diluted_cost", t("s_diluted"), POS, "circle"),
                                      ("price", t("s_price"), NEG, "diamond")]:
            fig.add_trace(go.Scatter(
                x=h[col] / h["price"] * 100 - 100, y=h["symbol"], mode="markers", name=name,
                marker=dict(size=16, color=color, symbol=sym, line=dict(width=2, color=color)),
                customdata=h[col], hovertemplate="%{y} " + name + ": %{customdata:,.2f}<extra></extra>",
            ))
        fig.update_layout(height=140 + 70 * len(h), margin=dict(t=20, b=10, l=10, r=10),
                          xaxis=dict(title=t("rel_price"), ticksuffix="%", gridcolor=GRID, zerolinecolor=INK2),
                          legend=dict(orientation="h", y=1.15), **CLEAR)
        plot(fig)

    st.subheader(t("all_stocks"))
    st.caption(t("all_stocks_caption"))
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
        last = r.stock_trades.groupby("symbol")["time"].max()
        per["last"] = per["symbol"].map(last)
        per["first"] = per["symbol"].map(cyc.groupby("symbol")["start"].min())
        sort_opts = {"sort_loss": ("closed_base", True), "sort_gain": ("closed_base", False),
                     "sort_recent": ("last", False), "sort_oldest": ("first", True),
                     "sort_trades": ("trades", False), "sort_symbol": ("symbol", True)}
        how = st.selectbox(t("sort_by"), list(sort_opts), format_func=t)
        col, asc = sort_opts[how]
        per = per.sort_values(col, ascending=asc, na_position="last")
        view = pd.DataFrame({
            t("c_symbol"): per["symbol"], t("col_ccy"): per["currency"], t("c_status"): per["status"],
            t("c_cycles"): per["cycles"], t("c_trades"): per["trades"],
            t("c_closed_pl", base=B): txt(per["closed_base"].where(per["closed_base"] != 0), "{:+,.0f}"),
            t("c_last_trade"): txt(per["last"], "{:%Y-%m-%d}"),
            t("c_cur_diluted"): txt(per["diluted_cost"], "{:,.2f}"),
            t("c_cur_diluted_base", base=B): txt(per["diluted_cost_base"], "{:,.2f}"),
        })
        st.dataframe(view,
                     hide_index=True, use_container_width=True, height=38 * (len(view) + 1) + 4)

# ---------- round trips ----------
with tab_t:
    rd = r.rounds
    if rd.empty:
        st.write(t("rounds_none"))
    else:
        done_all = rd[rd["done"]]
        done = done_all[done_all["kind"] != rounds.SWING]
        swing = done_all[done_all["kind"] == rounds.SWING]
        st.subheader(t("rounds_title"))
        st.caption(t("rounds_caption", base=B))
        m0, m1, m2, m3 = st.columns(4)
        m0.metric(t("m_rounds"), f"{len(done)}")
        m1.metric(t("m_win"), f"{(done['result_base'] > 0).mean():.0%}" if len(done) else "—")
        m2.metric(t("m_rounds_total"), m_(done["result_base"].sum()))
        m3.metric(t("m_avg_round"), m_(done["result_base"].mean()) if len(done) else "—")

        if not swing.empty:
            verdict = t("swing_verdict") if done["result_base"].sum() > 0 > swing["result_base"].sum() else ""
            st.info(md(t("swing_msg", n=len(swing), total=m_(swing["result_base"].sum()),
                         win=(swing["result_base"] > 0).mean()) + verdict))

        by = done_all.groupby("kind", as_index=False).agg(n=("result_base", "size"),
                                                          win=("result_base", lambda x: (x > 0).mean()),
                                                          total=("result_base", "sum"))
        by["kind"] = by["kind"].map(lambda k: t("kind_" + k))
        by.columns = [t("c_kind"), t("c_n"), t("c_win"), t("c_total", base=B)]
        st.dataframe(by.style.format({by.columns[2]: "{:.0%}", by.columns[3]: "{:+,.0f}"}), hide_index=True)

        per = done.groupby("symbol", as_index=False).agg(
            n=("result_base", "size"), win=("result_base", lambda x: (x > 0).mean()),
            total=("result_base", "sum")).sort_values("total", ascending=False)
        if not per.empty:
            fig = go.Figure(go.Bar(
                x=per["total"], y=per["symbol"], orientation="h",
                marker=dict(color=[POS if v >= 0 else NEG for v in per["total"]], cornerradius=4),
                text=[m_(v) for v in per["total"]], textposition="outside",
                customdata=[t("rounds_hover", n=n, win=f"{w:.0%}") for n, w in zip(per["n"], per["win"])],
                hovertemplate="%{y}<br>%{text} · %{customdata}<extra></extra>",
            ))
            fig.update_layout(height=max(320, 36 * len(per)), margin=dict(t=10, b=10, l=10, r=90),
                              xaxis=dict(title=t("rounds_axis", base=B), gridcolor=GRID, zerolinecolor=INK2),
                              yaxis=dict(autorange="reversed"), **CLEAR)
            plot(fig)

        st.subheader(t("one_stock"))
        symbols = per["symbol"].tolist() or sorted(rd["symbol"].unique())
        pick = st.selectbox(t("pick_stock"), symbols)
        one = rd[rd["symbol"] == pick]
        tv = pd.DataFrame({
            t("c_start"): one["start"], t("c_end"): txt(one["end"], "{:%Y-%m-%d %H:%M}"), t("c_kind"): one["kind"].map(lambda k: t("kind_" + k)),
            t("c_base_pos"): one["base"], t("c_round_qty"): one["qty"], t("c_round_trades"): one["trades"],
            t("c_result_local"): txt(one["result"], "{:+,.2f}"), t("c_per_share"): txt(one["per_share"], "{:+,.2f}"),
            t("c_result_base", base=B): txt(one["result_base"], "{:+,.0f}"),
            t("c_state"): one["done"].map({True: t("state_done"), False: t("state_open")}),
        })
        st.dataframe(tv.sort_values(tv.columns[0], ascending=False).style.format(
            {tv.columns[3]: "{:,.4g}", tv.columns[4]: "{:,.4g}"}),
            hide_index=True, use_container_width=True)

        tl = rounds.timeline(r.stock_trades, pick)
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=tl["time"], y=tl["ibkr_avg_cost"], name=t("s_ibkr_cost"), mode="lines",
                                 line=dict(color=INK2, width=2, shape="hv", dash="dot")))
        fig.add_trace(go.Scatter(x=tl["time"], y=tl["diluted_cost"], name=t("s_diluted"), mode="lines",
                                 line=dict(color=POS, width=2, shape="hv")))
        for side, color, sym in [("buy", POS, "triangle-up"), ("sell", NEG, "triangle-down")]:
            x = tl[tl["side"] == side]
            fig.add_trace(go.Scatter(
                x=x["time"], y=x["price"], name=t(side), mode="markers",
                marker=dict(color=color, size=12, symbol=sym), customdata=x[["qty", "shares"]],
                hovertemplate=t(side) + " %{customdata[0]:,.4g} @ %{y:,.2f}<br>" + t("after_pos")
                + " %{customdata[1]:,.4g}<extra></extra>"))
        lo, hi = tl["price"].min(), tl["price"].max()
        pad = (hi - lo) * 0.15 or hi * 0.05
        fig.update_layout(height=540, margin=dict(t=40, b=10, l=10, r=10), hovermode="closest",
                          yaxis=dict(title=t("price_axis", ccy=one["currency"].iloc[0]), gridcolor=GRID,
                                     range=[lo - pad, hi + pad]),
                          legend=dict(orientation="h", y=1.12), **CLEAR)
        st.caption(t("timeline_caption"))
        plot(fig)

# ---------- fees ----------
with tab_fees:
    with st.spinner(t("costing")):
        fc = load_costs(raw, METHODS[method_key], source)
    gross = trading + fc.stock
    st.subheader(t("fees_title"))
    st.caption(t("fees_caption"))
    f0, f1, f2, f3 = st.columns(4)
    f0.metric(t("f_total"), m_(-fc.total))
    f1.metric(t("f_orders"), f"{len(fc.trades):,}",
              help=t("f_orders_help", avg=m_(fc.stock / max(len(fc.trades), 1), False, 2)))
    f2.metric(t("f_annual"), m_(-fc.total * 365 / fc.days), help=t("f_annual_help", days=fc.days))
    f3.metric(t("f_share"), f"{fc.stock / gross:.0%}" if gross > 0 else "—", help=t("f_share_help"))

    if gross > 0:
        fig = go.Figure(go.Waterfall(
            x=[t("wf_gross"), t("wf_fees"), t("wf_net")], measure=["absolute", "relative", "total"],
            y=[gross, -fc.stock, 0], text=[m_(gross), m_(-fc.stock), m_(trading)], textposition="outside",
            increasing={"marker": {"color": POS}}, decreasing={"marker": {"color": NEG}},
            totals={"marker": {"color": INK2}}, connector={"line": {"color": GRID, "width": 1}},
            hovertemplate="%{x}<br>%{text}<extra></extra>"))
        fig.update_layout(height=420, margin=dict(t=40, b=10, l=10, r=10),
                          yaxis=dict(title=B, gridcolor=GRID, range=padded_range([gross, trading])), **CLEAR)
        plot(fig)

    if fc.usd_min_share > 0.3:
        st.warning(md(t("min_msg", share=fc.usd_min_share, ps=fc.usd_per_share, x=fc.usd_per_share / 0.005)))

    st.markdown("##### " + t("savings"))
    s0, s1 = st.columns(2)
    s0.metric(t("merge"), m_(fc.merge_saving, False), help=t("merge_help", n=fc.merge_orders))
    s0.caption(t("merge_caption", n=fc.merge_orders))
    if fc.tiered_actual_usd > 0:
        s1.metric(t("tiered"), m_(fc.tiered_saving, False), help=t("tiered_help"))
        s1.caption(md(t("tiered_caption", a=fc.tiered_actual_usd, e=fc.tiered_estimate_usd)))
    st.caption(t("savings_warn"))

    st.markdown("##### " + t("where"))
    names = [t("c_orders"), t("c_comm"), t("c_per_order"), t("c_bps")]
    fmt = {t("c_comm"): lambda v: m_(v, False), t("c_per_order"): lambda v: m_(v, False, 2), t("c_bps"): "{:.1f}"}
    v0, v1 = st.columns(2)
    with v0:
        st.caption(t("by_size", base=B))
        bs = fc.by_size.copy()
        bs.columns = [t("c_size")] + names
        st.dataframe(bs.style.format(fmt), hide_index=True, use_container_width=True)
    with v1:
        st.caption(t("by_mkt"))
        bm = fc.by_market.copy()
        bm.columns = [t("col_ccy")] + names
        st.dataframe(bm.style.format(fmt), hide_index=True, use_container_width=True)

    fig = go.Figure(go.Bar(
        x=fc.by_month["month"], y=fc.by_month["commission"], marker=dict(color=POS, cornerradius=4),
        text=[m_(v, False) for v in fc.by_month["commission"]], textposition="outside",
        customdata=fc.by_month["orders"],
        hovertemplate="%{x}<br>%{text} · %{customdata} " + t("orders_word") + "<extra></extra>"))
    fig.update_layout(title=dict(text=t("monthly"), font=TITLE), height=380,
                      margin=dict(t=50, b=10, l=10, r=10),
                      yaxis=dict(title=B, gridcolor=GRID, range=padded_range(fc.by_month["commission"].tolist(), 0.15)),
                      **CLEAR)
    plot(fig)

    st.caption(t("top_symbols"))
    top = fc.by_symbol.head(10).copy()
    top.columns = [t("c_symbol")] + names
    st.dataframe(top.style.format(fmt), hide_index=True, use_container_width=True)


# ---------- trading style ----------
MONEY_PARAMS = ("gross", "net", "total", "swing_total", "avg_win", "avg_loss", "pl", "best_pl", "fx")


def render_insight(i: style.Insight) -> str:
    p = dict(i.params)
    for k in MONEY_PARAMS:
        if k in p:
            p[k] = m_(p[k])
    if "commission" in p:
        p["commission"] = m_(-p["commission"])
    if "per_trade" in p:
        p["per_trade"] = m_(p["per_trade"], False, 2)
    if "worst" in p:
        p["worst"] = ", ".join(f"{s} {m_(v)}" for s, v in p["worst"])
    base_key = "fees_eat_profit" if i.key.startswith("fees_eat_profit") else i.key
    body = f"**{t(f'i_{i.key}_t', **p)}**\n\n{t(f'i_{base_key}_e', **p)}"
    if i.key == "cuts_losses" and i.params.get("but_big"):
        body += t("i_cuts_losses_but")
    if t.has(f"i_{base_key}_s"):
        body += f"\n\n💡 {t(f'i_{base_key}_s')}"
    return body


with tab_style:
    with st.spinner(t("profiling")):
        p = load_profile(raw, METHODS[method_key], source)
    mt = p.metrics
    label = t("style_" + p.style)
    if p.tags:
        names_ = [t("tag_" + k, **kw) for k, kw in p.tags]
        label += f"（{'、'.join(names_)}）" if lang == "中文" else f" ({', '.join(names_)})"
    st.subheader(t("style_title", style=label))
    st.caption(t("style_detail", tpd=mt["trades_per_day"], intraday=mt["intraday_share"], hold=mt["median_hold_days"]))

    k0, k1, k2, k3 = st.columns(4)
    k0.metric(t("k_win"), f"{mt['win_rate']:.0%}", help=t("k_win_help"))
    k1.metric(t("k_payoff"), f"{mt['payoff']:.2f}", help=t("k_payoff_help"))
    k2.metric(t("k_pf"), f"{mt['profit_factor']:.2f}", help=t("k_pf_help"))
    k3.metric(t("k_comm"), m_(-mt["commission"]), help=t("k_comm_help", avg=m_(mt["commission_per_trade"], False, 2)))

    labels = [t("hold_" + b) for b in p.holding_mix["bucket"]]
    fig = go.Figure(go.Bar(
        x=p.holding_mix["share"] * 100, y=labels, orientation="h",
        marker=dict(color=POS, cornerradius=4), text=[f"{v:.0%}" for v in p.holding_mix["share"]],
        textposition="outside", customdata=[t("hold_hover", share=f"{v:.0%}") for v in p.holding_mix["share"]],
        hovertemplate="%{y}: %{customdata}<extra></extra>",
    ))
    fig.update_layout(title=dict(text=t("hold_title"), font=TITLE), height=320,
                      margin=dict(t=50, b=10, l=10, r=40), xaxis=dict(ticksuffix="%", gridcolor=GRID, range=[0, 100]),
                      yaxis=dict(autorange="reversed"), **CLEAR)
    plot(fig)

    st.subheader(t("insights"))
    order = {"warn": 0, "info": 1, "good": 2}
    for i in sorted(p.insights, key=lambda x: order[x.level]):
        {"warn": st.warning, "info": st.info, "good": st.success}[i.level](md(render_insight(i)))
    st.caption(t("style_disclaimer"))

# ---------- currency ----------
with tab_fx:
    st.subheader(t("fx_title"))
    st.caption(t("fx_caption", base=B))
    d = r.decomposition
    if not d.empty:
        dd = pd.DataFrame({
            t("c_symbol"): d["symbol"], t("col_ccy"): d["currency"],
            t("c_ret_local"): d["return_local_pct"], t("c_ret_base", base=B): d["return_base_pct"],
            t("c_price_eff"): d["price_effect"], t("c_fx_eff"): d["fx_effect"], t("c_cross"): d["cross_effect"],
            t("c_gain_base", base=B): d["gain_base"],
        })
        st.dataframe(dd.style.format({c: "{:+.1f}%" for c in dd.columns[2:4]} | {c: "{:+,.0f}" for c in dd.columns[4:]}),
                     hide_index=True, use_container_width=True)

    st.subheader(t("fx_split_title"))
    st.caption(t("fx_split_caption"))
    x0, x1, x2 = st.columns(3)
    x0.metric(t("fx_on_shares"), m_(a["stock_fx"]))
    x1.metric(t("fx_on_cash"), m_(a["cash_fx"]))
    x2.metric(t("fx_conversion"), m_(a["conversion"]))

    st.subheader(t("cash_title"))
    st.caption(t("cash_caption", base=B))
    if not r.cash.empty:
        cc = r.cash
        cv = pd.DataFrame({
            t("col_ccy"): cc["currency"], t("c_balance"): cc["balance"], t("c_value_base", base=B): cc["value_base"],
            t("c_fx_realized"): cc["realized_fx"], t("c_fx_unrealized"): cc["unrealized_fx"],
            t("c_fx_total"): cc["realized_fx"] + cc["unrealized_fx"],
        })
        st.dataframe(cv.style.format({cv.columns[1]: "{:,.2f}", cv.columns[2]: "{:,.0f}"}
                                     | {c: "{:+,.0f}" for c in cv.columns[3:]}),
                     hide_index=True, use_container_width=True)
    st.caption(t("fx_source_note", source=t("fx_" + r.fx_source)))

# ---------- trades ----------
with tab_trades:
    st.subheader(t("trades_title"))
    s = r.sells.copy()
    if not s.empty:
        s["holding_days"] = s.apply(lambda x: (x["time"] - min(tm for tm, _ in x["lots"])).days, axis=1)
        tt = pd.DataFrame({
            t("c_time"): s["time"], t("c_symbol"): s["symbol"], t("col_ccy"): s["currency"],
            t("c_side"): s["side"].map(lambda v: t("side_" + v)), t("c_qty"): s["qty"], t("c_method"): s["method"],
            t("col_realized_local"): s["realized"], t("col_realized_base", base=B): s["realized_base"],
            t("c_hold_days"): s["holding_days"],
        })
        sym = st.multiselect(t("filter"), sorted(s["symbol"].unique()))
        if sym:
            tt = tt[tt[t("c_symbol")].isin(sym)]
        st.dataframe(tt.sort_values(t("c_time"), ascending=False).style.format(
            {t("c_qty"): "{:,.4g}", tt.columns[6]: "{:+,.2f}", tt.columns[7]: "{:+,.2f}"}),
            hide_index=True, use_container_width=True, height=720)
        st.download_button(t("download"), tt.to_csv(index=False).encode("utf-8-sig"), "truecost_trades.csv")
