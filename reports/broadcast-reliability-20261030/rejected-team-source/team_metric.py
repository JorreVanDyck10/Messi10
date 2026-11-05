"""Optional team-only metric with the original role-kit evidence preserved."""

from copy import deepcopy

import numpy as np

from .contracts import PipelineError


def validate_transform(value):
    matrix = np.asarray(value, float)
    if matrix.shape != (32, 32) or not np.isfinite(matrix).all() or np.linalg.norm(matrix) < 1e-9:
        raise PipelineError("Ongeldige kleurtransformatie voor teamherkenning.")
    return matrix


def transform_embedding(vector, matrix):
    transformed = matrix @ np.asarray(vector, float)
    return (transformed / max(1e-9, np.linalg.norm(transformed))).tolist()


def fit_metric_model(samples, transform):
    """Fit role evidence in original space and team prototypes in learned space."""
    root_histogram = isinstance(transform, str) and transform == "root_histogram_v1"
    matrix = None if root_histogram else validate_transform(transform)
    role_reference = samples.fit()
    changed = deepcopy(samples)
    changed.samples = [
        (
            priority,
            index,
            np.sqrt(np.maximum(vector, 0)).tolist() if root_histogram else transform_embedding(vector, matrix),
            lab,
        )
        for priority, index, vector, lab in samples.samples
    ]
    model = changed.fit()
    if root_histogram:
        model["embedding_power"] = 0.5
    else:
        model["embedding_transform"] = matrix.tolist()
    model["role_kit_reference"] = role_reference
    return model
