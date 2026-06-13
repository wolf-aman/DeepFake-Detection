import tempfile
import torchaudio
import torch
import soundfile as sf
from pathlib import Path
from typing import Tuple
import app.config as config


def preprocess_audio(audio_path: str) -> Tuple[torch.Tensor, int]:
    try:
        waveform, sample_rate = torchaudio.load(audio_path)
    except Exception:
        data, sample_rate = sf.read(audio_path)
        waveform = torch.FloatTensor(data).unsqueeze(0) if data.ndim == 1 else torch.FloatTensor(data.T)

    # Convert to mono
    if waveform.shape[0] > 1:
        waveform = waveform.mean(dim=0, keepdim=True)

    # Resample to target rate
    if sample_rate != config.SAMPLE_RATE:
        waveform = torchaudio.transforms.Resample(sample_rate, config.SAMPLE_RATE)(waveform)

    # Normalize amplitude; skip if silent to avoid NaN
    peak = torch.max(torch.abs(waveform))
    if peak > 1e-8:
        waveform = waveform / peak

    return waveform, config.SAMPLE_RATE


def save_temp_audio(file_bytes: bytes, suffix: str = ".wav") -> str:
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    tmp.write(file_bytes)
    tmp.close()
    return tmp.name


def cleanup_temp_file(path: str) -> None:
    try:
        Path(path).unlink(missing_ok=True)
    except Exception:
        pass