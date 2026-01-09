import streamlit as st
import requests
import pandas as pd
from streamlit_autorefresh import st_autorefresh

BASE = "https://voitureesp32-default-rtdb.europe-west1.firebasedatabase.app"
PATH = "timing"
URL = f"{BASE}/{PATH}.json"

# on garde un polling léger, mais on "réagit" seulement si ts change
st_autorefresh(interval=1000, key="poll_firebase")

@st.cache_data(ttl=1)
def fetch_timing():
    r = requests.get(URL, timeout=10)
    r.raise_for_status()
    return r.json()

st.title("⏱️ Timing (Firebase)")

# init session
if "last_seen_ts" not in st.session_state:
    st.session_state.last_seen_ts = None

try:
    data = fetch_timing()

    # cas: [null, {...}]
    if isinstance(data, list) and len(data) > 1 and data[1]:
        payload = data[1]
    else:
        payload = data or {}

    best = payload.get("best", {})
    last10 = payload.get("last10", [])

    # détecter le "dernier ts"
    newest_ts = None
    if isinstance(last10, list) and last10:
        newest_ts = max((x.get("ts") for x in last10 if isinstance(x, dict) and "ts" in x), default=None)

    # si nouveau ts -> notif
    if newest_ts is not None and newest_ts != st.session_state.last_seen_ts:
        if st.session_state.last_seen_ts is not None:
            st.success("✅ Nouvelle donnée reçue !")
        st.session_state.last_seen_ts = newest_ts

    st.subheader("🏆 Best")
    st.json(best)

    st.subheader("🕒 Last 10")
    if isinstance(last10, list) and last10:
        df = pd.DataFrame(last10)

        # tri + index propre
        if "ts" in df.columns:
            df = df.sort_values("ts", ascending=False).reset_index(drop=True)

        # colonne Lap n° = 1,2,3...
        df.insert(0, "Lap n°", df.index + 1)

        # renommer + option: enlever lap_index
        df = df.rename(columns={"lap_s": "Temps (s)", "timer_id": "Timer ID", "ts": "Timestamp"})
        if "lap_index" in df.columns:
            df = df.drop(columns=["lap_index"])

        st.dataframe(df, use_container_width=True)
    else:
        st.info("Aucune donnée dans last10")

except Exception as e:
    st.error(f"Erreur Firebase: {e}")
