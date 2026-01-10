import streamlit as st
import requests
import pandas as pd
from streamlit_autorefresh import st_autorefresh

st_autorefresh(interval=1000, key="firebase_refresh")

BASE = "https://voitureesp32-default-rtdb.europe-west1.firebasedatabase.app"
URL = f"{BASE}/timing.json"

@st.cache_data(ttl=1)
def fetch_firebase():
    r = requests.get(URL, timeout=10)
    r.raise_for_status()
    return r.json()

def find_node_with_keys(obj, keys=("best", "last10")):
    """Retourne le premier dict trouvé qui contient au moins une des clés demandées."""
    if isinstance(obj, dict):
        if any(k in obj for k in keys):
            return obj
        for v in obj.values():
            found = find_node_with_keys(v, keys)
            if found is not None:
                return found
    elif isinstance(obj, list):
        for v in obj:
            found = find_node_with_keys(v, keys)
            if found is not None:
                return found
    return None

st.title("⏱️ Timing (Firebase)")

data = fetch_firebase()

node = find_node_with_keys(data, keys=("best", "last10"))
if node is None:
    st.error("Je ne trouve pas 'best' ou 'last10' dans timing.json")
    st.subheader("DEBUG : contenu timing.json")
    st.json(data)
    st.stop()

best = node.get("best", {})
last10 = node.get("last10", [])

if isinstance(last10, dict):
    last10 = list(last10.values())

st.subheader("🏆 Best")
if best:
    st.json(best)
else:
    st.info("Aucun best disponible")

st.subheader("🕒 Last 10")
if isinstance(last10, list) and last10:
    df = pd.DataFrame(last10)
    if "ts" in df.columns:
        df = df.sort_values("ts", ascending=False)
    df = df.reset_index(drop=True)
    df.insert(0, "N°", df.index + 1)
    st.dataframe(df, use_container_width=True)
else:
    st.info("Aucune donnée dans last10")
