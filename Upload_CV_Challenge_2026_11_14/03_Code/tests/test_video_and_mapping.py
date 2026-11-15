import unittest
from fractions import Fraction
from pathlib import Path
from types import SimpleNamespace

from test_person1 import TempCase
from persoon1.core import read_json, write_json
from persoon1.modeling import class_mapping
from persoon1.video import extract, frames, inspect_video


class VideoTests(TempCase):
    def setUp(self):
        super().setUp()
        import av
        import numpy as np
        self.video = self.root / "synthetic-vfr.mp4"
        with av.open(str(self.video), "w") as out:
            stream = out.add_stream("libx264", rate=25)
            stream.width, stream.height, stream.pix_fmt = 80, 48, "yuv420p"
            for i, pts in enumerate((0, 1, 3, 6)):
                pixels = np.full((48, 80, 3), (i + 1) * 50, dtype=np.uint8)
                frame = av.VideoFrame.from_ndarray(pixels, format="rgb24")
                frame.pts, frame.time_base = pts, Fraction(1, 25)
                for packet in stream.encode(frame):
                    out.mux(packet)
            for packet in stream.encode():
                out.mux(packet)

    def test_actual_variable_presentation_times_are_preserved(self):
        decoded = list(frames(self.video))
        self.assertEqual([i for i, _, _ in decoded], [0, 1, 2, 3])
        for actual, expected in zip([t for _, t, _ in decoded], (0, 0.04, 0.12, 0.24)):
            self.assertAlmostEqual(actual, expected, places=5)
        self.assertEqual(decoded[0][2].size, (80, 48))

    def test_inspection_records_vfr_intervals(self):
        result = inspect_video(self.video, self.root / "video.json")
        self.assertEqual(result["decoded_frames"], 4)
        self.assertEqual(result["observed_frame_intervals_s"], [0.04, 0.08, 0.12])
        self.assertFalse(result["source_approved"])

    def test_extraction_does_not_renumber_source_frames(self):
        plan = self.root / "plan.json"
        write_json(plan, {"names": ["ball"], "windows": [{"group_id": "dev", "split": "train", "start_s": 0.03, "end_s": 0.2, "every_s": 0.06}]})
        result = extract(self.video, plan, self.root / "dataset")
        data = read_json(result["manifest"])
        self.assertEqual([f["frame_index"] for f in data["frames"]], [1, 2])
        self.assertTrue(all(f["label_status"] == "unlabelled" for f in data["frames"]))
        self.assertFalse((self.root / "dataset/labels").exists())

    def test_extraction_rejects_overlapping_windows(self):
        plan = self.root / "plan.json"
        write_json(plan, {"names": ["ball"], "windows": [
            {"group_id": "a", "split": "train", "start_s": 0, "end_s": 0.2},
            {"group_id": "b", "split": "val", "start_s": 0.1, "end_s": 0.3}]})
        with self.assertRaises(ValueError):
            extract(self.video, plan, self.root / "dataset")

    def test_mapping_uses_semantics_instead_of_local_ids(self):
        mapping = self.root / "mapping.json"
        write_json(mapping, {"sports ball": "ball"})
        model = SimpleNamespace(names={0: "person", 32: "sports ball"})
        self.assertEqual(class_mapping(model, mapping, ["ball"]), {32: 0})

    def test_mapping_rejects_unavailable_model_class(self):
        mapping = self.root / "mapping.json"
        write_json(mapping, {"player": "person"})
        with self.assertRaises(ValueError):
            class_mapping(SimpleNamespace(names={0: "person"}), mapping, ["person"])


if __name__ == "__main__":
    unittest.main()
