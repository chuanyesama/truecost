"""TrueCost - Streamlit front end.

Run:  streamlit run app/app.py
"""
from __future__ import annotations

import os
import sys
import tempfile
import threading
import time
from contextlib import contextmanager
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
import streamlit.components.v1 as components

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "app"))
import analytics  # noqa: E402
from i18n import Translator, money  # noqa: E402
from src import costs, flex, prices, report, rounds, style  # noqa: E402

RAW = ROOT / "data" / "raw"  # your own statements, never committed
FLEX_CACHE = RAW / "ibkr_flex_sync.csv"
SYNC_EVERY = 6 * 3600  # seconds; auto-refresh the synced statement when older than this


def local_files() -> list[Path]:
    """Newest first, so a fresh sync wins over an older manual download."""
    if os.environ.get("TRUECOST_DEMO"):
        return []
    return sorted(RAW.glob("*.csv"), key=lambda p: p.stat().st_mtime, reverse=True)


ACTIVITY_XML = RAW / "flex_activity.xml"  # history up to the last business day (refetched daily)
TODAY_XML = RAW / "flex_today.xml"        # today's executions (refetched on every refresh)


def _setting(name: str) -> str | None:
    try:
        v = st.secrets.get(name)
    except Exception:  # no secrets file
        v = None
    v = v or os.environ.get(name)
    return str(v) if v else None


def flex_credentials() -> tuple[str | None, str | None, str | None]:
    """Auto-sync is a paid feature; for now it runs only where a token is configured locally.
    Returns (token, activity query id, today's trade-confirmation query id or None)."""
    token, query = _setting("IBKR_FLEX_TOKEN"), _setting("IBKR_FLEX_QUERY_ID")
    if not (token and query):
        return None, None, None
    return token, query, _setting("IBKR_FLEX_TODAY_QUERY_ID")
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
    st.plotly_chart(fig, width="stretch")


def padded_range(values, pad: float = 0.18) -> list[float]:
    """y-range with room for labels above/below the bars (waterfall: cumulative values)."""
    lo, hi = min(0.0, *values), max(0.0, *values)
    span = (hi - lo) or 1.0
    return [lo - span * pad, hi + span * pad]

METHODS = {"lot_ibkr": None, "lot_fifo": "FIFO", "lot_lifo": "LIFO", "lot_hifo": "HIFO"}

st.set_page_config(page_title="TrueCost", page_icon="💱", layout="wide")
# colours, font and size live in .streamlit/config.toml; this adds what the theme can't
_dark = (st.context.theme.type or "light") == "dark"
st.markdown(f"""<style>
  :root {{
    --tc-card: {"#171a26" if _dark else "#ffffff"};
    --tc-shadow: {"none" if _dark else "0 1px 2px rgba(20,24,40,.04), 0 4px 16px rgba(20,24,40,.06)"};
    --tc-muted: {"#9aa0b4" if _dark else "#5b6175"};
    --tc-accent: {"#818cf8" if _dark else "#4f46e5"};
    --tc-hero: {"linear-gradient(135deg,#1e1b4b 0%,#172554 100%)" if _dark
                else "linear-gradient(135deg,#eef0ff 0%,#e6f0ff 100%)"};
  }}
  /* the main view gets the room; the sidebar is just controls */
  @media (min-width: 900px) {{
    section[data-testid="stSidebar"] {{ width: 290px !important; min-width: 290px !important; }}
  }}
  .block-container {{ padding-top: 2.2rem; max-width: 1280px; }}
  /* bordered containers become cards */
  [data-testid="stVerticalBlock"][class*="border"], div[data-testid="stVerticalBlockBorderWrapper"] {{
    background: var(--tc-card); box-shadow: var(--tc-shadow);
  }}
  [data-testid="stFileUploaderDropzone"] {{ background: var(--tc-card); border: 1.5px dashed var(--tc-accent); }}
  [data-testid="stMetricValue"] {{ font-weight: 650; letter-spacing: -0.01em; }}
  [data-testid="stMetricLabel"] p {{ color: var(--tc-muted); font-weight: 500; }}
  /* tabs read as navigation, not as small print */
  .stTabs [data-baseweb="tab-list"] {{ gap: 0.4rem; }}
  .stTabs [data-baseweb="tab"] p {{ font-size: 1rem; font-weight: 600; }}
  /* lists breathe */
  [data-testid="stMarkdownContainer"] li {{ margin-bottom: 0.5rem; line-height: 1.65; }}
  h1, h2, h3 {{ letter-spacing: -0.015em; }}
  .tc-hero {{ background: var(--tc-hero); border-radius: 1.1rem; padding: 2.2rem 2.4rem 2rem; margin-bottom: 1.2rem; }}
  .tc-eyebrow {{ color: var(--tc-accent); font-weight: 700; letter-spacing: .08em; text-transform: uppercase;
                 font-size: .8rem; margin-bottom: .6rem; }}
  .tc-hero h1 {{ font-size: 2.5rem; line-height: 1.2; margin: 0 0 .8rem; padding: 0; }}
  .tc-hero p {{ font-size: 1.15rem; color: var(--tc-muted); margin: 0; max-width: 46rem; }}
  .tc-pills {{ display: flex; flex-wrap: wrap; gap: .5rem; margin-top: 1.2rem; }}
  .tc-pill {{ background: var(--tc-card); border-radius: 999px; padding: .3rem .85rem; font-size: .9rem;
              font-weight: 500; box-shadow: var(--tc-shadow); }}
  @media (max-width: 640px) {{ .tc-hero {{ padding: 1.4rem; }} .tc-hero h1 {{ font-size: 1.7rem; }} }}
</style>""", unsafe_allow_html=True)
if _dark:
    # Streamlit's built-in dark theme has a red accent; match the light theme's indigo
    st.markdown("""<style>
      @import url("https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap");
      html { font-size: 18px; }
      body, .stApp, .stApp p, .stApp li, .stApp label, .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5 {
        font-family: Inter, "PingFang SC", "Microsoft YaHei", "Noto Sans SC", sans-serif; }
      .stApp { background: #0f1118; }
      section[data-testid="stSidebar"] { background: #151824; }
      label[data-baseweb="radio"]:has(input:checked) > div:first-child,
      label[data-baseweb="checkbox"]:has(input:checked) > div:first-child {
        background-color: #818cf8 !important; border-color: #818cf8 !important; }
      [data-testid="stBaseButton-primary"], [data-testid="stBaseButton-primaryFormSubmit"] {
        background: #6366f1; border-color: #6366f1; color: #fff; }
      [data-testid="stBaseButton-primary"]:hover { background: #818cf8; border-color: #818cf8; color: #fff; }
      .stTabs [data-baseweb="tab-highlight"] { background-color: #818cf8; }
      .stTabs [aria-selected="true"] p { color: #a5b4fc; }
      [data-testid="stMarkdownContainer"] a { color: #a5b4fc; }
    </style>""", unsafe_allow_html=True)
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
def load(data: bytes, method: str | None, source: str, live: tuple = ()):
    """live: (prices, rates) as tuples of (key, value): latest quotes and exchange rates
    that replace the statement's closing marks."""
    px, rates_now = live if live else ((), ())
    with _tmp(data) as path:
        return report.build(path, method, source, dict(px) or None, dict(rates_now) or None)


@st.cache_data(show_spinner=False, ttl=300, max_entries=50)
def latest_rate(ccy: str, base: str) -> float | None:
    try:
        return prices.latest_fx(ccy, base)
    except Exception:
        return None


@st.cache_data(show_spinner=False, ttl=300, max_entries=200)
def latest_price(ticker: str) -> float | None:
    try:
        bars, _ = prices.fetch_bars(ticker, "1D")
        return float(bars["close"].iloc[-1])
    except Exception:
        return None


def live_quotes(r) -> tuple:
    """Latest price for every holding (Yahoo, ~15 min delayed)."""
    ins = r.instruments.set_index("symbol") if not r.instruments.empty else None
    out = []
    for sym in r.holdings["symbol"] if not r.holdings.empty else []:
        if ins is None or sym not in ins.index:
            continue
        tk = prices.yahoo_symbol(ins["quote"][sym], ins["exchange"][sym], ins["underlying"][sym])
        p = latest_price(tk) if tk else None
        if p:
            out.append((sym, p))
    ccys = set(r.holdings["currency"]) if not r.holdings.empty else set()
    ccys |= set(r.cash.loc[r.cash["balance"].abs() > 0.01, "currency"]) if not r.cash.empty else set()
    rates_now = [(c, v) for c in sorted(ccys - {r.base}) if (v := latest_rate(c, r.base))]
    return (tuple(sorted(out)), tuple(rates_now)) if out or rates_now else ()


@st.cache_data(show_spinner=False, ttl=3600, max_entries=20)
def load_costs(data: bytes, method: str | None, source: str, live: tuple = ()):
    r = load(data, method, source, live)
    with _tmp(data) as path:
        return costs.analyse(r, path)


@st.cache_data(show_spinner=False, ttl=3600, max_entries=20)
def load_profile(data: bytes, method: str | None, source: str, live: tuple = ()):
    return style.profile(load(data, method, source, live))


def set_theme(dark: bool) -> None:
    """Save the viewer's choice where Streamlit keeps it (this browser only) and reload.

    Light is our own theme (Streamlit picks it when nothing is saved); dark is Streamlit's
    built-in one, the only kind it remembers across page loads."""
    save = ('w.localStorage.setItem(key, JSON.stringify({name: "Dark"}));' if dark
            else "w.localStorage.removeItem(key);")
    components.html(f"""<script>
      const w = window.parent;
      const tabs = [...w.document.querySelectorAll('button[role="tab"]')];
      const open = tabs.findIndex(b => b.getAttribute("aria-selected") === "true");
      const url = new URL(w.location.href);
      if (open >= 0) url.searchParams.set("tab", open);
      w.history.replaceState(null, "", url);
      const key = `stActiveTheme-${{w.location.pathname}}-v1`;
      {save}
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
        set_theme(not dark)
    st.header(t("upload_header"))
    up = st.file_uploader(t("upload_label"), type="csv")
    advanced = st.expander(t("advanced"))
    with advanced:
        method_key = st.selectbox(t("lot_method"), list(METHODS), format_func=t, help=t("lot_method_help"))

@st.cache_resource
def history_job() -> dict:
    """Shared state of the background history download (survives reruns)."""
    return {"thread": None, "error": None}


def history_stale() -> bool:
    return (not ACTIVITY_XML.exists()
            or time.time() - ACTIVITY_XML.stat().st_mtime > SYNC_EVERY
            or pd.Timestamp.fromtimestamp(ACTIVITY_XML.stat().st_mtime).date() < pd.Timestamp.now().date())


def start_history_download(token: str, query: str) -> None:
    """IBKR can take minutes to build the full history; never make the page wait for it."""
    job = history_job()
    if job["thread"] is not None and job["thread"].is_alive():
        return

    def work():
        try:
            xml = flex.fetch(token, query)
            ACTIVITY_XML.write_text(xml, encoding="utf-8")
            job["error"] = None
        except Exception as e:  # shown in the sidebar on the next rerun
            job["error"] = str(e) if isinstance(e, flex.FlexError) else type(e).__name__

    job["thread"] = threading.Thread(target=work, daemon=True)
    job["thread"].start()


def rebuild_cache(today_query: str | None) -> None:
    flex.save_statement(ACTIVITY_XML.read_text(encoding="utf-8"), FLEX_CACHE,
                        TODAY_XML.read_text(encoding="utf-8") if today_query and TODAY_XML.exists() else None)


def sync_now(token: str, query: str, today_query: str | None) -> None:
    """Refresh from IBKR without blocking the page.

    Today's executions (a few seconds) are fetched with a short time limit; the history
    is refreshed in the background when the saved copy is from an earlier day, and the
    page keeps showing the last saved data meanwhile. Only the very first sync, with
    nothing saved yet, has to wait for the history."""
    box = st.sidebar.empty()
    try:
        if history_stale():
            if ACTIVITY_XML.exists():
                start_history_download(token, query)
            else:
                box.info(t("sync_running"))
                ACTIVITY_XML.write_text(flex.fetch(token, query, on_wait=lambda n: box.info(t("sync_waiting", n=n))),
                                        encoding="utf-8")
        if today_query:
            box.info(t("sync_today"))
            try:
                TODAY_XML.write_text(flex.fetch(token, today_query, wait=2, attempts=8), encoding="utf-8")
            except Exception as e:
                st.sidebar.warning(t("sync_today_failed", err=str(e) if isinstance(e, flex.FlexError) else type(e).__name__))
        rebuild_cache(today_query)
        box.success(t("sync_done"))
    except flex.FlexError as e:
        box.error(t("sync_failed", err=str(e)))
    except Exception as e:  # network etc.
        box.error(t("sync_failed", err=type(e).__name__))


up = up or st.session_state.get("hero_upload")
token, query, today_query = flex_credentials()
synced = bool(token and up is None and not os.environ.get("TRUECOST_DEMO"))
if synced:
    with st.sidebar:
        st.markdown("##### " + t("sync_title"))
        # every visit starts with a refresh (today's trades take seconds); the button repeats it
        if st.button(t("sync_button"), type="primary", width="stretch") or not st.session_state.get("auto_synced"):
            st.session_state.auto_synced = True
            sync_now(token, query, today_query)
        elif ACTIVITY_XML.exists() and FLEX_CACHE.exists() and ACTIVITY_XML.stat().st_mtime > FLEX_CACHE.stat().st_mtime:
            rebuild_cache(today_query)  # the background download finished: use it
        job = history_job()
        if job["thread"] is not None and job["thread"].is_alive():
            st.info(t("history_updating"))
        elif job["error"]:
            st.warning(t("history_failed", err=job["error"]))
        if FLEX_CACHE.exists():
            age = pd.Timestamp.fromtimestamp(FLEX_CACHE.stat().st_mtime)
            st.caption(t("sync_last", when=f"{age:%Y-%m-%d %H:%M:%S}"))
        if not today_query:
            st.caption(t("sync_no_today"))

LOCAL_FILES = local_files()
demo = False
if up is not None:
    raw = up.getvalue()
elif LOCAL_FILES:
    raw = LOCAL_FILES[0].read_bytes()
    st.sidebar.info(t("local_file", name=LOCAL_FILES[0].name))
else:
    raw, demo = DEMO.read_bytes(), True

analytics.track_once("app_open", lang=lang, demo=demo)

try:
    with st.spinner(t("parsing")):
        probe = load(raw, None, "ecb")
except Exception as e:  # not an IBKR Activity Statement, or a format we don't handle yet
    analytics.track_once("statement_error", error=type(e).__name__)
    st.title("TrueCost")
    st.error(t("parse_error"))
    st.stop()

with advanced:
    sources = ["rba", "ecb"] if probe.base == "AUD" else ["ecb"]
    source = st.selectbox(t("fx_source"), sources, format_func=lambda s: t("fx_" + s))

with st.spinner(t("parsing")):
    r = load(raw, METHODS[method_key], source)
    LIVE = ()
    if synced and not demo and up is None:
        LIVE = live_quotes(r)
        if LIVE:
            r = load(raw, METHODS[method_key], source, LIVE)
            st.sidebar.caption(t("live_prices", when=f"{pd.Timestamp.now():%H:%M}"))
B = r.base
if up is not None:
    analytics.track_once("statement_uploaded", base=B, markets=int(r.stock_trades["currency"].nunique()),
                         trades=analytics.trades_bucket(len(r.stock_trades)), reconciles=bool(r.reconciles))

# ---------- paid report (demand test), feedback, privacy ----------
# prices shown in the viewer's currency (rounded local equivalents of the AUD price)
PRICES = {
    "report": {"AUD": 19, "USD": 12, "EUR": 11, "GBP": 10, "NZD": 21, "CAD": 17, "SGD": 16, "HKD": 95},
    "pro_month": {"AUD": 9, "USD": 6, "EUR": 5.5, "GBP": 4.9, "NZD": 10, "CAD": 8, "SGD": 8, "HKD": 45},
    "pro_year": {"AUD": 79, "USD": 52, "EUR": 48, "GBP": 42, "NZD": 87, "CAD": 72, "SGD": 70, "HKD": 400},
}


def price_of(item: str) -> str:
    table = PRICES[item]
    ccy = B if B in table else "USD"
    v = table[ccy]
    return money(v, ccy, sign=False, decimals=0 if float(v).is_integer() else 2)


def offer(kind: str, where: str) -> None:
    """Demand test: a priced button, then an optional email for the waitlist."""
    price = price_of("report" if kind == "report" else "pro_month")
    if st.button(t(f"{kind}_button", price=price, year=price_of("pro_year")), key=f"{kind}_{where}",
                 type="primary" if kind == "pro" else "secondary", width="stretch"):
        st.session_state[f"{kind}_{where}_open"] = True
        analytics.track("paid_report_click" if kind == "report" else "pro_click",
                        where=where, base=B, demo=demo, price=price)
    if st.session_state.get(f"{kind}_{where}_open"):
        st.info(t("offer_soon"))
        with st.form(f"waitlist_{kind}_{where}", clear_on_submit=True):
            email = st.text_input(t("offer_email"), placeholder="you@example.com")
            if st.form_submit_button(t("offer_notify")):
                if "@" in email and "." in email.split("@")[-1]:
                    analytics.track("waitlist_signup", product=kind, where=where, base=B, email=email.strip())
                    st.success(t("offer_thanks"))
                else:
                    st.warning(t("offer_bad_email"))


with st.sidebar:
    st.divider()
    st.markdown(f"##### ⭐ {t('pro_title')}")
    st.caption(t("pro_pitch"))
    offer("pro", "sidebar")
    st.caption(t("plans_pointer"))
    st.markdown(f"##### 📄 {t('offer_title')}")
    st.caption(t("offer_short"))
    offer("report", "sidebar")
    st.caption(t("sidebar_footer"))
m_ = lambda x, sign=True, d=0: money(x, B, sign, d)  # noqa: E731
a = r.attribution
trading = a["stock_price"]
currency = a["stock_fx"] + a["cash_fx"] + a["conversion"]
other = a["income_fees"]

# ---------- header ----------
if demo:
    pills = "".join(f'<span class="tc-pill">{p}</span>' for p in t("hero_pills"))
    st.markdown(f'''<div class="tc-hero"><div class="tc-eyebrow">TrueCost · IBKR</div>
      <h1>{t("hero_title")}</h1><p>{t("hero_sub")}</p><div class="tc-pills">{pills}</div></div>''',
                unsafe_allow_html=True)
    h0, h1 = st.columns([3, 2], vertical_alignment="center")
    with h0:
        st.file_uploader(t("hero_upload"), type="csv", key="hero_upload")
        st.caption(t("hero_private"))
    with h1:
        st.markdown(md(t("hero_or")))
else:
    st.title("TrueCost")
    st.caption(t("as_of", date=f"{r.end:%Y-%m-%d}", base=B, source=t("fx_" + r.fx_source)))
    if st.session_state.get("hero_upload") is not None:
        # keep the home-page upload box on screen, or Streamlit forgets the file on the next click
        st.file_uploader(t("hero_upload"), type="csv", key="hero_upload")
    if r.reconciles:
        st.success(md(t("reconciled_friendly", pl=m_(r.total_pl))))
    else:
        st.error(md(t("not_reconciled", diff=m_(r.total_pl - (r.nav_end - r.net_deposits)))))

tab_names = [t("tab_home")] + t("tabs")
try:  # the theme switch reloads the page; reopen the tab the viewer was on
    open_tab = tab_names[int(st.query_params.get("tab", 0))]
except (ValueError, IndexError):
    open_tab = tab_names[0]
(tab_guide, tab_overview, tab_cost, tab_chart, tab_t, tab_fees, tab_style, tab_fx,
 tab_trades) = st.tabs(tab_names, default=open_tab)
TAB = dict(zip(["overview", "cost", "chart", "rounds", "fees", "style", "fx", "trades"], t("tabs")))


def finding_cards() -> None:
    """The three things a newcomer should see first, from whichever account is loaded."""
    fc = load_costs(raw, METHODS[method_key], source, LIVE)
    c0, c1, c2 = st.columns(3)
    with c0.container(border=True):
        st.markdown(f"**{t('card_money')}**")
        st.metric(t("card_trading"), m_(trading))
        st.metric(t("card_fx"), m_(currency))
        if r.total_pl > 0:
            line = t("card_money_fx") if currency > trading else t("card_money_trade", fx=m_(currency))
        elif currency > 0:
            line = t("card_money_offset", trading=m_(-trading, False), fx=m_(currency, False))
        else:
            line = t("card_money_both")
        st.markdown(md(line))
        st.caption(t("card_go", tab=TAB["overview"]))
    with c1.container(border=True):
        st.markdown(f"**{t('card_cost')}**")
        h = r.holdings.copy()
        if not h.empty:
            h["price"] = h["symbol"].map(r.prices)
            zero = h[h["diluted_cost"] <= 0]
            if not zero.empty:
                z = zero.iloc[0]
                st.metric(z["symbol"], t("card_zero_value"))
                st.markdown(md(t("card_cost_zero", extra=money(-z["diluted_cost"] * z["shares"], z["currency"], False),
                                 ibkr=f"{z['ibkr_avg_cost']:,.2f}")))
            else:
                h["ibkr"] = 100 * (h["price"] / h["ibkr_avg_cost"] - 1)
                h["real"] = 100 * (h["price"] / h["diluted_cost"] - 1)
                g = h.loc[(h["real"] - h["ibkr"]).abs().idxmax()]
                st.metric(g["symbol"], f"{g['real']:+.1f}%", help=t("card_real_help"))
                st.markdown(t("card_cost_gap_line", ibkr=g["ibkr"], real=g["real"]))
        else:
            done = r.rounds[r.rounds["done"]] if not r.rounds.empty else r.rounds
            st.metric(t("card_rounds_label"), m_(done["result_base"].sum() if len(done) else 0))
            st.markdown(t("card_cost_rounds", n=len(done)))
        st.caption(t("card_go", tab=TAB["cost"]))
    with c2.container(border=True):
        st.markdown(f"**{t('card_fees')}**")
        st.metric(t("card_fees_label"), m_(-fc.total))
        gross = trading + fc.stock
        st.markdown(md(t("card_fees_share", share=fc.stock / gross) if gross > 0 and fc.stock > 0.3 * gross
                       else t("card_fees_avg", n=f"{len(fc.trades):,}",
                              avg=m_(fc.stock / max(len(fc.trades), 1), False, 2))))
        st.caption(t("card_go", tab=TAB["fees"]))
    prof = load_profile(raw, METHODS[method_key], source, LIVE)
    st.markdown(t("style_line", style=t("style_" + prof.style), tab=TAB["style"]))

# ---------- getting started ----------
with tab_guide:
    st.subheader(t("findings_demo") if demo else t("findings_you"))
    if demo:
        st.caption(t("demo_note"))
    finding_cards()
    if demo:
        st.divider()
        st.subheader(t("steps_title"))
        s0, s1, s2 = st.columns(3)
        for col, n in ((s0, 1), (s1, 2), (s2, 3)):
            with col.container(border=True):
                st.markdown(f"**{t(f'step{n}_t')}**")
                st.markdown(t(f"step{n}_d"))
        with st.expander(t("steps_detail")):
            st.markdown(t("guide_s1_body"))
            st.markdown(f"**{t('guide_s1_mistakes')}**")
            st.markdown(t("guide_s1_mistakes_body"))
            st.markdown(t("guide_s2_body"))
    with st.expander(t("tabs_explained")):
        st.markdown(t("guide_s3_table"))
    st.divider()
    st.subheader(t("guide_s4"))
    st.markdown(t("guide_s4_body"))
    st.markdown(md(t("plans_table", month=price_of("pro_month"), year=price_of("pro_year"),
                     report=price_of("report"))))
    g0, g1 = st.columns(2)
    with g0:
        offer("pro", "guide")
    with g1:
        offer("report", "guide")
    st.markdown(f"#### {t('guide_faq')}")
    for q in ("safe", "diff", "brokers", "advice"):
        with st.expander(t(f"faq_{q}_q")):
            st.markdown(t(f"faq_{q}_a"))
    st.divider()
    p0, p1 = st.columns(2, gap="large")
    with p0.container(border=True):
        st.markdown(f"#### {t('privacy_title')}")
        st.markdown(t("privacy_body"))
    with p1.container(border=True):
        st.markdown(f"#### {t('feedback_title')}")
        with st.form("feedback", clear_on_submit=True, border=False):
            text = st.text_area(t("feedback_label"), max_chars=1000, height=140)
            if st.form_submit_button(t("feedback_send")) and text.strip():
                analytics.track("feedback", text=text.strip(), lang=lang)
                st.success(t("feedback_thanks"))
    st.caption(t("disclaimer"))

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
                     hide_index=True, width="stretch")

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
        # a zero-cost holding has a negative diluted cost: show the words, not the number
        zero_label = t("zero_cost")
        extra = [t("already_up", amount=money(-d * n, c, sign=False)) for d, n, c in
                 zip(h["diluted_cost"], h["shares"], h["currency"])]
        show = pd.DataFrame({
            t("c_symbol"): h["symbol"], t("c_shares"): h["shares"], t("c_price"): h["price"],
            t("c_ibkr_cost"): h["ibkr_avg_cost"],
            t("c_diluted"): txt(h["diluted_cost"].where(~h["zero_cost"]), "{:,.2f}", zero_label),
            t("c_vs_ibkr"): h["vs_ibkr"],
            t("c_vs_diluted"): [e if z else f"{v:+.1f}%" for z, e, v in zip(h["zero_cost"], extra, h["vs_diluted"])],
            t("c_ibkr_cost_base", base=B): h["ibkr_avg_cost_base"],
            t("c_diluted_base", base=B): txt(h["diluted_cost_base"].where(~h["zero_cost"]), "{:,.2f}", zero_label),
            t("c_cycle_realized"): h["realized_this_cycle"],
        })
        cols = show.columns
        num = {cols[1]: "{:,.4g}", cols[2]: "{:,.2f}", cols[3]: "{:,.2f}",
               cols[5]: "{:+.1f}%", cols[7]: "{:,.2f}", cols[9]: "{:+,.0f}"}
        st.dataframe(show.style.format(num, na_rep="—"), hide_index=True, width="stretch")

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
            vals = h[col].where(~h["zero_cost"]) if col == "diluted_cost" else h[col]
            fig.add_trace(go.Scatter(
                x=vals / h["price"] * 100 - 100, y=h["symbol"], mode="markers", name=name,
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
            t("c_cur_diluted"): [t("zero_cost") if d <= 0 else ("—" if pd.isna(d) else f"{d:,.2f}")
                                 for d in per["diluted_cost"]],
            t("c_cur_diluted_base", base=B): [t("zero_cost") if d <= 0 else ("—" if pd.isna(d) else f"{d:,.2f}")
                                              for d in per["diluted_cost_base"]],
        })
        st.dataframe(view,
                     hide_index=True, width="stretch",
                     height=38 * (min(len(view), 25) + 1) + 4)  # up to 25 rows, then scroll inside

# ---------- chart ----------
@st.cache_data(show_spinner=False, ttl=900, max_entries=200)
def bars_for(ticker: str, range_key: str):
    return prices.fetch_bars(ticker, range_key)


# candle colours follow local convention: green-up in English, red-up in Chinese
UP, DOWN = ("#e34948", "#1baf7a") if lang == "中文" else ("#1baf7a", "#e34948")

with tab_chart:
    st.subheader(t("chart_title"))
    st_trades = r.stock_trades
    last_trade = st_trades.groupby("symbol")["time"].max().sort_values(ascending=False)
    ccy_of = st_trades.groupby("symbol")["currency"].first()
    ins = r.instruments.set_index("symbol") if not r.instruments.empty else pd.DataFrame(columns=["exchange", "underlying"])
    left, right = st.columns([2, 5])
    pick = left.selectbox(t("chart_stock"), list(last_trade.index), format_func=lambda s: f"{s} · {ccy_of[s]}")
    rk = right.segmented_control(t("chart_range"), list(prices.RANGES), default="6M", key="chart_range") or "6M"
    exch = ins["exchange"].get(pick) if pick in ins.index else None
    ticker = (prices.yahoo_symbol(ins["quote"][pick], exch, ins["underlying"][pick]) if pick in ins.index
              else None)
    if ticker is None:
        st.info(t("chart_unmapped", sym=pick, exch=exch or "?"))
    else:
        try:
            with st.spinner(t("chart_loading")):
                bars, ex_tz = bars_for(ticker, rk)
        except Exception:
            bars = None
            st.warning(t("chart_no_data", ticker=ticker))
        if bars is not None and not bars.empty:
            intraday = rk in prices.INTRADAY
            mine = st_trades[st_trades["symbol"] == pick]
            marks = prices.place_trades(mine, bars, r.statement_tz, intraday)
            fmt = "%m-%d %H:%M" if intraday else "%Y-%m-%d"
            label = pd.Series(bars.index.strftime(fmt), index=bars.index)
            rising = bars["close"] >= bars["open"]

            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.8, 0.2], vertical_spacing=0.03)
            fig.add_trace(go.Candlestick(
                x=label, open=bars["open"], high=bars["high"], low=bars["low"], close=bars["close"],
                increasing=dict(line=dict(color=UP), fillcolor=UP), decreasing=dict(line=dict(color=DOWN), fillcolor=DOWN),
                name=ticker, showlegend=False), row=1, col=1)
            fig.add_trace(go.Bar(x=label, y=bars["volume"], marker=dict(color=rising.map({True: UP, False: DOWN}),
                                 opacity=0.45), name=t("chart_volume"), showlegend=False,
                                 hovertemplate="%{x}<br>" + t("chart_volume") + " %{y:,.0f}<extra></extra>"), row=2, col=1)

            pad = (bars["high"].max() - bars["low"].min()) * 0.035
            for side, color, edge, sign in [("B", POS, "low", -1), ("S", NEG, "high", 1)]:
                mk = marks[marks["side"] == side]
                if mk.empty:
                    continue
                y = bars.loc[mk["bar"], edge].to_numpy() + sign * pad
                fig.add_trace(go.Scatter(
                    x=label[mk["bar"]].to_numpy(), y=y, mode="markers+text", text=[side] * len(mk),
                    textposition="middle center", textfont=dict(color="white", size=12),
                    marker=dict(size=22, color=color, line=dict(width=1.5, color="white")),
                    name=t("chart_" + side), showlegend=True,
                    customdata=mk[["count", "qty", "avg_price"]].to_numpy(),
                    hovertemplate="%{x}<br><b>" + t("chart_" + side) + "</b> · " + t("chart_hover")
                    + "<extra></extra>"), row=1, col=1)

            fig.update_layout(height=640, margin=dict(t=30, b=10, l=10, r=10), hovermode="closest",
                              legend=dict(orientation="h", y=1.06, x=0), xaxis_rangeslider_visible=False, **CLEAR)
            fig.update_xaxes(type="category", nticks=8, gridcolor=GRID, showspikes=True, spikethickness=1)
            fig.update_yaxes(gridcolor=GRID, title_text=t("price_axis", ccy=ccy_of[pick]), row=1, col=1)
            fig.update_yaxes(gridcolor=GRID, showticklabels=False, row=2, col=1)
            plot(fig)

            n_in = int(marks["count"].sum()) if not marks.empty else 0
            st.caption(t("chart_caption", shown=n_in, total=len(mine), ticker=ticker, tz=ex_tz))

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
            hide_index=True, width="stretch")

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
        fc = load_costs(raw, METHODS[method_key], source, LIVE)
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
        st.dataframe(bs.style.format(fmt), hide_index=True, width="stretch")
    with v1:
        st.caption(t("by_mkt"))
        bm = fc.by_market.copy()
        bm.columns = [t("col_ccy")] + names
        st.dataframe(bm.style.format(fmt), hide_index=True, width="stretch")

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
    st.dataframe(top.style.format(fmt), hide_index=True, width="stretch")


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
        p = load_profile(raw, METHODS[method_key], source, LIVE)
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
                     hide_index=True, width="stretch")

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
                     hide_index=True, width="stretch")
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
            hide_index=True, width="stretch", height=720)
        st.download_button(t("download"), tt.to_csv(index=False).encode("utf-8-sig"), "truecost_trades.csv")
