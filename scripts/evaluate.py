"""Avalia o detector no teste reservado, sem ajustar parâmetros ou pesos."""

import argparse
import csv
import json
import platform
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from analyze import load_model
from src.preparation.common import file_hash, write_csv, write_json


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--device", default="0")
    parser.add_argument("--output", type=Path, default=ROOT / "outputs/evaluation/detector-test")
    args = parser.parse_args()
    output = args.output.resolve()
    if output.exists():
        raise ValueError("Saída já existe; escolha uma pasta nova com --output.")
    settings = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
    inference = settings["inference"]
    dataset = ROOT / settings["pio_output"]
    with (dataset / "manifest.csv").open(encoding="utf-8-sig", newline="") as stream:
        rows = [row for row in csv.DictReader(stream) if row["split"] == "test"]
    if not rows:
        raise ValueError("Manifesto sem imagens de teste.")
    detector, metadata = load_model(ROOT / inference["detector"], "detect", {"chicken"})
    # Confiança baixa permite calcular a curva precision/recall e AP.
    # A contagem abaixo usa separadamente o limiar já fixado na aplicação.
    import torch
    import ultralytics

    output.mkdir(parents=True)
    started = time.monotonic()
    metrics = detector.val(
        data=str(dataset / "dataset.yaml"),
        split="test",
        device=args.device,
        imgsz=inference["detector_imgsz"],
        batch=8,
        workers=0,
        conf=0.001,
        iou=inference["iou"],
        max_det=inference["max_det"],
        plots=True,
        project=str(output),
        name="validation",
        exist_ok=False,
    )
    counts = []
    for row in rows:
        path = dataset / "images/test" / Path(row["source"]).name
        prediction = detector.predict(
            str(path),
            device=args.device,
            imgsz=inference["detector_imgsz"],
            conf=inference["confidence"],
            iou=inference["iou"],
            max_det=inference["max_det"],
            verbose=False,
        )[0]
        detected, annotated = len(prediction.boxes), int(row["box_count"])
        counts.append(
            {
                "image": path.name,
                "annotated": annotated,
                "detected": detected,
                "error": detected - annotated,
                "absolute_error": abs(detected - annotated),
                "limit_reached": detected >= inference["max_det"],
            }
        )
    write_csv(output / "counts.csv", counts, list(counts[0]))
    report = {
        "status": "complete",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "split": "test",
        "images": len(rows),
        "model": metadata,
        "manifest_sha256": file_hash(dataset / "manifest.csv"),
        "parameters": {**inference, "device": args.device, "metric_confidence": 0.001},
        "metrics": {key: float(value) for key, value in metrics.results_dict.items()},
        "counting": {
            "mae": sum(row["absolute_error"] for row in counts) / len(counts),
            "mean_error": sum(row["error"] for row in counts) / len(counts),
            "annotated_total": sum(row["annotated"] for row in counts),
            "detected_total": sum(row["detected"] for row in counts),
            "images_at_limit": sum(row["limit_reached"] for row in counts),
        },
        "hardware": {
            "platform": platform.platform(),
            "processor": platform.processor(),
            "gpu": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
        },
        "versions": {"torch": torch.__version__, "ultralytics": ultralytics.__version__},
        "seconds": round(time.monotonic() - started, 3),
        "classifier_evaluation": "pending: all reviewed crops were used for training",
        "integrated_dead_evaluation": "qualitative only; no independent individual health labels",
        "limitations": "Known groups/hashes separated; animal independence and near-duplicates not established.",
    }
    write_json(output / "summary.json", report)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"Erro na avaliação: {error}", file=sys.stderr)
        raise SystemExit(1)
