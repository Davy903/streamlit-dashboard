import streamlit as st
import requests

BASE = "https://voitureesp32-default-rtdb.europe-west1.firebasedatabase.app"
URL = f"{BASE}/.json"   # 🔥 RACINE TOTALE

st.title("DEBUG Firebase brut")

r = requests.get(URL, timeout=10)
st.write("Status:", r.status_code)
st.json(r.json())
