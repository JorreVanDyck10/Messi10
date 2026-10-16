"""Run with: python -m streamlit run streamlit_app.py"""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import asdict
from pathlib import Path

import cv2
import pandas as pd
import streamlit as st

from football_pipeline.contracts import PipelineError, digest_json
from football_pipeline.demo import default_points
from football_pipeline.detection import load_model_manifest
from football_pipeline.geometry import Calibration, create_calibration
from football_pipeline.pipeline import process_video
from football_pipeline.render import calibration_preview
from football_pipeline.video import ROOT, inspect_video, read_frame

st.set_page_config(page_title="Voetbal · tactical map", page_icon=":material/sports_soccer:", layout="wide")
st.title("Van voetbalbeeld naar veldpositie")
st.caption("Vaste overzichtscamera · handmatige kalibratie · gesynchroniseerde video en minimap")
st.info(
    "Gebruik een MP4 met constante framerate, vier zichtbare veldhoeken en een camera zonder pan of zoom."
)

MODEL_PATH = Path(os.environ.get("FOOTBALL_MODELS", ROOT / "configs/models.json"))
OUTPUT_ROOT = Path(os.environ.get("FOOTBALL_RUNS", ROOT / "runs"))


@st.cache_data(max_entries=8, show_spinner=False)
def cached_video_metadata(path: str, file_hash: str):
    # file_hash is an explicit cache input; staged files are content-addressed and immutable.
    return inspect_video(path)


@st.cache_data(max_entries=12, show_spinner=False)
def cached_frame(video, index):
    return read_frame(video, index)


st.subheader("1. Video kiezen")
upload = st.file_uploader("Voetbalvideo (.mp4)", type=["mp4"], key="video_upload")
if upload is None:
    st.caption("Kies een ontwikkelfragment van ongeveer 30–60 seconden om te beginnen.")
    st.stop()

try:
    upload_id = getattr(upload, "file_id", None) or hashlib.sha256(upload.getbuffer()).hexdigest()
    if st.session_state.get("active_upload_id") != upload_id:
        content = upload.getbuffer()
        file_hash = hashlib.sha256(content).hexdigest()
        upload_root = ROOT / "data/uploads"
        upload_root.mkdir(parents=True, exist_ok=True)
        staged = upload_root / f"{file_hash}.mp4"
        if not staged.is_file():
            temporary = staged.with_suffix(".upload")
            temporary.write_bytes(content)
            temporary.replace(staged)
        st.session_state.update(active_upload_id=upload_id, video_path=str(staged), video_hash=file_hash)
        for name in (
            "calibration",
            "calibration_signature",
            "draft_calibration",
            "draft_signature",
            "result",
        ):
            st.session_state.pop(name, None)
    with st.spinner("Videotijdlijn controleren…"):
        video = cached_video_metadata(st.session_state.video_path, st.session_state.video_hash)
    with st.container(horizontal=True):
        st.metric("Resolutie", f"{video.width} × {video.height}")
        st.metric("Framerate", f"{video.fps:.3f} fps")
        st.metric("Duur", f"{video.duration_s:.1f} s")
        st.metric("Frames", video.frame_count)
except (PipelineError, OSError) as exc:
    st.error(str(exc))
    st.stop()

st.subheader("2. Veld kalibreren")
st.write(
    "Voer oorspronkelijke pixelcoördinaten in. Volg de veldhoeken (0,0), (1,0), (1,1), (0,1). "
    "De twee middenlijnpunten zijn onafhankelijke controles en tellen niet mee bij het fitten."
)
calibration_upload = st.file_uploader(
    "Bestaande kalibratie laden (.json)", type=["json"], key="calibration_upload"
)
if calibration_upload is not None:
    try:
        loaded = Calibration(**json.loads(calibration_upload.getvalue()))
        loaded.validate_for(video)
        st.session_state.calibration = loaded
        st.session_state.calibration_signature = "loaded:" + loaded.identity
        st.success(f"Goedgekeurde kalibratie geladen; reviewer: {loaded.review['reviewer']}.")
    except (PipelineError, ValueError, TypeError, KeyError) as exc:
        st.error(f"Kalibratie niet geladen: {exc}")
        st.session_state.pop("calibration", None)
else:
    reference_index = st.slider(
        "Referentieframe", 0, video.frame_count - 1, 0, key=f"reference_{video.sha256}"
    )
    points_df = pd.DataFrame(default_points(video.width, video.height))
    points_df["x"], points_df["y"] = points_df["x"].astype(float), points_df["y"].astype(float)
    edited = st.data_editor(
        points_df,
        key=f"points_{video.sha256}",
        hide_index=True,
        disabled=["name", "role", "u", "v"],
        column_config={
            "x": st.column_config.NumberColumn("x (pixels)", min_value=0, max_value=video.width - 1),
            "y": st.column_config.NumberColumn("y (pixels)", min_value=0, max_value=video.height - 1),
        },
    )
    points = json.loads(edited.to_json(orient="records"))
    signature = digest_json({"points": points, "reference": reference_index, "video": video.sha256})
    previous_signature = st.session_state.get("calibration_signature")
    if previous_signature != signature:
        st.session_state.pop("calibration", None)
        st.session_state.pop("result", None)
    frame = cached_frame(video, reference_index)
    preview = calibration_preview(frame, points)
    st.image(
        cv2.cvtColor(preview, cv2.COLOR_BGR2RGB),
        caption="Pixelraster en ingevoerde veldpunten",
        width="stretch",
    )
    if st.button("Kalibratie berekenen", key="calculate"):
        try:
            draft = create_calibration(video, points, reference_index)
            st.session_state.draft_calibration = draft
            st.session_state.draft_signature = signature
        except PipelineError as exc:
            st.error(str(exc))
    draft = st.session_state.get("draft_calibration")
    if draft is not None and st.session_state.get("draft_signature") == signature:
        st.success(
            "Puntcontrole geslaagd. Afwijkingen: " + ", ".join(f"{e:.2f} px" for e in draft.check_errors_px)
        )
        with st.expander("Begin, midden en einde controleren", expanded=True):
            columns = st.columns(3)
            temporal = [0, video.frame_count // 2, video.frame_count - 1]
            for column, index in zip(columns, temporal):
                temporal_frame = calibration_preview(cached_frame(video, index), points, grid=False)
                column.image(cv2.cvtColor(temporal_frame, cv2.COLOR_BGR2RGB), caption=f"Frame {index}")
            st.caption(
                "Controleer dat lijnen en hoeken op alle drie beelden onder dezelfde markeringen blijven."
            )
        with st.form("approve_calibration"):
            reviewer = st.text_input("Naam reviewer")
            source = st.text_input("Videobron")
            usage = st.text_input("Toegelaten gebruik / bronvermelding")
            static = st.checkbox("Ik bevestig de puntvolgorde en een vaste camera op begin, midden en einde.")
            approve = st.form_submit_button("Kalibratie goedkeuren")
        if approve:
            try:
                draft.review = {
                    "approved": True,
                    "reviewer": reviewer,
                    "source": source,
                    "usage": usage,
                    "static_camera_confirmed": static,
                    "temporal_frames": temporal,
                }
                draft.validate_for(video)
                st.session_state.calibration = draft
                st.session_state.calibration_signature = signature
                st.success("Kalibratie goedgekeurd.")
            except PipelineError as exc:
                st.error(str(exc))

calibration = st.session_state.get("calibration")
if calibration is None:
    st.caption("Bereken en keur de kalibratie goed om verder te gaan.")
    st.stop()
st.download_button(
    "Kalibratie downloaden",
    json.dumps(asdict(calibration), indent=2),
    file_name="calibration.json",
    mime="application/json",
    key="download_calibration",
)

st.subheader("3. Verwerken")
try:
    models = load_model_manifest(MODEL_PATH)
    st.write(models.get("profile_name", "Modelprofiel"))
    semantic_classes = {value for spec in models["models"] for value in spec["class_mapping"].values()}
    if "player" not in semantic_classes:
        st.warning(
            "Dit profiel detecteert personen. Spelertracking vereist een model met expliciete spelerklassen."
        )
except PipelineError as exc:
    st.error(str(exc))
    st.caption("Eenmalige voorbereiding: python -m football_pipeline download-baseline")
    st.stop()

tracking = st.checkbox(
    "Spelertracking en trajecten toevoegen", disabled="player" not in semantic_classes, key="tracking"
)
acceptance_upload = None
if tracking:
    acceptance_upload = st.file_uploader(
        "Gecontroleerde MVP-acceptatie (.json)", type=["json"], key="mvp_acceptance"
    )
    st.caption(
        "Accepteer eerst de MVP-run met accept-mvp nadat de controlebeelden en afspeelbaarheid zijn beoordeeld."
    )

request_signature = digest_json(
    {
        "video": video.sha256,
        "calibration": calibration.identity,
        "models": models,
        "tracking": tracking,
        "acceptance": hashlib.sha256(acceptance_upload.getvalue()).hexdigest() if acceptance_upload else None,
    }
)
if st.session_state.get("result_request_signature") != request_signature:
    st.session_state.pop("result", None)

if st.button("Verwerken", type="primary", key="process", disabled=tracking and acceptance_upload is None):
    progress_bar = st.progress(0.0, text="Verwerking voorbereiden…")
    acceptance_path = None
    if acceptance_upload:
        acceptance_path = (
            ROOT
            / "data/uploads"
            / f"acceptance-{hashlib.sha256(acceptance_upload.getvalue()).hexdigest()}.json"
        )
        acceptance_path.write_bytes(acceptance_upload.getvalue())
    try:

        def show_progress(count, total, elapsed):
            progress_bar.progress(count / total, text=f"{count}/{total} frames · {elapsed:.1f} seconden")

        result = process_video(
            video.path,
            calibration,
            MODEL_PATH,
            OUTPUT_ROOT,
            tracker_config_path=ROOT / "configs/bytetrack.yaml" if tracking else None,
            mvp_acceptance_path=acceptance_path,
            progress=show_progress,
        )
        st.session_state.result = result
        st.session_state.result_request_signature = request_signature
        progress_bar.progress(1.0, text="Voltooid")
    except PipelineError as exc:
        st.error(str(exc))

result = st.session_state.get("result")
if result is not None:
    st.subheader("4. Resultaat")
    st.success("Eerder voltooid resultaat hergebruikt." if result.reused else "Video volledig verwerkt.")
    st.caption(f"Uitvoermap: {result.directory}")
    st.video(str(result.video_path))
    metrics = result.manifest["measurements"]
    with st.container(horizontal=True):
        st.metric("Verwerkingstijd", f"{metrics['runtime_s']:.1f} s")
        st.metric("Verwerkingssnelheid", f"{metrics['processing_fps']:.2f} fps")
        st.metric("Proces-RAM (bemonsterd)", f"{metrics['peak_process_ram_bytes_sampled'] / 2**20:.0f} MiB")
    for name, description, mime in (
        ("samengestelde_video.mp4", "Video downloaden", "video/mp4"),
        ("framegegevens.jsonl", "Framegegevens downloaden", "application/x-ndjson"),
        ("runmanifest.json", "Runmanifest downloaden", "application/json"),
    ):
        with (result.directory / name).open("rb") as stream:
            st.download_button(description, stream, file_name=name, mime=mime, key=f"download_{name}")
