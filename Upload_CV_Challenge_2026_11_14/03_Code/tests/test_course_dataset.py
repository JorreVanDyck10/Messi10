import io
import re
import zipfile

import pytest

from football_pipeline.course_dataset import archive_url, catalog, object_labels, select_games
from football_pipeline.research_archive import RangeArchive


class Response(io.BytesIO):
    status = 206

    def __init__(self, body, first, last, total):
        super().__init__(body)
        self.headers = {"Content-Range": f"bytes {first}-{last}/{total}"}


def test_range_archive_reads_zip_selectively_and_reuses_cached_blocks(monkeypatch):
    content = io.BytesIO()
    with zipfile.ZipFile(content, "w") as archive:
        archive.writestr("info.json", '{"info": {"version": "1.3", "game_id": "2"}}')
        archive.writestr(
            "clip/Labels-GameState.json", '{"info": {"version": "1.3", "game_id": "3", "name": "SNGS-003"}}'
        )
        archive.writestr("image.jpg", b"x" * 100000)
    payload = content.getvalue()
    requests = []

    def open_range(request, timeout):
        first, last = map(int, re.search(r"bytes=(\d+)-(\d+)", request.headers["Range"]).groups())
        requests.append((first, last))
        return Response(payload[first : last + 1], first, last, len(payload))

    monkeypatch.setattr("football_pipeline.research_archive.urlopen", open_range)
    reader = RangeArchive("https://example.test/immutable.zip", block_size=4096)
    with zipfile.ZipFile(reader) as archive:
        assert archive.read("info.json").startswith(b'{"info"')
        clips = catalog(archive)
        assert clips[0]["game_id"] == "3"
        count = len(requests)
        assert archive.read("info.json")
        assert len(requests) == count
    assert reader.downloaded < len(payload) / 2


def test_range_archive_rejects_whole_download_and_budget_overflow(monkeypatch):
    response = Response(b"x", 0, 0, 10000)
    response.status = 200
    monkeypatch.setattr("football_pipeline.research_archive.urlopen", lambda *a, **kw: response)
    with pytest.raises(ValueError, match="honor"):
        RangeArchive("https://example.test/data")
    monkeypatch.setattr(
        "football_pipeline.research_archive.urlopen", lambda *a, **kw: Response(b"x", 0, 0, 10000)
    )
    reader = RangeArchive("https://example.test/data", budget_bytes=100)
    with pytest.raises(ValueError, match="budget"):
        reader.read(500)


def test_match_split_removes_shared_matches_and_never_uses_test_archives():
    pools = {"train": [{"game_id": g} for g in "1234"], "valid": [{"game_id": g} for g in "3456"]}
    games, strategy = select_games(pools)
    assert strategy.startswith("official_valid")
    assert set(games["train"]) == {"1", "2"}
    assert not set(games["train"]) & set(games["val"])
    for split in ("test", "challenge", "../test"):
        with pytest.raises(ValueError):
            archive_url(split)


def test_provider_role_mapping_keeps_goalkeepers_players_and_unknown_people_separate():
    annotations = [
        {
            "supercategory": "object",
            "category_id": category,
            "bbox_image": {"x": 10, "y": 20, "w": 20, "h": 60},
        }
        for category in (1, 2, 3, 4, 7)
    ]
    labels, boxes = object_labels(annotations, 100, 100)
    assert [b["class_id"] for b in boxes] == [0, 0, 1, 2, 3]
    assert labels[-1].startswith("3 0.200000000 0.500000000 0.200000000 0.600000000")


def test_field_scoring_does_not_treat_internal_validity_as_ground_truth_accuracy(monkeypatch):
    from football_pipeline import course_field_evaluation as module

    results = iter(
        [
            {"valid": True, "errors_px": [1.0, 2.0]},
            {"valid": True, "errors_px": [4.0, 4.0]},
            {"valid": True, "errors_px": []},
            {"valid": False, "errors_px": []},
        ]
    )
    monkeypatch.setattr(module, "reprojection_metrics", lambda *a: next(results))
    monkeypatch.setattr(module, "labels_for_row", lambda row: {})
    measured = module.score([{"image_size": [300, 400]}] * 4, [{}] * 4, {})
    assert measured["correct"] == measured["wrong"] == measured["unscored_valid"] == 1
    assert measured["correct_fraction"] == 0.25


def test_field_selection_does_not_hide_lost_coverage_behind_fewer_false_projections():
    from football_pipeline.course_field_evaluation import improves_geometry

    baseline = {"correct": 12, "wrong": 2}
    assert improves_geometry({"correct": 13, "wrong": 2}, baseline)
    assert not improves_geometry({"correct": 13, "wrong": 3}, baseline, allow_error_reduction=True)
    assert not improves_geometry({"correct": 11, "wrong": 0}, baseline, allow_error_reduction=True)
    assert not improves_geometry({"correct": 12, "wrong": 1}, baseline)
    assert improves_geometry({"correct": 12, "wrong": 1}, baseline, allow_error_reduction=True)
