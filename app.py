import streamlit as st
import requests
import pandas as pd
from streamlit_autorefresh import st_autorefresh

# ✅ refresh auto toutes les 1s
st_autorefresh(interval=1000, key="firebase_refresh")

BASE = "https://voitureesp32-default-rtdb.europe-west1.firebasedatabase.app"
PATH = "timing"
URL = f"{BASE}/{PATH}.json"

@st.cache_data(ttl=1)
def fetch_timing():
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

def add_date_column(df, ts_col="ts", tz="Europe/Brussels"):
    if ts_col not in df.columns:
        return df
    ts_num = pd.to_numeric(df[ts_col], errors="coerce")
    unit = "ms" if ts_num.dropna().gt(1e12).any() else "s"
    dt = pd.to_datetime(ts_num, unit=unit, errors="coerce", utc=True).dt.tz_convert(tz)
    df = df.copy()
    df["date"] = dt.dt.strftime("%Y-%m-%d %H:%M:%S")
    return df

def pick_latest_timer_id(timing_dict):
    """
    Choisit la dernière session timer_id = celle dont le PREMIER ts (min) est le plus récent.
    """
    sessions = []
    for timer_id, session in timing_dict.items():
        if not isinstance(session, dict):
            continue
        last10 = to_list(session.get("last10"))
        ts_vals = []
        for it in last10:
            if isinstance(it, dict) and "ts" in it:
                ts_vals.append(it["ts"])
        if ts_vals:
            s = pd.to_numeric(pd.Series(ts_vals), errors="coerce").dropna()
            if not s.empty:
                first_ts = float(s.min())
                sessions.append((str(timer_id), first_ts))
    if not sessions:
        return None
    latest_timer_id, _ = max(sessions, key=lambda x: x[1])
    return latest_timer_id

st.title("⏱️ Timing (Firebase) — Dernière session")

# ✅ init session state (notif nouvelle donnée)
if "last_seen_ts" not in st.session_state:
    st.session_state.last_seen_ts = None

try:
    timing = fetch_timing() or {}
    if not isinstance(timing, dict) or not timing:
        st.warning("Aucune donnée trouvée dans /timing")
        st.stop()

    # ✅ 1) détecter le dernier timer_id
    latest_timer_id = pick_latest_timer_id(timing)
    if latest_timer_id is None:
        st.warning("Je ne trouve aucune session avec des timestamps (ts) dans last10.")
        st.stop()

    session = timing.get(latest_timer_id, {})
    best = session.get("best", {}) if isinstance(session, dict) else {}
    last10 = to_list(session.get("last10")) if isinstance(session, dict) else []

    st.success(f"Session affichée : timer_id = {latest_timer_id}")

    # ✅ 2) détecter nouvelle donnée (ts max dans last10)
    newest_ts = None
    if last10:
        newest_ts = max(
            (it.get("ts") for it in last10 if isinstance(it, dict) and "ts" in it),
            default=None
        )

    if newest_ts is not None and newest_ts != st.session_state.last_seen_ts:
        if st.session_state.last_seen_ts is not None:
            st.success("✅ Nouvelle donnée reçue !")
        st.session_state.last_seen_ts = newest_ts

    # ✅ 3) Affichage BEST
    st.subheader("🏆 Best (dernière session)")
    if isinstance(best, dict) and best:
        st.json(best)
    else:
        st.info("Aucun best disponible pour cette session.")

    # ✅ 4) Affichage LAST10
    st.subheader("🕒 Last 10 (dernière session)")
    if last10:
        df = pd.DataFrame(last10)

        # date lisible + tri ts décroissant
        if "ts" in df.columns:
            df = add_date_column(df, "ts")
            df["ts_num"] = pd.to_numeric(df["ts"], errors="coerce")
            df = df.sort_values("ts_num", ascending=False, na_position="last").drop(columns=["ts_num"])

        # colonne Lap n°
        df = df.reset_index(drop=True)
        df.insert(0, "Lap n°", df.index + 1)

        # renommage colonnes (optionnel)
        df = df.rename(columns={
            "lap_s": "Temps (s)",
            "time_s": "Temps (s)",
            "timer_id": "Timer ID",
            "ts": "Timestamp",
        })

        # enlever lap_index si présent
        if "lap_index" in df.columns:
            df = df.drop(columns=["lap_index"])

        # mettre date en premier si présente
        if "date" in df.columns:
            cols = ["Lap n°", "date"] + [c for c in df.columns if c not in ("Lap n°", "date")]
            df = df[cols]

        st.dataframe(df, use_container_width=True)
    else:
        st.info("Aucune donnée dans last10 pour cette session.")

except Exception as e:
    st.error(f"Erreur Firebase: {e}")
