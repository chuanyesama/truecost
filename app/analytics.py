"""Anonymous usage events (PostHog), fire-and-forget.

What is sent: event name, a random per-session id, and coarse, non-financial
properties (language, base currency, number of markets, a trade-count bucket,
which button was clicked). Never amounts, symbols, account ids or statement
contents. Waitlist emails are sent only when a viewer types one in.

Disabled unless a key is configured, so local runs and tests send nothing:
  Streamlit secrets:  POSTHOG_KEY = "phc_..."   (optional POSTHOG_HOST)
  or environment variables with the same names.
"""
from __future__ import annotations

import json
import os
import threading
import urllib.request
import uuid

import streamlit as st

DEFAULT_HOST = "https://eu.i.posthog.com"


def _config() -> tuple[str | None, str]:
    try:
        key, host = st.secrets.get("POSTHOG_KEY"), st.secrets.get("POSTHOG_HOST")
    except Exception:  # no secrets file
        key = host = None
    return key or os.environ.get("POSTHOG_KEY"), host or os.environ.get("POSTHOG_HOST") or DEFAULT_HOST


def session_id() -> str:
    if "anon_id" not in st.session_state:
        st.session_state.anon_id = uuid.uuid4().hex  # new every visit; no cross-session tracking
    return st.session_state.anon_id


def _send(host: str, payload: dict) -> None:
    try:
        req = urllib.request.Request(f"{host}/i/v0/e/", data=json.dumps(payload).encode(),
                                     headers={"Content-Type": "application/json"}, method="POST")
        urllib.request.urlopen(req, timeout=4).read()
    except Exception:
        pass  # analytics must never break the app


def track(event: str, **props) -> None:
    key, host = _config()
    if not key:
        return
    payload = {"api_key": key, "event": event, "distinct_id": session_id(),
               "properties": {**props, "$process_person_profile": False}}
    threading.Thread(target=_send, args=(host, payload), daemon=True).start()


def track_once(event: str, **props) -> None:
    """Send an event at most once per session (Streamlit reruns the script often)."""
    sent = st.session_state.setdefault("_sent_events", set())
    tag = event + json.dumps(props, sort_keys=True, default=str)
    if tag not in sent:
        sent.add(tag)
        track(event, **props)


def trades_bucket(n: int) -> str:
    for hi, label in [(50, "<50"), (200, "50-200"), (1000, "200-1000"), (5000, "1000-5000")]:
        if n < hi:
            return label
    return "5000+"
