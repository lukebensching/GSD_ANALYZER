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
    page_icon="🦫",
    layout="wide"
)

# -----------------------------
# HEADER (perfectly centered)
# -----------------------------
header_col = st.columns([1, 6, 1])[1]
with header_col:
    st.markdown(
        """
        <div style="text-align:center; margin-bottom:10px;">
            <h1 style="color:#D73F09; font-size:42px; margin-bottom:5px;">
                Gut Sound Analyzer
            </h1>
            <p style="color:#444; font-size:18px; margin-top:0;">
                Oregon State University – Cascades • AI‑Powered Gut Acoustics
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

# -----------------------------
# SECTION DIVIDER
# -----------------------------
st.markdown("<hr style='margin-top:10px; margin-bottom:30px;'>", unsafe_allow_html=True)

# -----------------------------
# PROJECT DESCRIPTION
# -----------------------------
st.markdown(
    """
    <div style="text-align:center; font-size:18px; max-width:800px; margin:auto; margin-bottom:25px;">
        The human digestive system produces a rich landscape of sounds — rumbles, gurgles, pops, 
        and subtle acoustic patterns that often go unnoticed. These sounds can reflect motility, 
        inflammation, or disruptions in normal gut activity, yet they’re rarely measured outside 
        clinical settings.
        <br><br>
        This project explores whether everyday abdominal audio recordings can be analyzed using 
        modern AI techniques to help identify meaningful gut sound patterns. By detecting acoustic 
        events and summarizing activity, this tool demonstrates how non‑invasive audio monitoring 
        could one day support early screening, symptom tracking, or research into conditions such 
        as IBS, Crohn’s disease, and other gastrointestinal disorders.
        <br><br>
        Upload an audio file below to see how the system interprets gut acoustics in real time.
    </div>
    """,
    unsafe_allow_html=True
)

# -----------------------------
# CENTERED FILE UPLOADER
# -----------------------------
center = st.columns([3, 4, 3])[1]
with center:
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
    center_btn = st.columns([3, 4, 3])[1]
    with center_btn:
        analyze_clicked = st.button("Analyze Audio")

    if analyze_clicked:

        # -----------------------------
        # PROGRESS BAR
        # -----------------------------
        progress = st.progress(0, text="Analyzing audio…")

        progress.progress(20, text="Loading audio…")

        files = {"file": (uploaded_file.name, uploaded_file, uploaded_file.type)}

        try:
            progress.progress(40, text="Detecting gut sound events…")

            response = requests.post(
                FASTAPI_URL,
                files=files,
                timeout=300
            )

            progress.progress(60, text="Extracting acoustic features…")
            progress.progress(80, text="Classifying events with AI…")
            progress.progress(100, text="Finalizing results…")

            progress.empty()

            if response.status_code == 200:
                result = response.json()

                # -----------------------------
                # SECTION DIVIDER
                # -----------------------------
                st.markdown("<hr style='margin-top:40px; margin-bottom:20px;'>", unsafe_allow_html=True)

                # -----------------------------
                # TABS
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

                        # EVENT COUNTS
                        types = [e["type"].lower() for e in result["events"]]
                        pop_count = types.count("pop")
                        gurgle_count = types.count("gurgle")
                        rumble_count = types.count("rumble")

                        st.markdown(
                            f"""
                            <div style="font-size:18px; margin-bottom:10px;">
                                <strong>Detected:</strong> 
                                {pop_count} pops • {gurgle_count} gurgles • {rumble_count} rumbles
                            </div>
                            """,
                            unsafe_allow_html=True
                        )

                        # TIMELINE
                        timeline = " | ".join([f"{e['time']}s" for e in result["events"]])
                        st.markdown(
                            f"""
                            <div style="font-family:monospace; font-size:16px; margin-bottom:15px;">
                                <strong>Timeline:</strong> {timeline}
                            </div>
                            """,
                            unsafe_allow_html=True
                        )

                        # TABLE
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
                        "<h3 style='color:#D73F09;'>Summary</h3>",
                        unsafe_allow_html=True
                    )
                    if "summary" in result:
                        st.markdown(
                            f"""
                            <div style="
                                background-color:#FAF7F2;
                                padding:20px;
                                border-radius:8px;
                                border-left:4px solid #D73F09;
                                font-size:17px;
                                line-height:1.6;
                                color:#1A1A1A;
                                max-width:800px;
                                margin:auto;
                            ">
                                {result['summary']}
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
                    else:
                        st.info("No summary returned by backend.")

            else:
                progress.empty()
                st.error(f"Backend error: {response.status_code}")
                st.write(response.text)

        except requests.exceptions.ReadTimeout:
            progress.empty()
            st.error("Backend timed out. Try a shorter audio clip or try again.")
        except Exception as e:
            progress.empty()
            st.error("An unexpected error occurred.")
            st.write(str(e))

# -----------------------------
# FOOTER
# -----------------------------
st.markdown(
    """
    <div style="text-align:center; margin-top:50px; color:#777; font-size:14px;">
        Oregon State University – Cascades<br>
        School of Engineering • 2026
    </div>
    """,
    unsafe_allow_html=True
)


            
            