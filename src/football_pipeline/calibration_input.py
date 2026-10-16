"""Known coordinate suggestions, never an automatic calibration approval."""

from copy import deepcopy
from pathlib import Path

from .contracts import PipelineError, VideoMetadata, read_json
from .video import ROOT


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
