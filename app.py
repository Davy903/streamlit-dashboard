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

# ---- payload robuste : dict direct OU liste [null, {...}] ----
payload = {}
if isinstance(data, list):
    payload = next((x for x in reversed(data) if isinstance(x, dict)), {})
elif isinstance(data, dict):
    payload = data

# ---- récupérer last10 (global) ----
last10 = payload.get("last10", [])
if isinstance(last10, dict):
    last10 = list(last10.values())

if not isinstance(last10, list) or len(last10) == 0:
    st.info("Aucune donnée dans last10")
    st.stop()

df_all = pd.DataFrame(last10)

# Harmoniser noms si ton JSON change (lap_* vs time_*)
if "lap_s" in df_all.columns and "time_s" not in df_all.columns:
    df_all = df_all.rename(columns={"lap_s": "time_s"})
if "lap_index" in df_all.columns and "time_index" not in df_all.columns:
    df_all = df_all.rename(columns={"lap_index": "time_index"})

# ---- tri global ----
if "ts" in df_all.columns:
    df_all = df_all.sort_values("ts", ascending=False)

# ---- dernière session (timer_id max parmi last10) ----
latest_timer_id = None
if "timer_id" in df_all.columns and not df_all["timer_id"].isna().all():
    latest_timer_id = int(df_all["timer_id"].max())

# =========================
# 🏆 BEST (dernière session)
# =========================
st.subheader("🏆 Best (dernière session)")

best = payload.get("best", {})

# Si best existe mais correspond peut-être à autre chose, on calcule un best sûr depuis last10
# (best = temps minimum de la dernière session)
best_from_df = None
if latest_timer_id is not None and "time_s" in df_all.columns:
    df_latest = df_all[df_all["timer_id"] == latest_timer_id].copy()
    if not df_latest.empty:
        # best = plus petit time_s de la session
        row = df_latest.loc[df_latest["time_s"].idxmin()]
        best_from_df = {
            "timer_id": int(row.get("timer_id")),
            "time_index": int(row.get("time_index")) if pd.notna(row.get("time_index")) else None,
            "time_s": float(row.get("time_s")) if pd.notna(row.get("time_s")) else None,
            "ts": int(row.get("ts")) if pd.notna(row.get("ts")) else None,
        }

# Affichage : si on a réussi à calculer best dernière session, on l'affiche
if best_from_df:
    st.json(best_from_df)
else:
    # fallback : afficher le best stocké
    st.json(best)

# =========================
# 🕒 LAST 10 (global)
# =========================
st.subheader("🕒 Last 10 (toutes sessions)")

df_show = df_all.head(10).reset_index(drop=True)
df_show.insert(0, "N°", df_show.index + 1)

df_show = df_show.rename(columns={
    "timer_id": "Session (timer_id)",
    "time_index": "Index",
    "time_s": "Temps (s)",
    "ts": "Timestamp"
})

st.dataframe(df_show, use_container_width=True)

# petit debug optionnel
if latest_timer_id is not None:
    st.caption(f"Dernière session détectée : timer_id = {latest_timer_id}")
