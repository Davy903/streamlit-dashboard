import streamlit as st
import paho.mqtt.client as mqtt
import json, time

BROKER = "20.251.215.215"
TOPIC = "capteurs/esp32"

if "last" not in st.session_state:
    st.session_state.last = {}

def on_message(client, userdata, msg):
    st.session_state.last = json.loads(msg.payload.decode())

client = mqtt.Client()
client.on_message = on_message
client.connect(BROKER, 1883, 60)
client.subscribe(TOPIC)
client.loop_start()

st.title("Live MQTT")
while True:
    st.json(st.session_state.last)
    time.sleep(1)
