"""Known coordinate suggestions, never an automatic calibration approval."""

from copy import deepcopy
from pathlib import Path

from .contracts import PipelineError, VideoMetadata, read_json
from .video import ROOT


def penalty_area_points(side: str, *, length=105.0, width=68.0) -> list[dict]:
    """Four penalty-area corners and two separate goal-area checks, without guessed clicks."""
    if side not in {"left", "right"} or not 60 <= length <= 150 or not 45 <= width <= 100:
        raise PipelineError("Kies links of rechts en geldige, bekende veldafmetingen.")
    big_top, big_bottom = (width / 2 - 20.16) / width, (width / 2 + 20.16) / width
    small_top, small_bottom = (width / 2 - 9.16) / width, (width / 2 + 9.16) / width
    near, far = (0, 16.5 / length) if side == "left" else (1 - 16.5 / length, 1)
    check_u = 5.5 / length if side == "left" else 1 - 5.5 / length
    definitions = [
        ("Strafschopgebied boven, linkerkant", "fit", near, big_top),
        ("Strafschopgebied boven, rechterkant", "fit", far, big_top),
        ("Strafschopgebied onder, rechterkant", "fit", far, big_bottom),
        ("Strafschopgebied onder, linkerkant", "fit", near, big_bottom),
        ("Doelgebied boven, hoek op 5,5 m van de doellijn", "check", check_u, small_top),
        ("Doelgebied onder, hoek op 5,5 m van de doellijn", "check", check_u, small_bottom),
    ]
    return [{"name": name, "role": role, "u": u, "v": v, "x": None, "y": None}
            for name, role, u, v in definitions]


def point_label(point: dict) -> str:
    """Friendly labels for the orientation used by the manual selection workflow."""
    labels = {
        (0, 0): "Linksboven (veldhoek)",
        (1, 0): "Rechtsboven (veldhoek)",
        (1, 1): "Rechtsonder (veldhoek)",
        (0, 1): "Linksonder (veldhoek)",
        (0.5, 0): "Middenlijn boven (op de zijlijn)",
        (0.5, 1): "Middenlijn onder (op de zijlijn)",
        (0.5, 0.5): "Middenstip",
        (0, 0.5): "Midden doellijn links",
        (1, 0.5): "Midden doellijn rechts",
    }
    return labels.get((point.get("u"), point.get("v")), point.get("name", "Veldpunt"))


def panoris_point_suggestion(video: VideoMetadata, root: Path = ROOT) -> list[dict] | None:
    try:
        config = read_json(root / "configs/panoris-pilot-points.json")
        if list(video.size) != config["image_size"]:
            return None
        hashes = {config["source_sha256"]}
        provenance_path = root / "reports/panoris-pilot-provenance.json"
        if provenance_path.is_file():
            provenance = read_json(provenance_path)
            if (
                provenance["source"]["sha256"] == config["source_sha256"]
                and provenance["source_frame_start"] == 0
                and provenance["source_frame_end_exclusive"] == 150
            ):
                hashes.add(provenance["clip"]["sha256"])
        if video.sha256 in hashes:
            return deepcopy(config["points"])
    except (PipelineError, KeyError, TypeError):
        pass
    return None
