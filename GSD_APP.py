#GSD APP 
#Lucas Bensching, Spring 2026

import streamlit as st
import librosa
import numpy as np
import json
import os
import pandas as pd 
import re
import matplotlib.pyplot as plt
from pydub import AudioSegment 
import tempfile 
import requests

# -----------------------
# CONFIG
# -----------------------
st.set_page_config(page_title="Gut Sound Analyzer", layout="centered")

# -----------------------
# AUDIO PROCESSING
# -----------------------
def load_audio(file):
    # If it's already WAV, load normally
    if file.name.lower().endswith(".wav"):
        y, sr = librosa.load(file, sr=16000, mono=True)
        return y, sr

    # Convert other formats to WAV
    audio = AudioSegment.from_file(file)
    temp_wav = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    audio.export(temp_wav.name, format="wav")

    y, sr = librosa.load(temp_wav.name, sr=16000, mono=True)
    return y, sr

def detect_events(y, sr):
    onset_frames = librosa.onset.onset_detect(
        y=y, sr=sr, hop_length=160
    )
    return librosa.frames_to_time(onset_frames, sr=sr, hop_length=160)


def extract_features(y, sr, times):
    feats = []
    win = int(0.3 * sr)

    for t in times:
        c = int(t * sr)
        seg = y[max(0, c-win//2):min(len(y), c+win//2)]

        if len(seg) < 200:
            continue

        feats.append({
            "time": float(round(t, 3)),
            "rms": float(np.mean(librosa.feature.rms(y=seg))),
            "centroid": float(np.mean(librosa.feature.spectral_centroid(y=seg, sr=sr))),
            "bandwidth": float(np.mean(librosa.feature.spectral_bandwidth(y=seg, sr=sr)))
        })
        
    return feats

def extract_json(text):
    text = text.strip()
    
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        text = match.group(0)
    
    return json.loads(text)


# -----------------------
# SIMPLE LOCAL CLASSIFIER (FAST)
# -----------------------
#def classify_local(f):
    #c = f["centroid"]
    #b = f["bandwidth"]
    #r = f["rms"]
    
    #if c < 220 and b < 180: #rumble, low c, low b, low r 
        #return "rumble"
    
    #if c > 650 and b < 250 and r > 0.02: #pop, high c, narrow b, sharp r 
        #return "pop"
    
    #if 220 <= c <= 650 and b >= 180: #gurgle, mid c, wide b 
        #return "gurgle"
    
    #return "gurgle" #else/fallback 

# -----------------------
# GPT ENRICHMENT (OPTIONAL)
# -----------------------

# -----------------------
# UI
# -----------------------

# ---- OSU Header ----
st.markdown("""
<div style='text-align:center; padding: 25px 0 10px 0;'>
    <h1 style='color:#D73F09; font-size: 48px; margin-bottom: -10px;'>
        Gut Sound Analyzer
    </h1>
    <p style='font-size:20px; color:#1A1A1A; margin-top: 0px;'>
        Upload an audio file to detect and classify gut sound events
    </p>
</div>
""", unsafe_allow_html=True)

st.markdown("<hr style='border:1px solid #E0D8CC;'>", unsafe_allow_html=True)

# ---- OSU Button Styling + Accent Headers ----
st.markdown("""
<style>

div.stButton > button {
    background-color: #D73F09;
    color: white;
    border-radius: 8px;
    border: 2px solid #A63406;
    padding: 0.6em 1.2em;
    font-size: 1.05em;
    font-weight: 600;
    transition: 0.2s ease-in-out;
}

div.stButton > button:hover {
    background-color: #A63406;
    border-color: #7A2504;
    transform: translateY(-2px);
}

div.stButton > button:active {
    transform: scale(0.98);
}

/* Accent-bar headers */
.accent-header {
    font-size: 26px;
    font-weight: 700;
    color: #1A1A1A;
    margin-top: 20px;
    position: relative;
    padding-left: 14px;
}

.accent-header:before {
    content: "";
    position: absolute;
    left: 0;
    top: 4px;
    width: 6px;
    height: 26px;
    background-color: #D73F09;
    border-radius: 3px;
}

</style>
""", unsafe_allow_html=True)

# ---- File Upload ----
FASTAPI_URL = "http://gsd-analyzer.onrender.com/analyze"

uploaded = st.file_uploader("Drop audio file here", type=["wav", "mp3", "m4a"])

if uploaded:

    st.audio(uploaded)

    # ---- SEND TO BACKEND ----
    with st.spinner("Analyzing audio with backend..."):
        files = {"file": (uploaded.name, uploaded.getvalue())}
        response = requests.post(FASTAPI_URL, files=files, timeout=120)

        if response.status_code != 200:
            st.error(f"Backend error: {response.text}")
            st.stop()

        backend_data = response.json()   # <-- REAL backend results
        events = backend_data.get("events", [])

    # ---- Local audio load ONLY for visuals ----
    with st.spinner("Preparing visuals..."):
        y, sr = load_audio(uploaded)

    # ---- Tabs ----
    tab1, tab2, tab3, tab4 = st.tabs(["Waveform", "Spectrogram", "Results", "Summary"])

    # ---- Waveform Tab ----
    with tab1:
        st.markdown("<div class='accent-header'>Waveform</div>", unsafe_allow_html=True)
        fig_wave, ax_wave = plt.subplots(figsize=(10, 3))
        librosa.display.waveshow(y, sr=sr, ax=ax_wave, color="#D73F09")
        ax_wave.set_xlabel("Time (s)")
        ax_wave.set_ylabel("Amplitude")
        st.pyplot(fig_wave)

    # ---- Spectrogram Tab ----
    with tab2:
        st.markdown("<div class='accent-header'>Spectrogram</div>", unsafe_allow_html=True)
        S = librosa.feature.melspectrogram(
            y=y, sr=sr, n_fft=1024, hop_length=160, n_mels=64
        )
        S_dB = librosa.power_to_db(S, ref=np.max)

        fig_spec, ax_spec = plt.subplots(figsize=(10, 3))
        img = librosa.display.specshow(
            S_dB, sr=sr, hop_length=160, x_axis="time", y_axis="mel",
            cmap="magma", ax=ax_spec
        )
        fig_spec.colorbar(img, ax=ax_spec, format="%+2.0f dB")
        st.pyplot(fig_spec)

    # ---- Backend Results Tab ----
    with tab3:
        st.markdown("<div class='accent-header'>Gut Sound Classification</div>", unsafe_allow_html=True)

        if len(events) == 0:
            st.warning("No events detected.")
        else:
            df = pd.DataFrame(events)
            df["time"] = df["time"].round(2)
            df["confidence"] = df["confidence"].round(2)
            df["type"] = df["type"].str.upper()

            st.dataframe(
                df[["time", "type", "confidence"]],
                use_container_width=True,
                hide_index=True
            )

    # ---- Summary Tab ----
    with tab4:
        st.markdown("<div class='accent-header'>Summary</div>", unsafe_allow_html=True)

        if len(events) == 0:
            st.write("No summary available.")
        else:
            df = pd.DataFrame(events)
            df["type"] = df["type"].str.upper()
            counts = df["type"].value_counts()

            col1, col2, col3 = st.columns(3)
            col1.metric("Rumbles", int(counts.get("RUMBLE", 0)))
            col2.metric("Gurgles", int(counts.get("GURGLE", 0)))
            col3.metric("Pops", int(counts.get("POP", 0)))




            
            
            
            