"""Audit penalty-area calibration against separate provider goal-area lines."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from pathlib import Path

import cv2
import numpy as np

from football_pipeline.calibration_input import penalty_area_points
from football_pipeline.contracts import PipelineError, VideoMetadata, digest_json, read_json, sha256_file, write_json
from football_pipeline.geometry import create_calibration
from football_pipeline.render import calibrated_field_preview


def line(points, width, height):
    xy = np.array([[p["x"] * width, p["y"] * height, 1] for p in points])
    if len(xy) < 2:
        raise ValueError("Not enough line observations.")
    return np.linalg.svd(xy, full_matrices=True)[2][-1]


def intersection(a, b):
    point = np.cross(a, b)
    if not np.isfinite(point).all() or abs(point[2]) < 1e-9:
        raise ValueError("Parallel or invalid provider lines.")
    return point[:2] / point[2]


def required_lines(side):
    return [f"Side line {side}", *(f"{size} rect. {side} {edge}"
            for size in ("Big", "Small") for edge in ("top", "bottom", "main"))]


def provider_points(pitch, row, side):
    fitted = {name: line(pitch[name], row["width"], row["height"]) for name in required_lines(side)}
    goal, big, small = [fitted[name] for name in (f"Side line {side}", f"Big rect. {side} main",
                                                f"Small rect. {side} main")]
    left, right = (goal, big) if side == "left" else (big, goal)
    pairs = [(left, fitted[f"Big rect. {side} top"]), (right, fitted[f"Big rect. {side} top"]),
             (right, fitted[f"Big rect. {side} bottom"]), (left, fitted[f"Big rect. {side} bottom"]),
             (small, fitted[f"Small rect. {side} top"]), (small, fitted[f"Small rect. {side} bottom"])]
    points = penalty_area_points(side)
    for point, pair in zip(points, pairs):
        point["x"], point["y"] = intersection(*pair).tolist()
    return points


def audit(root, output):
    root, output = root.resolve(), output.resolve()
    if output.exists():
        raise ValueError("Use a new output directory to preserve earlier evidence.")
    source = read_json(root / "manifest.json")
    if digest_json({k: v for k, v in source.items() if k != "fingerprint"}) != source["fingerprint"]:
        raise ValueError("Frozen source identity changed.")
    output.mkdir(parents=True)
    protocol = {"source_fingerprint": source["fingerprint"], "script_sha256": sha256_file(__file__),
                "selection": "First frame with all seven required polylines in each clip/side; no selection on errors.",
                "fit": "Four intersections of separate penalty-area boundary lines",
                "checks": "Two intersections of goal-area lines, excluded from fitting",
                "pitch_dimensions_m": [105, 68], "human_review_completed": False,
                "scope": "Provider-derived development geometry; no independent human ground truth or MVP approval."}
    write_json(output / "protocol.json", protocol)
    groups = defaultdict(list)
    for row in source["frames"]:
        groups[row["clip"]].append(row)
    results, previews, errors_m = [], set(), []
    for clip in sorted(groups):
        chosen = {}
        rows = sorted(groups[clip], key=lambda r: r["source_frame_index"])
        for row in rows:
            pitch = read_json(root / row["field_label"])
            for side in ("left", "right"):
                if side not in chosen and all(len(pitch.get(k, [])) >= 2 for k in required_lines(side)):
                    chosen[side] = row, pitch
            if len(chosen) == 2:
                break
        for side in ("left", "right"):
            record = {"clip": clip, "side": side, "split": rows[0]["split"]}
            if side not in chosen:
                record["status"] = "required_landmarks_missing"
                results.append(record)
                continue
            row, pitch = chosen[side]
            record.update(frame_id=row["frame_id"], game_id=row["game_id"], image=row["image"],
                          field_label=row["field_label"], field_label_sha256=sha256_file(root / row["field_label"]))
            try:
                points = provider_points(pitch, row, side)
                record["points"] = points
                video = VideoMetadata("provider-still.jpg", row["image_sha256"], row["width"], row["height"],
                                      25, 1, 1, "jpeg", 1 / 25)
                calibration = create_calibration(video, points)
                record.update(status="passed", median_check_px=float(np.median(calibration.check_errors_px)),
                              max_check_px=max(calibration.check_errors_px), homography=calibration.homography)
                inverse = np.linalg.inv(np.asarray(calibration.homography))
                corners = cv2.perspectiveTransform(np.array([[[0, 0], [1, 0], [1, 1], [0, 1]]], np.float64), inverse)[0]
                record["all_full_field_corners_visible"] = bool(
                    (corners[:, 0] >= 0).all() and (corners[:, 0] < row["width"]).all()
                    and (corners[:, 1] >= 0).all() and (corners[:, 1] < row["height"]).all())
                # Geometry only: use provider player boxes, not detector predictions.
                attributes = read_json(root / row["attributes"])
                differences = []
                for annotation in attributes["annotations"]:
                    if annotation.get("supercategory") != "object" or annotation.get("category_id") not in (1, 2):
                        continue
                    box, position = annotation.get("bbox_image", {}), annotation.get("bbox_pitch", {})
                    x, y = position.get("x_bottom_middle"), position.get("y_bottom_middle")
                    if x is None or y is None or not -52.5 <= x <= 52.5 or not -34 <= y <= 34:
                        continue
                    foot = [box["x"] + box["w"] / 2, box["y"] + box["h"], 1]
                    if not 0 <= foot[0] < row["width"] or not 0 <= foot[1] < row["height"] - 1:
                        continue
                    projected = np.asarray(calibration.homography) @ foot
                    if abs(projected[2]) < 1e-9:
                        continue
                    metric = projected[:2] / projected[2] * [105, 68] - [52.5, 34]
                    differences.append(float(np.linalg.norm(metric - [x, y])))
                record["provider_player_position_differences_m"] = differences
                errors_m.extend(differences)
                if row["game_id"] not in previews:
                    image = root / row["image"]
                    if sha256_file(image) != row["image_sha256"]:
                        raise ValueError("Source image changed.")
                    rendered = calibrated_field_preview(cv2.imread(str(image)), calibration)
                    preview = output / f"{row['frame_id']}-{side}.jpg"
                    cv2.imwrite(str(preview), rendered, [cv2.IMWRITE_JPEG_QUALITY, 93])
                    record["preview"] = preview.name
                    previews.add(row["game_id"])
            except (PipelineError, ValueError, np.linalg.LinAlgError) as exc:
                record.update(status="rejected", reason=str(exc))
            results.append(record)
        print(f"Geometry {clip}: {len(results)}/{len(groups)*2} clip/side cases", flush=True)
    counts = dict(Counter(r["status"] for r in results))
    result = {"protocol": protocol, "counts": counts, "cases": results,
              "passed_without_all_field_corners_visible": sum(r["status"] == "passed" and not r["all_full_field_corners_visible"] for r in results),
              "provider_position_comparison": {"objects": len(errors_m),
                  "median_m": float(np.median(errors_m)) if errors_m else None,
                  "p90_m": float(np.quantile(errors_m, 0.9)) if errors_m else None,
                  "scope": "Agreement with provider box ground positions, not independent measured positional accuracy."}}
    write_json(output / "summary.json", result)
    print({"counts": counts, "newly_supported_cases": result["passed_without_all_field_corners_visible"],
           "provider_position_comparison": result["provider_position_comparison"]}, flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("data/broadcast-sngsr-v1"))
    parser.add_argument("--output", type=Path, default=Path("reports/partial-calibration-v1"))
    args = parser.parse_args()
    audit(args.root, args.output)
