#GSD Backend 
#Lucas Bensching, Spring 2026 

from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import librosa
import numpy as np
import json
from openai import OpenAI
import tempfile
import re
from dotenv import load_dotenv
import os
import io
import base64
import soundfile as sf
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# -----------------------
# CONFIG
# -----------------------
load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------
# AUDIO PROCESSING
# -----------------------
def load_audio_bytes(file_bytes, filename):
    import io

    # Try direct decode with soundfile (WAV, FLAC, OGG, etc.)
    try:
        data, sr = sf.read(io.BytesIO(file_bytes))
        if len(data.shape) > 1:
            data = np.mean(data, axis=1)  # mono
        return data.astype(np.float32), sr
    except Exception:
        pass

    # Fallback: librosa + audioread (MP3, M4A, AAC, etc.)
    with tempfile.NamedTemporaryFile(delete=False, suffix=filename[-4:]) as tmp:
        tmp.write(file_bytes)
        tmp.flush()
        y, sr = librosa.load(tmp.name, sr=16000, mono=True)
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
        seg = y[max(0, c - win // 2):min(len(y), c + win // 2)]

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


def classify_with_gpt(features):
    prompt = f"""
Classify gut sound events.

Return ONLY JSON:
{{
  "events":[
    {{
      "time": float,
      "type": "pop|gurgle|rumble",
      "confidence": float
    }}
  ]
}}

DATA:
{json.dumps(features)}
"""

    response = client.responses.create(
        model="gpt-4o",
        input=prompt
    )

    return response.output_text


def generate_summary(events):
    prompt = f"""
You are analyzing gut sound events.

Write a short, clear summary of what the detected events mean.
Do NOT return JSON. Return plain English.

EVENT DATA:
{json.dumps(events)}
"""

    response = client.responses.create(
        model="gpt-4o",
        input=prompt
    )

    return response.output_text.strip()


def generate_spectrogram_image(y, sr):
    # Mel spectrogram
    S = librosa.feature.melspectrogram(y=y, sr=sr, n_mels=128, fmax=8000)
    S_dB = librosa.power_to_db(S, ref=np.max)

    fig, ax = plt.subplots(figsize=(6, 3))
    img = librosa.display.specshow(
        S_dB, sr=sr, x_axis="time", y_axis="mel", ax=ax
    )
    ax.set_title("Mel Spectrogram")
    fig.colorbar(img, ax=ax, format="%+2.0f dB")

    buf = io.BytesIO()
    plt.tight_layout()
    fig.savefig(buf, format="png", bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)

    img_bytes = buf.read()
    img_b64 = base64.b64encode(img_bytes).decode("utf-8")
    return img_b64


# -----------------------
# FASTAPI ENDPOINTS
# -----------------------
@app.get("/")
def root():
    return {"status": "ok", "message": "Gut Sound Analyzer backend running"}


@app.post("/analyze")
async def analyze_audio(file: UploadFile = File(...)):
    file_bytes = await file.read()

    # 1. Load audio
    y, sr = load_audio_bytes(file_bytes, file.filename)

    # 2. Detect events
    times = detect_events(y, sr)

    # 3. Extract features
    feats = extract_features(y, sr, times)

    # 4. GPT classification
    gpt_output = classify_with_gpt(feats)
    gpt_data = extract_json(gpt_output)

    # 5. GPT summary
    summary_text = generate_summary(gpt_data.get("events", []))

    # 6. Spectrogram
    spectrogram_b64 = generate_spectrogram_image(y, sr)

    # 7. Return JSON with events + summary + spectrogram
    return {
        "events": gpt_data.get("events", []),
        "summary": summary_text,
        "spectrogram": spectrogram_b64
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)


