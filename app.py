import streamlit as st
import requests
import pandas as pd
from streamlit_autorefresh import st_autorefresh

# REFRESH AUTO toutes les 1s
st_autorefresh(interval=1000, key="firebase_refresh")

BASE = "https://voitureesp32-default-rtdb.europe-west1.firebasedatabase.app"
PATH = "timing"
URL = f"{BASE}/{PATH}.json"

@st.cache_data(ttl=1)
def fetch_timing():
    r = requests.get(URL, timeout=10)
    r.raise_for_status()
    return r.json()


st.title("⏱️ Timing (Firebase)")

try:
    data = fetch_timing()

    # Cas: [null, {...}]
    if isinstance(data, list) and len(data) > 1 and data[1]:
        payload = data[1]
    else:
        payload = data or {}

    best = payload.get("best", {})
    last10 = payload.get("last10", [])

    st.subheader("🏆 Best")
    st.json(best)

    st.subheader("🕒 Last 10")
    if isinstance(last10, list) and last10:
        df = pd.DataFrame(last10)


        if "ts" in df.columns:
            df = df.sort_values("ts", ascending=False)
