import streamlit as st
import paho.mqtt.client as mqtt
import json
import time
from collections import deque

BROKER = "20.251.215.215"
PORT = 1883

st.write("MQTT connected:", client.is_connected())


TOPIC_TIME_EVENTS = "esp32/time_events"   # <- ton ESP32 publie ici
TOPIC_CAPTEURS     = "esp32/capteurs"     # <- optionnel, si tu veux aussi voir dist/temp/hum

# (Optionnel) auto-refresh propre Streamlit
try:
    from streamlit_autorefresh import st_autorefresh
    st_autorefresh(interval=1000, key="refresh")  # 1s
except Exception:
    pass

st.set_page_config(page_title="MQTT Timer Events", layout="centered")
st.title("⏱️ Timer events (MQTT)")

# --- stockage en mémoire ---
if "events" not in st.session_state:
    st.session_state.events = deque(maxlen=200)  # garde les 200 derniers events

if "last_capteurs" not in st.session_state:
    st.session_state.last_capteurs = {}

def fmt_mmss(seconds: int) -> str:
    mm = seconds // 60
    ss = seconds % 60
    return f"{mm:02d}:{ss:02d}"

def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
    except Exception:
        return

    if msg.topic == TOPIC_TIME_EVENTS:
        # payload attendu: {"timer_id":X,"time_index":Y,"time_s":Z}
        timer_id = int(payload.get("timer_id", -1))
        time_index = int(payload.get("time_index", -1))
        time_s = int(payload.get("time_s", -1))

        st.session_state.events.append({
            "timer_id": timer_id,
            "time_index": time_index,
            "time_s": time_s,
            "time_mmss": fmt_mmss(time_s),
            "received_at": time.strftime("%H:%M:%S"),
        })

    elif msg.topic == TOPIC_CAPTEURS:
        # payload attendu: {"temperature":...,"humidity":...,"distance":...}
        st.session_state.last_capteurs = payload

@st.cache_resource
def mqtt_start():
    client = mqtt.Client()
    client.on_message = on_message
    client.connect(BROKER, PORT, 60)
    client.subscribe([(TOPIC_TIME_EVENTS, 0), (TOPIC_CAPTEURS, 0)])  # capteurs optionnel
    client.loop_start()
    return client

client = mqtt_start()

# --- UI ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("Dernier time_event")
    if len(st.session_state.events) > 0:
        st.json(st.session_state.events[-1])
    else:
        st.info("Aucun time_event reçu pour le moment (approche un objet < 10cm pendant le timer).")

with col2:
    st.subheader("Derniers capteurs (optionnel)")
    if st.session_state.last_capteurs:
        st.json(st.session_state.last_capteurs)
    else:
        st.info("Aucun message capteurs reçu (topic esp32/capteurs).")

st.subheader("Historique (table)")
events_list = list(st.session_state.events)
if events_list:
    # Tri par timer_id puis time_index (optionnel)
    events_list = sorted(events_list, key=lambda x: (x["timer_id"], x["time_index"]))
    st.dataframe(events_list, use_container_width=True)
else:
    st.write("—")

st.caption("Topics écoutés : esp32/time_events (principal), esp32/capteurs (optionnel).")
