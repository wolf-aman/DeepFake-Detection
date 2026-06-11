from pathlib import Path
 
BASE_DIR = Path(__file__).parent
STORAGE_DIR = BASE_DIR / "storage"
EMBEDDINGS_DIR = STORAGE_DIR / "embeddings"
DATABASE_PATH = STORAGE_DIR / "speakers.db"
 
SAMPLE_RATE = 16000
VERIFICATION_THRESHOLD = 0.75
 
SPEAKER_MODEL_ID = "speechbrain/spkrec-ecapa-voxceleb"
# Wav2Vec2 fine-tuned on deepfake/bonafide audio classification
DEEPFAKE_MODEL_ID = "mo-thecreator/Deepfake-audio-detection"
 
EMBEDDINGS_DIR.mkdir(parents=True, exist_ok=True)
STORAGE_DIR.mkdir(parents=True, exist_ok=True)
 