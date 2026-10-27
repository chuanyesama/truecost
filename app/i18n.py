"""UI strings in English and Chinese. t("key", **params) formats in the
current language; missing keys fall back to English."""
from __future__ import annotations

SYMBOLS = {"AUD": "A$", "USD": "US$", "EUR": "€", "GBP": "£", "JPY": "¥", "CAD": "C$", "NZD": "NZ$",
           "HKD": "HK$", "SGD": "S$", "CHF": "CHF ", "CNH": "¥", "CNY": "¥"}

EN = {
    # app chrome
    "lang": "Language",
    "tab_home": "🏠 Home",
    "pro_status": "🚧 Pro is still being built and launches by 31 Mar 2027. Founding members lock in the first "
                  "year for A$49 (then A$79/year), or try one month for A$12 — full refund if it isn't live in time.",
    "launch_status": "🚧 **What's live today is the free version** — every analysis above and in the tabs works now. "
                     "**Pro, the annual report and the AI features are still being built.** Founding members can "
                     "already lock in Pro's first year for A$49, or one month for A$12 (full refund if it isn't live "
                     "by 31 Mar 2027); the "
                     "report button only registers interest. Your answers in the survey below decide what we build "
                     "first.",
    "survey_callout": "🙋 **Pro, the annual report and AI aren't live yet.** Tell us in 30 seconds what you'd want and "
                      "whether you'd pay → **Help us decide what's next**, further down this page.",
    "survey_title": "🙋 Help us decide what's next",
    "survey_sub": "30 seconds, every question optional. We read every answer.",
    "sv_pay_q": "Would you pay for Pro (auto-sync from IBKR, today's trades, one-click refresh) at about {price}/month?",
    "sv_pay_yes": "Yes, that price is fine", "sv_pay_cheaper": "Yes, but only if it were cheaper",
    "sv_pay_maybe": "Not sure yet", "sv_pay_no": "No, the free version is enough for me",
    "sv_price_q": "What monthly price feels fair to you?",
    "sv_price_free": "Nothing", "sv_per_month": "/mo",
    "sv_report_q": "Would you buy a one-off annual PDF report (for your records or your accountant) at about {price}?",
    "sv_report_yes": "Yes", "sv_report_maybe": "Maybe", "sv_report_no": "No",
    "sv_ai_q": "Which AI features would you actually use?",
    "sv_ai_placeholder": "Pick any",
    "sv_ai_ask": "Ask about my account in plain words (\"How much did NVDA make me this year?\")",
    "sv_ai_review": "A monthly review of my trading, written for me",
    "sv_ai_coach": "Spot my bad habits and remind me before I repeat them",
    "sv_ai_import": "Read statements from other brokers (Futu, Tiger, CommSec…)",
    "sv_ai_explain": "Explain my numbers (fees, currency, cost) in plain language",
    "sv_ai_text": "What would you most want AI to do for you — and what worries you about it (accuracy, privacy…)?",
    "sv_other": "Anything else? Missing features, confusing parts, numbers that look wrong…",
    "sv_email": "Email (optional — only if you'd like a reply or early access)",
    "sv_send": "Send answers",
    "survey_thanks": "Thank you! Your answers decide what we build next. 🙏",
    "feedback_placeholder": "Anything helps: a number that looks wrong, a word you didn't understand, a feature you miss…",
    "faq_pro_setup_q": "What will Pro need from me?",
    "faq_pro_setup_a": "A one-time setup of about 5 minutes: in the IBKR web portal (Performance & Reports → Flex "
                       "Queries) you create two queries (trade history and today's executions) and a Flex token, then "
                       "paste them into TrueCost. After that the site syncs by itself every time you open it. A Flex "
                       "token can only read reports — it can't place orders or move money. It lasts up to a year; "
                       "renewing it takes a minute in IBKR.",
    "hero_pills": ["💱 Trading vs currency", "🎯 Real cost after round trips", "💸 Every fee counted",
                   "📈 Charts with your buys & sells"],
    "offer_short": "Your year in one PDF, ready for your accountant.",
    "sidebar_footer": "🔒 Your statement is never stored · privacy notes at the bottom of 🏠 Home. "
                      "Not tax, financial or investment advice.",
    "hero_title": "Did your IBKR profit come from trading — or from the exchange rate?",
    "hero_sub": "Upload your IBKR statement and see, in your home currency: where your money really came from, "
                "your true cost after trading around positions, and how much fees are eating.",
    "hero_upload": "Drop your IBKR Activity Statement (CSV) here",
    "hero_private": "🔒 Processed for this visit only — nothing is stored. Free, no sign-up.",
    "hero_or": "No statement handy? **Scroll down** — the findings below are from a sample account.",
    "demo_note": "👀 Sample account (fictional). Upload your statement above to see your own.",
    "findings_demo": "What TrueCost finds — sample account",
    "findings_you": "Your 3 key findings",
    "card_money": "💱 Where the money came from",
    "card_money_big": "Trading {trading} · Currency {fx}",
    "card_money_fx": "Most of the profit came from the **exchange rate**, not from trading. Your broker never shows this split.",
    "card_money_trade": "Trading is the main source. Currency moved it by {fx}.",
    "card_money_offset": "Trading lost {trading}; the exchange rate made back {fx} of it. Your broker never shows this split.",
    "card_money_both": "Both trading and the exchange rate lost money.",
    "card_cost": "🎯 Real cost after round trips",
    "card_cost_zero_big": "{sym}: zero cost",
    "card_cost_zero": "Round trips have already paid back the whole position plus {extra} — the shares left are pure profit. IBKR still shows a cost of {ibkr}.",
    "card_cost_gap_big": "{sym}: {real:+.1f}% (IBKR shows {ibkr:+.1f}%)",
    "card_cost_gap": "Counting the profit and loss from selling and buying back, the real result differs from what IBKR shows.",
    "card_cost_rounds_big": "Round trips {total}",
    "card_cost_rounds": "{n} rounds of selling and buying back around a core position.",
    "card_fees": "💸 What trading cost",
    "card_fees_share": "Commissions ate **{share:.0%}** of your pre-fee trading profit.",
    "card_fees_avg": "{n} orders, {avg} each on average.",
    "card_go": "→ Details: **{tab}** tab",
    "card_trading": "📈 Trading", "card_fx": "💱 Currency", "card_zero_value": "Zero cost",
    "card_real_help": "Return on the diluted cost (counting your round trips)",
    "card_cost_gap_line": "IBKR shows **{ibkr:+.1f}%**; counting your round trips it's really **{real:+.1f}%**.",
    "card_rounds_label": "Round trips total", "card_fees_label": "Commissions & fees",
    "style_line": "Your trading style: **{style}** → see **{tab}**",
    "steps_title": "Your own numbers in 3 steps",
    "step1_t": "1 · Download", "step1_d": "IBKR Portal → Statements → **Activity** → CSV, English",
    "step2_t": "2 · Upload", "step2_d": "Drop the file in the box at the top of this page",
    "step3_t": "3 · See", "step3_d": "Your findings appear here; every tab goes deeper",
    "steps_detail": "Detailed download steps & common mistakes",
    "tabs_explained": "What each tab answers",
    "advanced": "⚙️ Advanced settings",
    "reconciled_friendly": "✅ Checked: everything adds up exactly to your account's actual profit/loss ({pl}).",
    "tab_guide": "👋 Get started",
    "guide_title": "Get started in 3 minutes",
    "guide_intro": "Your broker shows each currency separately and your *average* cost. TrueCost puts everything in "
                   "**your home currency** and answers questions your broker's screens don't:\n\n"
                   "- **Did I make money from trading, or did the exchange rate do it?**\n"
                   "- **What is my real cost after trading around a position (selling and buying back)?**\n"
                   "- **How much am I paying in fees — and how could I pay less?**\n\n"
                   "The numbers you see now come from a **sample account**. Follow the steps below to see your own.",
    "guide_s1": "Step 1 · Download your statement from IBKR",
    "guide_s1_body": "1. Log in to the **IBKR Portal** in a web browser (not the mobile app).\n"
                     "2. Top menu: **Performance & Reports → Statements**.\n"
                     "3. Find **Activity** under *Default Statements* and click the **→** arrow on its row.\n"
                     "4. In the window that opens:\n"
                     "   - **Period**: *Annual* for a past year, or *Year to Date* for this year\n"
                     "   - **Format**: **CSV**\n"
                     "   - **Language**: **English**\n"
                     "5. Click **Run / Download**. A file like `U1234567_20260101_20261009.csv` is saved.",
    "guide_s1_mistakes": "Common mistakes",
    "guide_s1_mistakes_body": "- **PDF or HTML instead of CSV** — TrueCost needs the CSV.\n"
                              "- **Language not English** — column names change and the file can't be read.\n"
                              "- **A Flex Query, Trade Confirmation or Tax report** — use the plain **Activity** statement.\n"
                              "- **Opened your account years ago?** Upload one year at a time for now "
                              "(Pro will merge multiple years automatically).",
    "guide_s2": "Step 2 · Upload it",
    "guide_s2_body": "Drag the file into **IBKR Activity Statement (CSV)** in the left sidebar "
                     "(on a phone, tap **»** at the top-left to open it). Results appear in a few seconds.\n\n"
                     "🔒 Your statement is processed for this visit only: the temporary file is deleted right after "
                     "parsing, nothing is stored, and no amounts, symbols or account numbers are ever sent anywhere.",
    "guide_s3": "Step 3 · Read your results",
    "guide_s3_table": "| Tab | The question it answers |\n|---|---|\n"
                      "| **Overview** | How much did I make in total, and how much came from trading vs currency? |\n"
                      "| **Real cost** | What did each position really cost after my round trips? Any zero-cost holdings? |\n"
                      "| **Chart** | Where exactly did I buy and sell on the price chart? |\n"
                      "| **Round trips** | Does trading around a core position actually make me money? |\n"
                      "| **Fees** | How much have commissions cost me, and how could I pay less? |\n"
                      "| **Trading style** | What kind of trader am I, and what do my habits cost me? |\n"
                      "| **Currency** | How much did exchange rates add to or take from my shares and cash? |\n"
                      "| **Trades** | Every closing trade, downloadable as CSV. |\n\n"
                      "Every page is checked against your account: the green ✅ bar at the top means TrueCost's "
                      "breakdown adds up exactly to *ending NAV − net deposits*.",
    "guide_s4": "Free or Pro?",
    "guide_s4_body": "Everything above is **free**. **Pro** is for active traders who don't want to download a file "
                     "every time:",
    "guide_faq": "Questions",
    "faq_safe_q": "Is it safe to upload my statement?",
    "faq_safe_a": "The free version never stores your file: it's parsed in memory for your visit and the temporary "
                  "copy is deleted immediately. Anonymous usage counts (e.g. \"a statement was uploaded\") never "
                  "include amounts, symbols or account numbers. You can also run TrueCost on your own computer — the "
                  "code is open source on GitHub.",
    "faq_diff_q": "Why don't my numbers match the IBKR app exactly?",
    "faq_diff_a": "IBKR shows profit in each stock's own currency and an average cost that ignores profits from "
                  "selling and buying back. TrueCost converts every trade at that day's exchange rate into your home "
                  "currency and also shows the *diluted* cost. The account total is the same — the green ✅ bar checks "
                  "it against ending NAV − net deposits.",
    "faq_brokers_q": "Which brokers and currencies are supported?",
    "faq_brokers_a": "Interactive Brokers, any base currency (AUD, USD, EUR, GBP, …), stocks and ETFs in US, European, "
                     "Nordic and Asian markets. Options, futures and other brokers are not supported yet.",
    "faq_advice_q": "Is this tax or investment advice?",
    "faq_advice_a": "No. TrueCost is a calculator for self-review. For your tax return, check the numbers with a "
                    "registered tax agent.",
    "guide_pointer": "New here? The **🏠 Home** tab shows how to get started.",
    "plans_pointer": "Free vs Pro: see the **🏠 Home** tab.",
    "sync_title": "🔄 IBKR auto-sync", "sync_button": "🔄 Refresh",
    "sync_today": "Fetching today's trades…",
    "sync_today_failed": "Couldn't get today's trades right now ({err}); showing what was saved.",
    "history_updating": "Updating your history in the background (IBKR can take a minute or two). "
                        "Showing your last saved data; press Refresh afterwards.",
    "history_failed": "Background history update failed ({err}); showing your last saved data.",
    "sync_no_today": "Add IBKR_FLEX_TODAY_QUERY_ID (a Trade Confirmation query) to include today's trades.",
    "live_prices": "Positions valued at latest prices ({when}, Yahoo, may be ~15 min delayed)",
    "sync_running": "Asking IBKR for your latest statement…",
    "sync_waiting": "IBKR is still preparing the statement… ({n})",
    "sync_done": "Synced — showing your latest trades.", "sync_failed": "Sync failed ({err}). Showing the last saved data.",
    "sync_last": "Last synced {when}",
    "parse_error": "This file doesn't look like an IBKR **Activity Statement** CSV. In the IBKR Portal choose "
                   "Performance & Reports → Statements → **Activity**, format **CSV**, language **English**, and try again.",
    "offer_title": "Annual report (PDF)",
    "offer_body": "Your year in one PDF: P/L in your home currency split into trading vs currency, every closed "
                  "trade with cost and proceeds at each day's rate, fees and round-trip results — ready to keep or "
                  "hand to your accountant.",
    "report_button": "Pre-order the report — about {price}",
    "pro_title": "TrueCost Pro",
    "pro_pitch": "Open the site and see today's trades and positions — synced from IBKR, one click to refresh. "
                 "Plus multi-year history, intraday charts and AI.",
    "pro_button_year": "⭐ Become a founding member — A$49 first year",
    "pro_button_month": "Try one month — A$12",
    "founder_terms_month": "You pay A$12 on Stripe's secure checkout (TrueCost never sees your card). It covers one "
                           "month of Pro from launch and doesn't renew. If Pro isn't live by 31 Mar 2027 you get a "
                           "full refund, and you can ask for one any time before launch: truecost.help@gmail.com.",
    "founder_terms_year": "You pay A$49 on Stripe's secure checkout (TrueCost never sees your card). It covers your first "
                     "year of Pro from launch — then A$79/year or A$9/month. If Pro isn't live by 31 Mar 2027 you get "
                     "a full refund, and you can ask for one any time before launch: truecost.help@gmail.com.",
    "founder_pay": "Continue to secure payment →",
    "plans_title": "Free vs Pro",
    "plans_table": "| | Free (live) | Pro (🚧 in development) |\n|---|---|---|\n"
                   "| Getting your data | Download CSV & upload | **Auto-sync, today's trades, one-click refresh** |\n"
                   "| Account | None, nothing stored | Sign in; encrypted IBKR token |\n"
                   "| P/L split, real cost, round trips, fees, style | ✅ | ✅ |\n"
                   "| Chart with your trades | Daily & weekly | + intraday (2H–1M) |\n"
                   "| History | One statement at a time | Multi-year, merged |\n"
                   "| AI: ask your account, monthly review | — | ✅ |\n"
                   "| Annual report (PDF) | {report} each | Included |\n\n"
                   "**Pro: {month}/month or {year}/year. Presale: A$49 for the first year, or A$12 for one month.**",
    "offer_soon": "Not live yet — nothing was charged. Leave your email and we'll tell you when it's ready "
                  "(with an early-bird price). Even better: fill in the short survey on 🏠 Home.",
    "offer_email": "Email (optional)", "offer_notify": "Notify me",
    "offer_thanks": "Thanks — you're on the list.", "offer_bad_email": "That email doesn't look right.",
    "feedback_title": "💬 Feedback & suggestions", "feedback_label": "What's missing, wrong or confusing?",
    "feedback_send": "Send", "feedback_thanks": "Thank you — we read every message!",
    "privacy_title": "🔒 Privacy",
    "privacy_body": "- Your statement is processed for your session only; the temporary file is deleted right after "
                    "parsing and results expire within an hour.\n"
                    "- We count anonymous usage events to improve TrueCost: page opened, language, whether a "
                    "statement was uploaded, base currency, number of markets, a rough trade-count range, and which "
                    "buttons were clicked. **No amounts, symbols, account numbers or statement contents.**\n"
                    "- A random id identifies one visit only; we don't track you across visits.\n"
                    "- Your email, feedback and survey answers are stored only if you send them, and used only to "
                    "improve TrueCost, reply or notify you.\n"
                    "- Analytics provider: PostHog (EU servers).",
    "theme_help": "Dark mode (saved in this browser; the page reloads)",
    "sort_by": "Sort by",
    "sort_loss": "Biggest loss first", "sort_gain": "Biggest gain first", "sort_recent": "Most recently traded",
    "sort_oldest": "First opened", "sort_trades": "Most trades", "sort_symbol": "Symbol A–Z",
    "c_last_trade": "Last trade",
    "tagline": "See what your Interactive Brokers account really earned — in your home currency.",
    "upload_header": "📄 Your statement",
    "upload_label": "IBKR Activity Statement (CSV)",
    "how_to": "How do I get it? (1 min)",
    "how_to_steps": "1. Log in to IBKR Portal → **Performance & Reports → Statements**\n"
                    "2. **Activity** → click the arrow\n"
                    "3. Period **Annual / Year to Date**, format **CSV**, language **English**\n"
                    "4. Drop the file above",
    "lot_method": "Lot-matching method",
    "lot_method_help": "See how realized vs unrealized P/L shifts under another method. The total never changes.",
    "lot_ibkr": "As recorded by IBKR", "lot_fifo": "FIFO", "lot_lifo": "LIFO", "lot_hifo": "Highest cost first",
    "fx_source": "Exchange-rate source",
    "fx_ecb": "ECB reference rates", "fx_rba": "RBA (accepted by the ATO)",
    "disclaimer": "For information and self-review only. Not tax, financial or investment advice.",
    "local_file": "Using local file: {name}",
    "demo_banner": "👀 You're looking at a **sample account** (fictional — prices and trades are simulated). "
                   "Upload your own IBKR statement on the left. It is processed for this session only and not stored.",
    "as_of": "As of {date} · base currency {base} · rates: {source}",
    "reconciled": "✅ Reconciled with your account: ending NAV {nav} − net deposits {dep} = {pl}",
    "not_reconciled": "⚠️ Off by {diff} — some data may be missing from the statement",
    "tabs": ["Overview", "Real cost", "Chart", "Round trips", "🧮 Calculator", "Fees", "Trading style", "Currency", "Trades"],
    "chart_title": "Price chart with your trades", "chart_stock": "Stock", "chart_range": "Range",
    "chart_loading": "Loading prices…", "chart_volume": "Volume",
    "chart_B": "Buy", "chart_S": "Sell",
    "chart_hover": "%{customdata[0]} trade(s), %{customdata[1]:,.4g} shares @ avg %{customdata[2]:,.2f}",
    "chart_unmapped": "No price data for {sym} (exchange {exch}) yet.",
    "chart_no_data": "Couldn't load prices for {ticker} right now — try again in a minute.",
    "chart_caption": "{shown} of your {total} trades in {ticker} fall in this range; trades in the same bar are combined "
                     "into one marker (hover for details). Times in the exchange's time zone ({tz}); pre/post-market "
                     "included on intraday ranges. Prices: Yahoo Finance, may be delayed.",
    "parsing": "Reading statement…", "costing": "Adding up fees…", "profiling": "Analysing your habits…",

    # overview
    "total_pl": "Total P/L ({base})", "from_trading": "📈 From trading", "from_fx": "💱 From currency",
    "other": "Other",
    "from_trading_help": "Gains and losses from price moves, after commissions, converted at each day's rate",
    "from_fx_help": "Exchange-rate moves while holding foreign currency (shares and cash) plus conversion spread",
    "other_help": "Interest, dividends, withholding tax, other fees",
    "fx_driven": "**Most of your profit came from the exchange rate, not from trading.** "
                 "Currency {fx}, trading {trading}. IBKR's P/L screens don't separate the two.",
    "fees_note": "\"From trading\" is after commissions — see the Fees tab for the breakdown.",
    "wf_trading": "Trading", "wf_fx": "Currency", "wf_other": "Interest / dividends / fees", "wf_total": "Total",
    "by_market": "Realized P/L by market",
    "by_market_caption": "IBKR shows each currency separately; in one currency you can see which market made or lost money.",
    "col_ccy": "Currency", "col_realized_local": "Realized (local)", "col_realized_base": "Realized ({base})",

    # real cost
    "real_cost_title": "Your real cost after trading around a position",
    "real_cost_caption": "**IBKR cost** = average of the remaining tax lots (ignores profit from selling and buying back). "
                         "**Diluted cost** = (total bought − total sold) ÷ shares held, since the position was last flat. "
                         "Profitable round trips push it down.",
    "no_holdings": "No open positions.",
    "zero_cost": "✅ zero cost", "already_up": "already up {amount}",
    "zero_cost_msg": "🎉 **{sym} is now a zero-cost holding**: you've taken back everything you put in plus {ccy} {extra:,.0f}. "
                     "The remaining {shares:,.4g} shares ({ccy} {value:,.0f}) are pure profit — IBKR still shows a cost of {ibkr:,.2f}.",
    "better_msg": "**{sym}**: IBKR shows {ibkr:+.1f}%; counting your round trips it's actually **{real:+.1f}%**.",
    "worse_msg": "**{sym}**: IBKR shows {ibkr:+.1f}%, but with round-trip losses included it's **{real:+.1f}%** — not as close to break-even as it looks.",
    "c_symbol": "Symbol", "c_shares": "Shares", "c_price": "Price", "c_ibkr_cost": "IBKR cost",
    "c_diluted": "Diluted cost", "c_vs_ibkr": "P/L vs IBKR cost", "c_vs_diluted": "P/L vs diluted",
    "c_ibkr_cost_base": "IBKR cost ({base})", "c_diluted_base": "Diluted cost ({base})",
    "c_cycle_realized": "Realized this cycle", "c_zero": "Zero cost",
    "rel_price": "Relative to current price (%)", "s_ibkr_cost": "IBKR cost", "s_diluted": "Diluted cost",
    "s_price": "Price",
    "all_stocks": "Every stock, including closed positions",
    "all_stocks_caption": "Each stock's history is split into cycles from first buy to fully sold. A closed cycle's "
                          "result is total sold − total bought (incl. commissions), independent of lot method.",
    "status_open": "Holding", "status_closed": "Closed", "status_zero": "Holding · zero cost",
    "c_status": "Status", "c_cycles": "Cycles", "c_trades": "Trades", "c_closed_pl": "Closed cycles P/L ({base})",
    "c_cur_diluted": "Diluted cost now", "c_cur_diluted_base": "Diluted cost now ({base})",

    # round trips
    "rounds_none": "No round trips found.",
    "rounds_title": "Round-trip scorecard",
    "rounds_caption": "A **round trip** is trading around a core position and returning to it: **sell → buy back**, or "
                      "**buy → sell back**. Result = cash from the round's trades (after commissions), in {base} so markets "
                      "can be compared. Buying more than the core and selling it back counts as an **oversized swing**, not a round trip.",
    "m_rounds": "Completed rounds", "m_win": "Win rate", "m_rounds_total": "Round trips total", "m_avg_round": "Average per round",
    "swing_msg": "**Oversized swings**: {n} times, total {total}, win rate {win:.0%}.",
    "swing_verdict": " Your round trips make money — the losses come from oversized swings.",
    "kind_sell_first": "Sell → buy back", "kind_buy_first": "Buy → sell back", "kind_swing": "Oversized swing",
    "c_kind": "Type", "c_n": "Rounds", "c_win": "Win rate", "c_total": "Total ({base})",
    "rounds_axis": "Round trips total ({base})", "rounds_hover": "{n} rounds · win rate {win}",
    "one_stock": "One stock: every round", "pick_stock": "Pick a stock",
    "c_start": "Start", "c_end": "End", "c_base_pos": "Core position", "c_round_qty": "Shares traded",
    "c_round_trades": "Trades", "c_result_local": "Result (local)", "c_per_share": "Per share", "c_result_base": "Result ({base})",
    "c_state": "State", "state_done": "Done", "state_open": "Not back to core",
    "timeline_caption": "Cost after every trade: profitable round trips push the diluted cost (blue) down; IBKR's cost (dotted) "
                        "doesn't move. If the blue line drops off the chart, the position is at zero cost.",
    "buy": "Buy", "sell": "Sell", "after_pos": "position after", "price_axis": "Price ({ccy})",

    # fees
    "fees_title": "What you paid to trade",
    "fees_caption": "A dollar or two per order is easy to miss — added up, it isn't. Includes commissions, exchange and "
                    "regulatory fees, transaction taxes and currency-conversion commissions, converted at each day's rate.",
    "f_total": "Total trading costs", "f_orders": "Orders", "f_orders_help": "Average {avg} per order",
    "f_annual": "At this pace, per year", "f_annual_help": "Extrapolated from {days} days of actual spending",
    "f_share": "Share of pre-fee trading profit", "f_share_help": "Stock commissions ÷ trading P/L before commissions",
    "wf_gross": "Trading P/L before fees", "wf_fees": "Commissions & fees", "wf_net": "Trading P/L after fees",
    "min_msg": "**{share:.0%} of your US orders paid the US$1 minimum commission.** The list price is US$0.005 per share, "
               "but your orders are small, so you actually paid a median of **US${ps:.3f} per share** ({x:.0f}× the list price).",
    "savings": "How much could be saved (estimates)",
    "merge": "Merge same-direction small orders",
    "merge_help": "{n} orders followed another order in the same stock and direction within 10 minutes and paid the minimum. "
                  "One combined order pays the minimum once.",
    "merge_caption": "{n} orders could have been combined with the previous one",
    "tiered": "US stocks on IBKR Tiered pricing",
    "tiered_help": "Tiered: US$0.0035/share, min US$0.35, plus exchange/clearing fees (estimated at ~US$0.0032/share; "
                   "the real figure depends on exchange and whether you add or take liquidity).",
    "tiered_caption": "Actual US${a:,.0f} → estimated US${e:,.0f}",
    "savings_warn": "⚠️ Savings are estimates. Tiered exchange fees vary by venue and order type and fall with monthly volume; "
                    "check IBKR's current rates before switching.",
    "where": "Where the money went",
    "by_size": "By order size ({base}) — small orders cost far more (1 bp = 0.01%)", "by_mkt": "By market",
    "c_size": "Order size", "c_orders": "Orders", "c_comm": "Commission", "c_per_order": "Per order", "c_bps": "Rate (bp)",
    "monthly": "Commission per month", "top_symbols": "Stocks with the most commission",
    "orders_word": "orders",

    # style
    "style_title": "Your trading style: {style}",
    "style_detail": "{tpd:.1f} trades per trading day; {intraday:.0%} of sells close a position opened the same day; "
                    "median holding period {hold:.1f} days.",
    "style_intraday": "Intraday", "style_short_term": "Short-term", "style_swing": "Swing", "style_long_term": "Long-term",
    "tag_rounds": "frequent round trips", "tag_high_freq": "high frequency", "tag_shorts": "shorts",
    "tag_markets": "{n} markets",
    "k_win": "Win rate (closed cycles)", "k_win_help": "A cycle runs from first buy to fully sold; won or lost in base currency",
    "k_payoff": "Payoff ratio", "k_payoff_help": "Average win ÷ average loss",
    "k_pf": "Profit factor", "k_pf_help": "Total wins ÷ total losses; below 1 means losing overall",
    "k_comm": "Commissions", "k_comm_help": "Average {avg} per trade",
    "hold_title": "How long the positions you sold were held", "hold_hover": "{share} of sells",
    "hold_intraday": "Same day", "hold_1_5d": "1–5 days", "hold_5_30d": "5–30 days", "hold_30d_plus": "30+ days",
    "insights": "What your data says",
    "style_disclaimer": "Statistical observations from your own trades, for self-review. Not investment advice and not about any specific security.",

    "i_fees_eat_profit_all_t": "Fees ate all of your trading profit",
    "i_fees_eat_profit_t": "Fees ate most of your trading profit",
    "i_fees_eat_profit_e": "Before fees you made {gross}; commissions were {commission} ({share:.0%} of that), leaving {net}. "
                           "Average {per_trade} per trade; {costly:.0%} of trades paid more than 0.1% of their value.",
    "i_fees_eat_profit_s": "Avoid small, fragmented orders (IBKR charges a minimum per order); execute the same idea in fewer "
                           "orders; check whether tiered pricing suits you.",
    "i_losing_before_fees_t": "Losing even before fees",
    "i_losing_before_fees_e": "Before fees {gross}; commissions cost another {commission}.",
    "i_losing_before_fees_s": "Trade less first, and find where the losses come from (see below).",
    "i_rounds_win_swings_lose_t": "Round trips make money, oversized swings lose it",
    "i_rounds_win_swings_lose_e": "{n} round trips total {total}; {n_swing} oversized swing(s) (adding more than the core position) total {swing_total}.",
    "i_rounds_win_swings_lose_s": "You're good at trading around a core position, but not when you size up. Consider capping "
                                  "adds above the core, e.g. at 1× the core size.",
    "i_rounds_lose_t": "Round trips are losing overall",
    "i_rounds_lose_e": "{n} rounds total {total}.",
    "i_rounds_lose_s": "Round trips add orders and fees; if they don't pay, do fewer of them.",
    "i_rounds_win_t": "Round trips are profitable", "i_rounds_win_e": "{n} rounds total {total}.",
    "i_big_losses_t": "A few big losses decided the result",
    "i_big_losses_e": "The 3 largest losses ({worst}) are {share:.0%} of all losses.",
    "i_big_losses_s": "Set a maximum loss per position (e.g. 1–2% of the account) and exit when it's hit; "
                      "large losses almost always come from oversized positions.",
    "i_profit_factor_t": "Wins don't cover losses",
    "i_profit_factor_e": "Closed-cycle win rate {win_rate:.0%}, average win {avg_win}, average loss {avg_loss}, "
                         "profit factor {pf:.2f} (below 1 means losing overall).",
    "i_profit_factor_s": "With a win rate near 50%, profit has to come from winners being bigger than losers: hold winners "
                         "a bit longer or cut the big losers.",
    "i_disposition_t": "Losers are held longer than winners",
    "i_disposition_e": "Median holding: losing cycles {loss_days:.1f} days, winning cycles {win_days:.1f} days.",
    "i_disposition_s": "This is the disposition effect: quick to take profits, slow to accept losses. Write exit rules down in advance.",
    "i_cuts_losses_t": "Most losing trades are cut quickly",
    "i_cuts_losses_e": "Median holding: losing cycles {loss_days:.1f} days, shorter than winning cycles ({win_days:.1f} days).",
    "i_cuts_losses_but": " The big losses above are the exception — the issue there is size, not speed.",
    "i_averaging_down_t": "You often add below your cost",
    "i_averaging_down_e": "{share:.0%} of your {adds} adds to an open position were below its average cost (averaging down).",
    "i_averaging_down_s": "Averaging down isn't wrong in itself, but it's a common route to oversized positions and big losses. "
                          "Decide in advance how many times you'll add.",
    "i_weak_market_t": "{ccy} market is a drag",
    "i_weak_market_e": "{ccy} stocks realized {pl}, while your best market ({best}) made {best_pl}.",
    "i_weak_market_s": "Markets you know less well (hours, liquidity, conversion costs) may deserve smaller positions.",
    "i_fx_driven_t": "Much of your profit came from currency",
    "i_fx_driven_e": "Currency contributed {fx}; total account P/L {total}.",
    "i_fx_driven_s": "Exchange rates move both ways — a stronger home currency will take it back. Treat it as risk, not skill.",

    # currency tab
    "fx_title": "Your holdings' return, split",
    "fx_caption": "Return in {base} = price effect + currency effect + cross term. The % a broker app shows is in the "
                  "stock's own currency, not the change in your {base} balance.",
    "c_ret_local": "Return (local)", "c_ret_base": "Return ({base})", "c_price_eff": "Price effect",
    "c_fx_eff": "Currency effect", "c_cross": "Cross term", "c_gain_base": "P/L ({base})",
    "fx_split_title": "Where the currency effect came from",
    "fx_split_caption": "Split by the daily reference rate. For very active accounts these sub-items are sensitive to "
                        "intraday timing (a 0.2% rate difference on every trade adds up); the total is not.",
    "fx_on_shares": "On shares while held", "fx_on_cash": "On foreign cash", "fx_conversion": "Conversion vs reference rate",
    "cash_title": "Foreign cash",
    "cash_caption": "Foreign currency sitting in the account changes value in {base} even if you never trade.",
    "c_balance": "Balance", "c_value_base": "Value ({base})", "c_fx_realized": "Realized FX", "c_fx_unrealized": "Unrealized FX",
    "c_fx_total": "FX total",
    "fx_source_note": "Rates: {source}. Currencies the source doesn't publish are derived from your own IBKR conversions; "
                      "ending values use IBKR's closing rates.",

    # trades tab
    "trades_title": "Every closing trade",
    "c_time": "Time", "c_side": "Side", "c_qty": "Qty", "c_method": "Lot method", "c_hold_days": "Days held (oldest lot)",
    "side_long": "long", "side_short": "short",
    "filter": "Filter symbols", "download": "Download CSV",
    # round-trip calculator tab
    "tc_title": "🧮 Round-trip calculator",
    "tc_caption": "Before you sell: the buy-back price that actually lowers your cost after commission. "
                  "After you've traded: your real cost next to IBKR's.",
    "tc_mode": "Mode", "tc_mode_plan": "Before: buy-back price", "tc_mode_review": "After: real cost",
    "tc_pick": "Stock", "tc_manual": "✏️ Enter my own numbers",
    "tc_pick_help": "Pick a holding to fill in your shares, cost, latest price and your usual commission.",
    "tc_hold": "What you hold now", "tc_shares": "Shares", "tc_cost": "Cost per share",
    "tc_basis": "Cost to use", "tc_basis_real": "Real cost", "tc_basis_ibkr": "IBKR cost",
    "tc_zero_note": "Your round trips have already paid this holding back, so the real cost is below zero.",
    "tc_sell_title": "What you plan to sell", "tc_qty": "Shares sold", "tc_sell": "Sell price",
    "tc_price_now": "Latest price: {price:,.2f}",
    "tc_fee_title": "Commission per order", "tc_fee": "Commission per order (leave empty to estimate)",
    "fee_mine": "Estimated from your own trades in this stock: {fee:,.2f} an order. A round trip is two orders.",
    "fee_ibkr": "Estimated at IBKR's US fixed rate (0.005 a share, min 1): {fee:,.2f} an order. "
                "A round trip is two orders.",
    "tc_fee_own": "A round trip is two orders: {fees:,.2f} in total.",
    "tc_need": "Enter the shares you hold, and how many you plan to sell at what price.",
    "tc_be": "Buy back below this to come out ahead",
    "tc_be_say": "Selling {q:,.0f} at {s:,.2f} with {fees:,.2f} in commission, you need to buy back below {be:,.2f} "
                 "— {gap:,.2f} ({pct:.2f}%) under your sell price.",
    "tc_if": "If you buy back at", "tc_gain": "This round", "tc_gain_help": "After {fees:,.2f} commission.",
    "tc_newcost": "Your new cost",
    "tc_table": "At different buy-back prices", "tc_th_b": "Buy back at", "tc_th_gain": "This round",
    "tc_th_cost": "New cost", "tc_up": "price rose", "tc_be_short": "break-even",
    "tc_target": "Want your cost down to…",
    "tc_tgt_ok": "Buy back at **{b:,.2f}** or lower ({pct:+.1f}% vs your sell price).",
    "tc_tgt_no": "Not possible in one round selling {q:,.0f} shares — sell more, or plan several rounds.",
    "tc_tgt_above": "That's above your current cost — any buy-back under {be:,.2f} already gets you there.",
    "tc_risk": "If the price keeps rising instead: buying back at {up:,.2f} (+5%) lifts your cost to {cost:,.2f}. "
               "Not buying back leaves you with {left:,.0f} shares.",
    "tc_fine": "Real cost = money still in the position ÷ shares held. Ignores tax and currency. "
               "A calculator, not advice on whether to trade.",
    "tc_review_note": "For your real holdings this is already worked out in **{tab}** — use this to try numbers by hand.",
    "tc_examples": "Start with an example", "tc_ex_good": "Sold high, bought back low",
    "tc_ex_bad": "Got it backwards", "tc_ex_zero": "Down to zero cost",
    "tc_first": "Your first purchase", "tc_bought": "Shares bought", "tc_price": "Price per share",
    "tc_rounds": "Each round trip",
    "tc_rounds_hint": "One row per round: shares sold, sell price, buy-back price. Add rows at the bottom; "
                      "select a row to delete it.",
    "tc_buy": "Bought back at", "tc_now": "Today's price",
    "tc_ibkr": "Cost IBKR shows", "tc_real": "Your real cost",
    "tc_say_same": "No round trips yet — both costs are the same.",
    "tc_say_zero": "Your round trips have already paid back the whole position, plus {extra:,.2f}. The shares you "
                   "hold now cost you nothing — but IBKR still shows {ibkr:,.2f}.",
    "tc_say_lower": "Your round trips lowered your real cost by {diff:,.2f} a share ({pct:+.1f}%).",
    "tc_say_higher": "These round trips raised your real cost by {diff:,.2f} a share: you sold lower than you "
                     "bought back.",
    "tc_review_fine": "IBKR's cost assumes first-in, first-out lots; fees ignored.",
    "tc_share": "Share it with a friend — the same calculator works without an IBKR statement: "
                "[chuanyesama.github.io/truecost/calculator.html](https://chuanyesama.github.io/truecost/calculator.html)",
}

ZH = {
    "lang": "语言",
    "tab_home": "🏠 首页",
    "pro_status": "🚧 专业版还在开发中，最晚 2027-03-31 上线。现在成为创始会员，首年只要 A$49（之后 A$79/年），"
                  "也可以先买一个月 A$12；没按时上线全额退款。",
    "launch_status": "🚧 **目前上线的是免费版**：上面和各个标签页里的分析现在都能直接用。"
                     "**专业版、年度报告和 AI 功能都还在开发中。** 专业版现在可以 A$49 锁定创始会员首年，或先买一个月 A$12"
                     "（2027-03-31 前没上线全额退款）；年度报告的按钮只是登记兴趣，不会扣款。"
                     "先做哪个，由你在下面问卷里的回答决定。",
    "survey_callout": "🙋 **专业版、年度报告和 AI 功能还没上线。** 花 30 秒告诉我们你想要什么、愿不愿意付费 → "
                      "见本页下方「**帮我们决定下一步**」。",
    "survey_title": "🙋 帮我们决定下一步做什么",
    "survey_sub": "30 秒，每题都可以不填。每一份回答我们都会看。",
    "sv_pay_q": "专业版（从 IBKR 自动同步、看到当天交易、一键刷新）大约 {price}/月，你会付费吗？",
    "sv_pay_yes": "会，这个价格可以", "sv_pay_cheaper": "会，但要更便宜才行",
    "sv_pay_maybe": "还不确定", "sv_pay_no": "不会，免费版就够了",
    "sv_price_q": "你觉得多少钱一个月比较合理？",
    "sv_price_free": "不付费", "sv_per_month": "/月",
    "sv_report_q": "一次性的年度 PDF 报告（自己留档或交给会计师），大约 {price}，你会买吗？",
    "sv_report_yes": "会", "sv_report_maybe": "可能", "sv_report_no": "不会",
    "sv_ai_q": "下面哪些 AI 功能你真的会用？",
    "sv_ai_placeholder": "可多选",
    "sv_ai_ask": "用大白话问我的账户（“我今年 NVDA 赚了多少？”）",
    "sv_ai_review": "每月自动给我写一份交易复盘",
    "sv_ai_coach": "找出我的坏习惯，在我重犯之前提醒我",
    "sv_ai_import": "读取其他券商的对账单（富途、老虎、CommSec……）",
    "sv_ai_explain": "用大白话解释我的数字（佣金、汇率、成本）",
    "sv_ai_text": "你最希望 AI 帮你做什么？对 AI 有什么顾虑（准不准、隐私……）？",
    "sv_other": "还有什么想说的？缺什么功能、哪里看不懂、哪个数字看着不对……",
    "sv_email": "邮箱（选填，想要回复或抢先体验再填）",
    "sv_send": "提交",
    "survey_thanks": "谢谢！你的回答会决定我们接下来先做什么。🙏",
    "feedback_placeholder": "什么都可以说：哪个数字看着不对、哪个词看不懂、缺了什么功能……",
    "faq_pro_setup_q": "专业版需要我做什么设置？",
    "faq_pro_setup_a": "一次性设置，大约 5 分钟：在 IBKR 网页版（业绩与报表 → Flex 查询）里建两个查询（历史交易、当天成交），"
                       "生成一个 Flex token，然后粘贴到 TrueCost。之后每次打开网站都会自动同步。Flex token 只能读取报表，"
                       "不能下单，也不能转账。它最长有效一年，到期后在 IBKR 里续一下，一分钟就好。",
    "hero_pills": ["💱 交易 vs 汇率", "🎯 做 T 后的真实成本", "💸 每一笔费用", "📈 K 线上的买卖点"],
    "offer_short": "一整年浓缩成一份 PDF，可直接交给会计师。",
    "sidebar_footer": "🔒 不保存你的对账单 · 隐私说明在「🏠 首页」底部。仅供参考，不构成税务、财务或投资建议。",
    "hero_title": "你在 IBKR 赚的钱，是交易赚的，还是汇率给的？",
    "hero_sub": "上传 IBKR 对账单，用你的本币看清：钱到底从哪来、做 T 之后的真实成本、佣金吃掉了多少。",
    "hero_upload": "把 IBKR 活动对账单（CSV）拖到这里",
    "hero_private": "🔒 只在本次访问中处理，不保存任何内容。免费，不用注册。",
    "hero_or": "手边没有对账单？**往下看**——下面是示例账户的分析结果。",
    "demo_note": "👀 示例账户（虚构）。在上方上传你的对账单，就能看到你自己的。",
    "findings_demo": "TrueCost 能发现什么——示例账户",
    "findings_you": "你的 3 个关键发现",
    "card_money": "💱 钱从哪来",
    "card_money_big": "交易 {trading} · 汇率 {fx}",
    "card_money_fx": "盈利主要来自**汇率**，不是交易。券商从不把这两者分开显示。",
    "card_money_trade": "交易是主要来源，汇率影响 {fx}。",
    "card_money_offset": "交易亏了 {trading}，汇率帮你挽回了 {fx}。券商从不把这两者分开显示。",
    "card_money_both": "交易和汇率都在亏钱。",
    "card_cost": "🎯 做 T 之后的真实成本",
    "card_cost_zero_big": "{sym}：零成本持股",
    "card_cost_zero": "做 T 已经把本金全部赚回，还多赚 {extra}——剩下的股票全是利润。IBKR 却仍显示成本 {ibkr}。",
    "card_cost_gap_big": "{sym}：实际 {real:+.1f}%（IBKR 显示 {ibkr:+.1f}%）",
    "card_cost_gap": "算上卖出再买回的盈亏，真实结果和 IBKR 显示的不一样。",
    "card_cost_rounds_big": "做 T 合计 {total}",
    "card_cost_rounds": "在底仓上先卖后买、先买后卖，一共 {n} 轮。",
    "card_fees": "💸 交易花了多少钱",
    "card_fees_share": "佣金吃掉了扣费前交易利润的 **{share:.0%}**。",
    "card_fees_avg": "共 {n} 笔订单，平均每笔 {avg}。",
    "card_go": "→ 详情见「**{tab}**」",
    "card_trading": "📈 交易", "card_fx": "💱 汇率", "card_zero_value": "零成本持股",
    "card_real_help": "按摊薄成本（算上做 T）计算的收益率",
    "card_cost_gap_line": "IBKR 显示 **{ibkr:+.1f}%**，算上做 T 实际是 **{real:+.1f}%**。",
    "card_rounds_label": "做 T 合计", "card_fees_label": "佣金与费用",
    "style_line": "你的交易风格：**{style}** → 详见「**{tab}**」",
    "steps_title": "3 步看到你自己的数字",
    "step1_t": "1 · 下载", "step1_d": "IBKR 网页版 → 报表 → **活动** → CSV、English",
    "step2_t": "2 · 上传", "step2_d": "把文件拖到本页顶部的框里",
    "step3_t": "3 · 查看", "step3_d": "你的发现会显示在这里，每个标签页还能看更多细节",
    "steps_detail": "详细下载步骤和常见错误",
    "tabs_explained": "每个页面回答什么问题",
    "advanced": "⚙️ 高级设置",
    "reconciled_friendly": "✅ 已核对：所有数字加起来，正好等于你账户的实际盈亏（{pl}）。",
    "tab_guide": "👋 新手教程",
    "guide_title": "3 分钟上手",
    "guide_intro": "券商按币种分开显示盈亏，显示的也只是*平均*成本。TrueCost 把所有东西换算成**你的本币**，"
                   "回答券商页面回答不了的问题：\n\n"
                   "- **我赚的钱，是交易赚的，还是汇率给的？**\n"
                   "- **做 T（卖出再买回）之后，我的真实成本是多少？**\n"
                   "- **我付了多少佣金和费用——怎样能少付一点？**\n\n"
                   "现在看到的数字来自**示例账户**。按下面的步骤，就能看到你自己的。",
    "guide_s1": "第 1 步 · 从 IBKR 下载对账单",
    "guide_s1_body": "1. 用**电脑浏览器**登录 IBKR 网页版（不是手机 App）。\n"
                     "2. 顶部菜单：**业绩与报告 → 报表**（英文界面是 Performance & Reports → Statements）。\n"
                     "3. 在「默认报表」里找到 **活动（Activity）**，点这一行右边的 **→** 箭头。\n"
                     "4. 在弹出的窗口里：\n"
                     "   - **期间**：过去的年份选*年度*，今年选*年初至今*\n"
                     "   - **格式**：**CSV**\n"
                     "   - **语言**：**English**（必须是英文）\n"
                     "5. 点**运行 / 下载**，会得到一个类似 `U1234567_20260101_20261009.csv` 的文件。",
    "guide_s1_mistakes": "常见错误",
    "guide_s1_mistakes_body": "- **下载成了 PDF 或 HTML**——TrueCost 需要的是 CSV。\n"
                              "- **语言选了中文**——列名会变，文件读不了。\n"
                              "- **用了自主查询（Flex）、成交确认或税务报表**——请用普通的**活动**对账单。\n"
                              "- **开户好几年了？** 目前请一次上传一年（专业版会自动合并多年数据）。",
    "guide_s2": "第 2 步 · 上传",
    "guide_s2_body": "把文件拖到左侧边栏的 **IBKR 活动对账单（CSV）** 框里"
                     "（手机上点左上角 **»** 打开侧边栏），几秒钟就出结果。\n\n"
                     "🔒 对账单只在本次访问中处理：解析完立即删除临时文件，不保存任何内容，"
                     "也不会把金额、股票代码或账户号码发到任何地方。",
    "guide_s3": "第 3 步 · 看懂结果",
    "guide_s3_table": "| 页面 | 回答什么问题 |\n|---|---|\n"
                      "| **总览** | 我一共赚了多少？其中交易赚的和汇率给的各是多少？ |\n"
                      "| **真实成本** | 做 T 之后，每只股票真实成本是多少？有没有零成本持股？ |\n"
                      "| **K线图** | 我在哪个价位、哪个时间买的卖的？ |\n"
                      "| **做T记录** | 在底仓上做差价，到底有没有赚钱？ |\n"
                      "| **费用** | 佣金花了多少？怎样能少付？ |\n"
                      "| **交易风格** | 我是哪种交易者？哪些习惯在花我的钱？ |\n"
                      "| **汇率拆解** | 汇率给我的股票和现金加了多少、减了多少？ |\n"
                      "| **交易明细** | 每一笔平仓，可下载 CSV。 |\n\n"
                      "每个页面都和你的账户对过账：顶部的绿色 ✅ 表示 TrueCost 的拆分加起来"
                      "正好等于「期末净值 − 净入金」。",
    "guide_s4": "免费版还是专业版？",
    "guide_s4_body": "上面所有分析都是**免费**的。**专业版**适合不想每次都手动下载文件的活跃交易者：",
    "guide_faq": "常见问题",
    "faq_safe_q": "上传对账单安全吗？",
    "faq_safe_a": "免费版从不保存你的文件：只在本次访问的内存里解析，临时文件立即删除。匿名统计"
                  "（比如「有人上传了对账单」）从不包含金额、股票代码或账户号码。你也可以在自己电脑上运行 TrueCost——"
                  "代码在 GitHub 上开源。",
    "faq_diff_q": "为什么和 IBKR App 里的数字不完全一样？",
    "faq_diff_a": "IBKR 按每只股票自己的币种显示盈亏，显示的平均成本也不含做 T 的盈亏。TrueCost 把每笔交易按当天汇率"
                  "换算成你的本币，并给出摊薄成本。账户总额是一样的——顶部绿色 ✅ 会用「期末净值 − 净入金」核对。",
    "faq_brokers_q": "支持哪些券商和币种？",
    "faq_brokers_a": "盈透证券（IBKR），任何基础货币（AUD、USD、EUR、GBP……），美股、欧股、北欧和亚洲市场的股票和 ETF。"
                     "暂不支持期权、期货和其他券商。",
    "faq_advice_q": "这算税务或投资建议吗？",
    "faq_advice_a": "不算。TrueCost 是帮你复盘的计算工具。报税时请让注册税务师核对数字。",
    "guide_pointer": "第一次用？「**🏠 首页**」有上手步骤。",
    "plans_pointer": "免费版和专业版的区别：见「**🏠 首页**」。",
    "sync_title": "🔄 IBKR 自动同步", "sync_button": "🔄 刷新",
    "sync_today": "正在获取今天的成交…",
    "sync_today_failed": "暂时拿不到今天的成交（{err}），先显示已保存的数据。",
    "history_updating": "正在后台更新历史数据（IBKR 生成报表可能要一两分钟）。先显示上次保存的数据，完成后点「刷新」。",
    "history_failed": "后台更新历史数据失败（{err}），先显示上次保存的数据。",
    "sync_no_today": "配置 IBKR_FLEX_TODAY_QUERY_ID（成交确认查询）后可显示当天交易。",
    "live_prices": "持仓按最新价格估值（{when}，Yahoo，约 15 分钟延迟）",
    "sync_running": "正在向 IBKR 请求最新对账单…",
    "sync_waiting": "IBKR 还在生成对账单…（{n}）",
    "sync_done": "同步完成，显示的是最新交易。", "sync_failed": "同步失败（{err}），先显示上次保存的数据。",
    "sync_last": "上次同步：{when}",
    "parse_error": "这个文件看起来不是 IBKR 的**活动对账单（Activity Statement）** CSV。请在 IBKR 网页版选择"
                   "业绩与报告 → 报表 → **活动**，格式选 **CSV**，语言选 **English**，再试一次。",
    "offer_title": "年度报告（PDF）",
    "offer_body": "把你一整年浓缩成一份 PDF：按本币计算的盈亏（交易 vs 汇率）、每笔平仓按当日汇率折算的成本和收入、"
                  "费用和做 T 成绩——方便自己留存，也可以直接交给会计师。",
    "report_button": "预约年度报告 — 预计 {price}",
    "pro_title": "TrueCost 专业版",
    "pro_pitch": "打开网站就能看到今天的交易和持仓——自动从 IBKR 同步，点一下就刷新。另有多年历史合并、分钟级 K 线和 AI 分析。",
    "pro_button_year": "⭐ 成为创始会员 — 首年 A$49",
    "pro_button_month": "先买一个月 — A$12",
    "founder_terms_month": "将跳转到 Stripe 安全付款页支付 A$12（TrueCost 看不到你的卡号）。从专业版上线起算一个月，"
                           "不自动续费。如果 2027-03-31 前没上线，全额退款；上线前也可以随时申请退款："
                           "truecost.help@gmail.com。",
    "founder_terms_year": "将跳转到 Stripe 安全付款页支付 A$49（TrueCost 看不到你的卡号）。从专业版上线起算一整年，"
                     "之后 A$79/年 或 A$9/月。如果 2027-03-31 前没上线，全额退款；上线前也可以随时申请退款："
                     "truecost.help@gmail.com。",
    "founder_pay": "去安全付款 →",
    "plans_title": "免费版 vs 专业版",
    "plans_table": "| | 免费版（已上线） | 专业版（🚧 开发中） |\n|---|---|---|\n"
                   "| 数据导入 | 自己下载 CSV 上传 | **自动同步、当天交易、一键刷新** |\n"
                   "| 账户 | 不用注册，不保存数据 | 登录；IBKR token 加密保存 |\n"
                   "| 盈亏拆解、真实成本、做T、费用、交易风格 | ✅ | ✅ |\n"
                   "| K线图 + 买卖点 | 日线、周线 | + 分钟级（2H–1M） |\n"
                   "| 历史范围 | 一次一份对账单 | 多年自动合并 |\n"
                   "| AI：问你的账户、每月复盘 | — | ✅ |\n"
                   "| 年度报告 PDF | 每份 {report} | 包含 |\n\n"
                   "**专业版：{month}/月，或 {year}/年。预售：首年 A$49，或单月 A$12。**",
    "offer_soon": "还没上线，没有扣款。留下邮箱，上线时第一时间通知你（并享受早鸟价）。也欢迎填一下「🏠 首页」的小问卷。",
    "offer_email": "邮箱（选填）", "offer_notify": "通知我",
    "offer_thanks": "谢谢，已登记！", "offer_bad_email": "邮箱格式好像不对。",
    "feedback_title": "💬 提意见", "feedback_label": "哪里缺了、错了或者看不懂？",
    "feedback_send": "发送", "feedback_thanks": "谢谢！每一条我们都会看。",
    "privacy_title": "🔒 隐私",
    "privacy_body": "- 你的对账单只在本次会话中处理，解析完立即删除临时文件，分析结果一小时内过期。\n"
                    "- 为了改进 TrueCost，我们统计匿名使用情况：打开页面、语言、是否上传了对账单、本币、"
                    "市场数量、交易笔数的大致区间、点击了哪些按钮。**不记录任何金额、股票代码、账户号码或对账单内容。**\n"
                    "- 每次访问使用一个随机编号，不会跨访问追踪你。\n"
                    "- 只有你主动提交时才会保存邮箱、反馈和问卷回答，仅用于改进 TrueCost、回复或通知你。\n"
                    "- 统计服务商：PostHog（欧洲服务器）。",
    "theme_help": "深色模式（保存在本浏览器，切换后页面会刷新）",
    "sort_by": "排序",
    "sort_loss": "亏得最多的在前", "sort_gain": "赚得最多的在前", "sort_recent": "最近交易的在前",
    "sort_oldest": "最早建仓的在前", "sort_trades": "交易笔数最多", "sort_symbol": "按代码 A–Z",
    "c_last_trade": "最后交易",
    "tagline": "看清你的 IBKR 账户用本币算到底赚了多少。",
    "upload_header": "📄 导入对账单",
    "upload_label": "IBKR 活动对账单（CSV）",
    "how_to": "怎么下载？（1 分钟）",
    "how_to_steps": "1. 登录 IBKR 网页版 → **业绩与报告 → 报表**\n"
                    "2. **活动（Activity）** 一行点 →\n"
                    "3. 期间选 **年度 / 年初至今**，格式 **CSV**，语言 **English**\n"
                    "4. 下载后拖到上面",
    "lot_method": "批次匹配方式",
    "lot_method_help": "换一种方式看已实现/未实现怎么变；总盈亏不会变",
    "lot_ibkr": "按 IBKR 实际记录", "lot_fifo": "FIFO 先进先出", "lot_lifo": "LIFO 后进先出", "lot_hifo": "HIFO 高价先出",
    "fx_source": "汇率来源",
    "fx_ecb": "欧洲央行参考汇率", "fx_rba": "澳洲央行 RBA（ATO 认可）",
    "disclaimer": "仅供参考和复盘，不构成税务、财务或投资建议。",
    "local_file": "正在使用本地文件：{name}",
    "demo_banner": "👀 你正在看**示例账户**（虚构，价格和交易都是模拟生成的）。在左侧上传你自己的 IBKR 对账单即可分析——"
                   "文件只在本次会话中处理，不会被保存。",
    "as_of": "截至 {date} · 基础货币 {base} · 汇率：{source}",
    "reconciled": "✅ 已与账户对账：期末净值 {nav} − 净入金 {dep} = {pl}",
    "not_reconciled": "⚠️ 对账差异 {diff}，对账单中可能缺少部分数据",
    "tabs": ["总览", "真实成本", "K线图", "做T记录", "🧮 做T计算器", "费用", "交易风格", "汇率拆解", "交易明细"],
    "chart_title": "K 线图与你的买卖点", "chart_stock": "股票", "chart_range": "时间范围",
    "chart_loading": "正在加载行情…", "chart_volume": "成交量",
    "chart_B": "买入", "chart_S": "卖出",
    "chart_hover": "%{customdata[0]} 笔，共 %{customdata[1]:,.4g} 股，均价 %{customdata[2]:,.2f}",
    "chart_unmapped": "暂时没有 {sym}（交易所 {exch}）的行情数据。",
    "chart_no_data": "暂时无法加载 {ticker} 的行情，请稍后再试。",
    "chart_caption": "你在 {ticker} 的 {total} 笔交易中，有 {shown} 笔落在这个时间范围内；同一根 K 线里的多笔交易合并成一个标记"
                     "（鼠标悬停看明细）。时间为交易所当地时间（{tz}）；日内范围包含盘前盘后。行情来自 Yahoo Finance，可能有延迟。",
    "parsing": "正在解析对账单…", "costing": "正在计算费用…", "profiling": "正在分析交易习惯…",

    "total_pl": "总盈亏（{base}）", "from_trading": "📈 交易赚的", "from_fx": "💱 汇率给的", "other": "其他",
    "from_trading_help": "股价涨跌带来的盈亏（已扣佣金），按当日汇率换算",
    "from_fx_help": "持有外币（股票 + 现金）期间的汇率变化，加上换汇价差",
    "other_help": "利息、分红、预扣税、杂费",
    "fx_driven": "**你的盈利主要来自汇率，而不是交易。** 汇率贡献 {fx}，交易本身 {trading}。IBKR 的盈亏页面不会把这两者分开。",
    "fees_note": "“交易赚的”已经扣掉了佣金，佣金明细见「费用」页。",
    "wf_trading": "交易", "wf_fx": "汇率", "wf_other": "利息/分红/费用", "wf_total": "总盈亏",
    "by_market": "各市场已实现盈亏",
    "by_market_caption": "IBKR 按币种分开显示；统一换成一种货币才看得出哪个市场在赚、哪个在亏。",
    "col_ccy": "币种", "col_realized_local": "已实现（本币）", "col_realized_base": "已实现（{base}）",

    "real_cost_title": "做 T 之后的真实成本",
    "real_cost_caption": "**IBKR 成本** = 剩余批次的平均价（不含做 T 盈亏）。"
                         "**摊薄成本** = (买入总额 − 卖出总额) ÷ 持股数，自上次清仓起算；做 T 赚了它就变低。",
    "no_holdings": "当前没有持仓。",
    "zero_cost": "✅ 零成本", "already_up": "已多赚 {amount}",
    "zero_cost_msg": "🎉 **{sym} 已是零成本持股**：本金已经全部赚回，还多赚了 {ccy} {extra:,.0f}。"
                     "剩下的 {shares:,.4g} 股（市值 {ccy} {value:,.0f}）全部是利润。IBKR 却仍显示成本 {ibkr:,.2f}。",
    "better_msg": "**{sym}**：IBKR 显示 {ibkr:+.1f}%，算上做 T 实际是 **{real:+.1f}%**。",
    "worse_msg": "**{sym}**：IBKR 显示 {ibkr:+.1f}%，但做 T 亏损摊进去后实际是 **{real:+.1f}%**——别以为快回本了。",
    "c_symbol": "代码", "c_shares": "股数", "c_price": "现价", "c_ibkr_cost": "IBKR 成本",
    "c_diluted": "摊薄成本", "c_vs_ibkr": "按 IBKR 盈亏%", "c_vs_diluted": "按摊薄 盈亏%",
    "c_ibkr_cost_base": "IBKR 成本（{base}）", "c_diluted_base": "摊薄成本（{base}）",
    "c_cycle_realized": "本轮已实现", "c_zero": "零成本",
    "rel_price": "相对现价（%）", "s_ibkr_cost": "IBKR 成本", "s_diluted": "摊薄成本", "s_price": "现价",
    "all_stocks": "所有股票（含已清仓）",
    "all_stocks_caption": "每只股票从建仓到清仓算一个周期。已清仓周期的结果 = 卖出总额 − 买入总额（含佣金），与批次方式无关。",
    "status_open": "持有中", "status_closed": "已清仓", "status_zero": "持有中 · 零成本",
    "c_status": "状态", "c_cycles": "周期数", "c_trades": "交易笔数", "c_closed_pl": "已清仓周期盈亏（{base}）",
    "c_cur_diluted": "当前摊薄成本", "c_cur_diluted_base": "当前摊薄成本（{base}）",

    "rounds_none": "没有识别到做 T。",
    "rounds_title": "做 T 成绩单",
    "rounds_caption": "**倒T** = 底仓不动，先卖后买回；**正T** = 先买后卖回。仓位回到原来的底仓就算一轮。"
                      "结果 = 这一轮的卖出所得 − 买入花费（含佣金），换算成 {base} 后才能跨市场比较。"
                      "加仓超过原底仓再卖回的，算**加仓波段**，不计入做 T。",
    "m_rounds": "完成的轮数", "m_win": "胜率", "m_rounds_total": "做 T 合计", "m_avg_round": "平均每轮",
    "swing_msg": "**加仓波段** {n} 次，合计 {total}，胜率 {win:.0%}。",
    "swing_verdict": "做 T 本身在赚钱，亏损主要来自加仓波段。",
    "kind_sell_first": "倒T（先卖后买）", "kind_buy_first": "正T（先买后卖）", "kind_swing": "加仓波段",
    "c_kind": "类型", "c_n": "轮数", "c_win": "胜率", "c_total": "合计（{base}）",
    "rounds_axis": "做 T 合计（{base}）", "rounds_hover": "{n} 轮 · 胜率 {win}",
    "one_stock": "单只股票：每一轮的结果", "pick_stock": "选择股票",
    "c_start": "开始", "c_end": "结束", "c_base_pos": "底仓", "c_round_qty": "做T股数",
    "c_round_trades": "笔数", "c_result_local": "结果（本币）", "c_per_share": "每股差价", "c_result_base": "结果（{base}）",
    "c_state": "状态", "state_done": "完成", "state_open": "未回到底仓",
    "timeline_caption": "成本随每笔交易的变化：做 T 赚钱时蓝线（摊薄成本）往下走，IBKR 成本（虚线）却不会反映。"
                        "摊薄成本跌出图外 = 已赚回的钱超过剩余持仓成本（零成本持股）。",
    "buy": "买入", "sell": "卖出", "after_pos": "之后持仓", "price_axis": "价格（{ccy}）",

    "fees_title": "你为交易付了多少钱",
    "fees_caption": "每笔只扣一两块，所以感觉不到；加起来才看得见。包含股票佣金、交易所/监管费、交易税和换汇佣金，按当日汇率换算。",
    "f_total": "交易成本合计", "f_orders": "下单笔数", "f_orders_help": "平均每笔 {avg}",
    "f_annual": "按目前速度，一年约", "f_annual_help": "按 {days} 天的实际花费推算",
    "f_share": "占扣费前交易利润", "f_share_help": "股票佣金 ÷ 扣佣金前的股价盈亏",
    "wf_gross": "扣费前交易盈亏", "wf_fees": "佣金与费用", "wf_net": "实际交易盈亏",
    "min_msg": "**{share:.0%} 的美股订单付的是 US$1 最低佣金。** 标价是每股 US$0.005，"
               "但你的订单太小，实际中位数是每股 **US${ps:.3f}**（标价的 {x:.0f} 倍）。",
    "savings": "能省多少（估算）",
    "merge": "合并同向小单",
    "merge_help": "{n} 笔订单与前一笔同股票、同方向，相隔不到 10 分钟，并且付的是最低佣金。合成一笔下单只付一次最低佣金。",
    "merge_caption": "{n} 笔订单可以和前一笔合并",
    "tiered": "美股改用阶梯计费（Tiered）",
    "tiered_help": "Tiered：每股 US$0.0035，最低 US$0.35，另付交易所/清算费（按每股约 US$0.0032 估算，实际随交易所和挂单方式变化）。",
    "tiered_caption": "实际 US${a:,.0f} → 估算 US${e:,.0f}",
    "savings_warn": "⚠️ 节省金额是估算：阶梯计费的交易所费用因交易所、挂单/吃单而不同，月交易量越大单价越低；切换前请在 IBKR 官网核对当前费率。",
    "where": "钱花在哪里",
    "by_size": "按订单大小（{base}）：小单的费率高得多（1 基点 = 0.01%）", "by_mkt": "按市场",
    "c_size": "订单大小", "c_orders": "笔数", "c_comm": "佣金", "c_per_order": "平均每笔", "c_bps": "费率（基点）",
    "monthly": "每月佣金", "top_symbols": "佣金最多的股票", "orders_word": "笔",

    "style_title": "你的交易风格：{style}",
    "style_detail": "平均每个交易日 {tpd:.1f} 笔；{intraday:.0%} 的卖出平掉的是当天买的仓位；持仓时间中位数 {hold:.1f} 天。",
    "style_intraday": "日内超短线", "style_short_term": "短线", "style_swing": "波段", "style_long_term": "中长线",
    "tag_rounds": "频繁做T", "tag_high_freq": "高频", "tag_shorts": "会做空", "tag_markets": "跨 {n} 个市场",
    "k_win": "已清仓周期胜率", "k_win_help": "从建仓到清仓算一个周期，按本币盈亏判断输赢",
    "k_payoff": "盈亏比", "k_payoff_help": "平均盈利 ÷ 平均亏损",
    "k_pf": "盈亏因子", "k_pf_help": "总盈利 ÷ 总亏损；低于 1 表示总体亏损",
    "k_comm": "佣金合计", "k_comm_help": "平均每笔 {avg}",
    "hold_title": "卖出时平掉的仓位持有了多久", "hold_hover": "{share} 的卖出",
    "hold_intraday": "当天内", "hold_1_5d": "1–5 天", "hold_5_30d": "5–30 天", "hold_30d_plus": "30 天以上",
    "insights": "数据告诉你的事",
    "style_disclaimer": "以上是根据你自己交易记录得出的统计观察，用来帮助复盘，不构成投资建议，也不针对任何具体证券。",

    "i_fees_eat_profit_all_t": "佣金吃掉了全部交易利润",
    "i_fees_eat_profit_t": "佣金吃掉了大部分交易利润",
    "i_fees_eat_profit_e": "扣佣金前交易赚 {gross}，佣金 {commission}（占 {share:.0%}），扣完只剩 {net}。"
                           "平均每笔佣金 {per_trade}，{costly:.0%} 的交易佣金超过成交额的 0.1%。",
    "i_fees_eat_profit_s": "减少小额、零碎的订单（IBKR 每笔有最低佣金）；同样的想法用更少的笔数执行；检查是否适用阶梯佣金。",
    "i_losing_before_fees_t": "扣佣金前交易就在亏",
    "i_losing_before_fees_e": "扣佣金前 {gross}，佣金又花了 {commission}。",
    "i_losing_before_fees_s": "先降低交易频率，找出亏损来源（看下面几条）。",
    "i_rounds_win_swings_lose_t": "做T赚钱，加仓波段亏钱",
    "i_rounds_win_swings_lose_e": "做T {n} 轮合计 {total}；加仓超过底仓的波段 {n_swing} 次合计 {swing_total}。",
    "i_rounds_win_swings_lose_s": "你擅长在底仓上做差价，但重仓加码时表现差：可以给“超过底仓的加仓”设一个上限，比如不超过底仓的 1 倍。",
    "i_rounds_lose_t": "做T整体在亏", "i_rounds_lose_e": "{n} 轮合计 {total}。",
    "i_rounds_lose_s": "做T会增加交易次数和佣金，结果不理想时可以先减少做T。",
    "i_rounds_win_t": "做T整体在赚", "i_rounds_win_e": "{n} 轮合计 {total}。",
    "i_big_losses_t": "少数几笔大亏决定了结果",
    "i_big_losses_e": "最大的 3 笔亏损（{worst}）占全部亏损的 {share:.0%}。",
    "i_big_losses_s": "给单笔持仓设一个最大亏损额（比如账户的 1–2%），到了就离场；大亏几乎都来自仓位过重。",
    "i_profit_factor_t": "赚的钱不够覆盖亏的钱",
    "i_profit_factor_e": "已清仓周期胜率 {win_rate:.0%}，平均盈利 {avg_win}，平均亏损 {avg_loss}，盈亏因子 {pf:.2f}（低于 1 表示总体亏损）。",
    "i_profit_factor_s": "胜率接近一半时，要靠“赚的比亏的多”才能盈利：让盈利单拿得比亏损单久一点，或者截断大亏。",
    "i_disposition_t": "亏损单拿得比盈利单久",
    "i_disposition_e": "亏损周期持有中位数 {loss_days:.1f} 天，盈利周期 {win_days:.1f} 天。",
    "i_disposition_s": "这是常见的“处置效应”：赚了急着走，亏了舍不得卖。可以提前写好止损条件。",
    "i_cuts_losses_t": "多数亏损单处理果断",
    "i_cuts_losses_e": "亏损周期持有中位数 {loss_days:.1f} 天，比盈利周期（{win_days:.1f} 天）短。",
    "i_cuts_losses_but": "不过上面那几笔大亏是例外，问题出在仓位而不是止损速度。",
    "i_averaging_down_t": "经常在成本价以下加仓",
    "i_averaging_down_e": "{adds} 次加仓里有 {share:.0%} 发生在价格低于持仓成本时（摊平）。",
    "i_averaging_down_s": "摊平本身不一定错，但它是重仓和大亏的主要来源之一，最好事先定好最多摊几次。",
    "i_weak_market_t": "{ccy} 市场拖累明显",
    "i_weak_market_e": "{ccy} 计价股票已实现 {pl}，而表现最好的 {best} 市场是 {best_pl}。",
    "i_weak_market_s": "不熟悉的市场（交易时间、流动性、换汇成本都不同）可以先降低仓位。",
    "i_fx_driven_t": "盈利很大一部分来自汇率",
    "i_fx_driven_e": "汇率贡献 {fx}，账户总盈亏 {total}。",
    "i_fx_driven_s": "汇率是双向的：本币走强时同样会吃掉利润。把它当作风险看待，不要算作交易能力。",

    "fx_title": "持仓收益拆解",
    "fx_caption": "{base} 收益 = 股价贡献 + 汇率贡献 + 交叉项。券商 App 显示的 % 是股票本币的收益，不等于你 {base} 余额的变化。",
    "c_ret_local": "本币收益%", "c_ret_base": "{base} 收益%", "c_price_eff": "股价贡献",
    "c_fx_eff": "汇率贡献", "c_cross": "交叉项", "c_gain_base": "盈亏（{base}）",
    "fx_split_title": "汇率影响来自哪里",
    "fx_split_caption": "按每日参考汇率划分。交易非常频繁的账户，这几个子项对汇率时点很敏感（每笔 0.2% 的汇率差累积起来不小），但合计数不受影响。",
    "fx_on_shares": "持股期间", "fx_on_cash": "外币现金", "fx_conversion": "换汇价 vs 参考汇率",
    "cash_title": "外币现金",
    "cash_caption": "账户里放着的外币，即使不交易，换算成 {base} 的价值也会随汇率波动。",
    "c_balance": "当前余额", "c_value_base": "价值（{base}）", "c_fx_realized": "已实现汇兑", "c_fx_unrealized": "未实现汇兑",
    "c_fx_total": "汇兑合计",
    "fx_source_note": "汇率来源：{source}。来源未公布的币种用你自己在 IBKR 的换汇价推算；期末按 IBKR 收盘汇率估值。",

    "trades_title": "每笔平仓明细",
    "c_time": "时间", "c_side": "方向", "c_qty": "数量", "c_method": "批次方式", "c_hold_days": "最早批次持有天数",
    "side_long": "多", "side_short": "空",
    "filter": "筛选代码", "download": "下载 CSV",
    # 做T计算器
    "tc_title": "🧮 做 T 计算器",
    "tc_caption": "卖出之前：算好扣掉佣金后，买回价要低于多少才真正降成本。做完之后：对比 IBKR 显示的成本和你的真实成本。",
    "tc_mode": "模式", "tc_mode_plan": "做 T 前：算买回价", "tc_mode_review": "做完后：算真实成本",
    "tc_pick": "股票", "tc_manual": "✏️ 自己填数字",
    "tc_pick_help": "选一只持仓，自动填好持股数、成本、最新价和你平时的佣金。",
    "tc_hold": "现在的持仓", "tc_shares": "持有股数", "tc_cost": "每股成本",
    "tc_basis": "用哪个成本", "tc_basis_real": "真实成本", "tc_basis_ibkr": "IBKR 成本",
    "tc_zero_note": "做 T 已经把这只股票的本金赚回来了，所以真实成本是负数。",
    "tc_sell_title": "这次打算卖出", "tc_qty": "卖出股数", "tc_sell": "卖出价",
    "tc_price_now": "最新价：{price:,.2f}",
    "tc_fee_title": "每笔佣金", "tc_fee": "每笔佣金（留空自动估算）",
    "fee_mine": "按你这只股票过去的交易估算：每笔 {fee:,.2f}。一卖一买共两笔。",
    "fee_ibkr": "按 IBKR 美股固定佣金估算（每股 0.005，最低 1）：每笔 {fee:,.2f}。一卖一买共两笔。",
    "tc_fee_own": "一卖一买共两笔，合计 {fees:,.2f}。",
    "tc_need": "先填持有股数，以及打算卖多少股、卖什么价。",
    "tc_be": "买回价低于这个数才不亏",
    "tc_be_say": "在 {s:,.2f} 卖出 {q:,.0f} 股、佣金共 {fees:,.2f}，买回价要低于 {be:,.2f}，"
                 "也就是比卖出价低 {gap:,.2f}（{pct:.2f}%）。",
    "tc_if": "如果买回价是", "tc_gain": "这一轮", "tc_gain_help": "已扣佣金 {fees:,.2f}。",
    "tc_newcost": "买回后的新成本",
    "tc_table": "不同买回价的结果", "tc_th_b": "买回价", "tc_th_gain": "这一轮", "tc_th_cost": "新成本",
    "tc_up": "涨了才买回", "tc_be_short": "保本",
    "tc_target": "想把成本降到……",
    "tc_tgt_ok": "买回价要在 **{b:,.2f}** 或以下（比卖出价 {pct:+.1f}%）。",
    "tc_tgt_no": "卖 {q:,.0f} 股做一轮做不到——多卖一些，或者分几轮。",
    "tc_tgt_above": "这比现在的成本还高——只要在 {be:,.2f} 以下买回就已经达到了。",
    "tc_risk": "如果卖了之后股价继续涨：在 {up:,.2f}（+5%）买回，成本会升到 {cost:,.2f}；"
               "不买回的话，你手里只剩 {left:,.0f} 股。",
    "tc_fine": "真实成本 = 仍投在这只股票里的钱 ÷ 持有股数。未计税和汇率。这只是计算工具，不建议你是否交易。",
    "tc_review_note": "你真实持仓的这些数字，**{tab}** 里已经自动算好了——这里用来手动试算。",
    "tc_examples": "先点一个例子看看", "tc_ex_good": "高抛低吸成功", "tc_ex_bad": "做 T 做反了", "tc_ex_zero": "做到零成本",
    "tc_first": "最初买入", "tc_bought": "买入股数", "tc_price": "每股价格",
    "tc_rounds": "每一轮做 T",
    "tc_rounds_hint": "每行一轮：卖出股数、卖出价、买回价。在表格最下面加一行；选中一行可以删除。",
    "tc_buy": "买回价", "tc_now": "现在的股价",
    "tc_ibkr": "IBKR 显示成本", "tc_real": "你的真实成本",
    "tc_say_same": "还没有做 T，两个成本一样。",
    "tc_say_zero": "做 T 已经把本金全部赚回，还多赚 {extra:,.2f}。你现在手里的股票等于零成本——IBKR 却仍显示成本 {ibkr:,.2f}。",
    "tc_say_lower": "做 T 让你每股真实成本降低了 {diff:,.2f}（{pct:+.1f}%）。",
    "tc_say_higher": "这几轮做 T 让每股真实成本升高了 {diff:,.2f}：卖得比买回的还低。",
    "tc_review_fine": "IBKR 成本按先进先出计算；未计佣金。",
    "tc_share": "分享给朋友——不用对账单也能用的网页版："
                "[chuanyesama.github.io/truecost/calculator.html](https://chuanyesama.github.io/truecost/calculator.html)",
}

LANGS = {"English": EN, "中文": ZH}


class Translator:
    def __init__(self, lang: str):
        self.d = LANGS.get(lang, EN)

    def __call__(self, key: str, **kw):
        s = self.d.get(key, EN.get(key, key))
        return s.format(**kw) if kw and isinstance(s, str) else s

    def has(self, key: str) -> bool:
        return key in self.d or key in EN


def money(x: float, ccy: str, sign: bool = True, decimals: int = 0) -> str:
    sym = SYMBOLS.get(ccy, f"{ccy} ")
    body = f"{sym}{abs(x):,.{decimals}f}"
    if not sign:
        return body
    return f"{'+' if x >= 0 else '−'}{body}"
