"""Limpeza conservadora do PIO e exportação no formato YOLO."""

import math
import re
import shutil
from collections import defaultdict
from pathlib import Path

import yaml
from PIL import Image

from .common import (
    SPLITS,
    assign_splits,
    file_hash,
    merge_related_groups,
    new_output,
    validate_splits,
    write_csv,
    write_json,
)


def read_boxes(path: Path) -> tuple[list[tuple], list[dict]]:
    """Descarta somente caixas sem área; outros defeitos exigem investigação."""
    boxes, discarded = [], []
    for number, line in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), 1):
        if not line.strip():
            continue
        values = tuple(float(value) for value in line.split())
        if len(values) != 5 or values[0] != 0 or not all(map(math.isfinite, values)):
            raise ValueError(f"Anotação inválida em {path}:{number}")
        _, x, y, width, height = values
        if width == 0 or height == 0:
            discarded.append({"line": number, "reason": "zero_area", "annotation": line})
            continue
        normalized = 0 <= x <= 1 and 0 <= y <= 1 and 0 < width <= 1 and 0 < height <= 1
        inside = x - width / 2 >= -1e-5 and y - height / 2 >= -1e-5
        inside = inside and x + width / 2 <= 1 + 1e-5 and y + height / 2 <= 1 + 1e-5
        if not normalized or not inside:
            raise ValueError(f"Caixa fora da imagem em {path}:{number}")
        boxes.append(values)
    return sorted(boxes), discarded


def collect_images(source: Path) -> tuple[list[dict], list[dict]]:
    records, discarded = [], []
    paths = sorted((source / "images").glob("*/*.jpg"))
    if not paths:
        raise ValueError(f"Nenhuma imagem encontrada em {source / 'images'}")
    for path in paths:
        match = re.fullmatch(r"([CP]-W[1-6])-(?:V)?\d+", path.stem)
        label_path = source / "labels" / path.parent.name / f"{path.stem}.txt"
        boxes, invalid = read_boxes(label_path)
        discarded.extend(
            {"source": label_path.relative_to(source).as_posix(), **item} for item in invalid
        )
        with Image.open(path) as image:
            image.load()
            width, height = image.size
        records.append(
            {
                "path": path,
                "source": path.relative_to(source).as_posix(),
                "original_split": path.parent.name,
                "capture_group": match[1] if match else "",
                "group": match[1] if match else "unknown",
                "sha256": file_hash(path),
                "label": "chicken",
                "boxes": boxes,
                "width": width,
                "height": height,
            }
        )
    return records, discarded


def select_unique_images(records: list[dict]) -> tuple[list[dict], list[dict]]:
    by_hash = defaultdict(list)
    for row in records:
        by_hash[row["sha256"]].append(row)
    selected, excluded = [], []
    for copies in by_hash.values():
        canonical = copies[0]
        if any(not row["capture_group"] for row in copies):
            for row in copies:
                excluded.append(
                    {
                        "source": row["source"],
                        "reason": "unknown_capture_group",
                        "sha256": row["sha256"],
                    }
                )
            continue
        # Não escolhe arbitrariamente entre rótulos diferentes para a mesma foto.
        if any(row["boxes"] != canonical["boxes"] for row in copies):
            for row in copies:
                excluded.append(
                    {
                        "source": row["source"],
                        "reason": "conflicting_annotations",
                        "sha256": row["sha256"],
                    }
                )
            continue
        selected.append(canonical)
        for row in copies[1:]:
            excluded.append(
                {"source": row["source"], "reason": "exact_duplicate", "sha256": row["sha256"]}
            )
    return selected, excluded


def prepare_pio(source: Path, output: Path, ratios: dict, seed: int) -> dict:
    records, discarded = collect_images(source)
    # Une os grupos ANTES de excluir cópias, preservando as relações de captura.
    merge_related_groups(records)
    selected, excluded = select_unique_images(records)
    assignment = assign_splits(selected, ratios, seed)
    for row in selected:
        row["split"] = assignment[row["group"]]
    counts = validate_splits(selected)
    new_output(output, source)

    for split in SPLITS:
        (output / "images" / split).mkdir(parents=True)
        (output / "labels" / split).mkdir(parents=True)
    for row in selected:
        name = row["path"].name
        shutil.copyfile(row["path"], output / "images" / row["split"] / name)
        lines = ["0 " + " ".join(f"{value:.6f}" for value in box[1:]) for box in row["boxes"]]
        label = output / "labels" / row["split"] / f"{row['path'].stem}.txt"
        label.write_text("\n".join(lines) + "\n", encoding="utf-8")
        row["box_count"] = len(row["boxes"])
        row["label_sha256"] = file_hash(label)

    configuration = {
        "path": output.resolve().as_posix(),
        "train": "images/train",
        "val": "images/val",
        "test": "images/test",
        "names": {0: "chicken"},
    }
    (output / "dataset.yaml").write_text(
        yaml.safe_dump(configuration, sort_keys=False), encoding="utf-8"
    )
    write_csv(
        output / "manifest.csv",
        selected,
        [
            "source",
            "original_split",
            "sha256",
            "label_sha256",
            "group",
            "split",
            "label",
            "width",
            "height",
            "box_count",
        ],
    )
    write_csv(output / "excluded.csv", excluded, ["source", "reason", "sha256"])
    write_csv(output / "discarded_boxes.csv", discarded, ["source", "line", "reason", "annotation"])
    summary = {
        "status": "ready",
        "seed": seed,
        "target_ratios": ratios,
        "counts": counts,
        "source_images": len(records),
        "selected_images": len(selected),
        "excluded_images": len(excluded),
        "discarded_boxes": len(discarded),
        "groups": assignment,
        "boxes": sum(len(row["boxes"]) for row in selected),
        "grouping": "house/week, joined by identical images before exclusions",
        "limitation": "Grouping does not establish independence of individual animals across weeks.",
    }
    write_json(output / "summary.json", summary)
    return summary
