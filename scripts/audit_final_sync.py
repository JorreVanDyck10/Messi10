"""Compare the curated final package with root source without treating omitted experiments as bugs."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
from pathlib import Path


def semantic_source(path):
    """Ignore explanatory docstrings and formatting when comparing executable Python syntax."""
    tree = ast.parse(path.read_text(encoding="utf-8-sig"))
    for node in ast.walk(tree):
        if (
            isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
            and node.body
            and isinstance(node.body[0], ast.Expr)
            and isinstance(node.body[0].value, ast.Constant)
            and isinstance(node.body[0].value.value, str)
        ):
            node.body.pop(0)
    return ast.dump(tree, include_attributes=False)


def audit(root):
    """Report source drift, missing internal modules and model identity in the final package."""
    source = root / "src/football_pipeline"
    packaged = root / "final/src/football_pipeline"
    names = {p.stem for p in packaged.glob("*.py")}
    identical, different, missing_imports = [], [], []
    for path in sorted(packaged.glob("*.py")):
        counterpart = source / path.name
        if counterpart.is_file():
            target = identical if semantic_source(path) == semantic_source(counterpart) else different
            target.append(path.name)
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8-sig"))):
            if isinstance(node, ast.ImportFrom) and node.level == 1 and node.module:
                if node.module.split(".")[0] not in names:
                    missing_imports.append({"file": path.name, "line": node.lineno, "module": node.module})
    models = []
    for name in ("models-broadcast.json", "models-school.json"):
        config = root / "final/configs" / name
        profile = json.loads(config.read_text(encoding="utf-8-sig"))
        specs = profile["models"] + [
            profile[k] for k in ("appearance", "kit_embedding", "role_context") if k in profile
        ]
        for spec in specs:
            path = (config.parent / spec["weights"]).resolve()
            result = {"profile": name, "model_id": spec["model_id"], "exists": path.is_file()}
            if path.is_file():
                data = path.read_bytes()
                pointer = data.startswith(b"version https://git-lfs.github.com/spec/v1\n")
                if pointer:
                    fields = dict(line.split(" ", 1) for line in data.decode().splitlines())
                    actual = fields["oid"].removeprefix("sha256:")
                else:
                    actual = hashlib.sha256(data).hexdigest()
                result.update(
                    materialized=not pointer,
                    identity_matches_profile=actual == spec.get("weights_sha256"),
                )
            models.append(result)
    return {
        "same_executable_modules": identical,
        "different_executable_modules": different,
        "root_modules_not_packaged": sorted(p.name for p in source.glob("*.py") if p.stem not in names),
        "missing_internal_imports": missing_imports,
        "model_files": models,
        "note": "LFS pointer identity is not a load test. Omitted research modules are not automatically required by final.",
    }


def main():
    """Write a deterministic package comparison without changing source or downloading models."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = audit(Path(__file__).resolve().parents[1])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "different_modules": len(result["different_executable_modules"]),
                "missing_internal_imports": result["missing_internal_imports"],
            }
        )
    )


if __name__ == "__main__":
    main()
