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

# payload robuste
payload = {}
if isinstance(data, list):
    payload = next((x for x in reversed(data) if isinstance(x, dict)), {})
elif isinstance(data, dict):
    payload = data

best = payload.get("best", {})
last10 = payload.get("last10", [])

if isinstance(last10, dict):
    last10 = list(last10.values())

st.subheader("🏆 Best (comme Firebase)")
st.json(best)

st.subheader("🕒 Last 10 (comme Firebase)")
if isinstance(last10, list) and last10:
    df = pd.DataFrame(last10)

    # optionnel: tri par ts si pas déjà trié
    if "ts" in df.columns:
        df = df.sort_values("ts", ascending=False).reset_index(drop=True)

    df.insert(0, "N°", df.index + 1)
    st.dataframe(df, use_container_width=True)
else:
    st.info("Aucune donnée dans last10")
