"""Recortes de saúde: aceita somente decisões explícitas no CSV de revisão."""

import csv
from collections import Counter
from pathlib import Path

from PIL import Image

from .common import (
    HEALTH_CLASSES,
    SPLITS,
    assign_splits,
    file_hash,
    merge_related_groups,
    new_output,
    validate_splits,
    write_csv,
    write_json,
)

REVIEW_FIELDS = ["image", "sha256", "label", "status", "group", "x1", "y1", "x2", "y2", "notes"]


def rgb_images(source: Path) -> list[dict]:
    records = []
    for label in HEALTH_CLASSES:
        paths = sorted((source / label).glob("*_rgb_*.jpg"))
        if not paths:
            raise ValueError(f"Nenhuma imagem RGB na classe {label}.")
        for path in paths:
            records.append(
                {
                    "image": path.relative_to(source).as_posix(),
                    "sha256": file_hash(path),
                    "label": label,
                }
            )
    return records


def load_review(source: Path, review: Path) -> tuple[list[dict], dict]:
    originals = {row["image"]: row for row in rgb_images(source)}
    with review.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        if not set(REVIEW_FIELDS).issubset(reader.fieldnames or []):
            raise ValueError("O CSV de revisão não tem todas as colunas esperadas.")
        rows = list(reader)
    if len({row["image"] for row in rows}) != len(rows) or set(originals) != {
        row["image"] for row in rows
    }:
        raise ValueError(
            "A revisão deve conter exatamente uma linha para cada imagem RGB original."
        )
    status_counts = Counter(row["status"] for row in rows)
    if set(status_counts) - {"pending", "accepted", "excluded"}:
        raise ValueError("Status desconhecido; use pending, accepted ou excluded.")
    if status_counts["pending"]:
        raise ValueError(
            f"Revisão incompleta: {status_counts['pending']} imagens pendentes em {review}."
        )

    accepted = []
    for row in rows:
        original = originals[row["image"]]
        if row["sha256"] != original["sha256"] or row["label"] != original["label"]:
            raise ValueError(f"Imagem ou rótulo de origem alterado: {row['image']}")
        if row["status"] == "excluded":
            if not row["notes"].strip():
                raise ValueError(f"Registre o motivo da exclusão: {row['image']}")
            continue
        if not row["group"].strip():
            raise ValueError(f"Informe o animal/sessão de captura: {row['image']}")
        path = source / row["image"]
        box = tuple(int(row[key]) for key in ("x1", "y1", "x2", "y2"))
        with Image.open(path) as image:
            image.load()
            width, height = image.size
        x1, y1, x2, y2 = box
        if not (0 <= x1 < x2 <= width and 0 <= y1 < y2 <= height):
            raise ValueError(f"Recorte inválido em {row['image']}: {box}")
        accepted.append({**row, "path": path, "box": box, "group": row["group"].strip()})
    if {row["label"] for row in accepted} != set(HEALTH_CLASSES):
        raise ValueError("A revisão precisa de imagens aceitas nas três classes.")
    return accepted, dict(status_counts)


def prepare_health(source: Path, review: Path, output: Path, ratios: dict, seed: int) -> dict:
    records, review_counts = load_review(source, review)
    merge_related_groups(records)
    # Uma só ocorrência por foto idêntica. Não escolhe entre recortes conflitantes.
    unique = {}
    for row in records:
        previous = unique.setdefault(row["sha256"], row)
        if previous["box"] != row["box"] or previous["label"] != row["label"]:
            raise ValueError(f"Decisões diferentes para uma imagem duplicada: {row['image']}")
    selected = list(unique.values())
    assignment = assign_splits(selected, ratios, seed)
    for row in selected:
        row["split"] = assignment[row["group"]]
    counts = validate_splits(selected)
    new_output(output, source)

    for split in SPLITS:
        for label in HEALTH_CLASSES:
            (output / split / label).mkdir(parents=True)
    for row in selected:
        # A imagem de origem já recebeu sua divisão antes de gerar qualquer recorte.
        name = f"{row['path'].stem}.png"
        relative = Path(row["split"]) / row["label"] / name
        with Image.open(row["path"]) as image:
            image.convert("RGB").crop(row["box"]).save(output / relative)
        row["crop"] = relative.as_posix()
        row["crop_sha256"] = file_hash(output / relative)
    # Mesmo recortes vindos de fotos distintas não devem repetir pixels entre divisões.
    validate_splits([{**row, "sha256": row["crop_sha256"]} for row in selected])
    write_csv(output / "manifest.csv", selected, REVIEW_FIELDS + ["split", "crop", "crop_sha256"])
    summary = {
        "status": "ready",
        "seed": seed,
        "target_ratios": ratios,
        "counts": counts,
        "review_sha256": file_hash(review),
        "review_counts": review_counts,
        "selected_crops": len(selected),
        "groups": assignment,
        "label_source": "Original image label, retained only after explicit single-bird crop review.",
    }
    write_json(output / "summary.json", summary)
    return summary
