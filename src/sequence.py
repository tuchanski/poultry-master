"""Associação simples de detecções e regra temporal para fotos sequenciais."""

import math
from datetime import datetime


def _center(box):
    return ((box[0] + box[2]) / 2, (box[1] + box[3]) / 2)


def _diagonal(box):
    return max(1.0, math.hypot(box[2] - box[0], box[3] - box[1]))


def _iou(a, b):
    x1, y1 = max(a[0], b[0]), max(a[1], b[1])
    x2, y2 = min(a[2], b[2]), min(a[3], b[3])
    intersection = max(0, x2 - x1) * max(0, y2 - y1)
    area_a = (a[2] - a[0]) * (a[3] - a[1])
    area_b = (b[2] - b[0]) * (b[3] - b[1])
    union = area_a + area_b - intersection
    return intersection / union if union else 0.0


def _associate(tracks, detections, frame_index, max_distance, min_iou, max_missed):
    """Greedy one-to-one matching; returns detection-index -> track."""
    candidates = []
    for track in tracks:
        if track["state"] == "lost" or frame_index - track["last_frame"] > max_missed + 1:
            continue
        for det_index, detection in enumerate(detections):
            old_box, new_box = track["box"], detection["box"]
            old_center, new_center = _center(old_box), _center(new_box)
            distance = math.hypot(new_center[0] - old_center[0], new_center[1] - old_center[1])
            normalized_distance = distance / _diagonal(old_box)
            overlap = _iou(old_box, new_box)
            if normalized_distance <= max_distance or overlap >= min_iou:
                candidates.append((normalized_distance + 1 - overlap, det_index, track))
    candidates.sort(key=lambda item: item[0])
    assigned_detections, assigned_tracks = set(), set()
    matches = {}
    for _, det_index, track in candidates:
        track_id = track["track_id"]
        if det_index in assigned_detections or track_id in assigned_tracks:
            continue
        matches[det_index] = track
        assigned_detections.add(det_index)
        assigned_tracks.add(track_id)
    return matches, assigned_tracks


def analyze_detections(frames, settings):
    """Attach temporary IDs and temporal states to timestamped detections.

    Each frame is a mapping with ``timestamp``, ``image`` and ``detections``.
    Timestamps are timezone-aware datetimes. Detection boxes use xyxy pixels.
    """
    stationary_seconds = settings["stationary_minutes"] * 60
    interval_seconds = settings["nominal_interval_seconds"]
    max_distance = settings["max_center_distance_diagonals"]
    motion_threshold = settings["motion_threshold_diagonals"]
    min_iou = settings["association_min_iou"]
    max_missed = settings["max_missed_frames"]
    min_observations = settings["minimum_stationary_observations"]
    tracks, observations, by_frame = [], [], []
    session_id = 1

    for frame_index, frame in enumerate(frames):
        if frame_index and (
            frame["timestamp"] - frames[frame_index - 1]["timestamp"]
        ).total_seconds() > settings["session_gap_seconds"]:
            session_id += 1
            for previous in tracks:
                if previous["state"] != "lost":
                    previous["state"] = "lost"
                    previous["lost_at"] = previous["last_seen"]
        detections = frame["detections"]
        matches, assigned_track_ids = _associate(
            tracks, detections, frame_index, max_distance, min_iou, max_missed
        )
        current = []
        for track in tracks:
            if track["state"] != "lost" and track["track_id"] not in assigned_track_ids:
                track["missed_frames"] += 1
                if track["missed_frames"] > max_missed:
                    track["state"] = "lost"
                    track["lost_at"] = frame["timestamp"].isoformat()

        for det_index, detection in enumerate(detections):
            timestamp = frame["timestamp"]
            box = detection["box"]
            track = matches.get(det_index)
            if track is None:
                track = {
                    "track_id": len(tracks) + 1,
                    "session_id": session_id,
                    "first_seen": timestamp.isoformat(),
                    "last_seen": timestamp.isoformat(),
                    "lost_at": None,
                    "last_frame": frame_index,
                    "box": box,
                    "state": "tracking",
                    "missed_frames": 0,
                    "stationary_seconds": 0.0,
                    "stationary_observations": 0,
                    "stationary_since": None,
                    "candidate_events": [],
                    "observations": 0,
                    "max_stationary_seconds": 0.0,
                }
                tracks.append(track)
                motion = None
                elapsed = 0.0
            else:
                old_center = _center(track["box"])
                new_center = _center(box)
                motion = math.hypot(new_center[0] - old_center[0], new_center[1] - old_center[1]) / _diagonal(track["box"])
                elapsed = max(
                    0.0,
                    (timestamp - datetime.fromisoformat(track["last_seen"])).total_seconds(),
                )
                observed_credit = min(elapsed, interval_seconds)
                if motion <= motion_threshold:
                    if track["stationary_since"] is None:
                        track["stationary_since"] = track["last_seen"]
                    track["stationary_seconds"] += observed_credit
                    track["stationary_observations"] += 1
                else:
                    track["stationary_since"] = None
                    track["stationary_seconds"] = 0.0
                    track["stationary_observations"] = 0
                    track["state"] = "tracking"
                track["max_stationary_seconds"] = max(
                    track["max_stationary_seconds"], track["stationary_seconds"]
                )
                track["last_seen"] = timestamp.isoformat()
                track["last_frame"] = frame_index
                track["box"] = box
                track["missed_frames"] = 0

            if (
                track["stationary_seconds"] >= stationary_seconds
                and track["stationary_observations"] >= min_observations
            ):
                if track["state"] != "stationary_candidate":
                    track["candidate_events"].append(timestamp.isoformat())
                track["state"] = "stationary_candidate"

            track["observations"] += 1
            row = {
                "timestamp": timestamp.isoformat(),
                "image": str(frame["image"]),
                "session_id": track["session_id"],
                "track_id": track["track_id"],
                "session_id": track["session_id"],
                "box": box,
                "center": list(_center(box)),
                "detection_confidence": detection["detection_confidence"],
                "elapsed_seconds": round(elapsed, 3),
                "normalized_motion": None if motion is None else round(motion, 5),
                "stationary_seconds": round(track["stationary_seconds"], 3),
                "state": track["state"],
            }
            observations.append(row)
            current.append({**row, "box": box})
        by_frame.append(current)

    summaries = []
    for track in tracks:
        summaries.append(
            {
                "track_id": track["track_id"],
                "first_seen": track["first_seen"],
                "last_seen": track["last_seen"],
                "lost_at": track["lost_at"],
                "final_state": track["state"],
                "observations": track["observations"],
                "candidate_events": track["candidate_events"],
                "max_stationary_seconds": round(track["max_stationary_seconds"], 3),
                "current_stationary_seconds": round(track["stationary_seconds"], 3),
            }
        )
    return summaries, observations, by_frame
