import copy
import json
import random
import tempfile
import unittest
from pathlib import Path

from persoon1.annotation import save_annotation
from persoon1.core import dataset_path, read_json, read_labels, require_approval, validate_dataset, write_json
from persoon1.metrics import evaluate, iou


class TempCase(unittest.TestCase):
    def setUp(self):
        self.base = Path(".cache/tests").resolve()
        self.base.mkdir(parents=True, exist_ok=True)
        self.tmp = tempfile.TemporaryDirectory(dir=self.base)
        self.root = Path(self.tmp.name).resolve()

    def tearDown(self):
        # Verify computed cleanup target before recursive removal on Windows.
        assert self.root.is_relative_to(self.base) and self.root != self.base
        self.tmp.cleanup()


class MetricsTests(unittest.TestCase):
    def setUp(self):
        self.box = {"class_id": 0, "bbox_xyxy": [10, 10, 30, 30]}
        self.pred = {**self.box, "confidence": 0.9}
        self.gt = {"a": [self.box]}

    def test_perfect_prediction(self):
        score = evaluate(self.gt, {"a": [self.pred]}, ["ball"])
        self.assertEqual(score["mAP50_95"], 1.0)
        self.assertEqual(score["errors"], [])

    def test_missing_prediction(self):
        score = evaluate(self.gt, {"a": []}, ["ball"])
        self.assertEqual(score["mAP50"], 0)
        self.assertEqual(score["errors"][0]["type"], "FN")

    def test_high_confidence_false_positive_changes_ap(self):
        fp = {**self.pred, "bbox_xyxy": [50, 50, 70, 70], "confidence": 0.99}
        score = evaluate(self.gt, {"a": [self.pred, fp]}, ["ball"])
        self.assertAlmostEqual(score["mAP50"], 0.5)

    def test_duplicate_is_not_second_true_positive(self):
        score = evaluate(self.gt, {"a": [self.pred, self.pred]}, ["ball"])
        self.assertEqual(score["per_class"][0]["TP"], 1)
        self.assertEqual(score["per_class"][0]["FP"], 1)
        self.assertEqual(score["per_class"][0]["precision"], 0.5)

    def test_stricter_iou_changes_localisation_score(self):
        shifted = {**self.pred, "bbox_xyxy": [13, 10, 33, 30]}
        score = evaluate(self.gt, {"a": [shifted]}, ["ball"])
        self.assertEqual(score["mAP50"], 1)
        self.assertLess(score["mAP50_95"], 1)

    def test_workpoint_does_not_truncate_ap_curve(self):
        score = evaluate(self.gt, {"a": [{**self.pred, "confidence": 0.1}]}, ["ball"], confidence=0.25)
        self.assertEqual(score["mAP50"], 1)
        self.assertEqual(score["per_class"][0]["FN"], 1)

    def test_missing_empty_frame_rejected(self):
        with self.assertRaises(ValueError):
            evaluate({**self.gt, "negative": []}, {"a": [self.pred]}, ["ball"])

    def test_wrong_class_does_not_match(self):
        score = evaluate(self.gt, {"a": [{**self.pred, "class_id": 1}]}, ["ball", "person"])
        self.assertEqual(score["mAP50"], 0)
        self.assertIsNone(score["per_class"][1]["AP50"])

    def test_nan_prediction_rejected(self):
        with self.assertRaises(ValueError):
            evaluate(self.gt, {"a": [{**self.pred, "confidence": float("nan")}]}, ["ball"])

    def test_iou_disjoint_and_identical(self):
        self.assertEqual(iou([0, 0, 1, 1], [2, 2, 3, 3]), 0)
        self.assertEqual(iou([0, 0, 1, 1], [0, 0, 1, 1]), 1)


class DatasetTests(TempCase):
    def setUp(self):
        super().setUp()
        from PIL import Image
        rng = random.Random(42)
        frames = []
        for i, split in enumerate(("train", "val", "test")):
            Image.frombytes("RGB", (64, 48), rng.randbytes(64 * 48 * 3)).save(self.root / f"{i}.png")
            (self.root / f"{i}.txt").write_text("0 0.5 0.5 0.2 0.2\n", encoding="utf-8")
            frames.append({"frame_id": f"f{i}", "video_id": "fixture", "frame_index": i * 250,
                           "timestamp_s": i * 10, "width": 64, "height": 48, "group_id": f"g{i}",
                           "split": split, "image": f"{i}.png", "label": f"{i}.txt", "label_status": "positive",
                           "annotator": "fixture-author", "reviewer": "fixture-reviewer", "review_status": "approved"})
        self.data = {"schema_version": "1.0", "names": ["ball"], "frames": frames}
        self.manifest = self.root / "manifest.json"
        write_json(self.manifest, self.data)

    def check(self, review=True):
        return validate_dataset(self.manifest, require_review=review, min_frames=3, max_frames=3)

    def update(self):
        write_json(self.manifest, self.data)

    def test_valid_fixture(self):
        self.assertEqual(self.check()["errors"], [])

    def test_default_frame_requirement_is_enforced(self):
        self.assertTrue(any("40" in e for e in validate_dataset(self.manifest)["errors"]))

    def test_cross_subset_group_is_rejected(self):
        self.data["frames"][1]["group_id"] = "g0"
        self.update()
        self.assertTrue(any("crosses subsets" in e for e in self.check()["errors"]))

    def test_temporal_leakage_is_rejected(self):
        self.data["frames"][1]["timestamp_s"] = 0.5
        self.update()
        self.assertTrue(any("too close" in e for e in self.check()["errors"]))

    def test_missing_label_is_not_negative(self):
        (self.root / "0.txt").unlink()
        self.assertTrue(self.check()["errors"])

    def test_empty_label_requires_negative_status(self):
        (self.root / "0.txt").write_text("")
        self.assertTrue(any("explicit" in e for e in self.check()["errors"]))

    def test_duplicate_pixels_are_rejected(self):
        (self.root / "1.png").write_bytes((self.root / "0.png").read_bytes())
        self.assertTrue(any("duplicate pixels" in e for e in self.check()["errors"]))

    def test_independent_review_is_required(self):
        self.data["frames"][0]["reviewer"] = "FIXTURE-AUTHOR"
        self.update()
        self.assertTrue(any("independent" in e for e in self.check()["errors"]))

    def test_content_change_changes_fingerprint(self):
        a = self.check()["dataset_fingerprint"]
        (self.root / "0.txt").write_text("0 0.4 0.5 0.2 0.2\n")
        self.assertNotEqual(a, self.check()["dataset_fingerprint"])

    def test_unsafe_paths_rejected(self):
        with self.assertRaises(ValueError):
            dataset_path(self.root, "../escape.txt")
        self.data["frames"][0]["frame_id"] = "../escape"
        self.update()
        with self.assertRaises(ValueError):
            self.check()

    def test_invalid_boxes(self):
        for text in ("0 nan 0.5 0.2 0.2", "0 0.9 0.5 0.4 0.2", "1 0.5 0.5 0.2 0.2", "0 0.5 0.5 0 0.2"):
            with self.subTest(text=text):
                (self.root / "bad.txt").write_text(text)
                with self.assertRaises(ValueError):
                    read_labels(self.root / "bad.txt", 1)

    def test_approval_never_accepts_an_unready_dataset(self):
        approval = self.root / "approval.json"
        write_json(approval, {"reviewers": ["a", "b"]})
        with self.assertRaises(ValueError):
            require_approval(self.manifest, approval)

    def test_annotation_edit_invalidates_old_review(self):
        result = save_annotation(self.manifest, {"frame_id": "f0", "action": "save", "annotator": "fixture-author",
                                                "boxes": [[0, 0.5, 0.5, 0.3, 0.3]]})
        self.assertEqual(result["review_status"], "open")
        self.assertEqual(result["reviewer"], "")
        self.assertTrue((self.root / "review-history.jsonl").is_file())

    def test_same_author_cannot_approve(self):
        with self.assertRaises(ValueError):
            save_annotation(self.manifest, {"frame_id": "f0", "action": "approve", "reviewer": "fixture-author"})

    def test_empty_annotation_requires_explicit_confirmation(self):
        with self.assertRaises(ValueError):
            save_annotation(self.manifest, {"frame_id": "f0", "action": "save", "annotator": "fixture-author", "boxes": []})

    def test_approval_preserves_saved_boxes(self):
        before = (self.root / "0.txt").read_text()
        result = save_annotation(self.manifest, {"frame_id": "f0", "action": "approve", "reviewer": "actual-second-fixture-user"})
        self.assertEqual(result["review_status"], "approved")
        self.assertEqual(before, (self.root / "0.txt").read_text())


if __name__ == "__main__":
    unittest.main()
