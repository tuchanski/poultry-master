"""Verifica caixas e confianças entregues ao associador sequencial."""

import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from PIL import Image

from src.pipeline import clip_box, detect_birds


class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.image = Image.new("RGB", (100, 80), "white")
        self.settings = dict(
            device="cpu", detector_imgsz=640, confidence=0.25, iou=0.7, max_det=1500
        )

    def detector(self, boxes, scores):
        xyxy, conf = Mock(), Mock()
        xyxy.tolist.return_value = boxes
        conf.tolist.return_value = scores
        return Mock(predict=Mock(return_value=[
            SimpleNamespace(boxes=SimpleNamespace(xyxy=xyxy, conf=conf))
        ]))

    def test_empty_detection(self):
        birds, limited = detect_birds(self.image, self.detector([], []), self.settings)
        self.assertEqual(birds, [])
        self.assertFalse(limited)

    def test_clipped_boxes_keep_their_confidence_and_sequential_ids(self):
        detector = self.detector(
            [[-2, -3, 20.2, 30], [200, 20, 300, 30], [50, 40, 110, 90]],
            [0.8, 0.5, 0.7],
        )
        birds, _ = detect_birds(self.image, detector, self.settings)
        self.assertEqual(birds, [
            {"id": 1, "box": [0, 0, 21, 30], "detection_confidence": 0.8},
            {"id": 2, "box": [50, 40, 100, 80], "detection_confidence": 0.7},
        ])

    def test_inconsistent_detections_fail(self):
        with self.assertRaisesRegex(ValueError, "inconsistentes"):
            detect_birds(self.image, self.detector([[0, 0, 10, 10]], []), self.settings)

    def test_nonfinite_coordinates_fail(self):
        with self.assertRaises(ValueError):
            clip_box([0, 0, float("nan"), 20], 100, 80)

    def test_invalid_confidence_fails(self):
        for score in (float("nan"), -0.1, 1.1):
            with self.subTest(score=score), self.assertRaises(ValueError):
                detect_birds(self.image, self.detector([[0, 0, 10, 10]], [score]), self.settings)

    def test_detection_limit_is_reported(self):
        self.settings["max_det"] = 1
        _, limited = detect_birds(
            self.image, self.detector([[0, 0, 10, 10]], [0.8]), self.settings
        )
        self.assertTrue(limited)


if __name__ == "__main__":
    unittest.main()
