"""Confere as bibliotecas e uma operação simples em CPU e, se disponível, GPU."""

import importlib.metadata
import json
import os
import platform
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
(ROOT / "outputs" / "ultralytics").mkdir(parents=True, exist_ok=True)
os.environ.setdefault("YOLO_CONFIG_DIR", str(ROOT / "outputs" / "ultralytics"))

import cv2
import sklearn
import torch
import torchvision
import ultralytics
from PIL import Image


def main():
    packages = ("torch", "torchvision", "ultralytics", "Pillow", "numpy", "scikit-learn", "PyYAML")
    result = {
        "python": platform.python_version(),
        "platform": platform.platform(),
        "packages": {name: importlib.metadata.version(name) for name in packages},
        "cpu_check": torch.ones(3).sum().item() == 3,
        "cuda_available": torch.cuda.is_available(),
    }
    if result["cuda_available"]:
        result["gpu"] = torch.cuda.get_device_name(0)
        result["gpu_memory_bytes"] = torch.cuda.get_device_properties(0).total_memory
        result["cuda_check"] = torch.ones(3, device="cuda").sum().item() == 3
    output = ROOT / "outputs" / "environment.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
