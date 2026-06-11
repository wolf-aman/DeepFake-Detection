import torch
import numpy as np
from pathlib import Path
from typing import List, Dict
import app.config as config
from app.services.audio_utils import preprocess_audio
from app.storage.db import insert_speaker, get_speaker, delete_speaker as db_delete_speaker
from speechbrain.inference.speaker import EncoderClassifier


_speaker_model = None


def get_speaker_model():
    """Load and cache the speaker verification model (singleton pattern)."""
    global _speaker_model
    if _speaker_model is None:
        _speaker_model = EncoderClassifier.from_hparams(
            source=config.SPEAKER_MODEL_ID,
            savedir="pretrained_models/spkrec-ecapa-voxceleb"
        )
    return _speaker_model


def extract_embedding(audio_path: str) -> np.ndarray:
    """
    Extract speaker embedding from audio file.
    
    Args:
        audio_path: Path to audio file
        
    Returns:
        NumPy array containing the speaker embedding
    """
    model = get_speaker_model()
    waveform, _ = preprocess_audio(audio_path)
    
    with torch.no_grad():
        embedding = model.encode_batch(waveform)
        embedding = embedding.squeeze().cpu().numpy()
    
    return embedding


def enroll_speaker(name: str, audio_files: List[str]) -> Dict:
    """
    Enroll a new speaker by computing and storing their average embedding.
    
    Args:
        name: Unique speaker name
        audio_files: List of paths to enrollment audio files
        
    Returns:
        Dictionary with enrollment result
        
    Raises:
        ValueError: If speaker name already exists
        RuntimeError: If embedding extraction fails
    """
    existing = get_speaker(name)
    if existing:
        raise ValueError(f"Speaker '{name}' already exists")
    
    embeddings = []
    for audio_file in audio_files:
        embedding = extract_embedding(audio_file)
        embeddings.append(embedding)
    
    avg_embedding = np.mean(embeddings, axis=0)
    
    embedding_path = config.EMBEDDINGS_DIR / f"{name}.npy"
    np.save(embedding_path, avg_embedding)
    
    relative_path = f"embeddings/{name}.npy"
    insert_speaker(name, relative_path)
    
    return {
        "message": "Speaker enrolled successfully",
        "name": name,
        "embedding_path": relative_path
    }


def verify_speaker(name: str, audio_path: str) -> Dict:
    """
    Verify if the audio belongs to the enrolled speaker.
    
    Args:
        name: Enrolled speaker name
        audio_path: Path to verification audio file
        
    Returns:
        Dictionary with verification result including similarity score and decision
        
    Raises:
        ValueError: If speaker not found
        FileNotFoundError: If embedding file doesn't exist
    """
    speaker = get_speaker(name)
    if not speaker:
        raise ValueError(f"Speaker '{name}' not found")
    
    embedding_path = config.STORAGE_DIR / speaker["embedding_path"]
    if not embedding_path.exists():
        raise FileNotFoundError(f"Embedding file not found for speaker '{name}'")
    
    enrolled_embedding = np.load(embedding_path)
    
    test_embedding = extract_embedding(audio_path)
    
    similarity = cosine_similarity(enrolled_embedding, test_embedding)
    
    verified = similarity >= config.VERIFICATION_THRESHOLD
    
    return {
        "similarity": float(similarity),
        "verified": bool(verified),
        "threshold": config.VERIFICATION_THRESHOLD
    }


def cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
    """
    Compute cosine similarity between two vectors.
    
    Args:
        vec1: First embedding vector
        vec2: Second embedding vector
        
    Returns:
        Cosine similarity score (0 to 1)
    """
    dot_product = np.dot(vec1, vec2)
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    return dot_product / (norm1 * norm2 + 1e-8)


def delete_speaker(name: str) -> Dict:
    """
    Delete a speaker and their embedding file.
    
    Args:
        name: Speaker name to delete
        
    Returns:
        Dictionary with deletion result
        
    Raises:
        ValueError: If speaker not found
    """
    speaker = get_speaker(name)
    if not speaker:
        raise ValueError(f"Speaker '{name}' not found")
    
    embedding_path = config.STORAGE_DIR / speaker["embedding_path"]
    embedding_path.unlink(missing_ok=True)
    
    db_delete_speaker(name)
    
    return {"message": "Speaker deleted successfully"}
