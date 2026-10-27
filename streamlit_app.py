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

from football_pipeline.app_results import show_result
from football_pipeline.calibration_input import panoris_point_suggestion, point_label
from football_pipeline.contracts import PipelineError, RunResult, digest_json, read_json, sha256_file
from football_pipeline.demo import default_points
from football_pipeline.detection import available_roles, load_model_manifest, validate_detection_devices
from football_pipeline.geometry import (
    Calibration,
    CalibrationControlError,
    create_calibration,
    point_coordinate_issues,
)
from football_pipeline.model_handoff import available_model_profiles
from football_pipeline.pipeline import process_video, validate_completed
from football_pipeline.point_picker import apply_point_click, point_picker
from football_pipeline.render import LABELS, calibration_preview
from football_pipeline.teams import configured_team_path
from football_pipeline.training_status_ui import show_training_status
from football_pipeline.video import ROOT, inspect_video, read_frame

st.set_page_config(page_title="Voetbal · tactical map", page_icon=":material/sports_soccer:", layout="wide")
st.title("Van voetbalbeeld naar veldpositie")
st.caption("Upload je voetbalvideo: veldherkenning, speler-ID’s en minimap worden automatisch verwerkt.")

MODEL_PATH = Path(os.environ.get("FOOTBALL_MODELS", ROOT / "configs/models.json"))
OUTPUT_ROOT = Path(os.environ.get("FOOTBALL_RUNS", ROOT / "runs"))

show_training_status(ROOT / "artifacts/joint-retrain-20261027-v2")

if linked_run := st.query_params.get("run"):
    from football_pipeline.app_results import linked_result

    try:
        if st.session_state.get("linked_run") != linked_run:
            st.session_state.result = linked_result(OUTPUT_ROOT, linked_run)
            st.session_state.linked_run = linked_run
        show_result(st.session_state.result)
    except (PipelineError, OSError) as exc:
        st.error(str(exc))
    st.stop()

if st.checkbox("Een opgeslagen teamanalyse openen", key="open_team_result"):
    team_runs = []
    for run_path in OUTPUT_ROOT.glob("*/runmanifest.json"):
        try:
            saved = read_json(run_path)
            if saved.get("status") == "completed" and saved.get("team_settings") is not None:
                team_runs.append((run_path.parent, saved))
        except PipelineError:
            continue
    team_runs.sort(key=lambda item: item[1].get("completed_at", ""), reverse=True)
    if team_runs:
        chosen = st.selectbox(
            "Opgeslagen teamanalyse",
            range(len(team_runs)),
            format_func=lambda i: (
                f"{team_runs[i][1].get('completed_at', '')[:19]} · {team_runs[i][0].name[:12]}"
            ),
            key="saved_team_run",
        )
        directory, saved = team_runs[chosen]
        try:
            active = st.session_state.get("result")
            if active is None or st.session_state.get("saved_team_selection") != str(directory):
                active = RunResult(directory, validate_completed(directory), reused=True)
                st.session_state.result = active
                st.session_state.saved_team_selection = str(directory)
            show_result(active)
        except (PipelineError, OSError) as exc:
            st.error(str(exc))
    else:
        st.caption("Nog geen voltooide teamanalyse beschikbaar.")
    st.stop()

# Saved results can be inspected immediately, without uploading or processing again.
if st.checkbox("Een opgeslagen veldtest visueel openen", key="open_field_review"):
    from football_pipeline.field_review_ui import visual_review

    saved_runs = []
    for run_path in OUTPUT_ROOT.glob("*/runmanifest.json"):
        try:
            saved = read_json(run_path)
            if saved.get("status") == "completed" and saved.get("calibration_mode") == "automatic":
                saved_runs.append((run_path.parent, saved))
        except PipelineError:
            continue
    saved_runs.sort(key=lambda item: item[1].get("completed_at", ""), reverse=True)
    if saved_runs:
        selected_run = st.selectbox(
            "Opgeslagen veldtest",
            range(len(saved_runs)),
            format_func=lambda i: (
                f"{saved_runs[i][1].get('completed_at', '')[:19]} · {saved_runs[i][1]['measurements'].get('calibration_usable_fraction', 0):.1%} bruikbaar · {saved_runs[i][0].name[:12]}"
            ),
            key="saved_field_run",
        )
        directory = saved_runs[selected_run][0]
        st.video(str(directory / "samengestelde_video.mp4"))
        try:
            visual_review(directory)
        except (PipelineError, OSError) as exc:
            st.error(str(exc))
    else:
        st.caption("Nog geen voltooide veldtest beschikbaar.")
    st.stop()


@st.cache_data(max_entries=8, show_spinner=False)
def cached_video_metadata(path: str, file_hash: str):
    # file_hash is an explicit cache input; staged files are content-addressed and immutable.
    return inspect_video(path)


@st.cache_data(max_entries=12, show_spinner=False)
def cached_frame(video, index):
    return read_frame(video, index)


st.subheader("1. Video kiezen")
automatic_analysis_enabled = st.toggle(
    "Alles automatisch analyseren na upload",
    value=True,
    key="automatic_analysis",
    help="Schakel uit om de kalibratie en het model zelf in te stellen.",
)
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
            "automatic_last_attempt",
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

if automatic_analysis_enabled:
    from football_pipeline.automatic_analysis_ui import automatic_analysis

    automatic_analysis(video, getattr(upload, "name", "upload.mp4"), OUTPUT_ROOT)
    st.stop()

st.subheader("2. Veld kalibreren")
mode = st.segmented_control(
    "Kalibratiemethode",
    ["Handmatig", "Automatische veldkalibratie"],
    default="Automatische veldkalibratie"
    if os.environ.get("FOOTBALL_CALIBRATION_MODE") == "automatic"
    else "Handmatig",
    selection_mode="single",
    required=True,
    key="calibration_mode",
)
automatic_mode = mode == "Automatische veldkalibratie"
if st.session_state.get("active_calibration_mode") != mode:
    st.session_state.active_calibration_mode = mode
    st.session_state.tracking = False
    st.session_state.pop("result", None)
field_source, field_usage, field_runtime = "", "", None
field_signature = None
field_ready = True
if automatic_mode:
    calibration = None
    st.write(
        "Veldpunten en lijnen worden voor ieder frame opnieuw herkend, ook wanneer hoeken buiten beeld zijn."
    )
    st.caption(
        "Blauw = berekende veldlijnen · groen = herkende lijnen · geel = herkende punten. "
        "Bij te weinig betrouwbare markeringen verschijnt ‘Veldpositie onbekend’."
    )
    st.info(
        "Deze modus gebruikt een standaardveld en een hoofdcamera langs de zijlijn. "
        "Veldposities zijn genormaliseerd. Onafhankelijke kwaliteitsbeoordeling blijft nodig."
    )
    field_runtime = Path(os.environ.get("FOOTBALL_FIELD_RUNTIME", ROOT / ".tools/field-runtime.json"))
    field_source = st.text_input("Videobron", key="field_source")
    field_usage = st.text_input("Toegelaten gebruik / bronvermelding", key="field_usage")
    field_ready = field_runtime.is_file() and bool(field_source.strip() and field_usage.strip())
    if not field_runtime.is_file():
        st.warning("De afzonderlijke veldmodelomgeving is nog niet ingesteld.")
        st.code("python scripts/setup_field_model.py", language="powershell")
    else:
        try:
            runtime = read_json(field_runtime)
            field_signature = digest_json(
                {
                    "runtime": runtime,
                    "worker": sha256_file(ROOT / "scripts/field_calibration_worker.py"),
                    "weights": {
                        name: [Path(runtime[name]).stat().st_size, Path(runtime[name]).stat().st_mtime_ns]
                        for name in ("weights_keypoints", "weights_lines")
                    },
                }
            )
        except (OSError, PipelineError, KeyError) as exc:
            st.error(f"Veldmodelomgeving niet gereed: {exc}")
            field_ready = False
    if not field_source.strip() or not field_usage.strip():
        st.caption("Vul de videobron en het toegelaten gebruik in om te verwerken.")
else:
    st.write(
        "Kies hieronder een veldpunt en klik op de bijbehorende plek in het videobeeld. "
        "De coördinaten worden automatisch ingevuld. Na elke klik ga je naar het volgende ontbrekende punt."
    )
    st.caption(
        "Volg de veldhoeken in het beeld: linksboven → rechtsboven → rechtsonder → linksonder. "
        "Klik daarna waar de middenlijn de bovenste en de onderste zijlijn raakt. "
        "Klik de hoeken van het speelveld, niet de hoeken van het videobeeld."
    )
    with st.expander("Waar horen de zes punten?"):
        st.code(
            "1. Linksboven ───── 5. Middenlijn boven ───── 2. Rechtsboven\n"
            "       │                    │                      │\n"
            "       │                 Middenstip                │\n"
            "       │                    │                      │\n"
            "4. Linksonder ───── 6. Middenlijn onder ───── 3. Rechtsonder",
            language=None,
        )
        st.caption(
            "Punt 5 en 6 liggen op de zijlijnen. De middenstip is geen vervanging voor deze twee punten."
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
        seed_key = f"point_seed_{video.sha256}"
        revision_key = f"point_revision_{video.sha256}"
        latest_key = f"point_latest_{video.sha256}"
        selected_key = f"selected_point_{video.sha256}"
        picker_key = f"picker_{video.sha256}"
        st.session_state.setdefault(seed_key, default_points(video.width, video.height))
        st.session_state.setdefault(revision_key, 0)
        suggested_points = panoris_point_suggestion(video)
        if suggested_points is not None:
            st.info(
                "Deze PANORIS-video wordt herkend. Je kunt de bestaande pilotpunten invullen en daarna zelf controleren."
            )
            if st.button("Pilotpunten invullen", key="load_pilot_points"):
                st.session_state[seed_key] = suggested_points
                st.session_state[revision_key] += 1
                st.session_state[f"reference_{video.sha256}"] = 0
                for name in (
                    "calibration",
                    "calibration_signature",
                    "draft_calibration",
                    "draft_signature",
                    "result",
                ):
                    st.session_state.pop(name, None)
                st.success("Pilotpunten ingevuld. Controleer de markeringen; dit is nog geen goedkeuring.")
        reference_index = st.slider(
            "Referentieframe", 0, video.frame_count - 1, 0, key=f"reference_{video.sha256}"
        )
        point_labels = [
            f"{i + 1}. {point_label(point)}" for i, point in enumerate(st.session_state[seed_key])
        ]
        selected = st.selectbox(
            "Welk veldpunt wil je aanwijzen?",
            range(len(st.session_state[seed_key])),
            format_func=lambda i: point_labels[i],
            key=selected_key,
        )
        picker_container = st.container()
        points_df = pd.DataFrame(st.session_state[seed_key])
        points_df.insert(0, "plek", [point_label(point) for point in st.session_state[seed_key]])
        points_df["x"], points_df["y"] = points_df["x"].astype(float), points_df["y"].astype(float)
        with st.expander("Puntentabel bekijken of precies bijstellen"):
            edited = st.data_editor(
                points_df,
                key=f"points_{video.sha256}_{st.session_state[revision_key]}",
                hide_index=True,
                disabled=["plek", "name", "role", "u", "v"],
                column_config={
                    "plek": st.column_config.TextColumn("Plek op het veld"),
                    "name": None,
                    "x": st.column_config.NumberColumn("x (pixels)", min_value=0, max_value=video.width - 1),
                    "y": st.column_config.NumberColumn("y (pixels)", min_value=0, max_value=video.height - 1),
                },
            )
        points = json.loads(edited.drop(columns=["plek"], errors="ignore").to_json(orient="records"))
        st.session_state[latest_key] = points
        signature = digest_json({"points": points, "reference": reference_index, "video": video.sha256})
        failure = st.session_state.get("calibration_failure")
        if failure and failure["signature"] != signature:
            st.session_state.pop("calibration_failure", None)
            failure = None
        previous_signature = st.session_state.get("calibration_signature")
        if previous_signature != signature:
            st.session_state.pop("calibration", None)
            st.session_state.pop("result", None)
        frame = cached_frame(video, reference_index)
        click_context = digest_json(
            {
                "video": video.sha256,
                "reference": reference_index,
                "revision": st.session_state[revision_key],
                "points": points,
                "selected": selected,
            }
        )

        def save_clicked_point():
            event = st.session_state[picker_key].clicked
            # Reject delayed browser events after changing frame, selection or table.
            current_points = st.session_state[latest_key]
            current_context = digest_json(
                {
                    "video": video.sha256,
                    "reference": st.session_state[f"reference_{video.sha256}"],
                    "revision": st.session_state[revision_key],
                    "points": current_points,
                    "selected": st.session_state[selected_key],
                }
            )
            try:
                updated = apply_point_click(
                    current_points,
                    event,
                    context=current_context,
                    selected=st.session_state[selected_key],
                    width=video.width,
                    height=video.height,
                )
            except PipelineError as exc:
                st.session_state["point_click_error"] = str(exc)
                return
            st.session_state[seed_key] = updated
            st.session_state[revision_key] += 1
            missing = [
                i for i, point in enumerate(updated) if point.get("x") is None or point.get("y") is None
            ]
            if missing:
                st.session_state[selected_key] = missing[0]
            for name in (
                "calibration",
                "calibration_signature",
                "draft_calibration",
                "draft_signature",
                "result",
            ):
                st.session_state.pop(name, None)

        with picker_container:
            if "point_click_error" in st.session_state:
                st.warning(st.session_state.pop("point_click_error"))
            point_picker(
                frame,
                points,
                selected,
                context=click_context,
                key=picker_key,
                on_clicked_change=save_clicked_point,
                diagnostics=failure.get("diagnostics") if failure else None,
            )
            st.caption(
                "Blauw = veldhoek · geel = onafhankelijk controlepunt · nummers volgen de keuzelijst. "
                "Gebruik zoom en de schuifbalken voor preciezer klikken. Kies een bestaand punt om het te verplaatsen."
            )
        issues = point_coordinate_issues(points)
        if issues:
            missing_labels = [point_label(point) for point in points if point_coordinate_issues([point])]
            st.info("Wijs nog aan of verbeter: " + "; ".join(missing_labels) + ".")
        else:
            st.success("Alle punten zijn ingevuld. Controleer de markeringen en bereken de kalibratie.")
        if st.button("Kalibratie berekenen", key="calculate", disabled=bool(issues)):
            try:
                draft = create_calibration(video, points, reference_index)
                st.session_state.draft_calibration = draft
                st.session_state.draft_signature = signature
                st.session_state.pop("calibration_failure", None)
            except PipelineError as exc:
                failure = {"signature": signature, "message": str(exc)}
                if isinstance(exc, CalibrationControlError):
                    failure.update(
                        diagnostics=exc.diagnostics,
                        median_px=exc.median_px,
                        maximum_px=exc.maximum_px,
                        median_limit_px=exc.median_limit_px,
                        maximum_limit_px=exc.maximum_limit_px,
                    )
                st.session_state.calibration_failure = failure
                st.rerun()
        failure = st.session_state.get("calibration_failure")
        if failure and failure["signature"] == signature:
            st.error(failure["message"])
            if failure.get("diagnostics"):
                st.dataframe(
                    [
                        {"Controlepunt": point_label(item), "Afwijking (pixels)": round(item["error_px"], 2)}
                        for item in failure["diagnostics"]
                    ],
                    hide_index=True,
                )
                st.caption(
                    f"Mediaan: {failure['median_px']:.2f} px (maximaal {failure['median_limit_px']:.2f}); "
                    f"grootste fout: {failure['maximum_px']:.2f} px (maximaal {failure['maximum_limit_px']:.2f})."
                )
                st.warning(
                    "Controleer de vier veldhoeken én de twee middenlijnpunten. De onderlinge afwijking "
                    "kan door een verkeerde klik, perspectief of panoramavervorming ontstaan. "
                    "Zoom in en klik op de echte snijpunten van de witte lijnen."
                )
                st.caption(
                    "Op het beeld: gekleurd punt = jouw klik; oranje kruis = berekende plek; "
                    "rode lijn = afwijking. Het kruis is een diagnose van de gekozen hoeken, "
                    "geen bewijs van de juiste plek: verplaats een controlepunt niet alleen om het kruis te raken."
                )
                if suggested_points is not None:
                    st.info(
                        "Voor deze herkende clip kun je bovenaan ‘Pilotpunten invullen’ gebruiken en die punten controleren."
                    )
        draft = st.session_state.get("draft_calibration")
        if draft is not None and st.session_state.get("draft_signature") == signature:
            st.success(
                "Puntcontrole geslaagd. Afwijkingen: "
                + ", ".join(f"{e:.2f} px" for e in draft.check_errors_px)
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
                static = st.checkbox(
                    "Ik bevestig de puntvolgorde en een vaste camera op begin, midden en einde.",
                    key="confirm_static_camera",
                )
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
profiles = available_model_profiles(MODEL_PATH, ROOT / "configs")
if not profiles:
    st.error("Er is geen modelprofiel beschikbaar.")
    st.stop()
selected_model_path = st.selectbox(
    "Modelprofiel",
    list(profiles),
    format_func=lambda path: profiles[path],
    key="model_profile",
)
try:
    models = load_model_manifest(selected_model_path)
    validate_detection_devices(models)
    profile_identity = digest_json(models)
    if st.session_state.get("active_model_profile") != profile_identity:
        st.session_state.active_model_profile = profile_identity
        st.session_state.tracking = False
        st.session_state.pop("result", None)
    semantic_classes = available_roles(models)
    st.caption(
        "Dit model onderscheidt: "
        + ", ".join(
            "scheidsrechter" if role == "referee" and models.get("appearance") else LABELS.get(role, role)
            for role in sorted(semantic_classes)
        )
        + (
            ". Alleen gedetecteerde spelers met hun voetpunt binnen het geldige veld tellen mee. "
            if "player" in semantic_classes
            else ". Personen blijven als persoon aangeduid; hun rol is onbekend. "
        )
        + "Zonder geldige veldherkenning is het aantal op het veld onbekend."
    )
    if models.get("appearance"):
        st.caption(
            "Spelers krijgen Team A, Team B of team onbekend. Bekende wedstrijdclips gebruiken de getrainde "
            "teamindeling; nieuwe video's verzamelen eerst shirtkleuren. A/B zijn geen clubnamen. "
            "Bij twijfel blijft de rol persoon of het team onbekend."
        )
    if "player" in semantic_classes and (
        "steward" not in semantic_classes or "spectator" not in semantic_classes
    ):
        st.warning(
            "Dit model heeft nog geen aparte herkenning voor stewards en supporters. "
            "Als het iemand verkeerd als speler classificeert, kan die binnen het veld toch meetellen."
        )
    if models.get("handoff", {}).get("human_review_completed") is False:
        st.caption(
            "Dit model is voorlopig. De menselijke labelreview staat nog open. "
            "Controleer gemiste personen, verkeerde rollen en onbekende teamindelingen."
        )
    if models.get("handoff", {}).get("broadcast_transfer_adequate") is False:
        st.warning(
            "De P004-basisdetector miste veel personen in de Broadcast-ontwikkelclip. "
            "De aanvullende rolclassifier is op die clip nog niet gevalideerd. "
            "Het profiel ‘Personen op GPU’ blijft beschikbaar voor algemene herkenning."
        )
    if "player" not in semantic_classes:
        st.warning(
            "Dit profiel detecteert personen. Spelertracking vereist een model met expliciete spelerklassen."
        )
        st.caption(
            "De minimap toont personen met een geldige veldpositie. Spelerrollen en individuele identiteit "
            "zijn onbekend."
        )
    elif not automatic_mode:
        st.info(
            "Spelermodel geselecteerd. Controleer eerst een run zonder tracking en leg de MVP-review vast; "
            "daarna kun je ID's en trajecten toevoegen."
        )
    else:
        st.info("Spelermodel geselecteerd. Het veldmodel plaatst de actuele detecties op de minimap.")
except PipelineError as exc:
    st.error(str(exc))
    st.caption("Eenmalige voorbereiding: python -m football_pipeline download-baseline")
    st.stop()

tracking = st.checkbox(
    "Spelertracking en trajecten toevoegen",
    disabled=not any("player" in spec["class_mapping"].values() for spec in models["models"]),
    key="tracking",
)
teams_enabled = (
    st.checkbox(
        "Teams op shirtkleur herkennen",
        value=True,
        disabled="player" not in semantic_classes,
        key="teams_enabled",
    )
    and "player" in semantic_classes
)
team_config_path = configured_team_path(models)
if automatic_mode:
    st.caption(
        "Speler-ID’s gebruiken cameracompensatie en worden bij camerawissels vernieuwd. "
        "Trajecten bevatten alleen actuele, geldige veldposities."
    )
acceptance_upload = None
if tracking and not automatic_mode:
    acceptance_upload = st.file_uploader(
        "Gecontroleerde MVP-acceptatie (.json)", type=["json"], key="mvp_acceptance"
    )
    st.caption(
        "Accepteer eerst de MVP-run met accept-mvp nadat de controlebeelden en afspeelbaarheid zijn beoordeeld."
    )

request_signature = digest_json(
    {
        "video": video.sha256,
        "calibration": field_signature if automatic_mode else calibration.identity,
        "calibration_mode": mode,
        "field_source": field_source,
        "field_usage": field_usage,
        "models": models,
        "tracking": tracking,
        "teams": sha256_file(team_config_path) if teams_enabled else None,
        "acceptance": hashlib.sha256(acceptance_upload.getvalue()).hexdigest() if acceptance_upload else None,
    }
)
if st.session_state.get("result_request_signature") != request_signature:
    st.session_state.pop("result", None)

if st.button(
    "Verwerken",
    type="primary",
    key="process",
    disabled=not field_ready or (tracking and not automatic_mode and acceptance_upload is None),
):
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
            fraction = (0.5 + count / total * 0.5) if automatic_mode else count / total
            progress_bar.progress(
                fraction, text=f"Detecties en minimap: {count}/{total} frames · {elapsed:.1f} seconden"
            )

        def show_field_progress(count, total, elapsed):
            progress_bar.progress(
                count / total * 0.5, text=f"Veldherkenning: {count}/{total} frames · {elapsed:.1f} seconden"
            )

        result = process_video(
            video.path,
            calibration,
            selected_model_path,
            OUTPUT_ROOT,
            tracker_config_path=ROOT / "configs/bytetrack.yaml" if tracking else None,
            team_config_path=team_config_path if teams_enabled else None,
            mvp_acceptance_path=acceptance_path,
            progress=show_progress,
            field_progress=show_field_progress if automatic_mode else None,
            field_runtime_path=field_runtime if automatic_mode else None,
            field_source=field_source,
            field_usage=field_usage,
        )
        st.session_state.result = result
        st.session_state.result_request_signature = request_signature
        progress_bar.progress(1.0, text="Voltooid")
    except (PipelineError, OSError, ValueError, KeyError) as exc:
        st.error(str(exc))

result = st.session_state.get("result")
if result is not None:
    show_result(result)
