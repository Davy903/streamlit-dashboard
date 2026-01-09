import streamlit as st
import requests
import pandas as pd

BASE = "https://voitureesp32-default-rtdb.europe-west1.firebasedatabase.app"
PATH = "timing"
URL = f"{BASE}/{PATH}.json"

@st.cache_data(ttl=2)
def fetch_timing():
    r = requests.get(URL, timeout=10)
    r.raise_for_status()
    data = r.json()
    return data

st.title("⏱️ Timing (Firebase)")

try:
    data = fetch_timing()

    # Ton JSON est une liste: [null, {...}]
    if isinstance(data, list) and len(data) > 1 and data[1]:
        payload = data[1]
    else:
        payload = data  # au cas où ça change

    best = payload.get("best")
    last10 = payload.get("last10", [])

    st.subheader("🏆 Best")
    st.json(best)

    st.subheader("🕒 Last 10")
    if isinstance(last10, list) and len(last10) > 0:
        df = pd.DataFrame(last10)

        # Tri par ts si présent
        if "ts" in df.columns:
            df = df.sort_values("ts", ascending=False)

        st.dataframe(df, use_container_width=True)
    else:
        st.info("Aucun événement dans last10")

except Exception as e:
    st.error(f"Erreur Firebase: {e}")
