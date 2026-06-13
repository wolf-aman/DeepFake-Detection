import torch
import numpy as np
from pathlib import Path
from typing import List, Dict
from speechbrain.inference.speaker import EncoderClassifier
import app.config as config
from app.services.audio_utils import preprocess_audio
from app.storage.db import insert_speaker, get_speaker, delete_speaker as db_delete, list_speakers

_encoder = None


def _get_encoder() -> EncoderClassifier:
    global _encoder
    if _encoder is None:
        _encoder = EncoderClassifier.from_hparams(
            source=config.SPEAKER_MODEL_ID,
            savedir="pretrained_models/spkrec-ecapa-voxceleb",
        )
    return _encoder


def _extract_embedding(audio_path: str) -> np.ndarray:
    encoder = _get_encoder()
    waveform, _ = preprocess_audio(audio_path)

    if waveform.dim() == 2:
        waveform = waveform.squeeze(0)

    with torch.no_grad():
        embedding = encoder.encode_batch(waveform.unsqueeze(0))

    return embedding.squeeze().cpu().numpy()


def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-8))


def enroll_speaker(name: str, audio_files: List[str]) -> Dict:
    if get_speaker(name):
        raise ValueError(f"Speaker '{name}' already exists. Delete it first to re-enroll.")

    embeddings = [_extract_embedding(f) for f in audio_files]
    avg_embedding = np.mean(embeddings, axis=0)

    embedding_path = config.EMBEDDINGS_DIR / f"{name}.npy"
    np.save(embedding_path, avg_embedding)

    insert_speaker(name, f"embeddings/{name}.npy")
    return {"message": "Speaker enrolled successfully", "name": name}


def verify_speaker(name: str, audio_path: str) -> Dict:
    speaker = get_speaker(name)
    if not speaker:
        raise ValueError(f"Speaker '{name}' not found.")

    embedding_file = config.STORAGE_DIR / speaker["embedding_path"]
    if not embedding_file.exists():
        raise FileNotFoundError(f"Embedding missing for '{name}'. Please re-enroll.")

    enrolled = np.load(embedding_file)
    test = _extract_embedding(audio_path)
    similarity = _cosine_similarity(enrolled, test)

    return {
        "similarity": similarity,
        "verified": similarity >= config.VERIFICATION_THRESHOLD,
        "threshold": config.VERIFICATION_THRESHOLD,
    }


def get_all_speakers() -> List[Dict]:
    return list_speakers()


def delete_speaker(name: str) -> Dict:
    speaker = get_speaker(name)
    if not speaker:
        raise ValueError(f"Speaker '{name}' not found.")

    (config.STORAGE_DIR / speaker["embedding_path"]).unlink(missing_ok=True)
    db_delete(name)
    return {"message": f"Speaker '{name}' deleted successfully."}