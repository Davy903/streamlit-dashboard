import streamlit as st
import requests

BASE = "https://voitureesp32-default-rtdb.europe-west1.firebasedatabase.app"
PATH = "timing"  # sans .json

url = f"{BASE}/{PATH}.json"   # construit UNE seule fois
st.write("URL:", url)

r = requests.get(url, timeout=10)
st.write("HTTP:", r.status_code)
st.code(r.text[:500])

if r.ok:
    st.json(r.json())
else:
    st.error(f"Erreur Firebase: {r.status_code}")
