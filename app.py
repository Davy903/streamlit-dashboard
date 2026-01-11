import streamlit as st
import requests
import pandas as pd
from streamlit_autorefresh import st_autorefresh

st_autorefresh(interval=1000, key="firebase_refresh")

BASE = "https://voitureesp32-default-rtdb.europe-west1.firebasedatabase.app"
URL = f"{BASE}/timing.json"

@st.cache_data(ttl=1)
def fetch():
    r = requests.get(URL, timeout=10)
    r.raise_for_status()
    return r.json()

st.title("⏱️ Timing (Firebase)")

data = fetch()

# ✅ TON CAS: timing = [null, {...}]
payload = {}
if isinstance(data, list) and len(data) > 1 and isinstance(data[1], dict):
    payload = data[1]
elif isinstance(data, dict):
    payload = data  # fallback si ça change un jour

best = payload.get("best", {})
last10 = payload.get("last10", [])

st.subheader("🏆 Best")
if best:
    st.json(best)
else:
    st.info("Aucun best disponible")

st.subheader("🕒 Last 10")
if isinstance(last10, list) and last10:
    df = pd.DataFrame(last10)

    # tri par timestamp décroissant
    if "ts" in df.columns:
        df["ts"] = pd.to_numeric(df["ts"], errors="coerce")
        df = df.sort_values("ts", ascending=False)

    df = df.reset_index(drop=True)
    df.insert(0, "Lap n°", df.index + 1)

    df = df.rename(columns={
        "lap_index": "Index",
        "lap_s": "Temps (s)",
        "timer_id": "Timer ID",
        "ts": "Timestamp"
    })

    st.dataframe(df, use_container_width=True)
else:
    st.info("Aucune donnée dans last10")
