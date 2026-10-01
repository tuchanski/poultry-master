"""Treina o classificador binário somente sobre recortes revisados e preparados."""

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
    parser.add_argument("--batch", type=int, default=16)
    parser.add_argument("--device", default="0")
    parser.add_argument("--name", default="classifier-baseline")
    parser.add_argument("--dataset", type=Path)
    parser.add_argument("--output", type=Path, default=ROOT / "models/classifier.pt")
    parser.add_argument(
        "--allow-demonstration",
        action="store_true",
        help="Aceita explicitamente treino sem validação/teste independentes.",
    )
    args = parser.parse_args()
    if args.epochs < 1 or args.batch < 1:
        parser.error("Épocas e lote devem ser positivos.")
    if Path(args.name).name != args.name or args.name in (".", ".."):
        parser.error("Escolha um nome simples para a execução.")
    settings = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
    dataset = (args.dataset or ROOT / settings["health_output"]).resolve()
    if not (dataset / "summary.json").is_file():
        raise ValueError("Prepare os recortes revisados antes de treinar o classificador.")
    summary = json.loads((dataset / "summary.json").read_text(encoding="utf-8"))
    if summary["status"] != "ready" or set(summary["classes"]) != {"healthy", "dead"}:
        raise ValueError("O dataset preparado não é binário ou não está pronto.")
    mode = summary["mode"]
    if mode not in ("grouped", "demonstration"):
        raise ValueError("Modo do dataset desconhecido.")
    if mode == "demonstration" and not args.allow_demonstration:
        raise ValueError(
            "Sem avaliação independente. Use --allow-demonstration para assumir essa limitação."
        )
    initial = ROOT / "models/pretrained" / settings["classifier_checkpoint"]
    if not initial.is_file():
        raise ValueError(f"Checkpoint inicial ausente: {initial}")
    run = ROOT / "outputs/training" / args.name
    if run.exists():
        raise ValueError("Execução já existe. Escolha outro --name.")

    from ultralytics import YOLO
    import torch
    import ultralytics
    from src.demonstration_training import DemonstrationTrainer

    started = time.monotonic()
    model = YOLO(str(initial))
    model.train(
        trainer=DemonstrationTrainer if mode == "demonstration" else None,
        data=str(dataset),
        epochs=args.epochs,
        batch=args.batch,
        imgsz=224,
        device=args.device,
        workers=0,
        seed=settings["seed"],
        project=str(run.parent),
        name=run.name,
        exist_ok=False,
        patience=0 if mode == "demonstration" else 5,
        val=mode == "grouped",
        plots=False,
        cache=False,
    )
    checkpoint = model.trainer.last if mode == "demonstration" else model.trainer.best
    args.output.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(checkpoint, args.output)
    with (run / "results.csv").open(newline="", encoding="utf-8") as stream:
        history = list(csv.DictReader(stream))
    metadata = {
        "task": "classify",
        "classes": model.names,
        "mode": mode,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "weights_sha256": file_hash(args.output),
        "initial_sha256": file_hash(initial),
        "dataset_manifest_sha256": file_hash(dataset / "manifest.csv"),
        "review_sha256": summary["review_sha256"],
        "run": str(run),
        "epochs_requested": args.epochs,
        "epochs_completed": len(history),
        "seed": settings["seed"],
        "imgsz": 224,
        "batch": args.batch,
        "seconds": round(time.monotonic() - started, 2),
        "torch": torch.__version__,
        "ultralytics": ultralytics.__version__,
        "selection": (
            "last epoch; fixed budget; no validation"
            if mode == "demonstration"
            else "best validation checkpoint"
        ),
        "independent_evaluation": summary["independent_evaluation"],
        "validation_metrics": None if mode == "demonstration" else model.trainer.metrics,
    }
    write_json(args.output.with_suffix(".json"), metadata)
    print(f"Classificador salvo em {args.output}")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError) as error:
        print(f"Erro: {error}", file=sys.stderr)
        raise SystemExit(1)
