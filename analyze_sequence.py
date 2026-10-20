"""Acompanha caixas de aves em fotos sequenciais e sinaliza imobilidade aparente."""

import argparse
import csv
import json
import math
import os
import re
import shutil
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from PIL import Image, ImageDraw, ImageOps

from analyze import ROOT, load_model
from src.preparation.common import file_hash
from src.sequence import analyze_detections
from src.pipeline import detect_birds

os.environ["YOLO_CONFIG_DIR"] = str(ROOT / "outputs/ultralytics")


def load_manifest(path):
    path = path.resolve()
    with path.open(newline="", encoding="utf-8-sig") as stream:
        reader = csv.DictReader(stream)
        if not reader.fieldnames or not {"image", "timestamp"}.issubset(reader.fieldnames):
            raise ValueError("O manifesto deve conter as colunas image e timestamp.")
        rows = []
        for line, row in enumerate(reader, start=2):
            image_text = (row.get("image") or "").strip()
            timestamp_text = (row.get("timestamp") or "").strip()
            if not image_text or not timestamp_text:
                raise ValueError(f"Manifesto incompleto na linha {line}.")
            try:
                timestamp = datetime.fromisoformat(timestamp_text)
            except ValueError as error:
                raise ValueError(f"Horário inválido na linha {line}: {timestamp_text}") from error
            if timestamp.tzinfo is None or timestamp.utcoffset() is None:
                raise ValueError(f"O horário da linha {line} precisa informar o fuso horário.")
            image_path = Path(image_text)
            if not image_path.is_absolute():
                image_path = path.parent / image_path
            image_path = image_path.resolve()
            if not image_path.is_file():
                raise ValueError(f"Imagem ausente na linha {line}: {image_path}")
            rows.append({"image": image_path, "timestamp": timestamp, "source_line": line})
    if not rows:
        raise ValueError("O manifesto não contém fotos.")
    if len({row["timestamp"] for row in rows}) != len(rows):
        raise ValueError("O manifesto contém horários repetidos; cada foto precisa de horário único.")
    original_order = [row["timestamp"] for row in rows]
    rows.sort(key=lambda row: row["timestamp"])
    return rows, original_order != [row["timestamp"] for row in rows]


def load_images_dir(path):
    """Read screenshot_<epoch-milliseconds>_<sequence>.png captures directly."""
    path = path.resolve()
    if not path.is_dir():
        raise ValueError(f"A pasta de imagens não existe: {path}")
    pattern = re.compile(r"^screenshot_(\d{13})_(\d+)\.(png|jpe?g)$", re.IGNORECASE)
    rows = []
    for image_path in path.iterdir():
        if not image_path.is_file():
            continue
        match = pattern.match(image_path.name)
        if not match:
            continue
        epoch_ms = int(match.group(1))
        timestamp = datetime.fromtimestamp(epoch_ms / 1000, tz=timezone.utc)
        rows.append({"image": image_path.resolve(), "timestamp": timestamp, "source_line": None})
    if not rows:
        raise ValueError(
            "Nenhuma captura encontrada. Esperado screenshot_<timestamp_ms>_<contador>.png."
        )
    if len({row["timestamp"] for row in rows}) != len(rows):
        raise ValueError("Há capturas com o mesmo timestamp nos nomes dos arquivos.")
    original_order = [row["timestamp"] for row in rows]
    rows.sort(key=lambda row: row["timestamp"])
    return rows, original_order != [row["timestamp"] for row in rows]


def sequence_settings(args):
    settings = {
        "stationary_minutes": args.stationary_minutes,
        "nominal_interval_seconds": args.nominal_interval_seconds,
        "motion_threshold_diagonals": args.motion_threshold_diagonals,
        "max_center_distance_diagonals": args.max_center_distance_diagonals,
        "association_min_iou": args.association_min_iou,
        "max_missed_frames": args.max_missed_frames,
        "minimum_stationary_observations": args.minimum_stationary_observations,
        "session_gap_seconds": args.session_gap_minutes * 60,
    }
    for key in (
        "stationary_minutes",
        "nominal_interval_seconds",
        "motion_threshold_diagonals",
        "max_center_distance_diagonals",
        "session_gap_seconds",
    ):
        if not math.isfinite(settings[key]) or settings[key] <= 0:
            raise ValueError(f"Parâmetro deve ser positivo: {key}")
    if not 0 <= settings["association_min_iou"] <= 1:
        raise ValueError("association_min_iou precisa estar entre 0 e 1.")
    if type(settings["max_missed_frames"]) is not int or settings["max_missed_frames"] < 0:
        raise ValueError("max_missed_frames precisa ser um inteiro não negativo.")
    if (
        type(settings["minimum_stationary_observations"]) is not int
        or settings["minimum_stationary_observations"] < 2
    ):
        raise ValueError("minimum_stationary_observations precisa ser inteiro >= 2.")
    return settings


def parse_roi(value):
    try:
        coordinates = tuple(float(part) for part in value.split(","))
    except ValueError as error:
        raise argparse.ArgumentTypeError("ROI deve ter o formato x1,y1,x2,y2.") from error
    if (
        len(coordinates) != 4
        or not all(math.isfinite(part) and 0 <= part <= 1 for part in coordinates)
        or coordinates[0] >= coordinates[2]
        or coordinates[1] >= coordinates[3]
    ):
        raise argparse.ArgumentTypeError(
            "ROI deve conter coordenadas normalizadas entre 0 e 1, com x1<x2 e y1<y2."
        )
    return coordinates


def filter_roi(detections, image_size, roi):
    if roi is None:
        return detections
    width, height = image_size
    x1, y1, x2, y2 = roi
    left, top, right, bottom = x1 * width, y1 * height, x2 * width, y2 * height
    return [
        detection
        for detection in detections
        if left <= (detection["box"][0] + detection["box"][2]) / 2 <= right
        and top <= (detection["box"][1] + detection["box"][3]) / 2 <= bottom
    ]


def annotate_frame(image, detections, candidates_only=False, hide_labels=False):
    annotated = image.copy()
    draw = ImageDraw.Draw(annotated)
    for detection in detections:
        candidate = detection["state"] == "stationary_candidate"
        if candidates_only and not candidate:
            continue
        x1, y1, x2, y2 = detection["box"]
        color = "red" if candidate else "dodgerblue"
        draw.rectangle((x1, y1, x2 - 1, y2 - 1), outline=color, width=3)
        if hide_labels:
            continue
        duration = detection["stationary_seconds"] / 60
        label = f"ID {detection['track_id']} | "
        label += f"IMOVEL {duration:.1f} min - verificar" if candidate else "acompanhando"
        bounds = draw.textbbox((0, 0), label, stroke_width=1)
        text_width = bounds[2] - bounds[0]
        text_x = max(0, min(x1, image.width - text_width - 2))
        text_y = max(0, y1 - 16)
        draw.text((text_x, text_y), label, fill=color, stroke_width=1, stroke_fill="black")
    return annotated


def write_csv(path, observations):
    columns = [
        "timestamp",
        "image",
        "session_id",
        "track_id",
        "x1",
        "y1",
        "x2",
        "y2",
        "center_x",
        "center_y",
        "detection_confidence",
        "elapsed_seconds",
        "normalized_motion",
        "stationary_seconds",
        "state",
    ]
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns)
        writer.writeheader()
        for observation in observations:
            x1, y1, x2, y2 = observation["box"]
            center_x, center_y = observation["center"]
            writer.writerow(
                {
                    "timestamp": observation["timestamp"],
                    "image": observation["image"],
                    "session_id": observation["session_id"],
                    "track_id": observation["track_id"],
                    "x1": x1,
                    "y1": y1,
                    "x2": x2,
                    "y2": y2,
                    "center_x": round(center_x, 2),
                    "center_y": round(center_y, 2),
                    "detection_confidence": observation["detection_confidence"],
                    "elapsed_seconds": observation["elapsed_seconds"],
                    "normalized_motion": observation["normalized_motion"],
                    "stationary_seconds": observation["stationary_seconds"],
                    "state": observation["state"],
                }
            )


def run(args):
    started = time.monotonic()
    output = args.output.resolve()
    if output.exists():
        raise ValueError("A pasta de saída já existe. Escolha uma pasta nova.")
    if args.images_dir:
        input_dir = args.images_dir.resolve()
        rows, sorted_manifest = load_images_dir(input_dir)
        input_info = {"type": "images_dir", "path": str(input_dir)}
    else:
        manifest = args.manifest.resolve()
        rows, sorted_manifest = load_manifest(manifest)
        input_info = {"type": "manifest_csv", "path": str(manifest)}
    settings = sequence_settings(args)
    config = args.config.resolve()
    config_data = json.loads(config.read_text(encoding="utf-8"))
    inference = config_data["inference"]
    if args.device:
        inference["device"] = args.device
    if args.confidence is not None:
        if not 0 < args.confidence <= 1:
            raise ValueError("confidence precisa estar entre 0 e 1.")
        inference["confidence"] = args.confidence
    detector_path = config.parent / inference["detector"]
    detector, detector_info = load_model(detector_path, "detect", {"chicken"})

    frames = []
    frame_metadata = []
    expected_size = None
    for row in rows:
        source = row["image"]
        with Image.open(source) as original:
            image = ImageOps.exif_transpose(original).convert("RGB")
        if expected_size is None:
            expected_size = image.size
        elif image.size != expected_size:
            raise ValueError(
                f"Dimensões de imagem incompatíveis em {source}: {image.size}; esperado {expected_size}."
            )
        detections, limit_reached = detect_birds(image, detector, inference)
        raw_detection_count = len(detections)
        detections = filter_roi(detections, image.size, args.roi)
        frames.append(
            {"timestamp": row["timestamp"], "image": source, "detections": detections}
        )
        frame_metadata.append(
            {
                "path": str(source),
                "sha256": file_hash(source),
                "timestamp": row["timestamp"].isoformat(),
                "detection_count": len(detections),
                "raw_detection_count": raw_detection_count,
                "detection_limit_reached": limit_reached,
            }
        )

    track_summaries, observations, frame_detections = analyze_detections(frames, settings)
    output.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f".{output.name}-", dir=output.parent))
    try:
        frame_dir = staging / "frames"
        frame_dir.mkdir()
        for index, (row, detections) in enumerate(zip(rows, frame_detections), start=1):
            with Image.open(row["image"]) as original:
                image = ImageOps.exif_transpose(original).convert("RGB")
            annotated = annotate_frame(
                image,
                detections,
                candidates_only=args.candidates_only,
                hide_labels=args.hide_labels,
            )
            filename = f"frame-{index:04d}-{row['image'].stem}.jpg"
            annotated.save(frame_dir / filename, quality=92)
            frame_metadata[index - 1]["annotated_image"] = str(Path("frames") / filename)

        candidate_tracks = sum(bool(track["candidate_events"]) for track in track_summaries)
        summary = {
            "frames_processed": len(rows),
            "raw_detections_total": sum(frame["raw_detection_count"] for frame in frame_metadata),
            "detections_after_roi_total": sum(frame["detection_count"] for frame in frame_metadata),
            "observations": len(observations),
            "tracks_created": len(track_summaries),
            "tracks_with_candidate_events": candidate_tracks,
            "candidate_events": sum(len(track["candidate_events"]) for track in track_summaries),
            "tracks_lost": sum(track["final_state"] == "lost" for track in track_summaries),
            "warning": (
                "Imobilidade aparente nas capturas observadas. Cada candidato exige "
                "verificação humana; o resultado não confirma óbito."
            ),
        }
        report = {
            "schema_version": 1,
            "analysis_id": str(uuid4()),
            "created_at": datetime.now().astimezone().isoformat(),
            "sequence_input": input_info,
            "input_sorted_by_timestamp": sorted_manifest,
            "camera_assumption": "câmera fixa, mesmo enquadramento e dimensões",
            "image_dimensions": {"width": expected_size[0], "height": expected_size[1]},
            "model": {"detector": detector_info},
            "detector_parameters": {
                key: inference[key]
                for key in ("device", "detector_imgsz", "confidence", "iou", "max_det")
            },
            "sequence_parameters": settings,
            "region_of_interest": args.roi,
            "visualization_parameters": {
                "candidates_only": args.candidates_only,
                "hide_labels": args.hide_labels,
            },
            "frames": frame_metadata,
            "summary": summary,
            "tracks": track_summaries,
            "artifacts": {"annotated_frames": "frames/", "observations_csv": "tracks.csv"},
            "processing_seconds": round(time.monotonic() - started, 3),
        }
        write_csv(staging / "tracks.csv", observations)
        (staging / "report.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
            encoding="utf-8",
        )
        staging.rename(output)
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise

    print(f"Fotos processadas: {summary['frames_processed']}")
    print(f"Detecções antes/depois do ROI: {summary['raw_detections_total']}/{summary['detections_after_roi_total']}")
    print(f"Trajetórias criadas: {summary['tracks_created']}")
    print(f"Trajetórias com candidato: {summary['tracks_with_candidate_events']}")
    print(f"Eventos candidatos: {summary['candidate_events']}")
    print(summary["warning"])
    if sorted_manifest:
        print("As fotos foram ordenadas pelos horários do manifesto.")
    if any(frame["detection_limit_reached"] for frame in frame_metadata):
        print("Aviso: o limite de detecções foi atingido em uma ou mais fotos.")
    print(f"Resultados: {output}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--manifest", type=Path, help="CSV com image,timestamp")
    source.add_argument(
        "--images-dir",
        type=Path,
        help="Pasta com screenshot_<timestamp_ms>_<contador>.png",
    )
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--config", type=Path, default=ROOT / "config.json")
    parser.add_argument("--device", help="cpu (padrão) ou índice da GPU, por exemplo 0")
    parser.add_argument("--confidence", type=float, help="limiar de confiança do detector")
    parser.add_argument(
        "--roi",
        type=parse_roi,
        help="região normalizada x1,y1,x2,y2; ex.: 0,0.30,1,1 para excluir a faixa superior",
    )
    parser.add_argument(
        "--candidates-only",
        action="store_true",
        help="desenha somente as caixas no estado de candidato nas imagens anotadas",
    )
    parser.add_argument(
        "--hide-labels",
        action="store_true",
        help="oculta os textos sobre as caixas nas imagens anotadas",
    )
    parser.add_argument("--stationary-minutes", type=float, default=5.0)
    parser.add_argument("--nominal-interval-seconds", type=float, default=30.0)
    parser.add_argument("--session-gap-minutes", type=float, default=3.0)
    parser.add_argument("--motion-threshold-diagonals", type=float, default=0.15)
    parser.add_argument("--max-center-distance-diagonals", type=float, default=0.75)
    parser.add_argument("--association-min-iou", type=float, default=0.05)
    parser.add_argument("--max-missed-frames", type=int, default=1)
    parser.add_argument("--minimum-stationary-observations", type=int, default=4)
    args = parser.parse_args()
    try:
        run(args)
    except Exception as error:
        print(f"Erro na análise sequencial: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
