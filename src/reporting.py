"""Resumo e imagem anotada a partir dos mesmos resultados individuais."""

from PIL import ImageDraw

WARNING = (
    "Condição aparente; requer verificação humana. O modelo não avalia sick. "
    "Healthy não confirma saúde. Confiança não é certeza clínica."
)


def summarize(birds):
    counts = {label: sum(bird["label"] == label for bird in birds) for label in ("healthy", "dead")}
    if sum(counts.values()) != len(birds):
        raise ValueError("Classe desconhecida no resumo.")
    return {
        "total_detected": len(birds),
        "total_classified": len(birds),
        "counts": counts,
        "percentages": {
            label: round(count / len(birds) * 100, 2) if birds else 0.0
            for label, count in counts.items()
        },
        "verification_candidates": counts["dead"],
        "message": "Análise concluída" if birds else "nenhuma ave detectada",
    }


def annotate(image, birds):
    annotated = image.copy()
    draw = ImageDraw.Draw(annotated)
    for bird in birds:
        color = "red" if bird["label"] == "dead" else "lime"
        x1, y1, x2, y2 = bird["box"]
        draw.rectangle((x1, y1, x2 - 1, y2 - 1), outline=color, width=2)
        label = f"#{bird['id']} {bird['label']} {bird['classification_confidence']:.0%}"
        if bird["requires_verification"]:
            label += " - verificar"
        text_box = draw.textbbox((0, 0), label, stroke_width=1)
        text_width = text_box[2] - text_box[0]
        text_x = max(0, min(x1, image.width - text_width - 2))
        draw.text((text_x, max(0, y1 - 13)), label, fill=color, stroke_width=1, stroke_fill="black")
    return annotated
