import sys
import types
from typing import Dict

import numpy as np
import torch

import app.config as config
from app.services.audio_utils import preprocess_audio

_feature_extractor = None
_model = None


def _load_model():
    """Lazy-load the audio deepfake classification model.

    Important: this model is an audio-classification model. It does not ship
    with a text tokenizer, so using AutoProcessor can fail by looking for a
    Wav2Vec2CTCTokenizer. AutoFeatureExtractor is the correct loader here.
    """
    global _feature_extractor, _model

    if _model is not None and _feature_extractor is not None:
        return

    try:
        # Prevent optional SpeechBrain integrations from breaking imports in
        # environments where k2/NLP extras are not installed.
        problematic_modules = [
            "speechbrain.integrations.k2_fsa",
            "speechbrain.integrations.nlp",
            "speechbrain.integrations.huggingface.wordemb",
            "speechbrain.k2_integration",
            "speechbrain.wordemb",
        ]

        for module_name in problematic_modules:
            if module_name not in sys.modules:
                sys.modules[module_name] = types.ModuleType(module_name)

        from transformers import AutoFeatureExtractor, AutoModelForAudioClassification

        print(f"Loading deepfake model: {config.DEEPFAKE_MODEL_ID}")

        _feature_extractor = AutoFeatureExtractor.from_pretrained(config.DEEPFAKE_MODEL_ID)
        _model = AutoModelForAudioClassification.from_pretrained(config.DEEPFAKE_MODEL_ID)
        _model.eval()

        print("Deepfake model loaded successfully")
    except Exception:
        import traceback

        print("ERROR loading deepfake model:")
        traceback.print_exc()
        raise


def detect_deepfake(audio_path: str) -> Dict:
    """Classify uploaded audio as Real/Fake and return confidence + explanation."""
    _load_model()

    waveform, _ = preprocess_audio(audio_path)
    audio_array = waveform.squeeze().detach().cpu().numpy().astype(np.float32)

    # Wav2Vec2-based classifiers need enough samples for stable inference.
    min_samples = config.SAMPLE_RATE
    if audio_array.ndim == 0:
        audio_array = np.array([float(audio_array)], dtype=np.float32)
    if len(audio_array) < min_samples:
        audio_array = np.pad(audio_array, (0, min_samples - len(audio_array)))

    inputs = _feature_extractor(
        audio_array,
        sampling_rate=config.SAMPLE_RATE,
        return_tensors="pt",
        padding=True,
    )

    with torch.no_grad():
        logits = _model(**inputs).logits

    probs = torch.softmax(logits, dim=-1).squeeze().detach().cpu().numpy()
    predicted_id = int(np.argmax(probs))
    raw_label = _model.config.id2label.get(predicted_id, str(predicted_id))
    confidence = float(probs[predicted_id])

    label = _normalize_label(raw_label)
    return {
        "label": label,
        "confidence": confidence,
        "raw_label": raw_label,
        "explanation": _build_explanation(label, confidence),
    }


def _normalize_label(raw: str) -> str:
    """Map model-specific labels to the demo's standard Real/Fake labels."""
    raw_lower = raw.lower()
    fake_keywords = ["fake", "spoof", "synthesized", "synthetic", "generated", "converted"]
    real_keywords = ["real", "bonafide", "bona-fide", "genuine", "human"]

    if any(keyword in raw_lower for keyword in fake_keywords):
        return "Fake"
    if any(keyword in raw_lower for keyword in real_keywords):
        return "Real"

    # Safe fallback for common binary configs where LABEL_1 often represents fake.
    return "Fake" if raw_lower in {"label_1", "1"} else "Real"


def _build_explanation(label: str, confidence: float) -> str:
    if label == "Real":
        if confidence >= 0.8:
            return "Audio appears to be natural human speech with no strong synthesis artifacts detected."
        return "Audio is likely genuine, but confidence is moderate. Re-recording in a quieter environment is recommended."

    if confidence >= 0.8:
        return "Audio shows strong patterns commonly associated with synthesized, spoofed, or voice-converted speech."
    return "Possible manipulation detected with moderate or low confidence. Manual review is recommended."
