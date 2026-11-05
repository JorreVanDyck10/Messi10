"""Track balancing cannot turn repeated views of one player into a majority."""

import unittest

import numpy as np

from football_pipeline.kit_embedding import dominant_teams
from football_pipeline.track_team_modes import balanced_modes, identity_exclusive_modes


class TrackBalancedModesTests(unittest.TestCase):
    def test_many_observations_do_not_outvote_many_distinct_players(self):
        vectors = [[1, 0, 0]] * 100 + [[0, 1, 0]] * 30 + [[0, 0, 1]] * 20
        ids = [1] * 100 + [1] * 30 + [2 + i // 4 for i in range(20)]
        ordinary, _ = dominant_teams(vectors, radius=0.1, separation=0.35)
        balanced, groups = balanced_modes(vectors, ids, radius=0.1, separation=0.35)
        self.assertFalse(any(np.allclose(center, [0, 0, 1]) for center in ordinary))
        self.assertTrue(any(np.allclose(center, [0, 0, 1]) for center in balanced))
        self.assertEqual(len(groups), 2)

    def test_untracked_observations_are_independent_and_match_original(self):
        vectors = [[1, 0, 0]] * 8 + [[0, 1, 0]] * 5 + [[0, 0, 1]] * 3
        ordinary = dominant_teams(vectors, radius=0.1, separation=0.35)
        balanced = balanced_modes(vectors, [None] * len(vectors), radius=0.1, separation=0.35)
        for old, new in zip(ordinary[0] + ordinary[1], balanced[0] + balanced[1]):
            np.testing.assert_array_equal(old, new)

    def test_no_cross_shot_identity_merging(self):
        vectors = [[1, 0, 0]] * 10 + [[0, 1, 0]] * 4 + [[0, 0, 1]] * 4
        same = [1] * 10 + [2] * 4 + [1] * 4
        scoped = [(0, 1)] * 10 + [(0, 2)] * 4 + [(1, 1)] * 4
        first = balanced_modes(vectors, same, radius=0.1, separation=0.35)
        second = balanced_modes(vectors, scoped, radius=0.1, separation=0.35)
        self.assertFalse(any(np.allclose(center, [0, 0, 1]) for center in first[0]))
        # Distinct shot IDs each receive a full vote; no prior-shot dilution.
        self.assertTrue(any(np.allclose(center, [1, 0, 0]) for center in second[0]))

    def test_mismatched_ids_and_nonfinite_samples_rejected(self):
        with self.assertRaises(ValueError):
            balanced_modes([[1, 0]], [], radius=0.1, separation=0.35)
        self.assertIsNone(balanced_modes([[np.nan, 0]] * 4, [1] * 4, radius=0.1, separation=0.35))

    def test_exclusion_needs_two_repeated_links_not_a_single_id_switch(self):
        vectors = [[1, 0, 0]] * 20 + [[0, 1, 0]] * 10 + [[0, 0, 1]] * 6
        linked = [1] * 10 + [2] * 10 + [1] * 5 + [2] * 5 + [3] * 6
        single = [1] * 10 + [2] * 10 + [1] * 5 + [4] * 5 + [3] * 6
        for ids, expected in ((linked, True), (single, False)):
            centers, _ = identity_exclusive_modes(vectors, ids, radius=0.1, separation=0.35)
            self.assertEqual(any(np.allclose(center, [0, 0, 1]) for center in centers), expected)

    def test_exclusion_without_repeated_identity_links_matches_original(self):
        vectors = [[1, 0, 0]] * 8 + [[0, 1, 0]] * 5 + [[0, 0, 1]] * 3
        for ids in ([None] * 16, list(range(16))):
            expected = dominant_teams(vectors, radius=0.1, separation=0.35)
            actual = identity_exclusive_modes(vectors, ids, radius=0.1, separation=0.35)
            for old, new in zip(expected[0] + expected[1], actual[0] + actual[1]):
                np.testing.assert_array_equal(old, new)


if __name__ == "__main__":
    unittest.main()
