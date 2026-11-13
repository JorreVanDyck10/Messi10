"""Zichtbare spelersdrempel met herstelbare oorspronkelijke waarden en uitleg over tijdelijke ID's."""

import json

import streamlit as st

from .participants import DISPLAY_CONFIDENCE, player_display_policy
from .tracking import load_tracker_config


def change_player_threshold():
    """Schakel bij een bewuste schuifwijziging naar strikt filteren, ook voor gevolgde spelers."""
    st.session_state.player_display_original = False
    st.session_state.player_display_dirty = True
    st.session_state.pop("result", None)


def restore_player_threshold():
    """Herstel de oorspronkelijke waarde én de uitzondering voor gevolgde detecties zonder configuratie te schrijven."""
    st.session_state.player_display_confidence = DISPLAY_CONFIDENCE
    st.session_state.player_display_original = True
    st.session_state.player_display_dirty = True
    st.session_state.pop("result", None)


def player_controls(models: dict, tracker_path, fps: float, tracking: bool) -> float | None:
    """Toon sessiegebonden weergave-instellingen; None betekent exact het oorspronkelijke spelersbeleid."""
    st.session_state.setdefault("player_display_original", True)
    st.session_state.setdefault("player_display_confidence", DISPLAY_CONFIDENCE)
    tracker = load_tracker_config(tracker_path)
    with st.container(border=True):
        st.markdown("**Spelersweergave**")
        confidence = st.slider(
            "Confidence-drempel spelers",
            min_value=0.10,
            max_value=0.95,
            step=0.01,
            format="%.2f",
            key="player_display_confidence",
            on_change=change_player_threshold,
            help="Hoger verbergt meer onzekere spelers; lager kan ook foutieve detecties tonen. Confidence is geen gemeten nauwkeurigheidspercentage.",
        )
        original = st.session_state.player_display_original
        st.caption(
            f"{'Oorspronkelijke' if original else 'Aangepaste'} instellingen · spelersdrempel {confidence:.2f}"
        )
        st.caption(
            "Oorspronkelijk beleid: gevolgde spelers blijven ook onder 0,25 zichtbaar."
            if original
            else "Strikt beleid: spelers onder de drempel verdwijnen uit boxen, minimap en tellingen, ook met een ID. Intern blijft tracking doorlopen."
        )
        st.button(
            "Oorspronkelijke instellingen herstellen",
            on_click=restore_player_threshold,
            key="restore_player_display",
        )
        st.caption(
            "Klik na aanpassen of herstellen op Verwerken. Model- en trackingdrempels worden niet overschreven; Andrews balinstellingen blijven gelijk."
        )
        snapshot = {"models": models, "player_policy": player_display_policy(), "tracker_config": tracker}
        st.download_button(
            "Oorspronkelijke model- en trackinginstellingen downloaden",
            json.dumps(snapshot, indent=2, ensure_ascii=False),
            file_name="oorspronkelijke-instellingen.json",
            mime="application/json",
            key="download_original_player_settings",
        )
    with st.expander("Hoe werkt de spelertracking?"):
        st.write(
            "ByteTrack koppelt spelerboxen tussen opeenvolgende frames met bewegingsvoorspelling en overlap. "
            "De volgnummers zijn tijdelijke ID’s, geen namen of rugnummers. Een speler kan na overlap of lange uitval een nieuw ID krijgen."
        )
        st.write(
            "Bij automatische veldherkenning wordt camerabeweging gecompenseerd. Bij een camerawissel of onbetrouwbare camerabeweging worden ID’s bewust vernieuwd. "
            "Zonder geldige veldpositie kan een beeld-ID blijven bestaan, maar wordt geen minimaptraject getekend."
        )
        st.caption(
            f"Tracking {'aan' if tracking else 'uit'} · hoge score {tracker['track_high_thresh']:.2f} · "
            f"lage score {tracker['track_low_thresh']:.2f} · nieuw ID vanaf {tracker['new_track_thresh']:.2f} · "
            f"buffer {tracker['track_buffer']} updates (circa {tracker['track_buffer'] / fps:.2f} s bij {fps:.2f} fps)."
        )
        st.caption(
            "Voorspelde tussenposities worden niet als nieuwe detecties getekend. Trackingkwaliteit wordt apart van detectie- en veldkwaliteit beoordeeld."
        )
    return None if original else confidence
