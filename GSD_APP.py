#GSD APP 
#Lucas Bensching, Spring 2026

import streamlit as st
import requests
import pandas as pd
import base64

# -----------------------------
# CONFIG
# -----------------------------
FASTAPI_URL = "https://gsd-analyzer.onrender.com/analyze"

st.set_page_config(
    page_title="Gut Sound Analyzer",
    page_icon="🔊",
    layout="wide"
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
            Gut Sound Analyzer
        </h1>
        <p style="color:white; margin:0; font-size:16px;">
            Oregon State University – Cascades • AI‑Powered Gut Acoustics
        </p>
    </div>
    """,
    unsafe_allow_html=True
)

# -----------------------------
# PROJECT DESCRIPTION
# -----------------------------
st.markdown(
    """
    <div style="text-align:center; font-size:18px; max-width:800px; margin:auto; margin-bottom:25px;">
        This tool analyzes abdominal audio recordings to detect gut sound events such as 
        <strong>rumbles, gurgles,</strong> and <strong>pops</strong>.  
        Using a FastAPI backend and AI‑powered acoustic models, the system extracts features, 
        identifies events, and generates a natural‑language summary of gut activity.
        <br><br>
        Upload an audio file below to begin the analysis.
    </div>
    """,
    unsafe_allow_html=True
)

# -----------------------------
# CENTERED FILE UPLOADER
# -----------------------------
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    uploaded_file = st.file_uploader(
        "Choose an audio file",
        type=["wav", "mp3", "m4a"],
        label_visibility="visible"
    )

# -----------------------------
# PROCESSING
# -----------------------------
if uploaded_file is not None:

    # Center the analyze button
    colA, colB, colC = st.columns([1, 2, 1])
    with colB:
        analyze_clicked = st.button("Analyze Audio")

    if analyze_clicked:

        # Temporary analyzing message
        analyzing_box = st.empty()
        analyzing_box.markdown(
            """
            <div style="padding:12px; background-color:#FAF7F2;
                        border-left:6px solid #D73F09; border-radius:6px;
                        margin-top:20px; margin-bottom:20px; text-align:center;">
                <strong>Analyzing audio... This may take a few seconds.</strong>
            </div>
            """,
            unsafe_allow_html=True
        )

        files = {"file": (uploaded_file.name, uploaded_file, uploaded_file.type)}

        try:
            response = requests.post(
                FASTAPI_URL,
                files=files,
                timeout=300
            )

            # Remove the analyzing message
            analyzing_box.empty()

            if response.status_code == 200:
                result = response.json()

                # -----------------------------
                # TABS (NO WAVEFORM TAB)
                # -----------------------------
                tab2, tab3, tab4 = st.tabs(
                    ["Spectrogram", "Events", "Summary"]
                )

                # -----------------------------
                # SPECTROGRAM TAB
                # -----------------------------
                with tab2:
                    st.markdown(
                        "<h3 style='color:#D73F09;'>Spectrogram</h3>",
                        unsafe_allow_html=True
                    )
                    if "spectrogram" in result:
                        spectrogram_bytes = base64.b64decode(result["spectrogram"])
                        st.image(spectrogram_bytes)
                    else:
                        st.info("No spectrogram returned by backend.")

                # -----------------------------
                # EVENTS TAB
                # -----------------------------
                with tab3:
                    st.markdown(
                        "<h3 style='color:#D73F09;'>Detected Gut Sound Events</h3>",
                        unsafe_allow_html=True
                    )

                    if "events" in result and len(result["events"]) > 0:
                        df = pd.DataFrame(result["events"])
                        df["time"] = df["time"].round(2)
                        df["confidence"] = df["confidence"].round(2)
                        df["type"] = df["type"].str.upper()

                        st.dataframe(
                            df[["time", "type", "confidence"]],
                            use_container_width=True,
                            hide_index=True
                        )
                    else:
                        st.info("No events returned by backend.")

                # -----------------------------
                # SUMMARY TAB
                # -----------------------------
                with tab4:
                    st.markdown(
                        "<h3 style='color:#D73F09;'>AI Summary</h3>",
                        unsafe_allow_html=True
                    )
                    if "summary" in result:
                        st.markdown(
                            f"""
                            <div style="background-color:#FAF7F2; padding:15px; border-radius:8px;
                                        border-left:4px solid #D73F09; color:#1A1A1A;">
                                {result['summary']}
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
                    else:
                        st.info("No summary returned by backend.")

            else:
                analyzing_box.empty()
                st.error(f"Backend error: {response.status_code}")
                st.write(response.text)

        except requests.exceptions.ReadTimeout:
            analyzing_box.empty()
            st.error("Backend timed out. Try a shorter audio clip or try again.")
        except Exception as e:
            analyzing_box.empty()
            st.error("An unexpected error occurred.")
            st.write(str(e))

            
            
            