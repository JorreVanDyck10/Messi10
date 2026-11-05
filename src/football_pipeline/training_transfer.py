"""Verified, local training-data transfers without copying virtual environments."""

from __future__ import annotations

import argparse
import json
import shutil
import zipfile
from pathlib import Path, PurePosixPath, PureWindowsPath

from .contracts import PipelineError, read_json, sha256_file, write_json
from .training_workbench import default_inputs, local_path
from .video import ROOT


def imported_source_root(root=ROOT):
    """Lees de oorspronkelijke bronroot uit een datapakket of de repositorycatalogus."""
    path = root / ".cache/training-import.json"
    if path.exists():
        return read_json(path)["source_root"]
    catalog = root / "datasets/training-runtime-v1/manifest.json"
    return read_json(catalog)["source_root"] if catalog.exists() else str(root)


def rebase(value, source_root, root=ROOT):
    """Rebind only absolute workspace paths; never guess a missing file by basename."""
    if isinstance(value, dict):
        return {k: rebase(v, source_root, root) for k, v in value.items()}
    if isinstance(value, list):
        return [rebase(v, source_root, root) for v in value]
    if isinstance(value, str):
        normalized, prefix = value.replace("\\", "/"), str(source_root).replace("\\", "/").rstrip("/")
        if normalized.casefold().startswith(prefix.casefold() + "/"):
            relative = normalized[len(prefix) + 1 :]
            parts = PurePosixPath(relative).parts
            if ".." in parts or PureWindowsPath(relative).is_absolute():
                raise PipelineError("Ongeldig werkruimtepad in trainingsdata")
            return str(root.joinpath(*parts).resolve())
    return value


def export_bundle(output, inputs, root=ROOT):
    """Verpak benodigde trainingsbeelden, labels, kenmerken en startgewichten met controlehashes."""
    from .detection import load_model_manifest

    files = set()

    def add(path):
        """Registreer alleen een bestaand trainingsbestand binnen de projectmap."""
        path = Path(path).resolve()
        if not path.is_relative_to(root.resolve()) or not path.is_file():
            raise PipelineError(f"Trainingsbestand ontbreekt of ligt buiten dit project: {path}")
        files.add(path)

    for key, value in inputs.items():
        path = local_path(value, root)
        if not path.exists():
            raise PipelineError(f"Trainingsbron ontbreekt: {key} ({path})")
        if path.is_dir():
            for p in path.rglob("*"):
                if p.is_file() and p.suffix.lower() in {
                    ".jpg",
                    ".jpeg",
                    ".png",
                    ".txt",
                    ".json",
                    ".yaml",
                    ".yml",
                    ".gz",
                }:
                    add(p)
        else:
            add(path)
    # Frozen field indices can point to original images outside the index directory.
    field = read_json(local_path(inputs["field"], root))
    source_root = imported_source_root(root)
    for row in rebase(field["frames"], source_root, root):
        add(row["image"])
        add(row["label"])
    # Appearance features retain their original image provenance and encoder state.
    import torch

    appearance = torch.load(local_path(inputs["appearance"], root), map_location="cpu", weights_only=True)
    for row in rebase(appearance["rows"], source_root, root):
        add(row["image"])
    models = load_model_manifest(local_path(inputs["profile"], root))
    for spec in models["models"] + [
        models[k] for k in ("appearance", "kit_embedding", "role_context") if k in models
    ]:
        add(spec["weights"])
    if inputs.get("andrew_dataset"):
        source = local_path(inputs["andrew_dataset"], root)
        for row in rebase(read_json(source / "manifest.json")["frames"], source_root, root):
            for key in ("image", "label"):
                path = Path(row[key])
                add(path if path.is_absolute() else source / path)
    if inputs.get("andrew_profile"):
        for spec in load_model_manifest(local_path(inputs["andrew_profile"], root))["models"]:
            add(spec["weights"])
    ball_profile = root / "configs/models-ball-broadcast-v3.json"
    if ball_profile.exists():
        add(ball_profile)
        for spec in load_model_manifest(ball_profile)["models"]:
            add(spec["weights"])
    names = {p.relative_to(root.resolve()).as_posix(): sha256_file(p) for p in sorted(files)}
    portable_inputs = {
        key: local_path(value, root).relative_to(root.resolve()).as_posix() for key, value in inputs.items()
    }
    manifest = {
        "schema_version": 1,
        "source_root": source_root,
        "inputs": portable_inputs,
        "files": names,
        "contains_environments": False,
        "human_review_completed": False,
    }
    output = Path(output).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists():
        raise PipelineError("Kies een nieuwe pakketnaam; een bestaand pakket wordt behouden")
    temporary = output.with_suffix(".partial.zip")
    with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_STORED, allowZip64=True) as archive:
        archive.writestr("training-transfer.json", json.dumps(manifest, ensure_ascii=False))
        for i, p in enumerate(sorted(files)):
            archive.write(p, "payload/" + p.relative_to(root.resolve()).as_posix())
            if i % 250 == 0:
                print(f"Pakket {i + 1}/{len(files)} bestanden", flush=True)
    temporary.replace(output)
    return manifest


def import_bundle(source, root=ROOT):
    """Controleer een data- of modelpakket en importeer zonder afwijkende bestaande bestanden te overschrijven."""
    with zipfile.ZipFile(source) as archive:
        info = archive.getinfo("training-transfer.json")
        if info.file_size > 16 * 1024**2:
            raise PipelineError("Pakketmanifest is te groot")
        manifest = json.loads(archive.read(info))
        if manifest.get("schema_version") != 1:
            raise PipelineError("Onbekend trainingspakket")
        targets = []
        for name, checksum in manifest["files"].items():
            parts = PurePosixPath(name).parts
            if (
                not parts
                or parts[0]
                not in {
                    "data",
                    "datasets",
                    "assets",
                    "artifacts",
                    "configs",
                    "models",
                    "weights",
                    "Andrew_Prototype",
                }
                or ".." in parts
                or "\\" in name
                or ":" in name
                or PurePosixPath(name).is_absolute()
                or Path(name).suffix.lower() in {".py", ".ps1", ".exe", ".bat", ".dll"}
            ):
                raise PipelineError("Onveilig of uitvoerbaar bestand in trainingspakket")
            target = root.joinpath(*parts).resolve()
            if not target.is_relative_to(root.resolve()):
                raise PipelineError("Pakketpad valt buiten het project")
            member = archive.getinfo("payload/" + name)
            if target.exists() and sha256_file(target) != checksum:
                raise PipelineError(f"Bestaand bestand verschilt en wordt behouden: {target}")
            targets.append((member, target, checksum))
        for member, target, checksum in targets:
            if target.exists():
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            temporary = target.with_name(target.name + ".transfer-partial")
            with archive.open(member) as src, temporary.open("wb") as dst:
                shutil.copyfileobj(src, dst, 1024**2)
            if sha256_file(temporary) != checksum:
                temporary.unlink()
                raise PipelineError(f"Pakketcontrole mislukt: {target}")
            temporary.replace(target)
    (root / ".cache").mkdir(exist_ok=True)
    write_json(
        root / (".cache/model-import-" + sha256_file(source)[:12] + ".json")
        if manifest.get("kind") == "models"
        else root / ".cache/training-import.json",
        {
            "source_root": manifest["source_root"],
            "inputs": manifest["inputs"],
            "archive_sha256": sha256_file(source),
            "verified_files": len(targets),
        },
    )
    if manifest.get("kind") == "models":
        from .detection import load_model_manifest

        tag = sha256_file(source)[:12]
        for kind, relative in manifest.get("profiles", {}).items():
            original = root / relative
            rebound = rebase(read_json(original), manifest["source_root"], root)
            prefix = "models-andrew" if kind == "andrew" else "models" if kind == "models" else "field"
            destination = root / "configs" / f"{prefix}-imported-{tag}.json"
            if kind in {"models", "andrew"}:
                rebound["profile_name"] = (
                    "Andrew · " if kind == "andrew" else ""
                ) + "Geïmporteerde trainingskandidaten · evaluatie nodig"
            destination.parent.mkdir(parents=True, exist_ok=True)
            write_json(destination, rebound)
            if kind in {"models", "andrew"}:
                load_model_manifest(destination)
            print(f"Proefprofiel, niet geactiveerd: {destination}", flush=True)
        merge_imported_models(manifest, root)
    return len(targets)


def merge_imported_models(manifest, root=ROOT):
    """Merge only the trained components; invalidate incompatible context heads."""
    from .detection import load_model_manifest

    completed = set(manifest.get("completed", []))
    if not completed:
        return
    profiles = manifest.get("profiles", {})
    model_tasks = completed & {"players", "ball", "roles", "shirt", "context"}
    if model_tasks and "models" in profiles:
        shared = root / "configs/models-shared-candidate.json"
        current = load_model_manifest(shared if shared.exists() else root / "configs/models-broadcast.json")
        incoming = rebase(read_json(root / profiles["models"]), manifest["source_root"], root)
        for task, semantic in (("players", "player"), ("ball", "ball")):
            if task in completed:
                updated = [m for m in incoming["models"] if semantic in m["class_mapping"].values()]
                if updated:
                    ordered, inserted = [], False
                    for model in current["models"]:
                        if semantic in model["class_mapping"].values():
                            if not inserted:
                                ordered.extend(updated)
                                inserted = True
                        else:
                            ordered.append(model)
                    current["models"] = ordered if inserted else ordered + updated
        for task, key in (("roles", "appearance"), ("shirt", "kit_embedding"), ("context", "role_context")):
            if task in completed and key in incoming:
                current[key] = incoming[key]
        if current.get("role_context"):
            import torch

            context = torch.load(current["role_context"]["weights"], map_location="cpu", weights_only=True)
            if (
                context["teacher_sha256"] != current["appearance"]["weights_sha256"]
                or context["kit_weights_sha256"] != current["kit_embedding"]["weights_sha256"]
            ):
                current.pop("role_context")
                print(
                    "Context weggelaten: train context opnieuw met het gecombineerde rol- en shirtmodel.",
                    flush=True,
                )
        current["profile_name"] = "Gezamenlijke trainingskandidaten · evaluatie nodig"
        current["handoff"] = {
            "human_review_completed": False,
            "independent_final_test_completed": False,
            "targets_met": False,
            "scope": "Merged training components; evaluation required",
        }
        write_json(shared, current)
        load_model_manifest(shared)
        print(f"Samengevoegd proefprofiel, niet geactiveerd: {shared}", flush=True)
    if completed & {"field_points", "field_lines"} and "field" in profiles:
        from .field_model_spec import validate_runtime_models

        shared = root / "configs/field-shared-candidate.json"
        current = read_json(shared if shared.exists() else root / ".tools/field-runtime.json")
        incoming = rebase(read_json(root / profiles["field"]), manifest["source_root"], root)
        for task, role in (("field_points", "keypoints"), ("field_lines", "lines")):
            if task in completed:
                current["models"][role] = incoming["models"][role]
                current["weights_" + role] = incoming["weights_" + role]
        current.update(schema_version=2, automatic_promotion=False)
        validate_runtime_models(current)
        write_json(shared, current)
        print(f"Samengevoegd veldproefprofiel, niet geactiveerd: {shared}", flush=True)


def export_models(output, job, root=ROOT):
    """Share only checkpoints, required start weights and their provenance."""
    files = set()
    profiles = {}

    def add(path):
        """Registreer een bestaand modelbestand binnen de projectmap voor de gewichtsoverdracht."""
        path = Path(path).resolve()
        if not path.is_relative_to(root.resolve()) or not path.is_file():
            raise PipelineError(f"Modelbestand ontbreekt of ligt buiten het project: {path}")
        files.add(path)

    def profile_files(path):
        """Verzamel een kandidaatprofiel met alle bijbehorende gewichten en trainingsrapporten."""
        add(path)
        data = read_json(path)
        specs = data.get("models", [])
        specs = list(specs.values()) if isinstance(specs, dict) else specs
        specs += [data[k] for k in ("appearance", "kit_embedding", "role_context") if k in data]
        for spec in specs:
            weight = spec.get("weights", spec.get("path"))
            if weight:
                add(path.parent / weight)
            if spec.get("training_report"):
                add(spec["training_report"])

    job = Path(job).resolve()
    if not job.is_relative_to((root / "artifacts/training-workbench").resolve()):
        raise PipelineError("Onbekende trainingsronde")
    status = read_json(job / "job.json")
    if status["status"] in {"starting", "running"} or not status.get("completed"):
        raise PipelineError("Laat minstens één model afronden en stop de ronde vóór export")
    for kind, name in (
        ("models", "candidate-profile.json"),
        ("field", "candidate-field-runtime.json"),
        ("andrew", "andrew/candidate-profile.json"),
    ):
        path = job / name
        if path.exists():
            profile_files(path)
            profiles[kind] = path.relative_to(root.resolve()).as_posix()
    add(job / "job.json")
    add(job / "spec.json")
    for task in status["completed"]:
        result = job / task / "result.json"
        add(result)
        target = Path(read_json(result)["weights"])
        if target.suffix == ".json":
            profile_files(target)
        else:
            add(target)
        for name in ("metrics.json", "training-report.json", "status.json"):
            path = target.parent / name
            if path.is_file():
                add(path)
    manifest = {
        "schema_version": 1,
        "kind": "models",
        "completed": status["completed"],
        "source_root": str(root.resolve()),
        "inputs": read_json(job / "spec.json")["inputs"],
        "profiles": profiles,
        "files": {p.relative_to(root.resolve()).as_posix(): sha256_file(p) for p in sorted(files)},
        "human_review_completed": False,
        "activated": False,
    }
    output = Path(output)
    if output.exists():
        raise PipelineError("Modelpakket bestaat al; kies een nieuwe naam")
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(".partial.zip")
    with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_STORED, allowZip64=True) as archive:
        archive.writestr("training-transfer.json", json.dumps(manifest, ensure_ascii=False))
        for path in sorted(files):
            archive.write(path, "payload/" + path.relative_to(root.resolve()).as_posix())
    temporary.replace(output)
    return manifest


def main():
    """Start pakketexport, modeloverdracht of gecontroleerde import via de opdrachtregel."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("export", "export-models", "import"))
    parser.add_argument("path", type=Path)
    parser.add_argument("--inputs", type=Path)
    parser.add_argument("--job", type=Path)
    args = parser.parse_args()
    if args.command == "export-models":
        if not args.job:
            parser.error("--job vereist voor modelgewichten")
        result = export_models(args.path, args.job)
        print(f"Klaar: {len(result['files'])} modelbestanden in {args.path}", flush=True)
    elif args.command == "export":
        inputs = read_json(args.inputs) if args.inputs else default_inputs()
        result = export_bundle(args.path, inputs)
        print(f"Klaar: {len(result['files'])} bestanden in {args.path}", flush=True)
    else:
        print(f"Gecontroleerd en geïmporteerd: {import_bundle(args.path)} bestanden", flush=True)


if __name__ == "__main__":
    main()
