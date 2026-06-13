from __future__ import annotations

import threading
from pathlib import Path
from typing import Protocol

import numpy as np
import torch
from app.config import Settings, settings
from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.services.audio import preprocess_audio, validate_speaker_name
from app.storage.db import SpeakerRepository


class SpeakerEmbedder(Protocol):
    def extract(self, audio_path: Path | str) -> np.ndarray:
        """Return a 1D speaker embedding vector for an audio file."""


class SpeechBrainECAPAEmbedder:
    """Lazy-loaded SpeechBrain ECAPA embedder.

    Implements the Singleton-style model cache behind a small interface, so the
    verification service does not depend on SpeechBrain details directly.
    """

    def __init__(self, app_settings: Settings = settings) -> None:
        self.settings = app_settings
        self._model: object | None = None
        self._lock = threading.Lock()

    def _get_model(self) -> object:
        if self._model is None:
            with self._lock:
                if self._model is None:
                    from speechbrain.inference.speaker import EncoderClassifier

                    self._model = EncoderClassifier.from_hparams(
                        source=self.settings.speaker_model_id,
                        savedir=str(self.settings.model_cache_dir / "spkrec-ecapa-voxceleb"),
                    )
        return self._model

    def extract(self, audio_path: Path | str) -> np.ndarray:
        model = self._get_model()
        waveform, _ = preprocess_audio(audio_path, self.settings)
        mono = waveform.squeeze(0)

        with torch.inference_mode():
            embedding = model.encode_batch(mono.unsqueeze(0))

        vector = embedding.squeeze().detach().cpu().numpy().astype(np.float32)
        return _normalize_vector(vector)


class SpeakerVerificationService:
    """Business logic for enrollment, verification, listing, and deletion."""

    def __init__(
        self,
        repository: SpeakerRepository,
        embedder: SpeakerEmbedder,
        app_settings: Settings = settings,
    ) -> None:
        self.repository = repository
        self.embedder = embedder
        self.settings = app_settings

    def enroll(self, name: str, audio_files: list[Path]) -> dict:
        display_name, slug = validate_speaker_name(name)
        if not audio_files:
            raise ValidationError("At least one audio file is required.")
        if len(audio_files) > self.settings.max_enrollment_files:
            raise ValidationError(f"Upload at most {self.settings.max_enrollment_files} files for one enrollment.")
        if self.repository.exists(display_name, slug):
            raise ConflictError(f"Speaker '{display_name}' already exists. Delete it before re-enrolling.")

        embeddings = [self.embedder.extract(path) for path in audio_files]
        averaged_embedding = _normalize_vector(np.mean(np.vstack(embeddings), axis=0))

        relative_path = Path("embeddings") / f"{slug}.npy"
        embedding_path = self.settings.storage_dir / relative_path
        temp_embedding_path = embedding_path.with_suffix(".tmp.npy")

        try:
            np.save(temp_embedding_path, averaged_embedding)
            temp_embedding_path.replace(embedding_path)
            record = self.repository.add(name=display_name, slug=slug, embedding_path=relative_path.as_posix())
        except Exception:
            embedding_path.unlink(missing_ok=True)
            temp_embedding_path.unlink(missing_ok=True)
            raise

        return {
            "message": "Speaker enrolled successfully",
            "name": record.name,
            "slug": record.slug,
            "samples_used": len(audio_files),
        }

    def verify(self, name: str, audio_path: Path) -> dict:
        record = self.repository.get_by_name_or_slug(name)
        if record is None:
            raise NotFoundError(f"Speaker '{name}' not found.")

        embedding_path = self.settings.storage_dir / record.embedding_path
        if not embedding_path.exists():
            raise NotFoundError(f"Embedding missing for '{record.name}'. Please re-enroll.")

        enrolled = np.load(embedding_path).astype(np.float32)
        test = self.embedder.extract(audio_path)
        similarity = cosine_similarity(enrolled, test)
        verified = similarity >= self.settings.verification_threshold

        return {
            "name": record.name,
            "similarity": round(similarity, 6),
            "verified": verified,
            "threshold": self.settings.verification_threshold,
        }

    def list_speakers(self) -> list[dict]:
        return [
            {"name": record.name, "slug": record.slug, "created_at": record.created_at}
            for record in self.repository.list_all()
        ]

    def delete(self, name: str) -> dict:
        record = self.repository.get_by_name_or_slug(name)
        if record is None:
            raise NotFoundError(f"Speaker '{name}' not found.")

        (self.settings.storage_dir / record.embedding_path).unlink(missing_ok=True)
        self.repository.delete(record.slug)
        return {"message": f"Speaker '{record.name}' deleted successfully.", "name": record.name}


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    if a.shape != b.shape:
        raise ValidationError("Embedding dimensions do not match. Please re-enroll the speaker.")
    denom = float(np.linalg.norm(a) * np.linalg.norm(b))
    if denom <= 1e-12:
        raise ValidationError("Could not compare silent or invalid embeddings.")
    return float(np.dot(a, b) / denom)


def _normalize_vector(vector: np.ndarray) -> np.ndarray:
    vector = np.asarray(vector, dtype=np.float32).reshape(-1)
    norm = np.linalg.norm(vector)
    if not np.isfinite(norm) or norm <= 1e-12:
        raise ValidationError("Model produced an invalid embedding. Try a clearer recording.")
    return vector / norm
