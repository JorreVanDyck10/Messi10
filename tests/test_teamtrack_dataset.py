import json

import pytest

from persoon1.teamtrack_dataset import build


def test_rebuilding_preserves_actual_annotation_edits(tmp_path):
    (tmp_path / "manifest.json").write_text(
        json.dumps({"frames": [{"annotator": "actual team member", "reviewer": "", "review_status": "open"}]}),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="Preserve actual annotation/review edits"):
        build(tmp_path)
