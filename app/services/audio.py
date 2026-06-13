from __future__ import annotations

import re
import math
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import soundfile as sf
import torch
from fastapi import UploadFile

from app.config import Settings, settings
from app.core.exceptions import ValidationError


@dataclass(frozen=True)
class AudioMetadata:
    path: Path
    sample_rate: int
    num_samples: int
    duration_seconds: float


def normalize_audio_suffix(filename: str | None, allowed_suffixes: Iterable[str]) -> str:
    suffix = Path(filename or "audio.wav").suffix.lower() or ".wav"
    if suffix not in allowed_suffixes:
        allowed = ", ".join(sorted(allowed_suffixes))
        raise ValidationError(f"Unsupported audio type '{suffix}'. Allowed types: {allowed}")
    return suffix


async def save_upload_to_temp(upload: UploadFile, app_settings: Settings = settings) -> Path:
    """Validate and stream an uploaded audio file to a temporary file."""

    suffix = normalize_audio_suffix(upload.filename, app_settings.allowed_audio_suffixes)
    total_bytes = 0
    temp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)

    try:
        while True:
            chunk = await upload.read(1024 * 1024)
            if not chunk:
                break
            total_bytes += len(chunk)
            if total_bytes > app_settings.max_upload_bytes:
                raise ValidationError(f"Audio file is too large. Max size is {app_settings.max_upload_mb} MB.")
            temp.write(chunk)
    finally:
        temp.close()

    path = Path(temp.name)
    if total_bytes == 0:
        path.unlink(missing_ok=True)
        raise ValidationError("Uploaded audio file is empty.")

    return path


def cleanup_temp_file(path: Path | str | None) -> None:
    if not path:
        return
    try:
        Path(path).unlink(missing_ok=True)
    except OSError:
        # Temp cleanup should never hide the primary API result/error.
        pass


def preprocess_audio(audio_path: Path | str, app_settings: Settings = settings) -> tuple[torch.Tensor, AudioMetadata]:
    """Load audio, convert it to mono 16 kHz float32, normalize amplitude, and validate length."""

    path = Path(audio_path)
    if not path.exists():
        raise ValidationError(f"Audio file not found: {path}")

    waveform, sample_rate = _load_audio(path)
    waveform = _as_mono_float_tensor(waveform)

    if waveform.numel() == 0:
        raise ValidationError("Audio contains no samples.")

    if not torch.isfinite(waveform).all():
        waveform = torch.nan_to_num(waveform)

    if sample_rate != app_settings.sample_rate:
        waveform = _resample_audio(waveform, sample_rate, app_settings.sample_rate)
        sample_rate = app_settings.sample_rate

    duration = waveform.shape[-1] / sample_rate
    if duration < app_settings.min_audio_seconds:
        raise ValidationError(
            f"Audio is too short ({duration:.2f}s). Please upload at least {app_settings.min_audio_seconds:.1f}s."
        )

    peak = torch.max(torch.abs(waveform))
    if peak <= 1e-8:
        raise ValidationError("Audio appears to be silent. Please upload a clearer recording.")

    waveform = (waveform / peak).clamp(min=-1.0, max=1.0)
    metadata = AudioMetadata(path=path, sample_rate=sample_rate, num_samples=waveform.shape[-1], duration_seconds=duration)
    return waveform.contiguous(), metadata


def _load_audio(path: Path) -> tuple[torch.Tensor, int]:
    try:
        import torchaudio

        return torchaudio.load(str(path))
    except Exception:
        data, sample_rate = sf.read(str(path), always_2d=True)
        tensor = torch.as_tensor(data.T, dtype=torch.float32)
        return tensor, int(sample_rate)


def _resample_audio(waveform: torch.Tensor, source_rate: int, target_rate: int) -> torch.Tensor:
    try:
        import torchaudio

        return torchaudio.transforms.Resample(source_rate, target_rate)(waveform)
    except Exception:
        from scipy.signal import resample_poly

        gcd = math.gcd(source_rate, target_rate)
        up = target_rate // gcd
        down = source_rate // gcd
        resampled = resample_poly(waveform.cpu().numpy(), up, down, axis=-1)
        return torch.as_tensor(resampled, dtype=torch.float32)


def _as_mono_float_tensor(waveform: torch.Tensor) -> torch.Tensor:
    if waveform.dim() == 1:
        waveform = waveform.unsqueeze(0)
    elif waveform.dim() > 2:
        waveform = waveform.reshape(waveform.shape[0], -1)

    waveform = waveform.to(dtype=torch.float32)
    if waveform.shape[0] > 1:
        waveform = waveform.mean(dim=0, keepdim=True)
    return waveform


def slugify_speaker_name(name: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9._ -]+", "", name).strip()
    cleaned = re.sub(r"\s+", "_", cleaned)
    cleaned = re.sub(r"_+", "_", cleaned)
    return cleaned.lower().strip("._-")


def validate_speaker_name(name: str) -> tuple[str, str]:
    display_name = " ".join(name.strip().split())
    if not display_name:
        raise ValidationError("Speaker name is required.")
    if len(display_name) > 80:
        raise ValidationError("Speaker name must be 80 characters or fewer.")

    slug = slugify_speaker_name(display_name)
    if len(slug) < 2:
        raise ValidationError("Speaker name must contain at least two letters or numbers.")
    return display_name, slug
