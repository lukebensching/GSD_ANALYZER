#GSD APP 
#Lucas Bensching, Spring 2026

import streamlit as st
import requests

# -----------------------------
# CONFIG
# -----------------------------
FASTAPI_URL = "https://gsd-analyzer.onrender.com/analyze"

st.set_page_config(
    page_title="Gut Sound Analyzer",
    page_icon="🔊",
    layout="centered"
)

# -----------------------------
# OSU-CASCADES HEADER
# -----------------------------
st.markdown(
    """
    <div style="
        background-color:#D73F09;
        padding:18px;
        border-radius:8px;
        text-align:center;
        margin-bottom:25px;">
        <h1 style="color:white; margin:0; font-size:32px;">
            🔊 Gut Sound Analyzer
        </h1>
        <p style="color:white; margin:0; font-size:16px;">
            Oregon State University – Cascades • AI‑Powered Gut Acoustics
        </p>
    </div>
    """,
    unsafe_allow_html=True
)

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
        st.markdown(
            """
            <div style="padding:12px; background-color:#FAF7F2;
                        border-left:6px solid #D73F09; border-radius:6px;
                        margin-top:20px; margin-bottom:20px;">
                <strong>⏳ Analyzing audio with backend...</strong>
            </div>
            """,
            unsafe_allow_html=True
        )

        # Prepare file for backend
        files = {"file": (uploaded_file.name, uploaded_file, uploaded_file.type)}

        try:
            response = requests.post(
                FASTAPI_URL,
                files=files,
                timeout=300
            )

            # -----------------------------
            # OSU-CASCADES THEMED RESULTS
            # -----------------------------
            if response.status_code == 200:
                result = response.json()

                st.markdown(
                    """
                    <div style="padding: 12px; background-color: #FAF7F2; 
                                border-left: 6px solid #D73F09; border-radius: 6px;
                                margin-top: 20px; margin-bottom: 20px;">
                        <h3 style="margin: 0; color: #1A1A1A;">Analysis Complete</h3>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                # Events Section
                if "events" in result:
                    st.markdown(
                        """
                        <h3 style="color:#D73F09; margin-top: 25px;">
                            Detected Gut Sound Events
                        </h3>
                        """,
                        unsafe_allow_html=True
                    )

                    event_icons = {
                        "gurgle": "💧",
                        "rumble": "🌩️",
                        "pop": "🫧",
                        "unknown": "❓"
                    }

                    for event in result["events"]:
                        icon = event_icons.get(event["type"], "🔊")
                        st.markdown(
                            f"""
                            <div style="
                                background-color:#F0E9DF;
                                padding:12px;
                                border-radius:8px;
                                margin-bottom:10px;
                                border-left:4px solid #D73F09;">
                                <strong style="font-size:16px;">
                                    {icon} {event['type'].capitalize()}
                                </strong><br>
                                <span style="color:#333;">
                                    Time: {event['time']} sec
                                </span><br>
                                <span style="color:#555;">
                                    Confidence: {event['confidence']:.2f}
                                </span>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )

                # Summary Section
                if "summary" in result:
                    st.markdown("<hr>", unsafe_allow_html=True)
                    st.markdown(
                        """
                        <h3 style="color:#D73F09;">AI Summary</h3>
                        """,
                        unsafe_allow_html=True
                    )
                    st.markdown(
                        f"""
                        <div style="background-color:#FAF7F2; padding:15px; border-radius:8px;
                                    border-left:4px solid #D73F09; color:#1A1A1A;">
                            {result['summary']}
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                # Spectrogram Section
                if "spectrogram" in result:
                    st.markdown("<hr>", unsafe_allow_html=True)
                    st.markdown(
                        """
                        <h3 style="color:#D73F09;">Spectrogram</h3>
                        """,
                        unsafe_allow_html=True
                    )
                    st.image(result["spectrogram"])

            else:
                st.error(f"Backend error: {response.status_code}")
                st.write(response.text)

        except requests.exceptions.ReadTimeout:
            st.error("⏱️ Backend timed out. Try a shorter audio clip or try again.")
        except Exception as e:
            st.error("An unexpected error occurred.")
            st.write(str(e))


            
            
            
            