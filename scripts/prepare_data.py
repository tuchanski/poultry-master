"""Ponto de entrada da etapa 2. Execute a partir de qualquer diretório."""

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.preparation.health import prepare_health
from src.preparation.pio import prepare_pio
from src.preparation.review import create_review


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepara os datasets sem modificar os originais.")
    parser.add_argument("dataset", choices=("pio", "health-review", "health"))
    parser.add_argument(
        "--mode",
        choices=("grouped", "demonstration"),
        default="grouped",
        help="demonstration gera só treino, sem validação/teste independentes.",
    )
    parser.add_argument("--config", type=Path, default=PROJECT_ROOT / "config.json")
    parser.add_argument(
        "--output", type=Path, help="Pasta nova para pio/health; caminho do CSV para health-review."
    )
    args = parser.parse_args()
    try:
        config_path = args.config.resolve()
        settings = json.loads(config_path.read_text(encoding="utf-8"))
        root = config_path.parent
        if args.dataset == "health-review":
            output = args.output or root / settings["health_review"]
            result = create_review(
                root / settings["health_source"],
                output,
                PROJECT_ROOT / "scripts/health_review.html",
            )
        elif args.dataset == "pio":
            output = args.output or root / settings["pio_output"]
            result = prepare_pio(
                root / settings["pio_source"], output, settings["split_ratios"], settings["seed"]
            )
        else:
            output = args.output or root / settings["health_output"]
            result = prepare_health(
                root / settings["health_source"],
                root / settings["health_review"],
                output,
                settings["split_ratios"],
                settings["seed"],
                selection=(
                    root / settings["health_selection"]
                    if settings.get("health_selection")
                    else None
                ),
                mode=args.mode,
            )
    except (OSError, ValueError, KeyError) as error:
        print(f"Erro: {error}", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
