import streamlit as st
import requests
import time

API_URL = "http://20.251.215.215:1880/api/time_event"

st.title("⏱ Timer events (ESP32)")

placeholder = st.empty()

while True:
    try:
        r = requests.get(API_URL, timeout=2)
        data = r.json()
        placeholder.json(data)
    except Exception as e:
        placeholder.error(f"Erreur API: {e}")

    time.sleep(1)
