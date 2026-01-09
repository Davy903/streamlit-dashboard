import streamlit as st
import requests
import time

FIREBASE_DB_URL = "https://voitureesp32-default-rtdb.europe-west1.firebasedatabase.app/timing.json"

st.set_page_config(page_title="Timer events (Firebase)", layout="centered")
st.title("⏱ Timer events (Firebase)")

placeholder = st.empty()

def fetch_last_events(limit=20):
    url = f'{FIREBASE_DB_URL}/time_events.json?orderBy="received_at"&limitToLast={limit}'
    r = requests.get(url, timeout=5)
    r.raise_for_status()
    data = r.json() or {}

    # Firebase renvoie un dict {key: event}
    events = list(data.values())

    # tri par received_at si présent
    events.sort(key=lambda x: x.get("received_at", ""))
    return events

while True:
    try:
        events = fetch_last_events(20)
        if events:
            st.subheader("Dernier event")
            placeholder.json(events[-1])

            st.subheader("Historique (20 derniers)")
            st.dataframe(events, use_container_width=True)
        else:
            placeholder.info("Aucun event pour l’instant.")
    except Exception as e:
        placeholder.error(f"Erreur Firebase: {e}")

    time.sleep(1)
