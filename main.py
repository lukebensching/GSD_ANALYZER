#Gut Sound Device (GSD), Main thread
#Lucas Bensching, Spring 2026 

import os
import uuid
import librosa
import librosa.display
import matplotlib.pyplot as plt
import numpy as np

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from pydub import AudioSegment
from openai import OpenAI

# ---------- Config ----------
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY not set in environment")

client = OpenAI(api_key=OPENAI_API_KEY)

app = FastAPI(title="Gut Sound Analysis API")

# ---------- CORS ----------
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def add_mobile_headers(request, call_next):
    response = await call_next(request)
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Access-Control-Expose-Headers"] = "*"
    return response

# ---------- Work Directory ----------
WORK_DIR = "workdir"
os.makedirs(WORK_DIR, exist_ok=True)

# ---------- Helpers ----------
def clean_json_text(text: str) -> str:
    text = text.strip()

    if text.startswith("```"):
        parts = text.split("```")
        cleaned = parts[1].strip()

        if cleaned.startswith("json"):
            cleaned = cleaned[4:].strip()

        if cleaned.endswith("```"):
            cleaned = cleaned.rsplit("```", 1)[0].strip()

        return cleaned

    return text


def save_upload_to_disk(upload: UploadFile, dest_path: str):
    with open(dest_path, "wb") as f:
        f.write(upload.file.read())
    return dest_path


def convert_to_wav(input_path: str) -> str:
    if input_path.lower().endswith(".wav"):
        return input_path

    output_path = os.path.splitext(input_path)[0] + ".wav"
    audio = AudioSegment.from_file(input_path)
    audio.export(output_path, format="wav")
    return output_path


def generate_spectrogram(audio_path: str) -> str:
    y, sr = librosa.load(audio_path, sr=16000)

    S = librosa.feature.melspectrogram(
        y=y,
        sr=sr,
        n_fft=1024,
        hop_length=160,
        n_mels=64,
        fmin=20,
        fmax=500,
    )
    log_S = librosa.power_to_db(S, ref=np.max)

    image_path = os.path.join(
        WORK_DIR, f"spectrogram_{uuid.uuid4().hex}.png"
    )

    plt.figure(figsize=(10, 4))
    librosa.display.specshow(
        log_S, sr=sr, hop_length=160, x_axis="time", y_axis="mel"
    )
    plt.colorbar(format="%+2.0f dB")
    plt.title("Gut Sound Log-Mel Spectrogram")
    plt.tight_layout()
    plt.savefig(image_path)
    plt.close()

    return image_path


# ---------- FIXED GPT‑4o CALL ----------
def analyze_spectrogram_with_gpt(image_path: str) -> str:
    """
    Correct multimodal call for the OpenAI Responses API.
    Uses the correct binary image format.
    """

    with open(image_path, "rb") as f:
        img_bytes = f.read()

    prompt = """
    Analyze this gut-sound spectrogram and return ONLY valid JSON:

    {
      "events": [
        {"type": "pop" | "gurgle" | "rumble", "time": float, "confidence": float}
      ]
    }
    """

    response = client.responses.create(
        model="gpt-4o",
        input=[
            {
                "type": "input_image",
                "image": {
                    "data": img_bytes
                }
            },
            {
                "type": "input_text",
                "text": prompt
            }
        ]
    )

    return str(response.output_text)


# ---------- Routes ----------
@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/analyze")
async def analyze(file: UploadFile = File(...)):
    try:
        raw_path = os.path.join(WORK_DIR, f"upload_{uuid.uuid4().hex}_{file.filename}")
        save_upload_to_disk(file, raw_path)

        wav_path = convert_to_wav(raw_path)
        spectrogram_path = generate_spectrogram(wav_path)

        result_text = analyze_spectrogram_with_gpt(spectrogram_path)
        cleaned = clean_json_text(result_text)

        import json
        try:
            result_json = json.loads(cleaned)
            return JSONResponse(content=result_json)
        except Exception:
            return JSONResponse(content={"raw_response": str(result_text)})

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"{e}")


@app.post("/mobile/analyze")
async def mobile_analyze(file: UploadFile = File(...)):
    try:
        raw_path = os.path.join(WORK_DIR, f"mobile_{uuid.uuid4().hex}_{file.filename}")
        save_upload_to_disk(file, raw_path)

        wav_path = convert_to_wav(raw_path)

        y, sr = librosa.load(wav_path, sr=16000)
        duration = float(len(y) / sr)

        spectrogram_path = generate_spectrogram(wav_path)

        result_text = analyze_spectrogram_with_gpt(spectrogram_path)
        cleaned = clean_json_text(result_text)

        import json
        try:
            data = json.loads(cleaned)
            events = data.get("events", [])
            return {"events": events, "duration": duration}
        except Exception:
            return {"raw_response": str(result_text), "duration": duration}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Mobile analysis failed: {e}")














