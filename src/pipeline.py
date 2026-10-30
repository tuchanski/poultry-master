"""Detecção de aves com caixas limitadas à imagem e confiança validada."""

import math


def clip_box(values, width, height):
    if len(values) != 4 or not all(math.isfinite(value) for value in values):
        raise ValueError("O detector retornou coordenadas inválidas.")
    x1, y1, x2, y2 = values
    box = [
        max(0, math.floor(x1)),
        max(0, math.floor(y1)),
        min(width, math.ceil(x2)),
        min(height, math.ceil(y2)),
    ]
    return box if box[2] > box[0] and box[3] > box[1] else None


def confidence(value):
    value = float(value)
    if not math.isfinite(value) or not 0 <= value <= 1:
        raise ValueError("O modelo retornou confiança inválida.")
    return value


def detect_birds(image, detector, settings):
    prediction = detector.predict(
        image,
        device=settings["device"],
        imgsz=settings["detector_imgsz"],
        conf=settings["confidence"],
        iou=settings["iou"],
        max_det=settings["max_det"],
        verbose=False,
    )[0]
    boxes = prediction.boxes.xyxy.tolist()
    scores = prediction.boxes.conf.tolist()
    if len(boxes) != len(scores):
        raise ValueError("Detecções inconsistentes.")
    birds = []
    for values, score in zip(boxes, scores):
        box = clip_box(values, *image.size)
        if box is not None:
            birds.append(
                {"id": len(birds) + 1, "box": box, "detection_confidence": confidence(score)}
            )
    return birds, len(boxes) >= settings["max_det"]
