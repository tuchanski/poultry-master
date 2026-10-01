"""Recortes de saúde: aceita somente decisões explícitas no CSV de revisão."""

import csv
import json
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


def load_review(
    source: Path, review: Path, selection: Path | None = None, require_groups: bool = True
) -> tuple[list[dict], dict]:
    originals = {row["image"]: row for row in rgb_images(source)}
    expected_images = set(originals)
    if selection is not None:
        selected_names = json.loads(selection.read_text(encoding="utf-8"))["images"]
        expected_images = set(selected_names)
        if not expected_images or len(expected_images) != len(selected_names):
            raise ValueError("Seleção vazia ou com imagens repetidas.")
        if not expected_images.issubset(originals):
            raise ValueError("A seleção contém imagens fora das classes healthy/dead.")
    with review.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        if not set(REVIEW_FIELDS).issubset(reader.fieldnames or []):
            raise ValueError("O CSV de revisão não tem todas as colunas esperadas.")
        rows = list(reader)
    if len({row["image"] for row in rows}) != len(rows) or expected_images != {
        row["image"] for row in rows
    }:
        raise ValueError("A revisão deve conter exatamente uma linha para cada imagem da seleção.")
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
        if require_groups and not row["group"].strip():
            raise ValueError(f"Informe o animal/sessão de captura: {row['image']}")
        if not require_groups and not row["group"].strip() and not row["notes"].strip():
            raise ValueError(f"Registre nas notas a ausência de grupo conhecido: {row['image']}")
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
        raise ValueError("A revisão precisa de imagens aceitas nas classes healthy e dead.")
    return accepted, dict(status_counts)


def prepare_health(
    source: Path,
    review: Path,
    output: Path,
    ratios: dict,
    seed: int,
    selection: Path | None = None,
    mode: str = "grouped",
) -> dict:
    if mode not in ("grouped", "demonstration"):
        raise ValueError("Modo inválido: use grouped ou demonstration.")
    records, review_counts = load_review(
        source, review, selection, require_groups=mode == "grouped"
    )
    if mode == "grouped":
        merge_related_groups(records)
    # Uma só ocorrência por foto idêntica. Não escolhe entre recortes conflitantes.
    unique = {}
    for row in records:
        previous = unique.setdefault(row["sha256"], row)
        if previous["box"] != row["box"] or previous["label"] != row["label"]:
            raise ValueError(f"Decisões diferentes para uma imagem duplicada: {row['image']}")
    selected = list(unique.values())
    assignment = (
        assign_splits(selected, ratios, seed)
        if mode == "grouped"
        else {row["group"]: "train" for row in selected}
    )
    for row in selected:
        row["split"] = assignment[row["group"]]
    counts = (
        validate_splits(selected)
        if mode == "grouped"
        else {"train": Counter(row["label"] for row in selected)}
    )
    new_output(output, source)

    for split in SPLITS if mode == "grouped" else ("train",):
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
    if mode == "grouped":
        validate_splits([{**row, "sha256": row["crop_sha256"]} for row in selected])
    write_csv(output / "manifest.csv", selected, REVIEW_FIELDS + ["split", "crop", "crop_sha256"])
    summary = {
        "status": "ready",
        "mode": mode,
        "classes": list(HEALTH_CLASSES),
        "independent_evaluation": (
            "pending" if mode == "demonstration" else "requires confirmation of capture groups"
        ),
        "seed": seed,
        "target_ratios": ratios,
        "counts": counts,
        "review_sha256": file_hash(review),
        "selection_sha256": file_hash(selection) if selection is not None else None,
        "review_counts": review_counts,
        "selected_crops": len(selected),
        "groups": assignment,
        "label_source": "Original image label, retained only after explicit single-bird crop review.",
    }
    write_json(output / "summary.json", summary)
    return summary
