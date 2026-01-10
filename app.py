import streamlit as st
import requests
import pandas as pd
from streamlit_autorefresh import st_autorefresh

st_autorefresh(interval=1000, key="refresh")

BASE = "https://voitureesp32-default-rtdb.europe-west1.firebasedatabase.app"
URL = f"{BASE}/timing.json"

@st.cache_data(ttl=1)
def fetch():
    r = requests.get(URL, timeout=10)
    r.raise_for_status()
    return r.json()

st.title("📊 Derniers événements reçus (Firebase)")

data = fetch()

# Firebase peut renvoyer {…} OU [null, {…}]
payload = {}
if isinstance(data, list):
    payload = next((x for x in reversed(data) if isinstance(x, dict)), {})
elif isinstance(data, dict):
    payload = data

last10 = payload.get("last10", None)

# last10 peut être dict OU list
if isinstance(last10, dict):
    last10 = list(last10.values())

if not isinstance(last10, list) or len(last10) == 0:
    st.info("Aucune donnée dans last10")
    st.stop()

df = pd.DataFrame(last10)

# ✅ TRI PAR TIMESTAMP (le + récent en premier)
if "ts" in df.columns:
    df = df.sort_values("ts", ascending=False).reset_index(drop=True)
else:
    # si jamais pas de ts, on affiche quand même
    df = df.reset_index(drop=True)

# ✅ Afficher le tout dernier event reçu (celui avec ts max)
st.subheader("🟢 Dernier event reçu")
st.json(df.iloc[0].to_dict())

# ✅ Tableau complet trié (les + récents en haut)
st.subheader("📋 Tableau (trié par ts)")
st.dataframe(df, use_container_width=True)
