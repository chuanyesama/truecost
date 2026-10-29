"""What TrueCost sells and for how much, shared by the Streamlit app and the web app."""
from __future__ import annotations

# prices shown in the viewer's currency (rounded local equivalents of the AUD price)
PRICES = {
    "report": {"AUD": 19, "USD": 12, "EUR": 11, "GBP": 10, "NZD": 21, "CAD": 17, "SGD": 16, "HKD": 95},
    "pro_month": {"AUD": 9, "USD": 6, "EUR": 5.5, "GBP": 4.9, "NZD": 10, "CAD": 8, "SGD": 8, "HKD": 45},
    "pro_year": {"AUD": 79, "USD": 52, "EUR": 48, "GBP": 42, "NZD": 87, "CAD": 72, "SGD": 70, "HKD": 400},
}

# presale: Pro's first year (A$49) or one month (A$12) through Stripe Payment Links
FOUNDER_URL = {"year": "https://buy.stripe.com/dRmeVe8MLd9w0MT7DmfEk00",
               "month": "https://buy.stripe.com/7sYfZi0gf4D067d9LufEk01"}
