"""Prepara o detector PIO sem modificar imagens ou anotações originais."""

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.preparation.pio import prepare_pio


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dataset", choices=("pio",))
    parser.add_argument("--config", type=Path, default=PROJECT_ROOT / "config.json")
    parser.add_argument("--output", type=Path, help="Pasta nova para o PIO preparado.")
    args = parser.parse_args()
    try:
        config_path = args.config.resolve()
        settings = json.loads(config_path.read_text(encoding="utf-8"))
        root = config_path.parent
        result = prepare_pio(
            root / settings["pio_source"],
            args.output or root / settings["pio_output"],
            settings["split_ratios"],
            settings["seed"],
        )
    except (OSError, ValueError, KeyError) as error:
        print(f"Erro: {error}", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
