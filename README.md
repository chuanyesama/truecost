# TrueCost

**See what your Interactive Brokers account really earned — in your home currency.**

Upload an IBKR Activity Statement and TrueCost answers the questions the broker's own screens don't. Works for any base currency; English and Chinese UI.

- **How much came from trading, and how much from the exchange rate?** Total P/L split into trading, currency and interest/fees. The split reconciles to *ending NAV − net deposits* to the cent, and the app checks this every time.
- **What is my real cost after trading around a position?** IBKR shows the average of the remaining tax lots. TrueCost also shows the *diluted* cost, which counts the profit from every sell-and-buy-back, and flags zero-cost holdings.
- **Did my round trips actually make money?** Each round (sell → buy back, or buy → sell back, to the core position) is detected regardless of the lot-matching method. Oversized adds are separated out as swings.
- **How much am I paying in fees, and why?** Commissions by order size, market and month, how often orders hit the minimum charge, and estimated savings from merging orders or switching pricing plans.
- **What kind of trader am I?** Holding-period mix, win rate, payoff ratio, profit factor, loss concentration and averaging-down frequency produce a style label and observations, each backed by its numbers. Suggestions cover process only, never which security to trade.

> Try it with the built-in **synthetic sample account** — no real data is included in this repository.

## Why

I trade US, European and Asian stocks through IBKR with a non-USD base currency. Over five months I found that:

- **my trading P/L was negative while my account was up** — more than 100% of the gain came from the exchange rate, and no IBKR screen separates the two;
- **commissions were larger than my entire pre-fee trading profit**, one small charge at a time: 81% of my US orders paid the minimum commission, about 20× the per-share list price;
- **my round trips were profitable, but oversized averaging-down swings lost several times that amount.**

TrueCost turns these findings into something any IBKR user can run on their own statement.

## How it works

| Module | What it does |
|---|---|
| `src/ingest.py` | Parses IBKR's multi-section Activity Statement CSV; reads the lot-matching election (FIFO/LIFO/…) IBKR records on each closing trade; folds in post-trade commission adjustments |
| `src/costbasis.py` | Replays trades into tax lots under any lot-matching method, including short positions; tracks lot-average and diluted cost in trade and base currency |
| `src/fx.py` | Daily rates for any base currency from ECB euro reference rates (or RBA F11.1 for AUD, the source the Australian Taxation Office accepts); currencies a source doesn't publish are derived from the user's own FX trades |
| `src/returns.py` | Gain in base currency = price effect + FX effect + cross term |
| `src/ledger.py` | Every cash movement; foreign cash pooled at average base-currency cost to measure FX P/L on cash; conversion price vs reference rate |
| `src/report.py` | Builds the whole report and checks that the attribution adds up to NAV − net deposits |
| `src/rounds.py` | Flat-to-flat holding cycles and round trips, independent of lot method |
| `src/costs.py` | Fee breakdown and savings scenarios |
| `src/style.py` | Trading-habit metrics → style label → evidence-based observations (language-neutral keys) |
| `app/app.py`, `app/i18n.py` | Streamlit UI, English / Chinese |

**Validation.** On a real account (1,700+ stock trades across 5 currencies): realized P/L matches IBKR in every currency (USD within 0.005%), position costs match IBKR's, and the base-currency attribution matches the statement's NAV change exactly. Tests generate synthetic accounts in AUD, USD and EUR and require the same reconciliation.

**A note on precision.** Splitting the currency effect into "on shares", "on cash" and "conversion spread" uses one reference rate per day. For very active accounts those sub-items are sensitive to intraday timing; the headline trading-vs-currency split is not (two rate sources agree within ~5%).

## Run locally

```bash
pip install -r requirements.txt
streamlit run app/app.py
```

- Tests: `python -m pytest`
- Regenerate the sample account: `python scripts/make_sample.py [BASE]`
- Put your own statements in `data/raw/` (git-ignored); set `TRUECOST_DEMO=1` to force the sample.

## Getting your statement

IBKR Portal → **Performance & Reports → Statements → Activity** → period *Annual* / *Year to Date*, format **CSV**, language **English**.

## Privacy

Uploaded statements are parsed in memory for your session; the temporary file is deleted as soon as parsing finishes, and cached results expire after an hour.

## Disclaimer

For information and self-review only. Not tax, financial or investment advice. Savings estimates for pricing plans are approximate — check IBKR's current rates.
