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
from pydub import AudioSegment
import re
from dotenv import load_dotenv
import os 

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
    # If WAV, load directly
    if filename.lower().endswith(".wav"):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            tmp.write(file_bytes)
            tmp.flush()
            y, sr = librosa.load(tmp.name, sr=16000, mono=True)
            return y, sr

    # Convert other formats to WAV
    with tempfile.NamedTemporaryFile(delete=False) as tmp_in:
        tmp_in.write(file_bytes)
        tmp_in.flush()

        audio = AudioSegment.from_file(tmp_in.name)
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


# -----------------------
# FASTAPI ENDPOINT
# -----------------------
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

    # 5. Return JSON
    return gpt_data


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

