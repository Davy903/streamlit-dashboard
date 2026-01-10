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

st.title("⏱️ 10 derniers temps (toutes sessions)")

data = fetch()

# Cas: [null, {...}] -> on prend le dernier dict non-null
payload = {}
if isinstance(data, list):
    payload = next((x for x in reversed(data) if isinstance(x, dict)), {})
elif isinstance(data, dict):
    payload = data

last10 = payload.get("last10", [])

# last10 peut être list OU dict
if isinstance(last10, dict):
    last10 = list(last10.values())

if not isinstance(last10, list) or len(last10) == 0:
    st.info("Aucune donnée dans last10")
    st.stop()

df = pd.DataFrame(last10)

# Tri global par timestamp
if "ts" in df.columns:
    df = df.sort_values("ts", ascending=False)

# On garde 10 lignes max (au cas où Firebase en contient plus)
df = df.head(10).reset_index(drop=True)

# Colonne 1..10 pour affichage
df.insert(0, "N°", df.index + 1)

# Renommer selon ton format (adapte si nécessaire)
df = df.rename(columns={
    "timer_id": "Session (timer_id)",
    "time_index": "Index",
    "time_s": "Temps (s)",
    "lap_index": "Index",
    "lap_s": "Temps (s)",
    "ts": "Timestamp"
})

st.dataframe(df, use_container_width=True)
