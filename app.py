import streamlit as st
import requests
import pandas as pd
from streamlit_autorefresh import st_autorefresh

# 🔁 refresh toutes les 1s (compteur qui change)
tick = st_autorefresh(interval=1000, key="firebase_refresh")

BASE = "https://voitureesp32-default-rtdb.europe-west1.firebasedatabase.app"
PATH = "timing"
URL = f"{BASE}/{PATH}.json"

@st.cache_data(ttl=0)  # pas de cache pour debug/temps réel
def fetch_timing(_tick):
    r = requests.get(URL, timeout=10)
    r.raise_for_status()
    return r.json()

st.title("⏱️ Timing (Firebase)")

try:
    data = fetch_timing(tick)

    # ✅ payload robuste : dict direct OU liste avec éléments null
    payload = {}
    if isinstance(data, dict):
        payload = data
    elif isinstance(data, list):
        for x in reversed(data):
            if isinstance(x, dict):
                payload = x
                break

    best = payload.get("best", {})
    last10 = payload.get("last10", [])

    st.subheader("🏆 Best")
    st.json(best)

    st.subheader("🕒 Last 10")

    # si last10 est un dict au lieu d'une liste, on convertit
    if isinstance(last10, dict):
        last10 = list(last10.values())

    if isinstance(last10, list) and last10:
        df = pd.DataFrame(last10)

        if "ts" in df.columns:
            df = df.sort_values("ts", ascending=False).reset_index(drop=True)

        st.dataframe(df, use_container_width=True)

        # 🔎 debug utile : quels timer_id sont présents ?
        if "timer_id" in df.columns:
            st.caption(f"timer_id présents: {sorted(df['timer_id'].dropna().unique().tolist())}")

    else:
        st.info("Aucun événement dans last10")

except Exception as e:
    st.error(f"Erreur Firebase: {e}")
