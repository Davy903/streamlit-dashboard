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

try:
    data = fetch() or {}

    # data doit être un dict: {"4": {...}, "5": {...}, ...}
    if not isinstance(data, dict) or len(data) == 0:
        st.info("Aucune donnée dans /timing")
        st.stop()

    # 🔥 prendre le timer_id le plus grand
    timer_ids = []
    for k in data.keys():
        try:
            timer_ids.append(int(k))
        except:
            pass

    if len(timer_ids) == 0:
        st.error("Aucun timer_id numérique trouvé dans /timing")
        st.json(data)
        st.stop()

    latest_id = max(timer_ids)
    payload = data.get(str(latest_id), {}) or {}

    best = payload.get("best", {})
    last10 = payload.get("last10", [])

    st.caption(f"Dernière session détectée : timer_id = {latest_id}")

    # ───── BEST ─────
    st.subheader("🏆 Best")
    if isinstance(best, dict) and best:
        st.json(best)
    else:
        st.info("Aucun best disponible")

    # ───── LAST 10 ─────
    st.subheader("🕒 Last 10")
    if isinstance(last10, dict):
        last10 = list(last10.values())

    if isinstance(last10, list) and last10:
        df = pd.DataFrame(last10)

        # tri par timestamp décroissant si présent
        if "ts" in df.columns:
            df["ts"] = pd.to_numeric(df["ts"], errors="coerce")
            df = df.sort_values("ts", ascending=False)

        df = df.reset_index(drop=True)
        df.insert(0, "Lap n°", df.index + 1)

        df = df.rename(columns={
            "lap_index": "Index",
            "lap_s": "Temps (s)",
            "time_index": "Index",
            "time_s": "Temps (s)",
            "timer_id": "Timer ID",
            "ts": "Timestamp"
        })

        st.dataframe(df, use_container_width=True)
    else:
        st.info("Aucune donnée dans last10")

except Exception as e:
    st.error(f"Erreur Firebase : {e}")
