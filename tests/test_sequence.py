"""Protege as regras temporais e a execução sequencial após remover a CLI antiga."""

import csv
import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from PIL import Image

import analyze_sequence
from src.sequence import analyze_detections


class SequenceTests(unittest.TestCase):
    def setUp(self):
        self.settings = dict(
            stationary_minutes=1, nominal_interval_seconds=30,
            max_center_distance_diagonals=1, motion_threshold_diagonals=0.15,
            association_min_iou=0.05, max_missed_frames=1,
            minimum_stationary_observations=2, session_gap_seconds=180,
        )
        self.start = datetime(2026, 10, 19, tzinfo=timezone.utc)

    def frame(self, seconds, boxes):
        return {
            "timestamp": self.start + timedelta(seconds=seconds), "image": "frame.png",
            "detections": [{"box": box, "detection_confidence": 0.9} for box in boxes],
        }

    def test_stationary_candidate_uses_observed_credit_and_records_one_event(self):
        frames = [self.frame(second, [[0, 0, 10, 10]]) for second in (0, 90, 120, 150)]
        tracks, observations, _ = analyze_detections(frames, self.settings)
        self.assertEqual(observations[1]["stationary_seconds"], 30)
        self.assertEqual(observations[1]["state"], "tracking")
        self.assertEqual(observations[2]["state"], "stationary_candidate")
        self.assertEqual(len(tracks[0]["candidate_events"]), 1)

    def test_movement_resets_stationary_credit(self):
        frames = [self.frame(0, [[0, 0, 10, 10]]), self.frame(30, [[0, 0, 10, 10]]),
                  self.frame(60, [[5, 0, 15, 10]])]
        tracks, observations, _ = analyze_detections(frames, self.settings)
        self.assertEqual(len(tracks), 1)
        self.assertEqual(observations[-1]["stationary_seconds"], 0)
        self.assertEqual(observations[-1]["state"], "tracking")

    def test_long_pause_starts_a_new_session_and_track(self):
        frames = [self.frame(0, [[0, 0, 10, 10]]), self.frame(181, [[0, 0, 10, 10]])]
        tracks, observations, _ = analyze_detections(frames, self.settings)
        self.assertEqual(tracks[0]["final_state"], "lost")
        self.assertEqual([row["session_id"] for row in observations], [1, 2])
        self.assertEqual([row["track_id"] for row in observations], [1, 2])

    def test_missing_frames_end_a_track_without_creating_a_candidate(self):
        frames = [self.frame(0, [[0, 0, 10, 10]]), self.frame(30, []), self.frame(60, []),
                  self.frame(90, [[0, 0, 10, 10]])]
        tracks, _, _ = analyze_detections(frames, self.settings)
        self.assertEqual(len(tracks), 2)
        self.assertEqual(tracks[0]["final_state"], "lost")
        self.assertFalse(any(track["candidate_events"] for track in tracks))

    def test_each_detection_has_a_distinct_track(self):
        frames = [self.frame(second, [[0, 0, 10, 10], [1, 0, 11, 10]]) for second in (0, 30)]
        tracks, _, by_frame = analyze_detections(frames, self.settings)
        self.assertEqual(len(tracks), 2)
        self.assertEqual(len({row["track_id"] for row in by_frame[-1]}), 2)

    def test_sequence_writes_outputs_without_a_classifier(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for name in ("first.png", "second.png"):
                Image.new("RGB", (20, 20), "white").save(root / name)
            manifest = root / "sequence.csv"
            manifest.write_text(
                "image,timestamp\nfirst.png,2026-10-19T10:00:00-03:00\n"
                "second.png,2026-10-19T10:00:30-03:00\n"
            )
            args = SimpleNamespace(
                output=root / "result", images_dir=None, manifest=manifest,
                config=analyze_sequence.ROOT / "config.json", device="cpu", confidence=None,
                roi=None, candidates_only=False, hide_labels=False,
                stationary_minutes=1, nominal_interval_seconds=30, session_gap_minutes=3,
                motion_threshold_diagonals=0.15, max_center_distance_diagonals=1,
                association_min_iou=0.05, max_missed_frames=1,
                minimum_stationary_observations=2,
            )
            detection = {"id": 1, "box": [1, 1, 10, 10], "detection_confidence": 0.9}
            with patch.object(analyze_sequence, "load_model", return_value=(object(), {})), \
                 patch.object(analyze_sequence, "detect_birds", return_value=([detection], False)):
                analyze_sequence.run(args)
            report = json.loads((args.output / "report.json").read_text())
            self.assertTrue(report)
            self.assertEqual(len(list((args.output / "frames").glob("*"))), 2)
            with (args.output / "tracks.csv").open(encoding="utf-8-sig", newline="") as stream:
                rows = list(csv.DictReader(stream))
            self.assertEqual(len(rows), 2)
            self.assertEqual({row["track_id"] for row in rows}, {"1"})
            self.assertTrue((root / "first.png").is_file())


if __name__ == "__main__":
    unittest.main()
