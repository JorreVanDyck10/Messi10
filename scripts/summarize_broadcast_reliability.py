"""Assemble current-profile runtime and provider-line development evidence."""

from pathlib import Path

from evaluate_temporal_broadcast import summarize

from football_pipeline.contracts import digest_json, read_json, sha256_file, write_json

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts/broadcast-reliability-20261030"
REPORTS = ROOT / "reports/broadcast-reliability-20261030"


def count_stats(rows):
    frames = [f for row in rows for f in row["counts"]["per_frame"]]
    available = [f for f in frames if f["predicted_players"] is not None]
    deltas = [f["predicted_players"] - f["reference_players"] for f in available]
    return {
        "frames": len(frames),
        "available": len(available),
        "unavailable": len(frames) - len(available),
        "mean_absolute_error_when_available": sum(abs(d) for d in deltas) / len(deltas) if deltas else None,
        "bias_when_available": sum(deltas) / len(deltas) if deltas else None,
        "exact_frames": sum(d == 0 for d in deltas),
        "exact_fraction_when_available": sum(d == 0 for d in deltas) / len(deltas) if deltas else None,
    }


def metrics(rows):
    result = summarize(rows)
    for split in ("train", "val"):
        selected = [row for row in rows if row["split"] == split]
        result[split]["counts"] = count_stats(selected)
        result[split]["reference_player_observations"] = sum(r["teams"]["total"] for r in selected)
        result[split]["goalkeepers_correct_team"] = sum(r["teams"]["goalkeepers_correct"] for r in selected)
        result[split]["goalkeepers_wrong_team"] = sum(r["teams"]["goalkeepers_wrong"] for r in selected)
    return result


def main():
    sources = {
        "automatic": [ARTIFACTS / "runtime-default-first-v1", ARTIFACTS / "runtime-extension-automatic-v1"],
        "provider": [ARTIFACTS / "runtime-provider-baseline-v1", ARTIFACTS / "runtime-extension-provider-v1"],
    }
    results = {}
    provenance = {}
    for geometry, roots in sources.items():
        rows = []
        for directory in roots:
            path = directory / "runtime-metrics.json"
            provenance[str(path.relative_to(ROOT))] = sha256_file(path)
            rows.extend(read_json(path)["per_clip"])
        results[geometry] = {
            "all_windows": metrics(rows),
            "per_window": {
                window: metrics(
                    [
                        r
                        for r in rows
                        if (
                            "middle"
                            if r["clip"].endswith("-middle")
                            else "last"
                            if r["clip"].endswith("-last")
                            else "first"
                        )
                        == window
                    ]
                )
                for window in ("first", "middle", "last")
            },
            "per_game": {
                game: metrics([r for r in rows if r["game_id"] == game])
                for game in sorted({r["game_id"] for r in rows})
            },
            "per_clip": rows,
        }
    audit = read_json(ARTIFACTS / "release-rank-audit-v1/metrics.json")["per_clip"]
    if any(r["projection_changes"] for r in audit if r["window"] != "first"):
        raise ValueError("Later rank-policy observations cannot be reused for the restored default")
    geometry = {}
    for split in ("train", "val"):
        selected = [r for r in audit if r["split"] == split]
        keys = (
            "frames",
            "correct",
            "wrong",
            "unavailable",
            "unscored_valid",
            "no_field_reference",
            "unsupported_field_reference",
        )
        geometry[split] = {key: sum(r["before"].get(key, 0) for r in selected) for key in keys}
        geometry[split]["reference_eligible_frames"] = sum(
            geometry[split][k] for k in ("correct", "wrong", "unavailable", "unscored_valid")
        )
    profile = read_json(ROOT / "configs/models-broadcast.json")
    if "field_settings" in profile:
        raise ValueError("Report expects the restored original field default")
    keeper_references = sum(
        p.get("goalkeeper", False) and p["role"] == "player" and p["on_pitch"]
        for version in (1, 2)
        for row in read_json(ROOT / f"data/broadcast-temporal-v{version}/manifest.json")["frames"]
        if row["split"] == "val"
        for p in row["people"]
    )
    result = {
        "active_profile_sha256": sha256_file(ROOT / "configs/models-broadcast.json"),
        "active_field_policy": "DEFAULT_SETTINGS; two_semantic_tertiles_no_refit; unless explicitly overridden",
        "model_weights_changed": False,
        "metrics": results,
        "field_reference_tolerance": geometry,
        "field_reference_per_clip": audit,
        "source_scores_sha256": provenance,
        "source_sha256": sha256_file(__file__),
        "dataset_fingerprints": [
            read_json(ROOT / f"data/broadcast-temporal-v{v}/manifest.json")["fingerprint"] for v in (1, 2)
        ],
        "dataset_frames": 2700,
        "validation_frames": 1350,
        "validation_games": 3,
        "validation_goalkeeper_observations": keeper_references,
        "tracking_scope": "Separate continuous6-secondwindows; no identity continuity across gaps or full-game claim",
        "later_automatic_reuse": "Previously computed rank-policy detector observations reused only after exact equality of every projection input to restoredDEFAULT was verified on all1800laterframes",
        "tolerance_definition": "Provider straight-line reprojection median<=0.5% and maximum<=1% of source image diagonal; automatic benchmark on assumed105x68template; not a human error classification or a distance-accuracy measurement",
        "limitations": [
            "Previously reused development matches; not independent final test",
            "Frames repeat the same players; player observations are not unique people",
            "Count error excludes unavailable calibration and can conceal cancellation of false positives and missed players",
            "Ownclip:251/1239valid under original field policy; accuracy and physical distances unverified",
            "31fieldreferences (5first-window,26later) outside supported border preprocessing remain unscored; recognition/tracking keeps every frame",
        ],
        "human_review_completed": False,
        "independent_final_test_completed": False,
        "targets_met": False,
    }
    result["evidence_digest"] = digest_json(result)
    write_json(REPORTS / "summary.json", result)
    print({g: d["all_windows"]["val"] for g, d in results.items()}, flush=True)
    print("Field tolerance", geometry, flush=True)


if __name__ == "__main__":
    main()
