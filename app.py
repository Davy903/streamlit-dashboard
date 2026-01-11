import streamlit as st
import requests
import pandas as pd
from streamlit_autorefresh import st_autorefresh

# ─────────────────────────────────────
# CONFIG
# ─────────────────────────────────────
BASE = "https://voitureesp32-default-rtdb.europe-west1.firebasedatabase.app"
PATH = "timing"
URL = f"{BASE}/{PATH}.json"

# refresh auto toutes les 1s
st_autorefresh(interval=1000, key="firebase_refresh")

# ─────────────────────────────────────
# FIREBASE FETCH
# ─────────────────────────────────────
@st.cache_data(ttl=1)
def fetch_timing():
    r = requests.get(URL, timeout=10)
    r.raise_for_status()
    return r.json()

# ─────────────────────────────────────
# UI
# ─────────────────────────────────────
st.title("⏱️ Timing (Firebase)")

try:
    data = fetch_timing() or {}

    # Cas Firebase : parfois [null, {...}]
    if isinstance(data, list):
        payload = data[1] if len(data) > 1 and isinstance(data[1], dict) else {}
    elif isinstance(data, dict):
        payload = data
    else:
        payload = {}

    best = payload.get("best", {})
    last10 = payload.get("last10", [])

    # Si last10 est un dict => list
    if isinstance(last10, dict):
        last10 = list(last10.values())

    # ───── BEST ─────
    st.subheader("🏆 Best")
    if isinstance(best, dict) and best:
        st.json(best)
    else:
        st.info("Aucun best disponible")

    # ───── LAST 10 ─────
    st.subheader("🕒 Last 10")
    if isinstance(last10, list) and len(last10) > 0:
        df = pd.DataFrame(last10)

        # tri par timestamp décroissant si présent
        if "ts" in df.columns:
            df["ts"] = pd.to_numeric(df["ts"], errors="coerce")
            df = df.sort_values("ts", ascending=False)

        # Lap n° 1..N
        df = df.reset_index(drop=True)
        df.insert(0, "Lap n°", df.index + 1)

        # renommage colonnes lisibles (selon ton format)
        df = df.rename(columns={
            "lap_s": "Temps (s)",
            "time_s": "Temps (s)",
            "timer_id": "Timer ID",
            "time_index": "Index",
            "ts": "Timestamp"
        })

        # optionnel : enlever la colonne lap_index si elle existe
        if "lap_index" in df.columns:
            df = df.drop(columns=["lap_index"])

        st.dataframe(df, use_container_width=True)
    else:
        st.info("Aucune donnée dans last10")

except Exception as e:
    st.error(f"Erreur Firebase : {e}")
