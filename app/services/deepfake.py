from __future__ import annotations

import os

os.environ.setdefault("TRANSFORMERS_NO_TF", "1")
os.environ.setdefault("TRANSFORMERS_NO_FLAX", "1")
os.environ.setdefault("TORCHDYNAMO_DISABLE", "1")

import sys
import types
import threading
from pathlib import Path
from typing import Protocol

import numpy as np
import torch

from app.config import Settings, settings
from app.core.exceptions import InferenceError
from app.services.audio import preprocess_audio


def _disable_unused_speechbrain_optional_modules() -> None:
    """
    SpeechBrain has optional lazy integrations like k2_fsa.
    This project does not use them, so we disable those optional modules
    before importing Transformers.
    """
    optional_modules = [
        "speechbrain.integrations.k2_fsa",
        "speechbrain.integrations.nlp",
        "speechbrain.integrations.huggingface.wordemb",
        "speechbrain.k2_integration",
        "speechbrain.wordemb",
    ]

    for module_name in optional_modules:
        dummy = types.ModuleType(module_name)
        dummy.__file__ = f"<disabled optional module: {module_name}>"
        dummy.__package__ = module_name.rpartition(".")[0]
        sys.modules[module_name] = dummy


class AudioAuthenticityDetector(Protocol):
    def detect(self, audio_path: Path | str) -> dict:
        """Classify audio as Real/Fake and return confidence metadata."""


class HuggingFaceDeepfakeDetector:
    """
    Lazy-loaded Hugging Face audio classifier for spoof/deepfake detection.

    Uses chunk-based inference because long files can hide local fake artifacts.
    """

    def __init__(self, app_settings: Settings = settings) -> None:
        self.settings = app_settings
        self._feature_extractor = None
        self._model = None
        self._lock = threading.Lock()

    def _get_model_id(self) -> str:
        return (
            getattr(self.settings, "deepfake_model_id", None)
            or getattr(self.settings, "DEEPFAKE_MODEL_ID", None)
            or "mo-thecreator/Deepfake-audio-detection"
        )

    def _get_sample_rate(self) -> int:
        return int(
            getattr(self.settings, "sample_rate", None)
            or getattr(self.settings, "SAMPLE_RATE", None)
            or 16000
        )

    def _get_fake_threshold(self) -> float:
        """
        Final decision threshold.

        0.5 means:
        fake_probability >= 0.5 => Fake
        fake_probability < 0.5  => Real

        Later we can tune this after testing multiple real/fake samples.
        """
        return float(
            getattr(self.settings, "deepfake_fake_threshold", None)
            or getattr(self.settings, "DEEPFAKE_FAKE_THRESHOLD", None)
            or 0.5
        )

    def _load(self) -> None:
        if self._feature_extractor is not None and self._model is not None:
            return

        with self._lock:
            if self._feature_extractor is not None and self._model is not None:
                return

            try:
                _disable_unused_speechbrain_optional_modules()

                from transformers import (
                    AutoFeatureExtractor,
                    AutoModelForAudioClassification,
                )

                model_id = self._get_model_id()
                print(f"Loading deepfake model: {model_id}")

                self._feature_extractor = AutoFeatureExtractor.from_pretrained(model_id)
                self._model = AutoModelForAudioClassification.from_pretrained(model_id)
                self._model.eval()

                print("Deepfake model loaded successfully")
                print("Model id2label:", self._model.config.id2label)
                print("Model label2id:", self._model.config.label2id)

            except Exception as exc:
                raise InferenceError(f"Deepfake model loading failed: {exc}") from exc

    def _prepare_audio(self, audio_path: Path | str) -> tuple[np.ndarray, int]:
        sample_rate = self._get_sample_rate()

        try:
            waveform, _ = preprocess_audio(audio_path, self.settings)
        except TypeError:
            waveform, _ = preprocess_audio(audio_path)

        audio = waveform.squeeze().detach().cpu().numpy().astype(np.float32)

        if audio.ndim != 1:
            audio = np.asarray(audio).reshape(-1).astype(np.float32)

        # Avoid empty or too-short input.
        min_samples = sample_rate
        if audio.shape[0] < min_samples:
            audio = np.pad(audio, (0, min_samples - audio.shape[0]))

        return audio, sample_rate

    def _make_chunks(
        self,
        audio: np.ndarray,
        sample_rate: int,
        chunk_seconds: float = 4.0,
        stride_seconds: float = 4.0,
        min_chunk_seconds: float = 1.0,
    ) -> list[np.ndarray]:
        """
        Split long audio into chunks.

        Example:
        93 sec audio with 4 sec chunks => around 24 chunks.
        """
        chunk_size = int(chunk_seconds * sample_rate)
        stride_size = int(stride_seconds * sample_rate)
        min_chunk_size = int(min_chunk_seconds * sample_rate)

        chunks: list[np.ndarray] = []

        start = 0
        while start < len(audio):
            end = start + chunk_size
            chunk = audio[start:end]

            if len(chunk) >= min_chunk_size:
                if len(chunk) < chunk_size:
                    chunk = np.pad(chunk, (0, chunk_size - len(chunk)))
                chunks.append(chunk.astype(np.float32))

            start += stride_size

        if not chunks:
            chunks.append(audio.astype(np.float32))

        return chunks

    def _get_id2label(self) -> dict[int, str]:
        if self._model is None:
            raise InferenceError("Deepfake model is not loaded.")

        return {
            int(k): str(v).lower().strip()
            for k, v in self._model.config.id2label.items()
        }

    def _predict_chunk(self, chunk: np.ndarray, sample_rate: int) -> dict:
        if self._feature_extractor is None or self._model is None:
            raise InferenceError("Deepfake model is not loaded.")

        try:
            inputs = self._feature_extractor(
                chunk,
                sampling_rate=sample_rate,
                return_tensors="pt",
                padding=True,
            )

            with torch.inference_mode():
                logits = self._model(**inputs).logits

        except Exception as exc:
            raise InferenceError(f"Deepfake model inference failed: {exc}") from exc

        probabilities = torch.softmax(logits, dim=-1).squeeze().detach().cpu().numpy()

        id2label = self._get_id2label()

        class_probabilities = {
            id2label.get(i, f"label_{i}"): float(prob)
            for i, prob in enumerate(probabilities)
        }

        predicted_id = int(np.argmax(probabilities))
        raw_label = id2label.get(predicted_id, f"label_{predicted_id}")
        confidence = float(probabilities[predicted_id])

        return {
            "predicted_id": predicted_id,
            "raw_label": raw_label,
            "confidence": confidence,
            "class_probabilities": class_probabilities,
        }

    def detect(self, audio_path: Path | str) -> dict:
        self._load()

        if self._feature_extractor is None or self._model is None:
            raise InferenceError("Deepfake model failed to load.")

        audio, sample_rate = self._prepare_audio(audio_path)
        chunks = self._make_chunks(audio, sample_rate)

        chunk_results = []
        fake_probs = []
        real_probs = []

        for index, chunk in enumerate(chunks):
            result = self._predict_chunk(chunk, sample_rate)

            probs = result["class_probabilities"]
            fake_prob = float(probs.get("fake", 0.0))
            real_prob = float(probs.get("real", 0.0))

            fake_probs.append(fake_prob)
            real_probs.append(real_prob)

            chunk_results.append(
                {
                    "chunk_index": index,
                    "raw_label": result["raw_label"],
                    "confidence": round(result["confidence"], 6),
                    "fake_probability": round(fake_prob, 6),
                    "real_probability": round(real_prob, 6),
                }
            )

        average_fake_probability = float(np.mean(fake_probs))
        average_real_probability = float(np.mean(real_probs))

        max_fake_probability = float(np.max(fake_probs))
        max_real_probability = float(np.max(real_probs))

        fake_threshold = self._get_fake_threshold()

        fake_chunk_count = int(sum(prob >= fake_threshold for prob in fake_probs))
        real_chunk_count = int(sum(prob > fake_threshold for prob in real_probs))

        fake_chunk_ratio = fake_chunk_count / max(len(chunks), 1)

        # Main decision:
        # If average fake probability crosses threshold, call it Fake.
        # Also flag Fake if many chunks are fake, even if average is slightly lower.
        is_fake = (
            average_fake_probability >= fake_threshold
            or fake_chunk_ratio >= 0.35
        )

        label = "Fake" if is_fake else "Real"
        confidence = (
            average_fake_probability if label == "Fake" else average_real_probability
        )

        result = {
            "label": label,
            "confidence": round(float(confidence), 6),
            "fake_probability": round(average_fake_probability, 6),
            "real_probability": round(average_real_probability, 6),
            "max_fake_probability": round(max_fake_probability, 6),
            "max_real_probability": round(max_real_probability, 6),
            "fake_chunk_count": fake_chunk_count,
            "real_chunk_count": real_chunk_count,
            "fake_chunk_ratio": round(fake_chunk_ratio, 6),
            "chunk_count": len(chunks),
            "chunk_seconds": 4.0,
            "raw_label": label.lower(),
            "predicted_id": 0 if label == "Fake" else 1,
            "class_probabilities": {
                "fake": round(average_fake_probability, 6),
                "real": round(average_real_probability, 6),
            },
            "model_id": self._get_model_id(),
            "audio_samples": int(audio.shape[0]),
            "duration_seconds": round(float(audio.shape[0] / sample_rate), 3),
            "sample_rate": sample_rate,
            "chunk_results_preview": chunk_results[:10],
            "explanation": build_deepfake_explanation(
                label=label,
                confidence=confidence,
                fake_probability=average_fake_probability,
                real_probability=average_real_probability,
                fake_chunk_count=fake_chunk_count,
                chunk_count=len(chunks),
                max_fake_probability=max_fake_probability,
            ),
        }

        print("Deepfake detection result:", result)
        return result


def build_deepfake_explanation(
    label: str,
    confidence: float,
    fake_probability: float,
    real_probability: float,
    fake_chunk_count: int,
    chunk_count: int,
    max_fake_probability: float,
) -> str:
    pct = confidence * 100
    fake_pct = fake_probability * 100
    real_pct = real_probability * 100
    max_fake_pct = max_fake_probability * 100

    if label == "Fake":
        return (
            f"The audio is classified as Fake. Average fake probability is "
            f"{fake_pct:.1f}%, and {fake_chunk_count}/{chunk_count} chunks crossed "
            f"the fake threshold. Maximum chunk fake probability was {max_fake_pct:.1f}%."
        )

    return (
        f"The audio is classified as Real with {pct:.1f}% confidence. "
        f"Average real probability is {real_pct:.1f}%, average fake probability is "
        f"{fake_pct:.1f}%, and {fake_chunk_count}/{chunk_count} chunks crossed the fake threshold."
    )


deepfake_detector = HuggingFaceDeepfakeDetector()


def detect_deepfake(audio_path: Path | str) -> dict:
    return deepfake_detector.detect(audio_path)