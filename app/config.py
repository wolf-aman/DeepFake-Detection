from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    """Central application settings.

    Keeping configuration in one immutable object makes the app easier to test
    and keeps business logic independent from hard-coded constants.
    """

    base_dir: Path = Path(__file__).resolve().parent
    sample_rate: int = 16_000
    verification_threshold: float = 0.75
    max_upload_mb: int = 25
    max_enrollment_files: int = 10
    min_audio_seconds: float = 0.3
    speaker_model_id: str = "speechbrain/spkrec-ecapa-voxceleb"
    deepfake_model_id: str = "garystafford/wav2vec2-deepfake-voice-detector"
    allowed_audio_suffixes: frozenset[str] = field(
        default_factory=lambda: frozenset({".wav", ".mp3", ".flac", ".m4a", ".ogg", ".webm"})
    )

    @property
    def project_root(self) -> Path:
        return self.base_dir.parent

    @property
    def storage_dir(self) -> Path:
        return self.base_dir / "storage"

    @property
    def embeddings_dir(self) -> Path:
        return self.storage_dir / "embeddings"

    @property
    def database_path(self) -> Path:
        return self.storage_dir / "speakers.db"

    @property
    def templates_dir(self) -> Path:
        return self.base_dir / "templates"

    @property
    def static_dir(self) -> Path:
        return self.base_dir / "static"

    @property
    def model_cache_dir(self) -> Path:
        return self.project_root / "pretrained_models"

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_mb * 1024 * 1024

    def create_directories(self) -> None:
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.embeddings_dir.mkdir(parents=True, exist_ok=True)
        self.model_cache_dir.mkdir(parents=True, exist_ok=True)


settings = Settings()
