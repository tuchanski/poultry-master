"""Analisa uma foto RGB com os dois modelos treinados do MVP."""

import argparse
import json
import math
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from PIL import Image, ImageOps

from src.pipeline import classify_birds
from src.preparation.common import file_hash
from src.reporting import WARNING, annotate, summarize

ROOT = Path(__file__).resolve().parent
os.environ["YOLO_CONFIG_DIR"] = str(ROOT / "outputs/ultralytics")


def load_model(path, task, labels):
    from ultralytics import YOLO

    if not path.is_file():
        raise ValueError(f"Peso ausente: {path}")
    metadata = json.loads(path.with_suffix(".json").read_text(encoding="utf-8"))
    digest = file_hash(path)
    if metadata["weights_sha256"] != digest:
        raise ValueError(f"Peso não corresponde aos metadados: {path}")
    model = YOLO(str(path))
    names = {str(key): value for key, value in model.names.items()}
    if (
        model.task != task
        or set(names.values()) != labels
        or metadata["task"] != task
        or metadata["classes"] != names
    ):
        raise ValueError(f"Modelo ou mapeamento incompatível: {path}")
    return model, {
        "path": str(path),
        "sha256": digest,
        "classes": names,
        "created_at": metadata["created_at"],
        "training_mode": metadata.get("mode"),
        "independent_evaluation": metadata.get("independent_evaluation", "pending"),
    }


def validate_settings(settings):
    for key in ("confidence", "iou"):
        value = settings[key]
        if not isinstance(value, (float, int)) or not math.isfinite(value) or not 0 < value <= 1:
            raise ValueError(f"Parâmetro inválido: {key}")
    for key in ("detector_imgsz", "classifier_imgsz", "max_det", "classifier_batch"):
        if type(settings[key]) is not int or settings[key] < 1:
            raise ValueError(f"Parâmetro deve ser inteiro positivo: {key}")


def run(args):
    started = time.monotonic()
    config = args.config.resolve()
    settings = json.loads(config.read_text(encoding="utf-8"))["inference"]
    if args.device:
        settings["device"] = args.device
    validate_settings(settings)
    source, output = args.image.resolve(), args.output.resolve()
    if output.exists():
        raise ValueError("A pasta de saída já existe. Escolha uma pasta nova.")
    with Image.open(source) as original:
        image = ImageOps.exif_transpose(original).convert("RGB")
    detector, detector_info = load_model(
        config.parent / settings["detector"], "detect", {"chicken"}
    )
    classifier, classifier_info = load_model(
        config.parent / settings["classifier"], "classify", {"healthy", "dead"}
    )
    birds, limit_reached = classify_birds(image, detector, classifier, settings)
    summary = summarize(birds)
    report = {
        "schema_version": 1,
        "analysis_id": str(uuid4()),
        "created_at": datetime.now().astimezone().isoformat(),
        "image": {
            "path": str(source),
            "sha256": file_hash(source),
            "width": image.width,
            "height": image.height,
            "coordinates": "pixels after EXIF orientation; xyxy, exclusive upper bounds",
        },
        "models": {"detector": detector_info, "classifier": classifier_info},
        "parameters": settings,
        "summary": summary,
        "birds": birds,
        "detection_limit_reached": limit_reached,
        "warning": WARNING,
        "annotated_image": str(output / "annotated.jpg"),
    }
    annotated = annotate(image, birds)
    # Só grava após inferência completa. JSON é o último arquivo, marcador de sucesso.
    output.mkdir(parents=True)
    annotated.save(output / "annotated.jpg", quality=95)
    report["processing_seconds"] = round(time.monotonic() - started, 3)
    temporary = output / "report.json.tmp"
    temporary.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )
    temporary.replace(output / "report.json")
    print(f"{summary['message']}. Total: {len(birds)}")
    for label, count in summary["counts"].items():
        print(f"{label}: {count} ({summary['percentages'][label]:.2f}%)")
    print(
        f"Potencialmente mortas — verificar presencialmente: {summary['verification_candidates']}"
    )
    if limit_reached:
        print("Limite de detecções atingido; a contagem pode estar truncada.")
    print(WARNING)
    print(f"Avaliação independente do classificador: {classifier_info['independent_evaluation']}")
    print(f"Resultados: {output}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--config", type=Path, default=ROOT / "config.json")
    parser.add_argument("--device", help="cpu (padrão) ou índice da GPU, por exemplo 0")
    args = parser.parse_args()
    try:
        run(args)
    except Exception as error:
        print(f"Erro na análise: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
