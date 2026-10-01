"""Verifica integridade das divisões e barreiras contra rótulos não revisados."""

import csv
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from src.preparation.common import (
    assign_splits,
    file_hash,
    merge_related_groups,
    validate_splits,
    write_csv,
)
from src.preparation.health import REVIEW_FIELDS, prepare_health, rgb_images
from src.preparation.pio import prepare_pio, read_boxes, select_unique_images
from src.preparation.review import create_review

RATIOS = {"train": 0.70, "val": 0.15, "test": 0.15}


class SplitTests(unittest.TestCase):
    def test_same_capture_and_transitive_duplicates_stay_together(self):
        records = [
            {"group": "a", "sha256": "photo-1"},
            {"group": "b", "sha256": "photo-1"},
            {"group": "b", "sha256": "photo-2"},
            {"group": "c", "sha256": "photo-2"},
        ]
        merge_related_groups(records)
        self.assertEqual(len({row["group"] for row in records}), 1)

    def test_split_is_reproducible_and_all_classes_are_present(self):
        records = [
            {"group": f"session-{group}", "label": label, "sha256": f"{label}-{group}"}
            for group in range(12)
            for label in ("healthy", "sick", "dead")
        ]
        splits = assign_splits(records, RATIOS, 42)
        self.assertEqual(splits, assign_splits(list(reversed(records)), RATIOS, 42))
        prepared = [{**row, "split": splits[row["group"]]} for row in records]
        counts = validate_splits(prepared)
        self.assertTrue(all(len(classes) == 3 for classes in counts.values()))

    def test_insufficient_groups_do_not_fall_back_to_random_images(self):
        rows = [{"group": "same-session", "label": "dead"}] * 10
        with self.assertRaisesRegex(ValueError, "três grupos"):
            assign_splits(rows, RATIOS, 42)

    def test_hash_leakage_is_rejected(self):
        rows = [
            {"group": "a", "sha256": "identical", "label": "chicken", "split": "train"},
            {"group": "b", "sha256": "identical", "label": "chicken", "split": "test"},
        ]
        with self.assertRaisesRegex(ValueError, "Vazamento"):
            validate_splits(rows)


class FilePreparationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)

    def tearDown(self):
        self.temporary.cleanup()

    def test_only_zero_area_boxes_are_discarded(self):
        label = self.root / "image.txt"
        label.write_text("0 0.5 0.5 0 0.1\n0 0.5 0.5 0.2 0.2\n", encoding="utf-8")
        boxes, discarded = read_boxes(label)
        self.assertEqual(len(boxes), 1)
        self.assertEqual(discarded[0]["line"], 1)
        for invalid in ("0 nan 0.5 0.2 0.2", "0 0.99 0.5 0.2 0.2", "1 0.5 0.5 0.2 0.2"):
            label.write_text(invalid, encoding="utf-8")
            with self.assertRaises(ValueError):
                read_boxes(label)

    def test_conflicting_annotations_are_all_excluded(self):
        rows = [
            {
                "source": "a.jpg",
                "sha256": "same",
                "capture_group": "C-W1",
                "boxes": [(0, 0.5, 0.5, 0.2, 0.2)],
            },
            {
                "source": "b.jpg",
                "sha256": "same",
                "capture_group": "C-W2",
                "boxes": [(0, 0.5, 0.5, 0.3, 0.3)],
            },
        ]
        selected, excluded = select_unique_images(rows)
        self.assertEqual(selected, [])
        self.assertEqual([row["reason"] for row in excluded], ["conflicting_annotations"] * 2)

    def test_pio_export_keeps_originals_and_creates_three_splits(self):
        source = self.root / "originals"
        for number in range(1, 4):
            image = source / "images" / "train" / f"C-W{number}-0001.jpg"
            label = source / "labels" / "train" / f"C-W{number}-0001.txt"
            image.parent.mkdir(parents=True, exist_ok=True)
            label.parent.mkdir(parents=True, exist_ok=True)
            Image.new("RGB", (20, 20), (number * 60, 0, 0)).save(image)
            label.write_text("0 0.5 0.5 0 0.1\n0 0.5 0.5 0.5 0.5\n", encoding="utf-8")
        before = file_hash(label)
        output = self.root / "prepared"
        summary = prepare_pio(source, output, RATIOS, 42)
        self.assertEqual(summary["selected_images"], 3)
        self.assertEqual(summary["discarded_boxes"], 3)
        self.assertEqual(file_hash(label), before)
        for split in ("train", "val", "test"):
            self.assertEqual(len(list((output / "images" / split).glob("*.jpg"))), 1)
        with self.assertRaisesRegex(ValueError, "já existe"):
            prepare_pio(source, output, RATIOS, 42)

    def make_health_images(self):
        source = self.root / "health-originals"
        for class_index, label in enumerate(("healthy", "sick", "dead")):
            (source / label).mkdir(parents=True)
            for session in range(3):
                color = (class_index * 70, session * 70, 20)
                Image.new("RGB", (20, 20), color).save(source / label / f"bird_rgb_{session}.jpg")
        return source

    def test_pending_health_review_is_not_exported(self):
        source = self.make_health_images()
        review = self.root / "review.csv"
        template = Path(__file__).resolve().parents[1] / "scripts" / "health_review.html"
        result = create_review(source, review, template)
        self.assertEqual(result["pending"], 9)
        output = self.root / "prepared"
        with self.assertRaisesRegex(ValueError, "pendentes"):
            prepare_health(source, review, output, RATIOS, 42)
        self.assertFalse(output.exists())
        with self.assertRaisesRegex(ValueError, "já existe"):
            create_review(source, review, template)

    def test_reviewed_crops_are_split_by_source_session(self):
        source = self.make_health_images()
        review = self.root / "review.csv"
        rows = []
        for original in rgb_images(source):
            session = Path(original["image"]).stem.rsplit("_", 1)[1]
            rows.append(
                {
                    **original,
                    "status": "accepted",
                    "group": f"session-{session}",
                    "x1": 1,
                    "y1": 2,
                    "x2": 15,
                    "y2": 17,
                    "notes": "synthetic fixture",
                }
            )
        write_csv(review, rows, REVIEW_FIELDS)
        output = self.root / "prepared"
        summary = prepare_health(source, review, output, RATIOS, 42)
        self.assertEqual(summary["selected_crops"], 9)
        with (output / "manifest.csv").open(encoding="utf-8-sig", newline="") as stream:
            manifest = list(csv.DictReader(stream))
        validate_splits(manifest)
        for path in output.glob("*/*/*.png"):
            with Image.open(path) as image:
                self.assertEqual(image.size, (14, 15))


if __name__ == "__main__":
    unittest.main()
