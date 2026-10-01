"""Treina o detector no PIO preparado, sem acessar a divisão de teste."""

import argparse
import csv
import json
import os
import shutil
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ["YOLO_CONFIG_DIR"] = str(ROOT / "outputs" / "ultralytics")

from src.preparation.common import file_hash, write_json


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--epochs", type=int, default=15)
    parser.add_argument("--batch", type=int, default=8)
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--device", default="0")
    parser.add_argument("--name", default="detector-baseline")
    args = parser.parse_args()
    if args.epochs < 1 or args.batch < 1 or args.imgsz < 32:
        parser.error("Épocas, lote e resolução devem ser positivos (imgsz >= 32).")
    if Path(args.name).name != args.name or args.name in (".", ".."):
        parser.error("O nome da execução deve ser um nome de pasta simples.")

    from ultralytics import YOLO
    import torch
    import ultralytics

    settings = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
    dataset = ROOT / settings["pio_output"]
    initial = ROOT / "models" / "pretrained" / settings["detector_checkpoint"]
    output = ROOT / "outputs" / "training" / args.name
    if output.exists():
        raise ValueError(f"Execução já existe: {output}. Escolha outro --name.")
    if not initial.is_file():
        raise ValueError(f"Checkpoint inicial ausente: {initial}")
    summary = json.loads((dataset / "summary.json").read_text(encoding="utf-8"))
    if summary["status"] != "ready":
        raise ValueError("O PIO ainda não está pronto para treinamento.")

    started = time.monotonic()
    model = YOLO(str(initial))
    model.train(
        data=str(dataset / "dataset.yaml"),
        epochs=args.epochs,
        batch=args.batch,
        imgsz=args.imgsz,
        device=args.device,
        workers=0,
        seed=settings["seed"],
        project=str(output.parent),
        name=output.name,
        exist_ok=False,
        patience=5,
        max_det=1500,
        cache=False,
        plots=False,
        amp=True,
        close_mosaic=min(5, args.epochs),
    )
    best = Path(model.trainer.best)
    if not best.is_file():
        raise ValueError("Treinamento não produziu um checkpoint best.pt.")
    destination = ROOT / "models" / "detector.pt"
    shutil.copyfile(best, destination)
    with (output / "results.csv").open(newline="", encoding="utf-8") as stream:
        history = list(csv.DictReader(stream))
    metadata = {
        "task": "detect",
        "classes": {"0": "chicken"},
        "created_at": datetime.now(timezone.utc).isoformat(),
        "weights_sha256": file_hash(destination),
        "initial_sha256": file_hash(initial),
        "dataset_manifest_sha256": file_hash(dataset / "manifest.csv"),
        "dataset": str(dataset),
        "run": str(output),
        "seed": settings["seed"],
        "epochs_requested": args.epochs,
        "epochs_completed": len(history),
        "batch": args.batch,
        "imgsz": args.imgsz,
        "max_det": 1500,
        "device": args.device,
        "seconds": round(time.monotonic() - started, 2),
        "torch": torch.__version__,
        "ultralytics": ultralytics.__version__,
        "selection": "best checkpoint on validation; test not used",
        "last_epoch": history[-1] if history else {},
        "best_validation_metrics": model.trainer.metrics,
    }
    write_json(destination.with_suffix(".json"), metadata)
    print(f"Detector salvo em {destination}")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError) as error:
        print(f"Erro: {error}", file=sys.stderr)
        raise SystemExit(1)
