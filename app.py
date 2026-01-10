import streamlit as st
import requests
import pandas as pd
from streamlit_autorefresh import st_autorefresh

st_autorefresh(interval=1000, key="firebase_refresh")

BASE = "https://voitureesp32-default-rtdb.europe-west1.firebasedatabase.app"
URL = f"{BASE}/timing.json"

@st.cache_data(ttl=1)
def fetch_timing():
    r = requests.get(URL, timeout=10)
    r.raise_for_status()
    return r.json()

st.title("⏱️ Timing (Firebase)")

data = fetch_timing() or {}

if not isinstance(data, dict) or not data:
    st.warning("Aucune donnée dans /timing")
    st.stop()

# ✅ dernier timer_id = le plus grand nombre
timer_ids = [k for k in data.keys() if str(k).isdigit()]
if not timer_ids:
    st.error("Je ne trouve aucun timer_id (clé numérique) dans /timing")
    st.json(data)
    st.stop()

latest_id = str(max(map(int, timer_ids)))
payload = data.get(latest_id, {}) or {}

best = payload.get("best", {})
last10 = payload.get("last10", [])

# last10 parfois dict → list
if isinstance(last10, dict):
    last10 = list(last10.values())

st.success(f"Session affichée : timer_id = {latest_id}")

st.subheader("🏆 Best")
if best:
    st.json(best)
else:
    st.info("Aucun best disponible")

st.subheader("🕒 Last 10")
if isinstance(last10, list) and last10:
    df = pd.DataFrame(last10)
    if "ts" in df.columns:
        df["ts"] = pd.to_numeric(df["ts"], errors="coerce")
        df = df.sort_values("ts", ascending=False)
    df = df.reset_index(drop=True)
    df.insert(0, "Lap n°", df.index + 1)
    st.dataframe(df, use_container_width=True)
else:
    st.info("Aucune donnée dans last10")
