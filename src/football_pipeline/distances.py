"""Schat waargenomen afstanden op basis van geldige veldposities. Ontbrekende frames en cameraresets onderbreken een meettraject."""

from collections import Counter
from dataclasses import dataclass
from math import hypot, isfinite

import numpy as np

from .contracts import FrameRecord, PipelineError
from .participants import counted_as_player, normalized_team_id

METHOD_VERSION = "observed_median3_step02_v1"


@dataclass(frozen=True)
class DistanceSettings:
    length_m: float = 105.0
    width_m: float = 68.0
    max_speed_m_s: float = 12.0
    step_s: float = 0.2

    def __post_init__(self):
        values = (self.length_m, self.width_m, self.max_speed_m_s, self.step_s)
        if not all(isfinite(x) and x > 0 for x in values):
            raise PipelineError("Afstandsinstellingen moeten positieve, eindige getallen zijn.")


def recorded_dimensions(calibration):
    """Use explicitly recorded dimensions, including those used for partial-field calibration."""
    dimensions = calibration.get("review", {}).get("field_dimensions_m") if calibration else None
    if isinstance(dimensions, dict):
        try:
            settings = DistanceSettings(float(dimensions["length"]), float(dimensions["width"]))
            return settings.length_m, settings.width_m, "Vastgelegd bij de kalibratie"
        except (KeyError, TypeError, ValueError):
            pass
    return 105.0, 68.0, "Aanname: standaardveld van 105 × 68 m"


def estimate_distances(records, duration_s, settings=DistanceSettings()):
    """Return summaries and independent measured intervals from an iterable of FrameRecords.

    Coverage is accepted measured time / full clip duration per temporary track.
    A reset starts a new identity namespace, even if incoming track IDs are reused.
    Raw per-frame jumps are rejected before smoothing, so filtering cannot hide a jump.
    """
    if not isfinite(duration_s) or duration_s <= 0:
        raise PipelineError("Een positieve clipduur is nodig voor de meetdekking.")
    tracks, active, intervals = {}, {}, []
    epoch, last_frame, last_time, serial = 0, None, None, 0

    def flush(key):
        nonlocal serial
        points = active.pop(key, [])
        if len(points) < 2:
            return
        serial += 1
        xy = np.array([p[2] for p in points])
        smooth = xy.copy()
        if len(points) >= 3:
            smooth[1:-1] = np.median(np.stack([xy[:-2], xy[1:-1], xy[2:]]), axis=0)
        anchor = 0
        for i in range(1, len(points)):
            dt = points[i][1] - points[anchor][1]
            if dt + 1e-9 < settings.step_s and i != len(points) - 1:
                continue
            distance = float(np.linalg.norm(smooth[i] - smooth[anchor]))
            if distance / dt <= settings.max_speed_m_s + 1e-9:
                item = tracks[key]
                item["distance_m"] += distance
                item["measured_s"] += dt
                teams = {p[3] for p in points[anchor : i + 1]}
                team = next(iter(teams)) if len(teams) == 1 else "unknown"
                intervals.append(
                    {
                        "track": key,
                        "track_id": item["track_id"],
                        "shot": item["shot"],
                        "segment": serial,
                        "start_s": points[anchor][1],
                        "timestamp_s": points[i][1],
                        "distance_m": distance,
                        "cumulative_m": item["distance_m"],
                        "measured_s": dt,
                        "team": team,
                    }
                )
            else:
                serial += 1
            anchor = i

    for record in records:
        if not isinstance(record, FrameRecord):
            record = FrameRecord.from_dict(record)
        reset = bool((record.tracking or {}).get("reset_tracks"))
        discontinuity = last_frame is not None and (
            record.frame_index != last_frame + 1
            or not isfinite(record.timestamp_s)
            or record.timestamp_s <= last_time
        )
        if reset or discontinuity:
            for key in list(active):
                flush(key)
            if reset:
                epoch += 1
        last_frame, last_time = record.frame_index, record.timestamp_s
        seen, duplicates = {}, Counter(d.track_id for d in record.detections if d.track_id is not None)
        for detection in record.detections:
            if detection.semantic_class != "player" or detection.track_id is None:
                continue
            key = f"{epoch}:{detection.track_id}"
            item = tracks.setdefault(
                key,
                {
                    "track": key,
                    "track_id": detection.track_id,
                    "shot": epoch + 1,
                    "distance_m": 0.0,
                    "measured_s": 0.0,
                    "teams": set(),
                },
            )
            if (
                duplicates[detection.track_id] != 1
                or not isfinite(record.timestamp_s)
                or not counted_as_player(record, detection)
            ):
                continue
            team = normalized_team_id(detection.team_id)
            item["teams"].add(team)
            position = (
                detection.field_position[0] * settings.length_m,
                detection.field_position[1] * settings.width_m,
            )
            seen[key] = (record.frame_index, record.timestamp_s, position, team)
        for key in list(active):
            if key not in seen:
                flush(key)
        for key, point in seen.items():
            if key in active:
                previous = active[key][-1]
                dt = point[1] - previous[1]
                if (
                    point[0] != previous[0] + 1
                    or dt <= 0
                    or hypot(point[2][0] - previous[2][0], point[2][1] - previous[2][1]) / dt
                    > settings.max_speed_m_s + 1e-9
                ):
                    flush(key)
            active.setdefault(key, []).append(point)
    for key in list(active):
        flush(key)
    summaries = []
    for item in tracks.values():
        teams = item.pop("teams")
        summaries.append(
            {
                **item,
                "team": next(iter(teams)) if len(teams) == 1 else "unknown",
                "distance_m": item["distance_m"] if item["measured_s"] else None,
                "coverage": min(1.0, item["measured_s"] / duration_s),
            }
        )
    return summaries, intervals
