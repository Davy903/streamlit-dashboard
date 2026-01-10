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

def normalize_ts(series):
    s = pd.to_numeric(series, errors="coerce")
    # ms si une valeur dépasse 1e12
    is_ms = s.dropna().gt(1e12).any()
    unit = "ms" if is_ms else "s"
    dt = pd.to_datetime(s, unit=unit, errors="coerce", utc=True).dt.tz_convert("Europe/Brussels")
    return s, dt

st.title("⏱️ Timing (Firebase) — Global")

data = fetch_firebase() or {}
timing = data if isinstance(data, dict) else {}

# --------- Collecte globale (toutes sessions) ----------
all_last = []
all_best = []

for timer_id, session in timing.items():
    if not isinstance(session, dict):
        continue

    best = session.get("best")
    if isinstance(best, dict) and best:
        b = best.copy()
        b.setdefault("timer_id", timer_id)
        all_best.append(b)

    last10 = to_list(session.get("last10"))
    for item in last10:
        if isinstance(item, dict) and item:
            it = item.copy()
            it.setdefault("timer_id", timer_id)
            all_last.append(it)

# --------- Best global (selon ts) ----------
st.subheader("🏆 Best (le plus récent)")

if all_best:
    dfb = pd.DataFrame(all_best)
    if "ts" in dfb.columns:
        ts_num, ts_dt = normalize_ts(dfb["ts"])
        dfb["ts_num"] = ts_num
        dfb["date"] = ts_dt.dt.strftime("%Y-%m-%d %H:%M:%S")
        dfb = dfb.sort_values("ts_num", ascending=False, na_position="last")
        best_row = dfb.iloc[0].drop(labels=[c for c in ["ts_num"] if c in dfb.columns]).to_dict()
        st.caption(f"Best enregistré le : {dfb.iloc[0].get('date', '')}")
        st.json(best_row)
    else:
        st.json(all_best[0])
else:
    st.info("Aucun best trouvé")

# --------- Last 10 global (selon ts) ----------
st.subheader("🕒 Last 10 (les plus récents, toutes sessions)")

if all_last:
    df = pd.DataFrame(all_last)

    if "ts" in df.columns:
        ts_num, ts_dt = normalize_ts(df["ts"])
        df["ts_num"] = ts_num
        df["date"] = ts_dt.dt.strftime("%Y-%m-%d %H:%M:%S")
        df = df.sort_values("ts_num", ascending=False, na_position="last").head(10)
        df = df.drop(columns=["ts_num"])
        # met date devant
        cols = ["date"] + [c for c in df.columns if c != "date"]
        df = df[cols]
    else:
        df = df.head(10)

    df = df.reset_index(drop=True)
    df.insert(0, "N°", df.index + 1)
    st.dataframe(df, use_container_width=True)
else:
    st.info("Aucune donnée last10 trouvée")
