"""Operações compartilhadas pela preparação dos dois datasets."""

import csv
import hashlib
import json
import math
import random
from collections import Counter, defaultdict
from pathlib import Path

SPLITS = ("train", "val", "test")
HEALTH_CLASSES = ("healthy", "sick", "dead")


def file_hash(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def merge_related_groups(records: list[dict]) -> None:
    """Une grupos ligados por imagens idênticas, inclusive ligações transitivas."""
    parent = {row["group"]: row["group"] for row in records}

    def find(group: str) -> str:
        while parent[group] != group:
            parent[group] = parent[parent[group]]
            group = parent[group]
        return group

    first_group = {}
    for row in records:
        group = find(row["group"])
        previous = first_group.setdefault(row["sha256"], group)
        left, right = sorted((find(previous), group))
        parent[right] = left

    for row in records:
        row["group"] = find(row["group"])


def assign_splits(records: list[dict], ratios: dict, seed: int) -> dict[str, str]:
    """Busca uma divisão próxima das proporções sem separar grupos de captura.

    A escolha usa apenas contagens e classes, nunca desempenho dos modelos.
    A semente e a ordenação tornam o resultado reproduzível.
    """
    if set(ratios) != set(SPLITS):
        raise ValueError("Informe as proporções train, val e test.")
    if any(not math.isfinite(value) or value <= 0 for value in ratios.values()):
        raise ValueError("As proporções devem ser positivas e finitas.")
    if not math.isclose(sum(ratios.values()), 1.0):
        raise ValueError("As proporções devem somar 1.")

    grouped = defaultdict(Counter)
    totals = Counter()
    for row in records:
        grouped[row["group"]][row["label"]] += 1
        totals[row["label"]] += 1
    if not totals:
        raise ValueError("Não há imagens aceitas para preparar.")
    for label in totals:
        if sum(label in counts for counts in grouped.values()) < 3:
            raise ValueError(f"A classe {label} precisa de pelo menos três grupos independentes.")

    generator = random.Random(seed)
    groups = sorted(grouped)
    best_assignment = None
    best_score = float("inf")
    # Poucos grupos grandes impedem proporções exatas. Preservar os grupos tem prioridade.
    for _ in range(5000):
        choices = generator.choices(SPLITS, weights=[ratios[s] for s in SPLITS], k=len(groups))
        counts = {split: Counter() for split in SPLITS}
        for group, split in zip(groups, choices):
            counts[split].update(grouped[group])
        if any(counts[split][label] == 0 for split in SPLITS for label in totals):
            continue
        score = sum(
            abs(counts[split][label] / total - ratios[split])
            for split in SPLITS
            for label, total in totals.items()
        )
        if score < best_score:
            best_score = score
            best_assignment = dict(zip(groups, choices))
    if best_assignment is None:
        raise ValueError(
            "Não foi possível representar todas as classes nas três divisões. Revise os grupos."
        )
    return best_assignment


def validate_splits(records: list[dict]) -> dict:
    """Falha se um grupo ou uma imagem de origem atravessar as divisões."""
    for key in ("group", "sha256"):
        seen = {}
        for row in records:
            previous = seen.setdefault(row[key], row["split"])
            if previous != row["split"]:
                raise ValueError(f"Vazamento entre divisões: {key}={row[key]}")
    labels = {row["label"] for row in records}
    counts = {
        split: Counter(row["label"] for row in records if row["split"] == split) for split in SPLITS
    }
    if any(counts[split][label] == 0 for split in SPLITS for label in labels):
        raise ValueError("Todas as classes devem estar presentes em cada divisão.")
    return counts


def new_output(path: Path, source: Path) -> None:
    """Recusa sobrescrever dados ou reutilizar uma saída antiga/parcial."""
    path, source = path.resolve(), source.resolve()
    if path == source or path.is_relative_to(source) or source.is_relative_to(path):
        raise ValueError("A saída deve ficar separada dos dados originais.")
    if path.exists():
        raise ValueError(f"A saída já existe: {path}. Use --output com uma pasta nova.")
    path.mkdir(parents=True)
