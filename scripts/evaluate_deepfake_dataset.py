from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

import argparse
import csv
import json
from typing import Iterable

from app.services.deepfake import detect_deepfake


AUDIO_EXTENSIONS = {".wav", ".mp3", ".flac", ".ogg", ".m4a", ".aac"}


def iter_audio_files(folder: Path, limit: int | None = None) -> Iterable[Path]:
    files = [
        path
        for path in folder.rglob("*")
        if path.is_file() and path.suffix.lower() in AUDIO_EXTENSIONS
    ]

    files = sorted(files)

    if limit is not None:
        files = files[:limit]

    return files


def expected_label_from_folder(folder_label: str) -> str:
    folder_label = folder_label.lower().strip()
    if folder_label == "real":
        return "Real"
    if folder_label == "fake":
        return "Fake"
    raise ValueError(f"Unsupported label: {folder_label}")


def evaluate_file(path: Path, expected_label: str) -> dict:
    result = detect_deepfake(path)

    predicted_label = result.get("label", "Unknown")
    is_correct = predicted_label.lower() == expected_label.lower()

    return {
        "file": str(path),
        "expected": expected_label,
        "predicted": predicted_label,
        "correct": is_correct,
        "confidence": result.get("confidence"),
        "fake_probability": result.get("fake_probability"),
        "real_probability": result.get("real_probability"),
        "max_fake_probability": result.get("max_fake_probability"),
        "max_real_probability": result.get("max_real_probability"),
        "fake_chunk_count": result.get("fake_chunk_count"),
        "chunk_count": result.get("chunk_count"),
        "fake_chunk_ratio": result.get("fake_chunk_ratio"),
        "duration_seconds": result.get("duration_seconds"),
        "model_id": result.get("model_id"),
        "raw_json": json.dumps(result, ensure_ascii=False),
    }


def print_summary(rows: list[dict]) -> None:
    total = len(rows)
    correct = sum(1 for row in rows if row["correct"])

    real_rows = [row for row in rows if row["expected"] == "Real"]
    fake_rows = [row for row in rows if row["expected"] == "Fake"]

    real_correct = sum(1 for row in real_rows if row["correct"])
    fake_correct = sum(1 for row in fake_rows if row["correct"])

    false_real = [
        row for row in rows
        if row["expected"] == "Fake" and row["predicted"] == "Real"
    ]

    false_fake = [
        row for row in rows
        if row["expected"] == "Real" and row["predicted"] == "Fake"
    ]

    print("\n========== DEEPFAKE EVALUATION SUMMARY ==========")
    print(f"Total files tested: {total}")
    print(f"Overall accuracy: {correct}/{total} = {(correct / total * 100) if total else 0:.2f}%")

    print("\n--- REAL class ---")
    print(f"Real files tested: {len(real_rows)}")
    print(f"Real correctly detected: {real_correct}/{len(real_rows)} = {(real_correct / len(real_rows) * 100) if real_rows else 0:.2f}%")

    print("\n--- FAKE class ---")
    print(f"Fake files tested: {len(fake_rows)}")
    print(f"Fake correctly detected: {fake_correct}/{len(fake_rows)} = {(fake_correct / len(fake_rows) * 100) if fake_rows else 0:.2f}%")

    print("\n--- Error counts ---")
    print(f"Fake predicted as Real: {len(false_real)}")
    print(f"Real predicted as Fake: {len(false_fake)}")

    print("\nTop 5 FAKE files wrongly predicted as Real:")
    for row in false_real[:5]:
        print(
            f"- {row['file']} | fake_prob={row['fake_probability']} | "
            f"max_fake={row['max_fake_probability']} | fake_chunks={row['fake_chunk_count']}/{row['chunk_count']}"
        )

    print("\nTop 5 REAL files wrongly predicted as Fake:")
    for row in false_fake[:5]:
        print(
            f"- {row['file']} | fake_prob={row['fake_probability']} | "
            f"max_fake={row['max_fake_probability']} | fake_chunks={row['fake_chunk_count']}/{row['chunk_count']}"
        )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--real-dir", required=True, type=Path)
    parser.add_argument("--fake-dir", required=True, type=Path)
    parser.add_argument("--output", default="deepfake_evaluation.csv", type=Path)
    parser.add_argument("--limit-per-class", type=int, default=None)

    args = parser.parse_args()

    if not args.real_dir.exists():
        raise FileNotFoundError(f"Real directory not found: {args.real_dir}")

    if not args.fake_dir.exists():
        raise FileNotFoundError(f"Fake directory not found: {args.fake_dir}")

    rows: list[dict] = []

    test_sets = [
        ("Real", args.real_dir),
        ("Fake", args.fake_dir),
    ]

    for expected_label, folder in test_sets:
        files = list(iter_audio_files(folder, args.limit_per_class))
        print(f"\nTesting {len(files)} {expected_label} files from: {folder}")

        for index, file_path in enumerate(files, start=1):
            print(f"[{expected_label}] {index}/{len(files)}: {file_path.name}")

            try:
                row = evaluate_file(file_path, expected_label)
            except Exception as exc:
                row = {
                    "file": str(file_path),
                    "expected": expected_label,
                    "predicted": "ERROR",
                    "correct": False,
                    "confidence": None,
                    "fake_probability": None,
                    "real_probability": None,
                    "max_fake_probability": None,
                    "max_real_probability": None,
                    "fake_chunk_count": None,
                    "chunk_count": None,
                    "fake_chunk_ratio": None,
                    "duration_seconds": None,
                    "model_id": None,
                    "raw_json": str(exc),
                }

            rows.append(row)

    fieldnames = [
        "file",
        "expected",
        "predicted",
        "correct",
        "confidence",
        "fake_probability",
        "real_probability",
        "max_fake_probability",
        "max_real_probability",
        "fake_chunk_count",
        "chunk_count",
        "fake_chunk_ratio",
        "duration_seconds",
        "model_id",
        "raw_json",
    ]

    with args.output.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print_summary(rows)
    print(f"\nSaved detailed report to: {args.output}")


if __name__ == "__main__":
    main()