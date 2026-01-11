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

st.title("⏱️ Timing (Firebase)")

data = fetch()

def extract_latest_payload(data):
    # Cas 1 : timing est une liste [null, {...}, {...}, ...]
    if isinstance(data, list):
        candidates = [x for x in data if isinstance(x, dict)]
        if not candidates:
            return {}, None

        # choisir celui avec le timer_id le plus grand (dans best.timer_id ou dans last10)
        def get_tid(p):
            b = p.get("best", {})
            if isinstance(b, dict) and "timer_id" in b:
                return b.get("timer_id", -1)
            l = p.get("last10", [])
            if isinstance(l, list) and l and isinstance(l[-1], dict):
                return l[-1].get("timer_id", -1)
            return -1

        latest = max(candidates, key=get_tid)
        return latest, get_tid(latest)

    # Cas 2 : timing est un dict {"1": {...}, "2": {...}}
    if isinstance(data, dict):
        # si le dict contient déjà best/last10
        if "best" in data or "last10" in data:
            tid = data.get("best", {}).get("timer_id") if isinstance(data.get("best"), dict) else None
            return data, tid

        # sinon on prend la plus grande clé numérique
        keys = []
        for k in data.keys():
            try:
                keys.append(int(k))
            except:
                pass
        if not keys:
            return {}, None
        kmax = str(max(keys))
        return data.get(kmax, {}), int(kmax)

    return {}, None

payload, latest_tid = extract_latest_payload(data)

if not payload:
    st.info("Aucune donnée trouvée dans /timing")
    st.stop()

best = payload.get("best", {})
last10 = payload.get("last10", [])
if isinstance(last10, dict):
    last10 = list(last10.values())

if latest_tid is not None:
    st.caption(f"Dernière session détectée : timer_id = {latest_tid}")

st.subheader("🏆 Best")
if isinstance(best, dict) and best:
    st.json(best)
else:
    st.info("Aucun best disponible")

st.subheader("🕒 Last 10")
if isinstance(last10, list) and last10:
    df = pd.DataFrame(last10)

    if "ts" in df.columns:
        df["ts"] = pd.to_numeric(df["ts"], errors="coerce")
        df = df.sort_values("ts", ascending=False)

    df = df.reset_index(drop=True)
    df.insert(0, "Lap n°", df.index + 1)

    df = df.rename(columns={
        "lap_index": "Index",
        "lap_s": "Temps (s)",
        "timer_id": "Timer ID",
        "ts": "Timestamp"
    })

    st.dataframe(df, use_container_width=True)
else:
    st.info("Aucune donnée dans last10")
