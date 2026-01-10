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

def find_node_with_keys(obj, keys=("best", "last10")):
    """Retourne le premier dict trouvé qui contient au moins une des clés demandées."""
    if isinstance(obj, dict):
        if any(k in obj for k in keys):
            return obj
        for v in obj.values():
            found = find_node_with_keys(v, keys)
            if found is not None:
                return found
    elif isinstance(obj, list):
        for v in obj:
            found = find_node_with_keys(v, keys)
            if found is not None:
                return found
    return None

def to_list(x):
    """last10 peut être list ou dict (push ids)."""
    if x is None:
        return []
    if isinstance(x, list):
        return x
    if isinstance(x, dict):
        return list(x.values())
    return []

def normalize_ts(df, col="ts"):
    """
    Ajoute une colonne ts_dt (datetime) si ts existe.
    Gère ts en secondes ou millisecondes.
    """
    if col not in df.columns:
        return df

    ts = pd.to_numeric(df[col], errors="coerce")
    # Heuristique: si > 1e12 on considère ms, sinon s
    is_ms = ts.dropna().gt(1e12).any()
    unit = "ms" if is_ms else "s"
    df["ts_dt"] = pd.to_datetime(ts, unit=unit, errors="coerce", utc=True).dt.tz_convert("Europe/Brussels")
    return df

st.title("⏱️ Timing (Firebase)")

data = fetch_firebase()
node = find_node_with_keys(data, keys=("best", "last10"))

if node is None:
    st.error("Je ne trouve pas 'best' ou 'last10' dans timing.json")
    st.subheader("DEBUG : contenu timing.json")
    st.json(data)
    st.stop()

best = node.get("best", {}) or {}
last10_raw = node.get("last10", [])

last10 = to_list(last10_raw)

# --- Tableau: toujours les 10 plus récents selon ts ---
st.subheader("🕒 Last 10 (les plus récents)")

if last10:
    df = pd.DataFrame(last10)

    if "ts" in df.columns:
        df = normalize_ts(df, "ts")
        df = df.sort_values("ts", ascending=False, na_position="last")
        df = df.head(10)  # ✅ garde vraiment les 10 plus récents
        # Option: mettre la date lisible devant
        if "ts_dt" in df.columns:
            df.insert(0, "date", df["ts_dt"].dt.strftime("%Y-%m-%d %H:%M:%S"))
    else:
        # Pas de ts => on garde l'ordre reçu, mais on limite à 10
        df = df.head(10)

    df = df.reset_index(drop=True)
    df.insert(0, "N°", df.index + 1)
    st.dataframe(df, use_container_width=True)
else:
    st.info("Aucune donnée dans last10")

# --- Best (et sa date si possible) ---
st.subheader("🏆 Best")

if best:
    # Si best contient un ts, on affiche une date lisible
    if isinstance(best, dict) and "ts" in best:
        ts = pd.to_numeric(pd.Series([best.get("ts")]), errors="coerce")
        is_ms = ts.dropna().gt(1e12).any()
        unit = "ms" if is_ms else "s"
        best_dt = pd.to_datetime(ts.iloc[0], unit=unit, errors="coerce", utc=True)
        if pd.notna(best_dt):
            best_dt = best_dt.tz_convert("Europe/Brussels")
            st.caption(f"Best enregistré le : {best_dt.strftime('%Y-%m-%d %H:%M:%S')}")
    st.json(best)
else:
    st.info("Aucun best disponible")
