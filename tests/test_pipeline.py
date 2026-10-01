import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from PIL import Image

from src.pipeline import classify_birds, clip_box
from src.reporting import annotate, summarize


class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.image = Image.new("RGB", (100, 80), "white")
        self.settings = dict(
            device="cpu",
            detector_imgsz=640,
            confidence=0.25,
            iou=0.7,
            max_det=1500,
            classifier_imgsz=224,
            classifier_batch=1,
        )

    def detector(self, boxes, scores):
        xyxy, conf = Mock(), Mock()
        xyxy.tolist.return_value = boxes
        conf.tolist.return_value = scores
        return Mock(
            predict=Mock(
                return_value=[SimpleNamespace(boxes=SimpleNamespace(xyxy=xyxy, conf=conf))]
            )
        )

    def test_empty_detection_skips_classifier(self):
        classifier = Mock()
        birds, limited = classify_birds(
            self.image, self.detector([], []), classifier, self.settings
        )
        classifier.predict.assert_not_called()
        self.assertFalse(limited)
        self.assertEqual(summarize(birds)["percentages"], {"healthy": 0.0, "dead": 0.0})

    def test_clipped_boxes_stay_associated_with_classification(self):
        classifier = Mock()
        classifier.names = {0: "healthy", 1: "dead"}  # Intentionally reversed from real weights.
        classifier.predict.side_effect = [
            [SimpleNamespace(probs=SimpleNamespace(top1=1, top1conf=0.2))],
            [SimpleNamespace(probs=SimpleNamespace(top1=0, top1conf=0.9))],
        ]
        detector = self.detector(
            [[-2, -3, 20.2, 30], [200, 20, 300, 30], [50, 40, 110, 90]], [0.8, 0.5, 0.7]
        )
        birds, _ = classify_birds(self.image, detector, classifier, self.settings)
        self.assertEqual([b["box"] for b in birds], [[0, 0, 21, 30], [50, 40, 100, 80]])
        self.assertEqual([b["label"] for b in birds], ["dead", "healthy"])
        self.assertEqual([b["detection_confidence"] for b in birds], [0.8, 0.7])
        self.assertTrue(birds[0]["requires_verification"])
        self.assertEqual(classifier.predict.call_args_list[0].args[0][0].size, (21, 30))
        summary = summarize(birds)
        self.assertEqual(summary["counts"], {"healthy": 1, "dead": 1})
        self.assertEqual(summary["total_detected"], summary["total_classified"])
        annotated = annotate(self.image, birds)
        self.assertNotEqual(annotated.tobytes(), self.image.tobytes())
        self.assertEqual(self.image.getpixel((0, 0)), (255, 255, 255))

    def test_missing_classification_fails(self):
        classifier = Mock(predict=Mock(return_value=[]))
        with self.assertRaisesRegex(ValueError, "Nem todos"):
            classify_birds(
                self.image, self.detector([[0, 0, 10, 10]], [0.8]), classifier, self.settings
            )

    def test_nonfinite_coordinates_fail(self):
        with self.assertRaises(ValueError):
            clip_box([0, 0, float("nan"), 20], 100, 80)

    def test_detection_limit_is_reported(self):
        self.settings["max_det"] = 1
        classifier = Mock()
        classifier.names = {0: "healthy"}
        classifier.predict.return_value = [
            SimpleNamespace(probs=SimpleNamespace(top1=0, top1conf=0.9))
        ]
        _, limited = classify_birds(
            self.image, self.detector([[0, 0, 10, 10]], [0.8]), classifier, self.settings
        )
        self.assertTrue(limited)


if __name__ == "__main__":
    unittest.main()
