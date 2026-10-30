import torch

from football_pipeline.field_layout import POINTS_UV
from scripts.train_sparse_field_head import sparse_targets


def test_sparse_targets_keep_unknown_channels_and_correct_a_known_displaced_peak():
    logits = torch.zeros(58, 10, 12)
    logits[0, 0, 0] = 3
    output = logits.softmax(0)
    points = [[0.0, 0.0, 0] for _ in POINTS_UV]
    points[0] = [0.5, 0.5, 2]
    indices, targets = sparse_targets(output, points)
    torch.testing.assert_close(targets.sum(1), torch.ones(len(targets)))
    corner = int((indices == 0).nonzero()[0])
    center = int((indices == 5 * 12 + 6).nonzero()[0])
    assert targets[corner, 0] < output[0, 0, 0]
    assert targets[center, 0] > output[0, 5, 6]
    # An unannotated channel keeps its relation to other unknown channels.
    torch.testing.assert_close(targets[:, 1] / targets[:, 2], torch.ones(len(targets)))
    assert len(indices) == len(set(indices.tolist()))


def test_no_known_landmarks_retains_exact_teacher_distribution():
    torch.manual_seed(19)
    output = torch.randn(58, 10, 12).softmax(0)
    points = [[0.0, 0.0, 0] for _ in POINTS_UV]
    indices, targets = sparse_targets(output, points)
    torch.testing.assert_close(targets, output.flatten(1)[:, indices].T)
