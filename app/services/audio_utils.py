import tempfile
import torchaudio
import torch
from pathlib import Path
from typing import Tuple
import app.config as config


def preprocess_audio(audio_path: str) -> Tuple[torch.Tensor, int]:
    """
    Preprocess audio file: load, convert to mono, resample to target sample rate, and normalize.
    
    Args:
        audio_path: Path to the audio file
        
    Returns:
        Tuple of (audio_tensor, sample_rate)
        
    Raises:
        RuntimeError: If audio file cannot be loaded
    """
    waveform, sample_rate = torchaudio.load(audio_path)
    
    if waveform.shape[0] > 1:
        waveform = torch.mean(waveform, dim=0, keepdim=True)
    
    if sample_rate != config.SAMPLE_RATE:
        resampler = torchaudio.transforms.Resample(
            orig_freq=sample_rate,
            new_freq=config.SAMPLE_RATE
        )
        waveform = resampler(waveform)
    
    waveform = waveform / (torch.max(torch.abs(waveform)) + 1e-8)
    
    return waveform, config.SAMPLE_RATE


def save_temp_audio(file_bytes: bytes, suffix: str = ".wav") -> str:
    """
    Save uploaded file bytes to a temporary file.
    
    Args:
        file_bytes: Audio file bytes
        suffix: File extension
        
    Returns:
        Path to temporary file
    """
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    temp_file.write(file_bytes)
    temp_file.close()
    return temp_file.name


def cleanup_temp_file(file_path: str):
    """
    Delete temporary file safely.
    
    Args:
        file_path: Path to temporary file
    """
    try:
        Path(file_path).unlink(missing_ok=True)
    except Exception:
        pass
