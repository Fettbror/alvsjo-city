from dotenv import load_dotenv
load_dotenv()

import os
from datetime import datetime

import requests
import streamlit as st

st.set_page_config(page_title="Älvsjö → City", layout="centered")

API_KEY = os.getenv("TRAFIKLAB_API_KEY")
if not API_KEY:
    st.error("Missing TRAFIKLAB_API_KEY")
    st.stop()

ALVSJO_EXT_ID = "740000789"
BASE = "https://api.resrobot.se/v2.1"

st.title("🚆 Älvsjö → City")
st.caption("Pendeltåg som stannar vid Odenplan")


@st.cache_data(ttl=15)
def fetch_departures():
    res = requests.get(
        f"{BASE}/departureBoard",
        params={
            "id": ALVSJO_EXT_ID,
            "format": "json",
            "accessId": API_KEY,
            "duration": 90,
        },
        timeout=20,
    )
    res.raise_for_status()
    return res.json().get("Departure", [])


def is_commuter_train(dep: dict) -> bool:
    p = dep.get("ProductAtStop") or {}
    return p.get("catOut") == "JLT"


def is_towards_city(dep: dict) -> bool:
    return str(dep.get("directionFlag", "")) == "2"


deps = fetch_departures()
filtered = [d for d in deps if is_commuter_train(d) and is_towards_city(d)]

if not filtered:
    st.info("No upcoming commuter trains right now.")
else:
    for d in filtered:
        time = d.get("time", "")
        line = (d.get("ProductAtStop") or {}).get("displayNumber") or "?"
        direction = d.get("direction", "")

        html = f"""
<div style="padding: 0.25rem 0;">
  <div style="color: #9ca3af; font-size: 0.95rem; margin-bottom: 0.2rem;">
    {direction}
  </div>

  <div style="font-size: 2.8rem; font-weight: 800; line-height: 1.05; margin-bottom: 0.25rem;">
    {time}
  </div>

  <div style="font-size: 1.15rem;">
    🚆 Pendeltåg {line}
  </div>
</div>
"""
        st.markdown(html, unsafe_allow_html=True)
        st.divider()

st.caption(f"Last updated: {datetime.now().strftime('%H:%M:%S')}")
