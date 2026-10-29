"""Toont afstandsschattingen uit opgeslagen waarnemingen zonder detectie opnieuw uit te voeren."""

import json
from dataclasses import asdict
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

from .contracts import PipelineError, read_json
from .distances import METHOD_VERSION, DistanceSettings, estimate_distances, recorded_dimensions


@st.cache_data(max_entries=8, show_spinner=False)
def distance_tables(directory, records_hash, duration_s, settings, method_version=METHOD_VERSION):
    with (Path(directory) / "framegegevens.jsonl").open(encoding="utf-8") as stream:
        summaries, intervals = estimate_distances(
            (json.loads(line) for line in stream if line.strip()), duration_s, DistanceSettings(**settings)
        )
    return pd.DataFrame(summaries), pd.DataFrame(intervals)


def show_distances(result):
    directory, manifest = result.directory, result.manifest
    token = directory.name[:16]
    st.subheader("Elke gemeten meter in beeld")
    st.caption(
        "Geschatte afstand binnen deze clip, per tijdelijke speler-ID. Meetgaten en camerawissels "
        "worden onderbroken. Een ID is geen geverifieerde speleridentiteit."
    )
    calibration_path = directory / "calibration.json"
    calibration = read_json(calibration_path) if calibration_path.is_file() else {}
    length, width, source = recorded_dimensions(calibration)
    settings_key = f"distance_settings_{token}"
    saved = st.session_state.get(settings_key, asdict(DistanceSettings(length, width)))
    with st.expander("Veldafmetingen en meetmethode"):
        st.caption(source)
        with st.form(f"distance_form_{token}"):
            with st.container(horizontal=True):
                length = st.number_input(
                    "Veldlengte voor afstand (m)",
                    60.0,
                    150.0,
                    float(saved["length_m"]),
                    key=f"distance_length_{token}",
                )
                width = st.number_input(
                    "Veldbreedte voor afstand (m)",
                    45.0,
                    100.0,
                    float(saved["width_m"]),
                    key=f"distance_width_{token}",
                )
                speed = st.number_input(
                    "Technische spronggrens (m/s)",
                    1.0,
                    50.0,
                    float(saved["max_speed_m_s"]),
                    key=f"distance_speed_{token}",
                )
            st.caption(
                "Mediaanfilter van 3 frames · meetstappen van 0,2 s · geen aanvulling van ontbrekende posities."
            )
            if st.form_submit_button("Afstanden bijwerken", icon=":material/refresh:"):
                saved = asdict(DistanceSettings(length, width, speed))
                st.session_state[settings_key] = saved
    st.caption(
        f"Veld: {saved['length_m']:g} × {saved['width_m']:g} m · "
        + (source if settings_key not in st.session_state else "Ingesteld voor deze analyse in deze sessie")
        + ". Afstanden zijn schattingen; onafhankelijke nauwkeurigheid is niet gemeten."
    )
    video = manifest["video"]
    duration = video.get("duration_s") or video["frame_count"] * video["fps_den"] / video["fps_num"]
    with st.spinner("Opgeslagen veldposities samenvatten…"):
        table, intervals = distance_tables(
            str(directory), manifest["artifacts"]["framegegevens.jsonl"], duration, saved, METHOD_VERSION
        )
    if table.empty:
        st.info(
            "Niet beschikbaar: deze analyse bevat geen tijdelijke speler-ID’s. Kies een analyse met tracking."
        )
        return
    team_path = directory / "teaminstellingen.json"
    model = read_json(team_path) if team_path.is_file() else {}
    names = {key: model.get("teams", {}).get(key, {}).get("name", f"Team {key}") for key in ("A", "B")}
    names["unknown"] = "Onbekend / wisselend"
    colors = [
        model.get("teams", {}).get(k, {}).get("display_color", c)
        for k, c in (("A", "#5BB8FF"), ("B", "#FFB45B"))
    ] + ["#93A4BA"]
    selected_team = st.selectbox(
        "Filter op team",
        ["all", "A", "B", "unknown"],
        format_func=lambda k: "Alle teams" if k == "all" else names[k],
        key=f"distance_team_{token}",
    )
    filtered = table if selected_team == "all" else table[table.team == selected_team]
    filtered = filtered.sort_values("distance_m", ascending=False, na_position="last")
    if not intervals.empty:
        st.caption("Teamtotalen over de hele clip")
        with st.container(horizontal=True):
            for team in ("A", "B", "unknown"):
                values = intervals[intervals.team == team]
                st.metric(
                    names[team],
                    f"{values.distance_m.sum():.1f} m" if len(values) else "Niet beschikbaar",
                    border=True,
                )
        st.caption(
            "Teamtotalen tellen alleen gemeten intervallen met dezelfde teamindeling; overige intervallen zijn onbekend."
        )
    display = filtered.copy()
    display["Speler"] = display.apply(lambda row: f"#{row.track_id} · shot {row.shot}", axis=1)
    display["Team"] = display.team.map(names)
    display["distance_m"] = display.distance_m.map(lambda x: "Niet beschikbaar" if pd.isna(x) else f"{x:.1f}")
    st.dataframe(
        display[["Speler", "Team", "distance_m", "measured_s", "coverage"]].rename(
            columns={
                "distance_m": "Geschatte afstand (m)",
                "measured_s": "Gemeten tijd (s)",
                "coverage": "Meetdekking",
            }
        ),
        hide_index=True,
        column_config={
            "Geschatte afstand (m)": st.column_config.TextColumn(),
            "Gemeten tijd (s)": st.column_config.NumberColumn(format="%.2f"),
            "Meetdekking": st.column_config.NumberColumn(format="percent"),
        },
    )
    st.caption("Meetdekking = geaccepteerde meettijd van deze ID gedeeld door de volledige clipduur.")
    available = filtered[filtered.measured_s > 0].sort_values("distance_m", ascending=False)
    if not available.empty:
        labels = {row.track: f"#{row.track_id} · shot {row.shot}" for row in available.itertuples()}
        track_teams = {row.track: names[row.team] for row in available.itertuples()}
        selected = st.multiselect(
            "Spelers op de grafiek",
            list(labels),
            default=list(labels)[:3],
            format_func=labels.get,
            max_selections=5,
            key=f"distance_tracks_{token}",
        )
        rows = []
        for item in intervals[intervals.track.isin(selected)].to_dict("records"):
            label = labels[item["track"]]
            rows.extend(
                [
                    {
                        **item,
                        "Speler": label,
                        "Team": track_teams[item["track"]],
                        "Tijd (s)": item["start_s"],
                        "Afstand (m)": item["cumulative_m"] - item["distance_m"],
                    },
                    {
                        **item,
                        "Speler": label,
                        "Team": track_teams[item["track"]],
                        "Tijd (s)": item["timestamp_s"],
                        "Afstand (m)": item["cumulative_m"],
                    },
                ]
            )
        if rows:
            chart = (
                alt.Chart(pd.DataFrame(rows))
                .mark_line()
                .encode(
                    x=alt.X("Tijd (s):Q"),
                    y=alt.Y("Afstand (m):Q", scale=alt.Scale(zero=True)),
                    color=alt.Color("Team:N", scale=alt.Scale(domain=list(names.values()), range=colors)),
                    strokeDash="Speler:N",
                    detail="segment:N",
                    tooltip=["Speler:N", "Team:N", "Tijd (s):Q", "Afstand (m):Q"],
                )
            )
            st.altair_chart(chart)
    else:
        st.info("Niet beschikbaar: binnen dit filter zijn geen aaneengesloten geldige meetintervallen.")
    export = table.assign(
        team_name=table.team.map(names), **saved, method_version=METHOD_VERSION, clip_duration_s=duration
    )
    with st.container(horizontal=True):
        st.download_button(
            "Afstanden downloaden (CSV)",
            export.to_csv(index=False).encode("utf-8-sig"),
            "spelerafstanden.csv",
            "text/csv",
            key=f"distance_csv_{token}",
            icon=":material/download:",
        )
        if not intervals.empty:
            export_intervals = intervals.assign(**saved, method_version=METHOD_VERSION)
            st.download_button(
                "Meetintervallen downloaden (CSV)",
                export_intervals.to_csv(index=False).encode("utf-8-sig"),
                "afstandintervallen.csv",
                "text/csv",
                key=f"distance_intervals_{token}",
            )


def distance_panel(result):
    try:
        show_distances(result)
    except (PipelineError, OSError, ValueError, KeyError) as exc:
        st.error(f"Afstanden niet beschikbaar: {exc}")
