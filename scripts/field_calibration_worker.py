"""PnLCalib network adapter. Execute with .tools/pnlcalib-env, never the player-training venv.

Upstream networks and heatmap extraction are imported from the pinned external GPL-2.0 checkout.
This adapter uses ground keypoints plus independent line-network consistency, not PnL 3D refinement.
"""

from __future__ import annotations

import argparse
import importlib.metadata
import json
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from football_pipeline.contracts import sha256_file, write_json  # noqa: E402
from football_pipeline.field_layout import (  # noqa: E402
    COORDINATE_SYSTEM,
    LINES_UV,
    POINTS_UV,
    POLICY,
    UPSTREAM_REVISION,
    UPSTREAM_URL,
)
from football_pipeline.field_model_spec import validate_runtime_models  # noqa: E402


def main():
    """Laad PnLCalib in zijn eigen omgeving, verwerk de bronframes en schrijf herleidbare punten- en
    lijnwaarnemingen.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--video", type=Path, required=True)
    parser.add_argument("--runtime", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--source", required=True)
    parser.add_argument("--usage", required=True)
    parser.add_argument("--fps-num", type=int, required=True)
    parser.add_argument("--fps-den", type=int, required=True)
    parser.add_argument("--frames", type=int, required=True)
    args = parser.parse_args()
    adapter_sources = {
        str(p): sha256_file(p)
        for p in (
            Path(__file__),
            ROOT / "src/football_pipeline/field_layout.py",
            ROOT / "src/football_pipeline/field_model_spec.py",
            ROOT / "src/football_pipeline/automatic_calibration.py",
        )
    }
    worker_hash = adapter_sources[str(Path(__file__))]
    if not args.source.strip() or not args.usage.strip():
        parser.error("Bron en toegelaten gebruik zijn vereist.")
    runtime = json.loads(args.runtime.read_text(encoding="utf-8"))
    repository = Path(runtime["repository"])
    revision = subprocess.check_output(["git", "-C", str(repository), "rev-parse", "HEAD"], text=True).strip()
    if revision != UPSTREAM_REVISION or runtime["upstream"]["url"] != UPSTREAM_URL:
        raise ValueError("Unexpected upstream revision")
    for name, expected in runtime["source_sha256"].items():
        if sha256_file(repository / name) != expected:
            raise ValueError(f"Upstream source changed: {name}")
    validate_runtime_models(runtime)
    if sha256_file(repository / "LICENSE") != runtime["upstream"]["license_sha256"]:
        raise ValueError("Upstream license changed")
    sys.path.insert(0, str(repository))
    import cv2
    import torch
    import torchvision.transforms.functional as tvf
    import yaml
    from model.cls_hrnet import get_cls_net
    from model.cls_hrnet_l import get_cls_net as get_line_net
    from utils.utils_heatmap import (
        coords_to_dict,
        get_keypoints_from_heatmap_batch_maxpool,
        get_keypoints_from_heatmap_batch_maxpool_l,
    )

    from football_pipeline.automatic_calibration import estimate_frame

    started = time.perf_counter()
    device = runtime["device"]
    if device.startswith("cuda") and not torch.cuda.is_available():
        raise ValueError("CUDA niet beschikbaar. Configureer --device cpu bij setup_field_model.py.")
    torch.set_num_threads(4)
    models = []
    for constructor, config, weights in (
        (get_cls_net, "hrnetv2_w48.yaml", runtime["weights_keypoints"]),
        (get_line_net, "hrnetv2_w48_l.yaml", runtime["weights_lines"]),
    ):
        with (repository / "config" / config).open() as stream:
            model = constructor(yaml.safe_load(stream))
        model.load_state_dict(torch.load(weights, map_location="cpu", weights_only=True))
        models.append(model.to(device).eval())
    capture = cv2.VideoCapture(str(args.video))
    width, height = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH)), int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
    count, statuses = 0, Counter()
    args.output.mkdir(parents=True, exist_ok=True)
    temporary = args.output / "observations.partial.jsonl"
    inference_s = 0.0
    try:
        with temporary.open("w", encoding="utf-8") as stream, torch.inference_mode():
            while True:
                ok, frame = capture.read()
                if not ok:
                    break
                if frame.shape[:2] != (height, width):
                    raise ValueError("Video dimensions changed")
                tick = time.perf_counter()
                image = tvf.to_tensor(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)).unsqueeze(0)
                image = tvf.resize(image, [540, 960], antialias=True).to(device)
                keypoints = coords_to_dict(
                    get_keypoints_from_heatmap_batch_maxpool(models[0](image)[:, :-1]),
                    threshold=float("-inf"),
                    ground_plane_only=True,
                )[0]
                lines = coords_to_dict(
                    get_keypoints_from_heatmap_batch_maxpool_l(models[1](image)[:, :-1]),
                    threshold=float("-inf"),
                    ground_plane_only=True,
                )[0]
                points = [
                    {
                        "id": k,
                        "x": p["x"] * width / 960,
                        "y": p["y"] * height / 540,
                        "confidence": min(1.0, max(0.0, p["p"])),
                        "raw_score": p["p"],
                    }
                    for k, p in keypoints.items()
                    if k in POINTS_UV
                ]
                detected_lines = [
                    {
                        "id": k,
                        "xy": [
                            [p["x_1"] * width / 960, p["y_1"] * height / 540],
                            [p["x_2"] * width / 960, p["y_2"] * height / 540],
                        ],
                        "confidence": min(1.0, max(0.0, min(p["p_1"], p["p_2"]))),
                        "raw_scores": [p["p_1"], p["p_2"]],
                    }
                    for k, p in lines.items()
                    if k in LINES_UV
                ]
                row = {
                    "frame_index": count,
                    "timestamp_s": count * args.fps_den / args.fps_num,
                    "image_size": [width, height],
                    "points": points,
                    "lines": detected_lines,
                }
                inference_s += time.perf_counter() - tick
                statuses[estimate_frame(row, (width, height))["status"]] += 1
                stream.write(json.dumps(row, allow_nan=False) + "\n")
                count += 1
                if count % 10 == 0:
                    print(f"{count}/{args.frames} frames", flush=True)
        if count != args.frames:
            raise ValueError(f"Decoded {count} frames, expected {args.frames}")
        observations = args.output / "observations.jsonl"
        temporary.replace(observations)
        dependencies = {
            name: importlib.metadata.version(name)
            for name in ("torch", "torchvision", "numpy", "opencv-python", "scipy", "PyYAML")
        }
        if any(sha256_file(p) != expected for p, expected in adapter_sources.items()):
            raise ValueError("Adapter source changed during inference; rerun with a stable source tree")
        manifest = {
            "schema_version": 2,
            "score_storage": "all_ground_peaks_before_threshold",
            "evidence_kind": "pnlcalib",
            "kind": "automatic_field_observations",
            "coordinate_system": COORDINATE_SYSTEM,
            "video": {
                "sha256": sha256_file(args.video),
                "image_size": [width, height],
                "frame_count": count,
                "fps_num": args.fps_num,
                "fps_den": args.fps_den,
            },
            "source": args.source.strip(),
            "usage": args.usage.strip(),
            "policy": POLICY,
            "upstream": runtime["upstream"],
            "upstream_source_sha256": runtime["source_sha256"],
            "models": runtime["models"],
            "dependencies": dependencies,
            "pip_freeze": runtime["pip_freeze"],
            "worker_sha256": worker_hash,
            "adapter_sha256": adapter_sources,
            "observations_sha256": sha256_file(observations),
            "template": {
                "length": 105,
                "width": 68,
                "units": "assumed_template_not_measured",
                "orientation": POLICY["orientation"],
            },
            "measurements": {
                "runtime_s": time.perf_counter() - started,
                "inference_s": inference_s,
                "frames": count,
                "status_counts": dict(statuses),
                "usable_fraction": statuses["valid"] / count if count else 0,
                "device": device,
                "gpu": torch.cuda.get_device_name(device) if device.startswith("cuda") else None,
            },
            "human_evaluation": "pending",
            "independent_accuracy_claim": False,
        }
        write_json(args.output / "automatic_calibration.json", manifest)
        print(json.dumps(manifest["measurements"]), flush=True)
    finally:
        capture.release()


if __name__ == "__main__":
    main()
