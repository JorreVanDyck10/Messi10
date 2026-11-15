import hashlib

import pytest

from football_pipeline.contracts import PipelineError, read_json, write_json
from football_pipeline.repository_training import CATALOG, prepare_repository, verify_repository
from football_pipeline.training_transfer import imported_source_root


def catalog(root, name="data/train/labels.txt"):
    target = root / name
    target.parent.mkdir(parents=True)
    target.write_bytes(b"0 0.5 0.5 0.1 0.2\r\n")
    path = root / CATALOG
    path.parent.mkdir(parents=True)
    write_json(
        path,
        {
            "source_root": "C:/Messi10",
            "inputs": {"players": "data/train"},
            "files": {name: hashlib.sha256(target.read_bytes()).hexdigest()},
        },
    )
    return target


def test_repository_checkout_can_train_from_another_folder_without_zip(tmp_path):
    target = catalog(tmp_path)
    assert imported_source_root(tmp_path) == "C:/Messi10"
    record = prepare_repository(tmp_path)
    assert record["verified_files"] == 1
    assert record["verified_bytes"] == target.stat().st_size
    assert read_json(tmp_path / ".cache/training-import.json")["source"] == "repository"
    assert imported_source_root(tmp_path) == "C:/Messi10"


@pytest.mark.parametrize("condition", ["missing", "pointer", "changed"])
def test_repository_validation_rejects_missing_lfs_or_modified_data(tmp_path, condition):
    target = catalog(tmp_path)
    if condition == "missing":
        target.unlink()
    elif condition == "pointer":
        target.write_text("version https://git-lfs.github.com/spec/v1\noid sha256:" + "a" * 64)
    else:
        target.write_text("changed label")
    with pytest.raises(PipelineError, match="trainingsbestanden niet bruikbaar"):
        verify_repository(tmp_path)
    assert not (tmp_path / ".cache/training-import.json").exists()


def test_repository_preparation_preserves_selected_custom_package(tmp_path):
    catalog(tmp_path)
    (tmp_path / ".cache").mkdir()
    selected = {"source_root": "D:/Other", "inputs": {"players": "custom"}, "archive_sha256": "a" * 64}
    write_json(tmp_path / ".cache/training-import.json", selected)
    prepare_repository(tmp_path)
    assert read_json(tmp_path / ".cache/training-import.json") == selected
    assert read_json(tmp_path / ".cache/repository-training.json")["verified_files"] == 1


def test_ci_can_check_lfs_pointer_hashes_without_activating_training(tmp_path):
    target = catalog(tmp_path)
    manifest = read_json(tmp_path / CATALOG)
    expected = manifest["files"]["data/train/labels.txt"]
    length = target.stat().st_size
    target.write_text(f"version https://git-lfs.github.com/spec/v1\noid sha256:{expected}\nsize {length}\n")
    _, total = verify_repository(tmp_path, allow_lfs_pointers=True)
    assert total == length
    assert not (tmp_path / ".cache/training-import.json").exists()
    target.write_text(f"version https://git-lfs.github.com/spec/v1\noid sha256:{'f' * 64}\nsize {length}\n")
    with pytest.raises(PipelineError, match="trainingsbestanden niet bruikbaar"):
        verify_repository(tmp_path, allow_lfs_pointers=True)
