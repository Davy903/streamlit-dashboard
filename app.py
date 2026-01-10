import streamlit as st
import requests
import pandas as pd
from streamlit_autorefresh import st_autorefresh

# Refresh auto toutes les 1s
st_autorefresh(interval=1000, key="refresh")

BASE = "https://voitureesp32-default-rtdb.europe-west1.firebasedatabase.app"
URL = f"{BASE}/timing.json"

@st.cache_data(ttl=1)
def fetch():
    r = requests.get(URL, timeout=10)
    r.raise_for_status()
    return r.json()

st.title("📊 Dernières données Firebase")

data = fetch()

# Firebase peut renvoyer {…} OU [null, {…}]
payload = {}
if isinstance(data, list):
    payload = next((x for x in reversed(data) if isinstance(x, dict)), {})
elif isinstance(data, dict):
    payload = data

last10 = payload.get("last10")

# Si last10 est un dict -> list
if isinstance(last10, dict):
    last10 = list(last10.values())

if not isinstance(last10, list) or len(last10) == 0:
    st.info("Aucune donnée reçue depuis Firebase")
    st.stop()

# DataFrame direct
df = pd.DataFrame(last10)

# (Optionnel) tri par timestamp si présent
if "ts" in df.columns:
    df = df.sort_values("ts", ascending=False)

df = df.reset_index(drop=True)

st.dataframe(df, use_container_width=True)
