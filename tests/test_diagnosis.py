import unittest

from scripts.diagnose_models import overlaps, true_positives


class MatchingTests(unittest.TestCase):
    def test_duplicate_detections_do_not_match_the_same_bird_twice(self):
        boxes = [[0, 0, 10, 10], [1, 1, 10, 10], [20, 20, 30, 30]]
        targets = [[0, 0, 10, 10], [20, 20, 30, 30]]
        self.assertEqual(true_positives(boxes, targets), 2)

    def test_partial_and_disjoint_boxes_are_not_full_bird_matches(self):
        self.assertEqual(true_positives([[0, 0, 2, 2], [20, 20, 30, 30]], [[0, 0, 10, 10]]), 0)

    def test_empty_and_identical_boxes(self):
        self.assertEqual(true_positives([], [[0, 0, 10, 10]]), 0)
        self.assertEqual(true_positives([[0, 0, 10, 10]], []), 0)
        self.assertEqual(overlaps([[0, 0, 10, 10]], [[0, 0, 10, 10]])[0, 0], 1)
