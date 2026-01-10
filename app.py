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

def to_list(x):
    if x is None:
        return []
    if isinstance(x, list):
        return x
    if isinstance(x, dict):
        return list(x.values())
    return []

def ts_unit_from_series(s: pd.Series) -> str:
    s = pd.to_numeric(s, errors="coerce").dropna()
    if s.empty:
        return "ms"  # défaut
    return "ms" if (s > 1e12).any() else "s"

def add_date_column(df, ts_col="ts", tz="Europe/Brussels"):
    if ts_col not in df.columns:
        return df
    ts_num = pd.to_numeric(df[ts_col], errors="coerce")
    unit = "ms" if ts_num.dropna().gt(1e12).any() else "s"
    dt = pd.to_datetime(ts_num, unit=unit, errors="coerce", utc=True).dt.tz_convert(tz)
    df = df.copy()
    df["date"] = dt.dt.strftime("%Y-%m-%d %H:%M:%S")
    return df

st.title("⏱️ Timing (Firebase) — Dernière session")

data = fetch_firebase() or {}
timing = data if isinstance(data, dict) else {}

# -------- Trouver le dernier timer_id (session la plus récente) --------
sessions = []
for timer_id, session in timing.items():
    if not isinstance(session, dict):
        continue

    last10 = to_list(session.get("last10"))
    # récupérer tous les ts de la session
    ts_list = []
    for it in last10:
        if isinstance(it, dict) and "ts" in it:
            ts_list.append(it["ts"])

    if ts_list:
        ts_series = pd.to_numeric(pd.Series(ts_list), errors="coerce").dropna()
        if not ts_series.empty:
            first_ts = ts_series.min()   # premier temps de la session
            sessions.append((str(timer_id), float(first_ts)))

if not sessions:
    st.warning("Aucune session avec ts trouvée dans /timing/*/last10")
    st.stop()

# timer_id dont le premier ts est le plus grand = session commencée le plus récemment
latest_timer_id, latest_first_ts = max(sessions, key=lambda x: x[1])

st.success(f"Dernière session détectée : timer_id = {latest_timer_id}")

session = timing.get(latest_timer_id, {})
best = session.get("best", {}) if isinstance(session, dict) else {}
last10 = to_list(session.get("last10", [])) if isinstance(session, dict) else []

# -------- Affichage BEST --------
st.subheader("🏆 Best (de la dernière session)")
if isinstance(best, dict) and best:
    st.json(best)
else:
    st.info("Aucun best disponible pour cette session")

# -------- Affichage LAST10 --------
st.subheader("🕒 Last 10 (de la dernière session)")
if last10:
    df = pd.DataFrame(last10)

    # tri par ts (le plus récent en haut)
    if "ts" in df.columns:
        df = add_date_column(df, "ts")
        df["ts_num"] = pd.to_numeric(df["ts"], errors="coerce")
        df = df.sort_values("ts_num", ascending=False, na_position="last").drop(columns=["ts_num"])
        # mettre la date devant
        cols = ["date"] + [c for c in df.columns if c != "date"]
        df = df[cols]

    df = df.reset_index(drop=True)
    df.insert(0, "N°", df.index + 1)
    st.dataframe(df, use_container_width=True)
else:
    st.info("Aucune donnée dans last10 pour cette session")
