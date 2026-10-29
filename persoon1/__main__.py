"""Start de datacommandos via python -m persoon1 en geeft argumenten aan de juiste werkstap door."""

import argparse
import json
import sys
from pathlib import Path

from .core import canonical_hash, environment, now, read_json, require_approval, sha256, validate_dataset, write_json


def parser():
    """Bouw de commandoregelparser met afzonderlijke subcommando's en argumenten voor data, annotatie,
    training en evaluatie.
    """
    root = argparse.ArgumentParser(description="Persoon 1: data, annotation, training and evaluation")
    sub = root.add_subparsers(dest="command", required=True)
    p = sub.add_parser("doctor", help="Record actual hardware and installed software")
    p.add_argument("--output", default="reports/environment.json")
    p = sub.add_parser("inspect-video", help="Inspect actual presentation timestamps")
    p.add_argument("--video", required=True)
    p.add_argument("--output", required=True)
    p = sub.add_parser("extract", help="Extract explicit source windows without creating final labels")
    p.add_argument("--video", required=True)
    p.add_argument("--plan", required=True)
    p.add_argument("--output", required=True)
    p = sub.add_parser("validate", help="Check labels, groups, duplicate images and reviews")
    p.add_argument("--manifest", required=True)
    p.add_argument("--output", required=True)
    p.add_argument("--require-review", action="store_true")
    p = sub.add_parser("predict", help="Export automatic proposals, overlays and detector handoff")
    p.add_argument("--manifest", required=True)
    p.add_argument("--weights", required=True)
    p.add_argument("--mapping", required=True)
    p.add_argument("--output", required=True)
    p.add_argument("--split", choices=["train", "val", "test"], default="val")
    p.add_argument("--imgsz", type=int, default=640)
    p.add_argument("--device", default="0")
    p.add_argument("--confidence", type=float, default=0.001)
    p.add_argument("--freeze")
    p.add_argument("--approvals")
    p = sub.add_parser("annotate", help="Local assisted box annotation and independent review")
    p.add_argument("--manifest", required=True)
    p.add_argument("--proposals")
    p.add_argument("--split", choices=["train", "val", "test", "all"], default="train")
    p.add_argument("--port", type=int, default=8765)
    p = sub.add_parser("train", help="Train after real dataset and team review")
    p.add_argument("--manifest", required=True)
    p.add_argument("--approvals", required=True)
    p.add_argument("--config", default="configs/train-reference.json")
    p.add_argument("--weights", required=True)
    p.add_argument("--output", required=True)
    p.add_argument("--device", default="0")
    p.add_argument("--smoke", action="store_true")
    p.add_argument("--provisional-ai-labels", action="store_true", help="Explicit provisional experiment; does not count as human team review")
    p = sub.add_parser("evaluate", help="Score mapped predictions and produce FP/FN records")
    p.add_argument("--manifest", required=True)
    p.add_argument("--predictions", required=True)
    p.add_argument("--output", required=True)
    p.add_argument("--work-confidence", type=float, default=0.25)
    p.add_argument("--freeze")
    p.add_argument("--approvals")
    p.add_argument("--provisional-ai-labels", action="store_true")
    p = sub.add_parser("freeze", help="Freeze model, dataset and inference before independent test")
    p.add_argument("--manifest", required=True)
    p.add_argument("--approvals", required=True)
    p.add_argument("--weights", required=True)
    p.add_argument("--inference", required=True, help="Completed development run.json")
    p.add_argument("--output", required=True)
    p = sub.add_parser("compare", help="Compare evaluations only when conditions are equivalent")
    p.add_argument("--baseline", required=True)
    p.add_argument("--candidate", required=True)
    p.add_argument("--output", required=True)
    return root


def execute(args):
    """Vertaal het geparsete subcommando naar de bijbehorende datastap en controleer bij vergelijkingen
    dat meetmethoden en bronidentiteiten aansluiten.
    """
    if args.command == "doctor":
        result = environment()
        write_json(args.output, result)
        return result
    if args.command == "inspect-video":
        from .video import inspect_video
        return inspect_video(args.video, args.output)
    if args.command == "extract":
        from .video import extract
        return extract(args.video, args.plan, args.output)
    if args.command == "validate":
        result = validate_dataset(args.manifest, require_review=args.require_review)
        write_json(args.output, result)
        if result["errors"]:
            print(json.dumps({"error_count": len(result["errors"]), "warning_count": len(result["warnings"]),
                              "first_errors": result["errors"][:5], "counts": result["counts"],
                              "complete_report": args.output}, indent=2, ensure_ascii=False))
            raise ValueError("Dataset validation failed; see the recorded report")
        return result
    if args.command == "predict":
        from .modeling import predict_manifest
        return predict_manifest(args.manifest, args.weights, args.mapping, args.output, args.split,
                                args.imgsz, args.device, args.confidence, args.freeze, args.approvals)
    if args.command == "annotate":
        from .annotation import serve
        return serve(args.manifest, args.proposals, args.split, args.port)
    if args.command == "train":
        from .modeling import train
        return train(args.manifest, args.approvals, args.config, args.weights, args.output, args.device, args.smoke, args.provisional_ai_labels)
    if args.command == "evaluate":
        from .modeling import evaluate_run
        return evaluate_run(args.manifest, args.predictions, args.output, args.work_confidence, args.freeze, args.approvals, args.provisional_ai_labels)
    if args.command == "freeze":
        report = require_approval(args.manifest, args.approvals)
        run = read_json(args.inference)
        if run.get("split") == "test" or run["weights_sha256"] != sha256(args.weights):
            raise ValueError("Use a development inference run for the selected exact weights")
        if run["manifest_sha256"] != sha256(args.manifest):
            raise ValueError("Development inference belongs to a different manifest")
        result = {"created_at": now(), "dataset_fingerprint": report["dataset_fingerprint"],
                  "weights_sha256": sha256(args.weights), "inference_config_hash": canonical_hash(run["config"]),
                  "inference_config": run["config"], "environment": environment()}
        target = Path(args.output)
        if target.exists() or target.with_suffix(".test-access.jsonl").exists():
            raise ValueError("Freeze already exists or was exposed; do not overwrite")
        write_json(target, result)
        return result
    if args.command == "compare":
        a, b = read_json(args.baseline), read_json(args.candidate)
        for key in ("method", "split", "manifest_sha256", "label_fingerprint", "workpoint", "review_policy"):
            if a[key] != b[key]:
                raise ValueError(f"Not a comparable evaluation: {key}")
        if [c["name"] for c in a["per_class"]] != [c["name"] for c in b["per_class"]]:
            raise ValueError("Evaluated class meanings differ")
        for key in ("imgsz", "confidence", "nms_iou", "max_det"):
            if a["inference_config"][key] != b["inference_config"][key]:
                raise ValueError(f"Inference conditions differ: {key}")
        result = {"recorded_at": now(), "baseline": args.baseline, "candidate": args.candidate,
                  "deltas": {k: b[k] - a[k] if a[k] is not None and b[k] is not None else None for k in ("mAP50", "mAP50_95")},
                  "conclusion": "Requires error examples, sample-size assessment and review; no automatic improvement claim"}
        write_json(args.output, result)
        return result


def main():
    """Parse de opdracht, voer de gekozen werkstap uit en vertaal bekende invoerfouten naar een leesbare
    melding en procesexitcode.
    """
    try:
        result = execute(parser().parse_args())
        if result is not None:
            print(json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False))
    except (ValueError, OSError, KeyError, ImportError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
