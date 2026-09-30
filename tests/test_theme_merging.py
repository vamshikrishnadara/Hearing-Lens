"""Behavioral checks for the small-group policy without model dependencies."""
import unittest
import numpy as np
from pipeline.theme_merging import merge_small_groups


def directions(degrees):
    radians = np.deg2rad(degrees)
    return np.column_stack((np.cos(radians), np.sin(radians)))


class ThemeMergingTests(unittest.TestCase):
    def test_similar_small_group_joins_larger_group_without_mutation_or_loss(self):
        groups = [[0, 1, 2], [3], [4, 5, 6]]
        vectors = directions([0, 0, 0, 10, 90, 90, 90])
        original = vectors.copy()
        merged, info = merge_small_groups(vectors, groups)
        self.assertEqual(merged, [[0, 1, 2, 3], [4, 5, 6]])
        self.assertEqual(groups, [[0, 1, 2], [3], [4, 5, 6]])
        np.testing.assert_array_equal(vectors, original)
        self.assertEqual(info['initial_theme_ids_by_group'], [[1, 2], [3]])
        self.assertEqual(sorted(sum(merged, [])), list(range(7)))

    def test_unrelated_small_group_is_retained(self):
        groups = [[0, 1, 2], [3]]
        merged, info = merge_small_groups(directions([0, 0, 0, 90]), groups)
        self.assertEqual(merged, groups)
        self.assertEqual(info['history'], [])

    def test_two_small_groups_can_merge_but_sized_groups_do_not(self):
        merged, _ = merge_small_groups(directions([0, 0, 10, 10]), [[0, 1], [2, 3]])
        self.assertEqual(merged, [[0, 1, 2, 3]])
        groups = [[0, 1, 2], [3, 4, 5]]
        merged, _ = merge_small_groups(directions([0] * 6), groups)
        self.assertEqual(merged, groups)

    def test_chain_cannot_bridge_dissimilar_original_groups(self):
        merged, info = merge_small_groups(directions([0, 30, 60]), [[0], [1], [2]])
        self.assertEqual(len(merged), 2)
        self.assertEqual(len(info['history']), 1)
        self.assertEqual(sorted(map(len, merged)), [1, 2])

    def test_highest_similarity_wins_and_exact_ties_use_initial_order(self):
        _, info = merge_small_groups(directions([0, 20, 25]), [[0], [1], [2]])
        first = info['history'][0]
        self.assertEqual((first['left_initial_theme_ids'], first['right_initial_theme_ids']), ([2], [3]))
        _, info = merge_small_groups(directions([0] * 6), [[0, 1], [2, 3], [4, 5]])
        first = info['history'][0]
        self.assertEqual((first['left_initial_theme_ids'], first['right_initial_theme_ids']), ([1], [2]))

    def test_zero_center_and_single_group_remain_unchanged(self):
        groups = [[0, 1], [2]]
        merged, _ = merge_small_groups(np.array([[1., 0.], [-1., 0.], [1., 0.]]), groups)
        self.assertEqual(merged, groups)
        merged, info = merge_small_groups(np.array([[1., 0.]]), [[0]])
        self.assertEqual(merged, [[0]])
        self.assertEqual(info['final_count'], 1)

    def test_similarity_boundary_is_inclusive(self):
        for similarity, expected_count in [(0.75, 1), (0.749, 2)]:
            vectors = np.array([[1., 0.], [similarity, np.sqrt(1 - similarity ** 2)]])
            merged, _ = merge_small_groups(vectors, [[0], [1]])
            self.assertEqual(len(merged), expected_count)
