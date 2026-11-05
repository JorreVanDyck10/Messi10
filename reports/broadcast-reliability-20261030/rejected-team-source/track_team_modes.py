"""Experimental kit modes: each tracked identity has one total appearance vote.

No provider labels enter fitting. Track IDs are namespaced at camera resets.
Short tracks and untracked observations remain eligible. Production continues
to use the ordinary sample-count modes until this policy passes validation.
"""

from collections import Counter, defaultdict

import numpy as np

from .contracts import Detection, digest_json
from .kit_embedding import PitchTeamSamples, dominant_teams
from .teams import lab_to_hex


def balanced_modes(vectors, identities, *, radius, separation):
    if len(vectors) != len(identities):
        raise ValueError("Appearance samples and identities differ")
    # Missing IDs must never be treated as one shared person.
    keys = [("sample", i) if key is None else ("track", key) for i, key in enumerate(identities)]
    counts = Counter(keys)
    weights = np.asarray([1 / counts[key] for key in keys])
    points = np.asarray(vectors, np.float64)
    if points.ndim != 2 or len(points) < 4 or not np.isfinite(points).all():
        return None
    if all(count == 1 for count in counts.values()):
        return dominant_teams(vectors, radius=radius, separation=separation)
    points /= np.maximum(np.linalg.norm(points, axis=1, keepdims=True), 1e-9)
    distances = np.clip(1 - points @ points.T, 0, 2)
    remaining, centers, groups = np.ones(len(points), bool), [], []
    for _ in range(2):
        support = (distances <= radius) & remaining[None, :]
        sizes = support.sum(1)
        votes = support @ weights
        votes[(~remaining) | (sizes < 2)] = -1
        chosen = int(votes.argmax())
        if votes[chosen] < 0:
            return None
        members = np.flatnonzero(support[chosen])
        center = np.average(points[members], axis=0, weights=weights[members])
        center /= max(1e-9, np.linalg.norm(center))
        centers.append(center)
        groups.append(members)
        remaining &= (1 - points @ center) >= separation
    if 1 - np.dot(*centers) < separation:
        return None
    order = sorted(range(2), key=lambda i: tuple(np.round(centers[i], 6)))
    return [centers[i] for i in order], [groups[i] for i in order]


def identity_exclusive_modes(vectors, identities, *, radius, separation):
    """Veto opposing modes linked repeatedly by at least two tracked people.

    A single identity switch cannot veto a candidate. Unknown identities never
    establish a link. Apart from this veto, sample votes and centers retain
    the production algorithm exactly.
    """
    if len(vectors) != len(identities):
        raise ValueError("Appearance samples and identities differ")
    points = np.asarray(vectors, np.float64)
    if points.ndim != 2 or len(points) < 4 or not np.isfinite(points).all():
        return None
    points /= np.maximum(np.linalg.norm(points, axis=1, keepdims=True), 1e-9)
    distances = np.clip(1 - points @ points.T, 0, 2)
    remaining, centers, groups = np.ones(len(points), bool), [], []
    first_tracks = Counter()
    for turn in range(2):
        support = (distances <= radius) & remaining[None, :]
        sizes = support.sum(1)
        sizes[~remaining] = 0
        while True:
            chosen = int(sizes.argmax())
            if sizes[chosen] < 2:
                return None
            members = np.flatnonzero(support[chosen])
            tracks = Counter(identities[i] for i in members if identities[i] is not None)
            shared = sum(count >= 2 and first_tracks[key] >= 2 for key, count in tracks.items())
            if not turn or shared < 2:
                break
            sizes[chosen] = 0
        center = points[members].mean(0)
        center /= max(1e-9, np.linalg.norm(center))
        centers.append(center)
        groups.append(members)
        first_tracks = tracks
        remaining &= (1 - points @ center) >= separation
    if 1 - np.dot(*centers) < separation:
        return None
    order = sorted(range(2), key=lambda i: tuple(np.round(centers[i], 6)))
    return [centers[i] for i in order], [groups[i] for i in order]


def representative_modes(vectors, identities, *, radius, separation):
    """Use a robust appearance median per temporary identity before clustering."""
    if len(vectors) != len(identities):
        raise ValueError("Appearance samples and identities differ")
    points = np.asarray(vectors, np.float64)
    if points.ndim != 2 or len(points) < 4 or not np.isfinite(points).all():
        return None
    tracks = defaultdict(list)
    for i, key in enumerate(identities):
        tracks[("sample", i) if key is None else ("track", key)].append(i)
    members = list(tracks.values())
    medians = [np.median(points[group], axis=0) for group in members]
    fitted = dominant_teams(medians, radius=radius, separation=separation)
    if fitted is None:
        return None
    centers, groups = fitted
    return centers, [np.asarray([i for j in group for i in members[j]]) for group in groups]


def fit_track_balanced(frames, settings, fps, *, rule="balanced"):
    samples, identities, epoch = PitchTeamSamples(settings, fps), {}, 0
    for frame in frames:
        epoch += bool(frame["reset"])
        for row in frame["detections"]:
            detection = Detection(**row)
            index = frame["frame_index"]
            samples.add(detection, index)
            key = digest_json([index, detection.detection_id])
            identities[key] = (epoch, detection.track_id) if detection.track_id is not None else None
    selected = sorted(samples.samples)[: settings["max_samples"]]
    result = samples.fit()
    policies = {
        "balanced": balanced_modes,
        "exclusive": identity_exclusive_modes,
        "representative": representative_modes,
    }
    result["sampling_policy"] = rule
    result["status"] = "insufficient_groups"
    for team in result["teams"].values():
        team.update(prototype_lab=None, prototype_embedding=None, shirt_color=None)
    fitted = policies[rule](
        [s[2] for s in selected],
        [identities[s[0]] for s in selected],
        radius=settings["embedding_radius"],
        separation=settings["embedding_separation"],
    )
    if fitted is None:
        return result
    centers, groups = fitted
    for team, center, members in zip(result["teams"].values(), centers, groups):
        if len({selected[i][1] for i in members}) < settings["min_cluster_frames"]:
            result["status"] = "insufficient_frames"
            return result
        labs = [selected[i][3] for i in members if selected[i][3] is not None]
        lab = np.median(labs, axis=0).tolist() if labs else [50.0, 0.0, 0.0]
        team.update(prototype_lab=lab, prototype_embedding=center.tolist(), shirt_color=lab_to_hex(lab))
    result["status"] = "available"
    return result
