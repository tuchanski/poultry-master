"""Seleciona imagens binárias e sugere caixas sem aprovar nenhum recorte."""

import argparse
import csv
import json
import math
import os
import random
import sys
from collections import Counter
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ["YOLO_CONFIG_DIR"] = str(ROOT / "outputs" / "ultralytics")

from src.preparation.common import HEALTH_CLASSES, file_hash, write_csv, write_json
from src.preparation.health import REVIEW_FIELDS, rgb_images
from src.preparation.review import write_review_page


def select_images(source: Path, per_class: int, seed: int) -> list[dict]:
    if per_class < 1:
        raise ValueError("A quantidade por classe deve ser positiva.")
    unique = {}
    for row in rgb_images(source):
        previous = unique.setdefault(row["sha256"], row)
        if previous["label"] != row["label"]:
            raise ValueError("Imagem idêntica em classes diferentes.")
    generator = random.Random(seed)
    selected = []
    for label in HEALTH_CLASSES:
        candidates = [row for row in unique.values() if row["label"] == label]
        if per_class > len(candidates):
            raise ValueError(f"Existem apenas {len(candidates)} imagens únicas de {label}.")
        selected.extend(generator.sample(candidates, per_class))
    return sorted(selected, key=lambda row: (row["label"], row["image"]))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--per-class", type=int, default=40)
    parser.add_argument("--device", default="0")
    parser.add_argument("--conf", type=float, default=0.4)
    parser.add_argument("--imgsz", type=int, default=320)
    parser.add_argument(
        "--manual",
        action="store_true",
        help="Cria só a seleção para revisão manual, sem sugestões.",
    )
    parser.add_argument("--output", type=Path)
    parser.add_argument("--prior-review", type=Path, default=ROOT / "data/review/health.csv")
    args = parser.parse_args()
    if not 0 < args.conf <= 1:
        parser.error("--conf deve estar entre 0 e 1.")
    if args.imgsz < 32:
        parser.error("--imgsz deve ser pelo menos 32.")
    settings = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
    source = ROOT / settings["health_source"]
    review = args.output or ROOT / settings["health_review"]
    if review.parent.exists():
        raise ValueError(
            "A pasta de saída já existe. Use --output em uma pasta nova para preservar decisões."
        )
    selected = select_images(source, args.per_class, settings["seed"])
    previous = {}
    if args.prior_review.is_file():
        with args.prior_review.open(encoding="utf-8-sig", newline="") as stream:
            previous = {row["image"]: row for row in csv.DictReader(stream)}

    weights = ROOT / "models/detector.pt"
    model = None
    if not args.manual:
        from ultralytics import YOLO

        if not weights.is_file():
            raise ValueError("Treine o detector antes de gerar sugestões.")
        model = YOLO(str(weights))
        if model.task != "detect" or set(model.names.values()) != {"chicken"}:
            raise ValueError("O modelo não é o detector chicken esperado.")
    rows, suggestions = [], []
    for original in selected:
        candidates = []
        if model is not None:
            with Image.open(source / original["image"]) as image:
                width, height = image.size
                prediction = model.predict(
                    image.convert("RGB"),
                    device=args.device,
                    imgsz=args.imgsz,
                    conf=args.conf,
                    max_det=20,
                    verbose=False,
                )[0]
            for box, confidence in zip(
                prediction.boxes.xyxy.tolist(), prediction.boxes.conf.tolist()
            ):
                x1, y1 = max(0, math.floor(box[0])), max(0, math.floor(box[1]))
                x2, y2 = min(width, math.ceil(box[2])), min(height, math.ceil(box[3]))
                if x2 > x1 and y2 > y1:
                    candidates.append({"box": [x1, y1, x2, y2], "confidence": round(confidence, 5)})
        row = {
            **original,
            "status": "pending",
            "group": "",
            "notes": "",
            "x1": "",
            "y1": "",
            "x2": "",
            "y2": "",
            "candidates": candidates,
        }
        if len(candidates) == 1:
            row.update(dict(zip(("x1", "y1", "x2", "y2"), candidates[0]["box"])))
        prior = previous.get(row["image"])
        if prior:
            if prior["sha256"] != row["sha256"] or prior["label"] != row["label"]:
                raise ValueError(f"Revisão anterior não corresponde à origem: {row['image']}")
            # Preserva também caixas manuais ainda pendentes, grupos e notas.
            if prior["status"] != "pending" or prior["x1"] != "":
                row.update({field: prior[field] for field in REVIEW_FIELDS})
            else:
                row.update(group=prior["group"], notes=prior["notes"])
        rows.append(row)
        suggestions.append({"image": row["image"], "candidates": candidates})

    review.parent.mkdir(parents=True)
    write_csv(review, rows, REVIEW_FIELDS)
    write_review_page(source, review, ROOT / "scripts/health_review.html", rows)
    write_json(
        review.parent / "selection.json",
        {
            "images": [row["image"] for row in rows],
            "seed": settings["seed"],
            "per_class": args.per_class,
            "classes": list(HEALTH_CLASSES),
        },
    )
    report = {
        "mode": "manual" if args.manual else "suggested",
        "detector_sha256": file_hash(weights) if model is not None else None,
        "conf": args.conf if model is not None else None,
        "imgsz": args.imgsz if model is not None else None,
        "max_det": 20,
        "total": len(rows),
        "suggestion_counts": dict(Counter(len(row["candidates"]) for row in rows)),
        "decisions": dict(Counter(row["status"] for row in rows)),
        "suggestions": suggestions,
    }
    write_json(review.parent / "suggestions.json", report)
    print(
        json.dumps({key: value for key, value in report.items() if key != "suggestions"}, indent=2)
    )
    print(f"Revise no navegador: {review.with_suffix('.html')}")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError) as error:
        print(f"Erro: {error}", file=sys.stderr)
        raise SystemExit(1)
