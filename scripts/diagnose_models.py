"""Compara recortes revisados e ajustes do detector sem acessar o teste PIO."""

import argparse
import csv
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from analyze import load_model
from src.pipeline import clip_box
from src.preparation.common import file_hash, write_csv, write_json


def overlaps(boxes, targets):
    boxes = np.asarray(boxes, dtype=float).reshape(-1, 4)
    targets = np.asarray(targets, dtype=float).reshape(-1, 4)
    start = np.maximum(boxes[:, None, :2], targets[None, :, :2])
    end = np.minimum(boxes[:, None, 2:], targets[None, :, 2:])
    intersection = np.maximum(end - start, 0).prod(axis=2)
    area = (boxes[:, 2:] - boxes[:, :2]).prod(axis=1)
    target_area = (targets[:, 2:] - targets[:, :2]).prod(axis=1)
    return intersection / np.maximum(area[:, None] + target_area - intersection, 1e-12)


def true_positives(boxes, targets):
    """Pareamento guloso, na ordem de confiança, com uma anotação por detecção."""
    matrix = overlaps(boxes, targets)
    matched = 0
    for row in matrix:
        if len(row) and row.max() >= 0.5:
            index = row.argmax()
            matrix[:, index] = -1
            matched += 1
    return matched


def read_rows(path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def classify(model, image, device):
    result = model.predict(image, imgsz=224, device=device, verbose=False)[0]
    return model.names[result.probs.top1], float(result.probs.top1conf)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--device", default="0")
    parser.add_argument(
        "--health-imgsz", type=int, help="Resolução alternativa apenas no diagnóstico de saúde."
    )
    parser.add_argument("--health-only", action="store_true", help="Não executa a grade PIO.")
    parser.add_argument("--output", type=Path, default=ROOT / "outputs/diagnosis/round-01")
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("Use uma pasta de saída nova.")
    settings = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
    inference = settings["inference"]
    detector, detector_info = load_model(ROOT / inference["detector"], "detect", {"chicken"})
    classifier, classifier_info = load_model(
        ROOT / inference["classifier"], "classify", {"dead", "healthy"}
    )
    args.output.mkdir(parents=True)
    health = []
    health_root = ROOT / settings["health_output"]
    for row in read_rows(health_root / "manifest.csv"):
        with Image.open(ROOT / settings["health_source"] / row["image"]) as original:
            image = original.convert("RGB")
        reference = [int(row[key]) for key in ("x1", "y1", "x2", "y2")]
        manual_label, manual_confidence = classify(classifier, image.crop(reference), args.device)
        prediction = detector.predict(
            image,
            imgsz=args.health_imgsz or inference["detector_imgsz"],
            conf=inference["confidence"],
            iou=inference["iou"],
            max_det=inference["max_det"],
            device=args.device,
            verbose=False,
        )[0]
        boxes = prediction.boxes.xyxy.tolist()
        values = overlaps(boxes, [reference]).flatten()
        best = int(values.argmax()) if len(values) else None
        best_iou = float(values[best]) if best is not None else 0.0
        auto_label, auto_confidence = "", ""
        if best_iou >= 0.5:
            box = clip_box(boxes[best], *image.size)
            auto_label, auto_confidence = classify(classifier, image.crop(box), args.device)
        health.append(
            {
                "image": row["image"],
                "label": row["label"],
                "manual_prediction": manual_label,
                "manual_confidence": manual_confidence,
                "manual_correct": manual_label == row["label"],
                "detections": len(boxes),
                "best_iou": best_iou,
                "matched": best_iou >= 0.5,
                "auto_prediction": auto_label,
                "auto_confidence": auto_confidence,
                "auto_correct": auto_label == row["label"] if auto_label else "",
            }
        )
    write_csv(args.output / "health-crops.csv", health, list(health[0]))
    matched = [row for row in health if row["matched"]]
    health_summary = {
        "training_diagnostic_only": True,
        "reviewed_images": len(health),
        "detector_imgsz": args.health_imgsz or inference["detector_imgsz"],
        "manual_correct": sum(row["manual_correct"] for row in health),
        "matched_at_iou_05": len(matched),
        "manual_correct_on_matched": sum(row["manual_correct"] for row in matched),
        "auto_correct_on_matched": sum(row["auto_correct"] for row in matched),
        "missed_reviewed_birds": len(health) - len(matched),
        "per_class": {
            label: {
                "images": sum(row["label"] == label for row in health),
                "manual_correct": sum(
                    row["label"] == label and row["manual_correct"] for row in health
                ),
                "matched": sum(row["label"] == label for row in matched),
            }
            for label in ("dead", "healthy")
        },
    }
    write_json(args.output / "health-summary.json", health_summary)
    print("Health diagnostic:", health_summary, flush=True)
    if args.health_only:
        write_json(
            args.output / "summary.json",
            {
                "status": "complete",
                "health": health_summary,
                "detector": detector_info,
                "classifier": classifier_info,
                "inference": inference,
                "device": args.device,
                "health_manifest_sha256": file_hash(health_root / "manifest.csv"),
                "limitations": "Training diagnostic; only the reviewed bird has a label. Best-IoU pairing uses manual annotation, not deployment logic. No test data used.",
            },
        )
        return

    pio = ROOT / settings["pio_output"]
    rows = [row for row in read_rows(pio / "manifest.csv") if row["split"] == "val"]
    if not rows:
        raise ValueError("Validação vazia.")
    experiments = []
    for nms_iou in (0.7, 0.5):
        for threshold in (0.25, 0.4, 0.55):
            records = []
            for row in rows:
                name = Path(row["source"]).name
                targets = []
                width, height = int(row["width"]), int(row["height"])
                for line in (
                    (pio / "labels/val" / Path(name).with_suffix(".txt")).read_text().splitlines()
                ):
                    _, x, y, w, h = map(float, line.split())
                    targets.append(
                        [
                            (x - w / 2) * width,
                            (y - h / 2) * height,
                            (x + w / 2) * width,
                            (y + h / 2) * height,
                        ]
                    )
                prediction = detector.predict(
                    str(pio / "images/val" / name),
                    imgsz=inference["detector_imgsz"],
                    conf=threshold,
                    iou=nms_iou,
                    max_det=inference["max_det"],
                    device=args.device,
                    verbose=False,
                )[0]
                order = prediction.boxes.conf.argsort(descending=True)
                boxes = prediction.boxes.xyxy[order].tolist()
                tp = true_positives(boxes, targets)
                records.append(
                    {
                        "image": name,
                        "annotated": len(targets),
                        "detected": len(boxes),
                        "tp": tp,
                        "fp": len(boxes) - tp,
                        "fn": len(targets) - tp,
                        "error": len(boxes) - len(targets),
                    }
                )
            tp, fp, fn = (sum(row[key] for row in records) for key in ("tp", "fp", "fn"))
            precision, recall = tp / max(tp + fp, 1), tp / max(tp + fn, 1)
            result = {
                "confidence": threshold,
                "nms_iou": nms_iou,
                "images": len(records),
                "precision_at_iou_05": precision,
                "recall_at_iou_05": recall,
                "f1_at_iou_05": 2 * tp / max(2 * tp + fp + fn, 1),
                "count_mae": sum(abs(row["error"]) for row in records) / len(records),
                "count_bias": sum(row["error"] for row in records) / len(records),
            }
            experiments.append(result)
            write_csv(
                args.output / f"val-conf{threshold}-iou{nms_iou}.csv", records, list(records[0])
            )
            write_json(args.output / "validation-grid.json", experiments)
            print("Validation:", result, flush=True)
    write_json(
        args.output / "summary.json",
        {
            "status": "complete",
            "detector": detector_info,
            "classifier": classifier_info,
            "health_manifest_sha256": file_hash(health_root / "manifest.csv"),
            "pio_manifest_sha256": file_hash(pio / "manifest.csv"),
            "device": args.device,
            "health": health_summary,
            "validation": experiments,
            "limitations": "Health is training data, one reviewed bird per image; other detections have no health labels. Best-IoU crop pairing is an oracle diagnostic, not deployment selection. PIO validation only; greedy matching at IoU 0.5, not COCO AP. No settings or weights changed.",
        },
    )


if __name__ == "__main__":
    main()
