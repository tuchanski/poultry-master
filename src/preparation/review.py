"""Cria a fila de revisão e uma página HTML local, sem servidor."""

import json
from pathlib import Path

from .common import write_csv
from .health import REVIEW_FIELDS, rgb_images


def create_review(source: Path, review: Path, template: Path) -> dict:
    page = review.with_suffix(".html")
    if review.exists() or page.exists():
        raise ValueError(f"A revisão já existe em {review.parent}; ela não será sobrescrita.")
    rows = []
    first_image = {}
    for original in rgb_images(source):
        previous = first_image.setdefault(original["sha256"], original)
        if previous["label"] != original["label"]:
            raise ValueError(f"Imagem idêntica em classes diferentes: {original['image']}")
        duplicate = previous["image"] != original["image"]
        rows.append(
            {
                **original,
                "status": "excluded" if duplicate else "pending",
                "group": "",
                "x1": "",
                "y1": "",
                "x2": "",
                "y2": "",
                "notes": f"Duplicata exata de {previous['image']}" if duplicate else "",
            }
        )
    review.parent.mkdir(parents=True, exist_ok=True)
    write_csv(review, rows, REVIEW_FIELDS)
    for row in rows:
        row["url"] = (source / row["image"]).resolve().as_uri()
    content = template.read_text(encoding="utf-8")
    # JSON seguro dentro de um bloco script; imagens só são abertas localmente.
    data = json.dumps(rows, ensure_ascii=False).replace("<", "\\u003c")
    page.write_text(content.replace("__REVIEW_DATA__", data), encoding="utf-8")
    return {
        "status": "needs_review",
        "images": len(rows),
        "pending": sum(row["status"] == "pending" for row in rows),
        "csv": str(review),
        "page": str(page),
    }
