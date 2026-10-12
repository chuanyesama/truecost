"""UI strings in English and Chinese. t("key", **params) formats in the
current language; missing keys fall back to English."""
from __future__ import annotations

SYMBOLS = {"AUD": "A$", "USD": "US$", "EUR": "€", "GBP": "£", "JPY": "¥", "CAD": "C$", "NZD": "NZ$",
           "HKD": "HK$", "SGD": "S$", "CHF": "CHF ", "CNH": "¥", "CNY": "¥"}

EN = {
    # app chrome
    "lang": "Language",
    "parse_error": "This file doesn't look like an IBKR **Activity Statement** CSV. In the IBKR Portal choose "
                   "Performance & Reports → Statements → **Activity**, format **CSV**, language **English**, and try again.",
    "offer_title": "Annual report (PDF)",
    "offer_body": "Your year in one PDF: P/L in your home currency split into trading vs currency, every closed "
                  "trade with cost and proceeds at each day's rate, fees and round-trip results — ready to keep or "
                  "hand to your accountant.",
    "offer_button": "Get the report — {price}",
    "offer_soon": "Coming soon! Leave your email and we'll tell you when it's ready (and give you an early-bird price).",
    "offer_email": "Email (optional)", "offer_notify": "Notify me",
    "offer_thanks": "Thanks — you're on the list.", "offer_bad_email": "That email doesn't look right.",
    "feedback_title": "💬 Feedback", "feedback_label": "What's missing, wrong or confusing?",
    "feedback_send": "Send", "feedback_thanks": "Thank you!",
    "privacy_title": "🔒 Privacy",
    "privacy_body": "- Your statement is processed for your session only; the temporary file is deleted right after "
                    "parsing and results expire within an hour.\n"
                    "- We count anonymous usage events to improve TrueCost: page opened, language, whether a "
                    "statement was uploaded, base currency, number of markets, a rough trade-count range, and which "
                    "buttons were clicked. **No amounts, symbols, account numbers or statement contents.**\n"
                    "- A random id identifies one visit only; we don't track you across visits.\n"
                    "- Your email and feedback are stored only if you type them in, and used only to reply or notify you.\n"
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
    "tabs": ["Overview", "Real cost", "Round trips", "Fees", "Trading style", "Currency", "Trades"],
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
    "zero_cost": "✅ zero cost",
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
}

ZH = {
    "lang": "语言",
    "parse_error": "这个文件看起来不是 IBKR 的**活动对账单（Activity Statement）** CSV。请在 IBKR 网页版选择"
                   "业绩与报告 → 报表 → **活动**，格式选 **CSV**，语言选 **English**，再试一次。",
    "offer_title": "年度报告（PDF）",
    "offer_body": "把你一整年浓缩成一份 PDF：按本币计算的盈亏（交易 vs 汇率）、每笔平仓按当日汇率折算的成本和收入、"
                  "费用和做 T 成绩——方便自己留存，也可以直接交给会计师。",
    "offer_button": "获取报告 — {price}",
    "offer_soon": "即将推出！留下邮箱，上线时第一时间通知你（并享受早鸟价）。",
    "offer_email": "邮箱（选填）", "offer_notify": "通知我",
    "offer_thanks": "谢谢，已登记！", "offer_bad_email": "邮箱格式好像不对。",
    "feedback_title": "💬 反馈", "feedback_label": "哪里缺了、错了或者看不懂？",
    "feedback_send": "发送", "feedback_thanks": "谢谢！",
    "privacy_title": "🔒 隐私",
    "privacy_body": "- 你的对账单只在本次会话中处理，解析完立即删除临时文件，分析结果一小时内过期。\n"
                    "- 为了改进 TrueCost，我们统计匿名使用情况：打开页面、语言、是否上传了对账单、本币、"
                    "市场数量、交易笔数的大致区间、点击了哪些按钮。**不记录任何金额、股票代码、账户号码或对账单内容。**\n"
                    "- 每次访问使用一个随机编号，不会跨访问追踪你。\n"
                    "- 只有你主动填写时才会保存邮箱和反馈，仅用于回复或通知你。\n"
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
    "tabs": ["总览", "真实成本", "做T记录", "费用", "交易风格", "汇率拆解", "交易明细"],
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
    "zero_cost": "✅ 零成本",
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
