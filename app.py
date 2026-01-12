from dotenv import load_dotenv
load_dotenv()

import os
from datetime import datetime
from streamlit_autorefresh import st_autorefresh
from zoneinfo import ZoneInfo
import requests
import streamlit as st

st.set_page_config(page_title="Älvsjö → City", layout="centered")
st_autorefresh(interval=30_000, key="auto_refresh")




API_KEY = os.getenv("TRAFIKLAB_API_KEY")
if not API_KEY:
    st.error("Missing TRAFIKLAB_API_KEY")
    st.stop()

ALVSJO_EXT_ID = "740000789"
BASE = "https://api.resrobot.se/v2.1"

st.title("🚆 Älvsjö → City")

now = datetime.now().strftime("%H:%M:%S")
st.caption(f"Refreshed {now}")


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
        raw_time = d.get("time", "")          # "22:57:00"
        time = d.get("time", "")[:5]

        raw_date = d.get("date", "")          # "2026-01-12"
        line = d.get("ProductAtStop", {}).get("displayNumber")
        direction = d.get("direction")
        platform = d.get("rtPlatform") or d.get("platform") or d.get("stopPlatform")


        # Bygg en timezone-aware datetime i Stockholm-tid
        tz = ZoneInfo("Europe/Stockholm")
        now = datetime.now(tz)

        dep_dt = datetime.strptime(f"{raw_date} {raw_time}", "%Y-%m-%d %H:%M:%S").replace(tzinfo=tz)
        mins = int((dep_dt - now).total_seconds() // 60)

        # Om API ibland ger lite “bakåt” vid refresh, clampa till 0
        mins = max(mins, 0)

        time_hhmm = raw_time[:5]

        platform_html = f'<span style="color:#9ca3af; font-size: 1.0rem; margin-left: 0.6rem;">Perrong {platform}</span>' if platform else ""


        html = f"""
        <div style="color: #ffffff; font-size: 1.2rem; font-weight: 600; margin-bottom: 0.1rem;">
    {direction}
    </div>


    <div style="font-size: 1.9rem; font-weight: 700; line-height: 1.1; margin-top: 0.15rem;">
        {time_hhmm}
    </div>

    <div style="font-size: 2.6rem; font-weight: 800; line-height: 1.1;">
        Avgår om {mins} min
    </div>

    <div style="margin-top: 0.25rem;">
        <span style="color:#ffffff; font-size: 1.25rem; font-weight: 700;">
        🚆 Pendeltåg {line}
        </span>
        {platform_html}
    </div>
    </div>
    """
        st.markdown(html, unsafe_allow_html=True)
        st.divider()

st.caption(f"Last updated: {datetime.now().strftime('%H:%M:%S')}")
