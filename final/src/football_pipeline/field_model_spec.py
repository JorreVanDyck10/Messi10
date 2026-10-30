"""Pinned model provenance; dependency-free so the setup can bootstrap a clean machine."""

UPSTREAM_URL = "https://github.com/mguti97/PnLCalib"
UPSTREAM_REVISION = "8c87391d6f4ea40c5e4d65e61529916c7a49ce62"
RELEASE_WEIGHTS = {
    "keypoints": {
        "name": "SV_kp",
        "sha256": "7ea78fa76aaf94976a8eca428d6e3c59697a93430cba1a4603e20284b61f5113",
    },
    "lines": {
        "name": "SV_lines",
        "sha256": "d72f4ed71734a2e3df9fa084f666e9b8adaef21bf69bac8952d6d3f970ff7455",
    },
}


def validate_runtime_models(runtime):
    """Accept pinned releases or traceable local fine-tunes, always verifying actual bytes."""
    import hashlib
    import json
    import re
    from pathlib import Path

    def checksum(path):
        with Path(path).open("rb") as stream:
            return hashlib.file_digest(stream, "sha256").hexdigest()

    if set(runtime.get("models", {})) != set(RELEASE_WEIGHTS):
        raise ValueError("Both field model roles are required")
    for role, expected in RELEASE_WEIGHTS.items():
        model = runtime["models"][role]
        key = "weights_keypoints" if role == "keypoints" else "weights_lines"
        if Path(runtime[key]).resolve() != Path(model["path"]).resolve():
            raise ValueError("Runtime model paths disagree")
        if not re.fullmatch(r"[a-f0-9]{64}", str(model.get("sha256", ""))):
            raise ValueError("Missing model hash")
        if checksum(model["path"]) != model["sha256"]:
            raise ValueError("Weight hash mismatch")
        if model.get("kind", "release") == "release":
            if model["name"] != expected["name"] or model["sha256"] != expected["sha256"]:
                raise ValueError("Unexpected release weights")
        elif model.get("kind") == "finetuned":
            if model.get("base_model") != expected or not re.fullmatch(
                r"[a-f0-9]{64}", str(model.get("dataset_fingerprint", ""))
            ):
                raise ValueError("Fine-tuned model lacks base model/dataset lineage")
            report_path = Path(model["training_report"])
            if checksum(report_path) != model["training_report_sha256"]:
                raise ValueError("Training report changed")
            report = json.loads(report_path.read_text(encoding="utf-8"))
            saved = report.get("models", {}).get(role, {})
            if (
                report.get("status") != "complete"
                or saved.get("status") != "complete"
                or saved.get("sha256") != model["sha256"]
                or report.get("dataset_fingerprint") != model["dataset_fingerprint"]
                or report.get("is_smoke_test") != model.get("is_smoke_test")
            ):
                raise ValueError("Fine-tuned model does not match a completed training report")
        else:
            raise ValueError("Unsupported field model kind")
