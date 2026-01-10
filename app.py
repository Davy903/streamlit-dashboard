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

# payload robuste : dict direct OU liste [null, {...}]
payload = {}
if isinstance(data, list):
    payload = next((x for x in reversed(data) if isinstance(x, dict)), {})
elif isinstance(data, dict):
    payload = data

last10 = payload.get("last10", [])
if isinstance(last10, dict):
    last10 = list(last10.values())

if not isinstance(last10, list) or len(last10) == 0:
    st.info("Aucune donnée dans last10")
    st.stop()

df = pd.DataFrame(last10)

# Harmoniser noms si ton JSON change (lap_* vs time_*)
if "lap_s" in df.columns and "time_s" not in df.columns:
    df = df.rename(columns={"lap_s": "time_s"})
if "lap_index" in df.columns and "time_index" not in df.columns:
    df = df.rename(columns={"lap_index": "time_index"})

# Tri global par timestamp (comme ton code)
if "ts" in df.columns:
    df = df.sort_values("ts", ascending=False).reset_index(drop=True)

# ----------------------------
# 🏆 Best de la dernière session
# ----------------------------
st.subheader("🏆 Best (dernière session)")

best_last_session = None
if "timer_id" in df.columns and "time_s" in df.columns:
    latest_timer_id = df["timer_id"].max()  # dernière session = id le plus grand
    df_latest = df[df["timer_id"] == latest_timer_id].copy()

    if not df_latest.empty:
        row = df_latest.loc[df_latest["time_s"].idxmin()]  # meilleur temps = min time_s
        best_last_session = {
            "timer_id": int(row["timer_id"]) if pd.notna(row["timer_id"]) else None,
            "time_index": int(row["time_index"]) if "time_index" in row and pd.notna(row["time_index"]) else None,
            "time_s": float(row["time_s"]) if pd.notna(row["time_s"]) else None,
            "ts": int(row["ts"]) if "ts" in row and pd.notna(row["ts"]) else None,
        }

if best_last_session:
    st.json(best_last_session)
else:
    st.info("Impossible de calculer le best (pas assez de données).")

# ----------------------------
# 🕒 10 derniers temps (toutes sessions)
# ----------------------------
st.subheader("🕒 10 derniers temps (toutes sessions)")

df_show = df.head(10).copy().reset_index(drop=True)
df_show.insert(0, "N°", df_show.index + 1)

df_show = df_show.rename(columns={
    "timer_id": "Session (timer_id)",
    "time_index": "Index",
    "time_s": "Temps (s)",
    "ts": "Timestamp"
})

st.dataframe(df_show, use_container_width=True)
