"""Streamlit demo UI for the Traffic Inspection Agent."""
import base64
import json
import os
import tempfile
import logging

import cv2
import numpy as np
import streamlit as st

logging.basicConfig(level=logging.INFO)

st.set_page_config(
    page_title="Traffic Inspection Agent",
    page_icon="🚦",
    layout="wide",
)

st.title("🚦 Traffic Inspection Agent")
st.markdown(
    "_An embodied agent that selects reusable computer-vision skills to inspect traffic feeds "
    "and report anomalies._"
)

# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Configuration")
    use_roi = st.toggle("Enable ROI filter", value=False)
    use_llm = st.toggle("Use LLM Planner (Claude)", value=False)
    sample_fps = st.slider("Sample FPS", min_value=1.0, max_value=10.0, value=3.0, step=0.5)
    motion_threshold = st.slider("Motion threshold (px)", min_value=2, max_value=50, value=10)
    min_stop_duration = st.slider("Min stop duration (s)", min_value=1.0, max_value=30.0, value=5.0, step=0.5)

# ── Main inputs ───────────────────────────────────────────────────────────────
col1, col2 = st.columns([2, 1])

with col1:
    prompt = st.text_area(
        "Inspection prompt",
        value="Inspect this road and tell me if any vehicle is stopped.",
        height=80,
    )

with col2:
    source_mode = st.radio("Video source", ["Upload file", "Enter path"])

uploaded_file = None
video_path = None

if source_mode == "Upload file":
    uploaded_file = st.file_uploader("Upload video", type=["mp4", "avi", "mov", "mkv"])
else:
    video_path = st.text_input("Video path", placeholder="assets/videos/demo_road.mp4")

run_button = st.button("▶ Run Inspection", type="primary")

# ── Run pipeline ──────────────────────────────────────────────────────────────
if run_button:
    # Determine source
    source = None
    tmp_path = None

    if source_mode == "Upload file" and uploaded_file is not None:
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
        tmp.write(uploaded_file.read())
        tmp.flush()
        tmp_path = tmp.name
        source = tmp_path
    elif source_mode == "Enter path" and video_path:
        source = video_path
    else:
        st.error("Please provide a video source.")
        st.stop()

    if not os.path.exists(source) and not source.startswith("rtsp://"):
        st.error(f"Video source not found: {source}")
        st.stop()

    # Apply sidebar config
    from app.config import settings
    settings.SAMPLE_FPS = sample_fps
    settings.MOTION_THRESHOLD = motion_threshold
    settings.MIN_STOP_DURATION = min_stop_duration

    with st.spinner("Running inspection..."):
        try:
            from app.pipelines.traffic_inspection import TrafficInspectionPipeline
            pipeline = TrafficInspectionPipeline()
            result = pipeline.run(
                prompt=prompt,
                source=source,
                use_roi=use_roi,
                use_llm_planner=use_llm,
                save_report=True,
                save_video=False,
            )
        except Exception as e:
            st.error(f"Pipeline error: {e}")
            if tmp_path:
                os.unlink(tmp_path)
            st.stop()

    if tmp_path:
        os.unlink(tmp_path)

    # ── Results ───────────────────────────────────────────────────────────────
    st.success("Inspection complete!")

    st.subheader("Execution Plan")
    for i, skill in enumerate(result.plan, 1):
        st.markdown(f"**{i}.** `{skill}`")

    st.subheader("Summary")
    st.info(result.summary)

    # Show last annotated frame if available
    last_frame = result.metadata.get("last_frame")
    if last_frame is not None and isinstance(last_frame, np.ndarray):
        st.subheader("Last Annotated Frame")
        frame_rgb = cv2.cvtColor(last_frame, cv2.COLOR_BGR2RGB)
        st.image(frame_rgb, use_container_width=True)

    if result.events:
        st.subheader("Stopped Vehicle Events")
        events_data = [e.model_dump() for e in result.events]
        st.dataframe(events_data)
    else:
        st.info("No stopped vehicle events detected.")

    meta_display = {k: v for k, v in result.metadata.items() if k != "last_frame"}
    with st.expander("Metadata"):
        st.json(meta_display)
