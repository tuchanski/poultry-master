"""Carregamento de pesos com validação de metadados e integridade."""

import json
import os
from pathlib import Path

from src.preparation.common import file_hash

ROOT = Path(__file__).resolve().parents[1]
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

