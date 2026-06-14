from pathlib import Path
import os
 
BASE_DIR = Path(__file__).parent
STORAGE_DIR = BASE_DIR / "storage"
EMBEDDINGS_DIR = STORAGE_DIR / "embeddings"
DATABASE_PATH = STORAGE_DIR / "speakers.db"


def _env_flag(name: str, default: bool = False) -> bool:
    """Read a boolean feature flag from an environment variable."""
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}

 
SAMPLE_RATE = 16000
VERIFICATION_THRESHOLD = 0.75

# Keep the bonus KYC workflow hidden from the main demo by default.
# Enable it with: ENABLE_KYC_DEMO=true uv run fastapi dev app/main.py
ENABLE_KYC_DEMO = _env_flag("ENABLE_KYC_DEMO", default=False)
 
SPEAKER_MODEL_ID = "speechbrain/spkrec-ecapa-voxceleb"
# Wav2Vec2 fine-tuned on deepfake/bonafide audio classification
DEEPFAKE_MODEL_ID = "mo-thecreator/Deepfake-audio-detection"
 
EMBEDDINGS_DIR.mkdir(parents=True, exist_ok=True)
STORAGE_DIR.mkdir(parents=True, exist_ok=True)
 