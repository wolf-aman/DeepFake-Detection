import numpy as np
import torch
from typing import Dict
import sys
import types
import app.config as config
from app.services.audio_utils import preprocess_audio

_processor = None
_model = None


def _load_model():
    global _processor, _model
    if _model is None:
        try:
            # Block ALL problematic SpeechBrain lazy import modules
            problematic_modules = [
                'speechbrain.integrations.k2_fsa',
                'speechbrain.integrations.nlp',
                'speechbrain.integrations.huggingface.wordemb',
                'speechbrain.k2_integration',
                'speechbrain.wordemb',
            ]
            
            for mod_name in problematic_modules:
                if mod_name not in sys.modules:
                    sys.modules[mod_name] = types.ModuleType(mod_name)
            
            from transformers import AutoProcessor, AutoModelForAudioClassification
            
            print(f"Loading deepfake model: {config.DEEPFAKE_MODEL_ID}")
            
            _processor = AutoProcessor.from_pretrained(config.DEEPFAKE_MODEL_ID)
            _model = AutoModelForAudioClassification.from_pretrained(config.DEEPFAKE_MODEL_ID)
            _model.eval()
            
            print("Deepfake model loaded successfully")
        except Exception as e:
            import traceback
            print("ERROR loading deepfake model:")
            traceback.print_exc()
            raise


def detect_deepfake(audio_path: str) -> Dict:
    _load_model()

    waveform, _ = preprocess_audio(audio_path)
    audio_array = waveform.squeeze().numpy().astype(np.float32)

    # Wav2Vec2 needs at least 1 second of audio
    min_samples = config.SAMPLE_RATE
    if len(audio_array) < min_samples:
        audio_array = np.pad(audio_array, (0, min_samples - len(audio_array)))

    inputs = _processor(
        audio_array,
        sampling_rate=config.SAMPLE_RATE,
        return_tensors="pt",
        padding=True,
    )

    with torch.no_grad():
        logits = _model(**inputs).logits

    probs = torch.softmax(logits, dim=-1).squeeze().numpy()
    predicted_id = int(np.argmax(probs))
    raw_label = _model.config.id2label[predicted_id]
    confidence = float(probs[predicted_id])

    label = _normalize_label(raw_label)
    return {
        "label": label,
        "confidence": confidence,
        "explanation": _build_explanation(label, confidence),
    }


def _normalize_label(raw: str) -> str:
    # Map model-specific labels to standard Real/Fake regardless of model variant
    keywords = ["fake", "spoof", "synthesized", "generated", "converted"]
    return "Fake" if any(k in raw.lower() for k in keywords) else "Real"


def _build_explanation(label: str, confidence: float) -> str:
    if label == "Real":
        if confidence >= 0.8:
            return "Audio appears to be natural human speech with no detected synthesis artifacts."
        return "Audio likely genuine but confidence is moderate. Consider re-recording in a quieter environment."
    else:
        if confidence >= 0.8:
            return "Audio shows strong patterns inconsistent with natural speech, likely synthesized or voice-converted."
        return "Possible manipulation detected with low confidence. Manual review recommended."