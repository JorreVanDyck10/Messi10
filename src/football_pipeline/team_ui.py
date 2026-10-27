"""Native Streamlit inspection and explicitly submitted team corrections."""

import copy
import json
from pathlib import Path

import altair as alt
import cv2
import pandas as pd
import streamlit as st

from .contracts import FrameRecord, PipelineError, read_json
from .field_review_ui import source_frame
from .participants import player_summary
from .render import render_frame
from .team_results import apply_team_corrections
from .teams import TEAM_IDS, UNKNOWN_COLOR
from .tracking import Trajectories


@st.cache_data(max_entries=4, show_spinner=False)
def team_tables(directory: str, records_hash: str):
    counts, tracks = [], {}
    with (Path(directory) / "framegegevens.jsonl").open(encoding="utf-8") as stream:
        for line in stream:
            record = FrameRecord.from_dict(json.loads(line))
            summary = player_summary(record)
            counts.append(
                {
                    "frame_index": record.frame_index,
                    "timestamp_s": record.timestamp_s,
                    "total": summary["on_field"],
                    **summary["by_team"],
                }
            )
            for d in record.detections:
                if d.semantic_class != "player" or d.track_id is None:
                    continue
                item = tracks.setdefault(
                    d.track_id,
                    {
                        "ID": d.track_id,
                        "Eerste frame": record.frame_index,
                        "Laatste frame": record.frame_index,
                        "Team": "onbekend",
                    },
                )
                item["Laatste frame"] = record.frame_index
                if d.team_id:
                    item["Team"] = d.team_id
    return pd.DataFrame(counts), sorted(tracks.values(), key=lambda t: t["ID"])


@st.cache_data(max_entries=32, show_spinner=False)
def frame_window(directory: str, records_hash: str, index: int, fps: float):
    rows = []
    start = max(0, index - round(5 * fps) + 1)
    with (Path(directory) / "framegegevens.jsonl").open(encoding="utf-8") as stream:
        for i, line in enumerate(stream):
            if i > index:
                break
            if i >= start:
                rows.append(json.loads(line))
    return rows


def count_chart(table, model):
    # Separate line segments explicitly so field loss never bridges a missing interval.
    rows, segment = [], 0
    for item in table.to_dict("records"):
        if pd.isna(item["total"]):
            segment += 1
            continue
        for key in (*TEAM_IDS, "unknown"):
            rows.append(
                {
                    "Tijd (s)": item["timestamp_s"],
                    "Aantal": item[key],
                    "Team": f"{key} · {model['teams'][key]['name']}" if key in TEAM_IDS else "Onbekend",
                    "Segment": f"{key}:{segment}",
                }
            )
    if not rows:
        st.caption("Geen teamtellingen beschikbaar: de veldpositie of spelerrol is onbekend.")
        return
    chart = (
        alt.Chart(pd.DataFrame(rows))
        .mark_line(point=True)
        .encode(
            x=alt.X("Tijd (s):Q"),
            y=alt.Y("Aantal:Q", scale=alt.Scale(zero=True)),
            color=alt.Color(
                "Team:N",
                scale=alt.Scale(
                    domain=[f"{k} · {model['teams'][k]['name']}" for k in TEAM_IDS] + ["Onbekend"],
                    range=[model["teams"][k]["display_color"] for k in TEAM_IDS] + [UNKNOWN_COLOR],
                ),
            ),
            detail="Segment:N",
            tooltip=["Tijd (s):Q", "Team:N", "Aantal:Q"],
        )
    )
    st.altair_chart(chart)


def show_teams(result):
    directory, manifest = result.directory, result.manifest
    token = manifest["cache_key"][:16]
    records_hash = manifest["artifacts"]["framegegevens.jsonl"]
    model = read_json(directory / "teaminstellingen.json")
    corrections = read_json(directory / "teamcorrecties.json")
    table, tracks = team_tables(str(directory), records_hash)
    st.subheader("Teams en telling")
    st.caption(
        "Aantallen zijn actuele waargenomen spelers binnen het geldige veld. "
        "Speler-ID’s zijn tijdelijk per shot. Een kleurmatchscore is geen waarschijnlijkheid."
    )
    if model["status"] != "available":
        st.info(
            "Automatische shirtkleuren zijn onvoldoende onderscheidbaar. Je kunt shirtprototypes of speler-ID’s corrigeren."
        )
    maximum = manifest["video"]["frame_count"] - 1
    index = st.slider("Exact bronframe voor teams", 0, maximum, key=f"team_frame_{token}") if maximum else 0
    selected = table.iloc[index]
    with st.container(horizontal=True):
        for key, name in [
            ("total", "Totaal"),
            *[(k, model["teams"][k]["name"]) for k in TEAM_IDS],
            ("unknown", "Onbekend"),
        ]:
            count = selected[key]
            st.metric(name, "Onbekend" if pd.isna(count) else str(int(count)))
    st.caption(
        f"Frame {index} · {selected['timestamp_s']:.3f} s. De onderstaande weergave toont exact dit bronframe."
    )
    fps = manifest["video"]["fps_num"] / manifest["video"]["fps_den"]
    try:
        rows = frame_window(str(directory), records_hash, index, fps)
        histories = Trajectories(fps)
        for row in rows:
            record = FrameRecord.from_dict(row)
            histories.update(record.detections, record.frame_index)
        frame = source_frame(manifest["video"]["path"], manifest["video"]["sha256"], index)
        st.image(
            cv2.cvtColor(render_frame(frame, record, histories), cv2.COLOR_BGR2RGB),
            caption="Teamlabels, telling en tactical map van hetzelfde frame",
        )
        st.dataframe(
            pd.DataFrame(
                [
                    {
                        "ID": d.track_id,
                        "Team": d.team_id or "onbekend",
                        "Status": d.team_status,
                        "Herkomst": d.team_source,
                        "Kleurmatchscore": d.team_match_score,
                    }
                    for d in record.detections
                    if d.semantic_class == "player"
                ]
            ),
            hide_index=True,
        )
    except (OSError, PipelineError) as exc:
        st.caption(f"Frameweergave niet beschikbaar: {exc}")
    count_chart(table, model)
    with st.expander("Teamindeling corrigeren"):
        st.caption(
            "Wijzigingen worden pas verwerkt bij ‘Correcties toepassen’. Een ID-koppeling geldt voor de hele "
            "tijdelijke track. Afwijkende doelmankleuren blijven onbekend totdat je ze koppelt."
        )
        if tracks:
            st.dataframe(pd.DataFrame(tracks), hide_index=True)
        if corrections["track_overrides"]:
            st.write("Opgeslagen ID-correcties", corrections["track_overrides"])
        with st.form(f"team_corrections_{token}"):
            edits = copy.deepcopy(corrections["teams"])
            for key in TEAM_IDS:
                team = model["teams"][key]
                st.markdown(f"**Team {key}**")
                name = st.text_input("Teamnaam", team["name"], max_chars=40, key=f"team_name_{key}_{token}")
                display = st.color_picker(
                    "Weergavekleur", team["display_color"], key=f"team_display_{key}_{token}"
                )
                change_shirt = st.checkbox("Shirtprototype aanpassen", key=f"team_change_shirt_{key}_{token}")
                shirt = st.color_picker(
                    "Shirtkleur",
                    team.get("shirt_color") or team["display_color"],
                    key=f"team_shirt_{key}_{token}",
                )
                edits.setdefault(key, {}).update(name=name.strip(), display_color=display)
                if change_shirt:
                    edits[key]["shirt_color"] = shirt
            selected_track = st.selectbox(
                "Speler-ID corrigeren",
                [None] + [str(t["ID"]) for t in tracks],
                format_func=lambda x: "Geen speler-ID geselecteerd" if x is None else f"Speler #{x}",
                key=f"team_track_{token}",
            )
            choice = st.selectbox(
                "Koppeling voor geselecteerde ID",
                ["Geen wijziging", "A", "B", "Onbekend", "Automatisch herstellen"],
                format_func=lambda x: model["teams"][x]["name"] if x in TEAM_IDS else x,
                key=f"team_override_{token}",
            )
            submitted = st.form_submit_button("Correcties toepassen", type="primary")
        if submitted:
            overrides = copy.deepcopy(corrections["track_overrides"])
            if selected_track is not None and choice != "Geen wijziging":
                if choice == "Automatisch herstellen":
                    overrides.pop(selected_track, None)
                else:
                    overrides[selected_track] = choice if choice in TEAM_IDS else None
            request = {**corrections, "teams": edits, "track_overrides": overrides}
            try:
                with st.spinner("Teamlabels, telling en video bijwerken…"):
                    corrected = apply_team_corrections(directory, request, directory.parent)
                st.session_state.result = corrected
                if st.query_params.get("run") == directory.name:
                    st.query_params["run"] = corrected.directory.name
                    st.session_state.linked_run = corrected.directory.name
                st.rerun()
            except (OSError, PipelineError) as exc:
                st.error(str(exc))
