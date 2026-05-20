#GSD APP 
#Lucas Bensching, Spring 2026

import streamlit as st
import requests
import io

# -----------------------------
# CONFIG
# -----------------------------
FASTAPI_URL = "https://gsd-analyzer.onrender.com/analyze"

st.set_page_config(
    page_title="Gut Sound Analyzer",
    page_icon="🔊",
    layout="centered"
)

st.title("🔊 Gut Sound Analyzer")
st.write("Upload an audio file and the backend will analyze gut sounds using AI.")

# -----------------------------
# FILE UPLOAD
# -----------------------------
uploaded_file = st.file_uploader(
    "Upload audio (.wav, .mp3, .m4a)",
    type=["wav", "mp3", "m4a"]
)

if uploaded_file is not None:
    st.audio(uploaded_file, format="audio/wav")

    if st.button("Analyze Audio"):
        st.write("⏳ Analyzing audio with backend...")

        # Prepare file for backend
        files = {"file": (uploaded_file.name, uploaded_file, uploaded_file.type)}

        try:
            response = requests.post(
                FASTAPI_URL,
                files=files,
                timeout=300
            )

            if response.status_code == 200:
                result = response.json()

                st.success("Analysis complete!")

                # Display events
                if "events" in result:
                    st.subheader("Detected Gut Sound Events")
                    for event in result["events"]:
                        st.write(f"- **{event['type']}** at {event['time']} sec (confidence {event['confidence']:.2f})")

                # Display GPT summary
                if "summary" in result:
                    st.subheader("AI Summary")
                    st.write(result["summary"])

                # Display spectrogram if backend returns it
                if "spectrogram" in result:
                    st.subheader("Spectrogram")
                    st.image(result["spectrogram"])

            else:
                st.error(f"Backend error: {response.status_code}")
                st.write(response.text)

        except requests.exceptions.ReadTimeout:
            st.error("⏱️ Backend timed out. Try a shorter audio clip or try again.")
        except Exception as e:
            st.error("An unexpected error occurred.")
            st.write(str(e))


            
            
            
            