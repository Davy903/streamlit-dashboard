import streamlit as st
import requests
import pandas as pd
from streamlit_autorefresh import st_autorefresh

# Refresh auto toutes les 1s
st_autorefresh(interval=1000, key="firebase_refresh")

BASE = "https://voitureesp32-default-rtdb.europe-west1.firebasedatabase.app"
URL = f"{BASE}/timing.json"

@st.cache_data(ttl=1)
def fetch_firebase():
    r = requests.get(URL, timeout=10)
    r.raise_for_status()
    return r.json()

st.title("⏱️ Timing (Firebase)")

# ======================
# Récupération Firebase
# ======================
data = fetch_firebase()

# Firebase peut renvoyer {…} OU [null, {…}]
payload = {}
if isinstance(data, list):
    payload = next((x for x in reversed(data) if isinstance(x, dict)), {})
elif isinstance(data, dict):
    payload = data

# ======================
# BEST (tel quel Firebase)
# ======================
st.subheader("🏆 Best")

best = payload.get("best", {})
if best:
    st.json(best)
else:
    st.info("Aucun best disponible")

# ======================
# LAST 10 (tel quel Firebase)
# ======================
st.subheader("🕒 Last 10")

last10 = payload.get("last10", [])

# last10 peut être dict OU list
if isinstance(last10, dict):
    last10 = list(last10.values())

if isinstance(last10, list) and len(last10) > 0:
    df = pd.DataFrame(last10)

    # Tri par timestamp si présent (le + récent en haut)
    if "ts" in df.columns:
        df = df.sort_values("ts", ascending=False)

    df = df.reset_index(drop=True)
    df.insert(0, "N°", df.index + 1)

    st.dataframe(df, use_container_width=True)
else:
    st.info("Aucune donnée dans last10")
