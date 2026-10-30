"""Verify and bind the reviewed training files shipped through Git and Git LFS."""

from __future__ import annotations

import argparse
import json
from pathlib import Path, PurePosixPath

from .contracts import PipelineError, read_json, sha256_file, write_json
from .video import ROOT

CATALOG = Path("datasets/training-runtime-v1/manifest.json")


def verify_repository(root=ROOT, *, allow_lfs_pointers=False):
    manifest = read_json(root / CATALOG)
    failures = []
    total = 0
    for name, expected in manifest["files"].items():
        parts = PurePosixPath(name).parts
        if not parts or ".." in parts or ":" in name or "\\" in name or PurePosixPath(name).is_absolute():
            raise PipelineError("Ongeldig pad in de trainingscatalogus")
        path = root.joinpath(*parts).resolve()
        if not path.is_relative_to(root.resolve()):
            raise PipelineError("Trainingspad valt buiten het project")
        if not path.is_file():
            failures.append((name, "ontbreekt"))
            continue
        with path.open("rb") as stream:
            pointer = stream.read(128).startswith(b"version https://git-lfs.github.com/spec/v1")
        if pointer:
            if not allow_lfs_pointers:
                failures.append((name, "Git LFS-pointer; voer git lfs pull uit"))
            else:
                lines = path.read_text(encoding="utf-8").splitlines()
                fields = dict(line.split(" ", 1) for line in lines if " " in line)
                if fields.get("oid") != "sha256:" + expected or not fields.get("size", "").isdigit():
                    failures.append((name, "Git LFS-pointer verwijst naar andere inhoud"))
                else:
                    total += int(fields["size"])
        elif sha256_file(path) != expected:
            failures.append((name, "SHA-256 wijkt af"))
        else:
            total += path.stat().st_size
    if failures:
        first = "; ".join(f"{name}: {reason}" for name, reason in failures[:6])
        raise PipelineError(f"{len(failures)} trainingsbestanden niet bruikbaar. {first}")
    if "bytes" in manifest and total != manifest["bytes"]:
        raise PipelineError("De totale trainingsgrootte wijkt af van de catalogus")
    return manifest, total


def prepare_repository(root=ROOT):
    manifest, total = verify_repository(root)
    metadata = {
        "source_root": manifest["source_root"],
        "inputs": manifest["inputs"],
        "verified_files": len(manifest["files"]),
        "verified_bytes": total,
        "source": "repository",
        "catalog_sha256": sha256_file(root / CATALOG),
    }
    (root / ".cache").mkdir(parents=True, exist_ok=True)
    write_json(root / ".cache/repository-training.json", metadata)
    selected = root / ".cache/training-import.json"
    if not selected.exists() or read_json(selected).get("source") == "repository":
        write_json(selected, metadata)
    return metadata


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("verify", "prepare", "check-git"), default="prepare", nargs="?")
    args = parser.parse_args()
    try:
        if args.command in {"verify", "check-git"}:
            manifest, total = verify_repository(allow_lfs_pointers=args.command == "check-git")
            result = {"verified_files": len(manifest["files"]), "verified_bytes": total}
            if args.command == "check-git":
                result["lfs_pointer_hashes_allowed"] = True
        else:
            result = prepare_repository()
        print(json.dumps(result, indent=2), flush=True)
    except PipelineError as exc:
        parser.exit(1, f"Trainingsdata niet klaar: {exc}\n")


if __name__ == "__main__":
    main()
