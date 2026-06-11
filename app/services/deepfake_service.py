import torch
from typing import Dict
import app.config as config
from app.services.audio_utils import preprocess_audio


_deepfake_model = None


def get_deepfake_model():
    """Load and cache the deepfake detection model (singleton pattern)."""
    global _deepfake_model
    if _deepfake_model is None:
        # Lazy import to avoid import chain issues
        from transformers import pipeline
        _deepfake_model = pipeline(
            "audio-classification",
            model=config.DEEPFAKE_MODEL_ID,
            device=0 if torch.cuda.is_available() else -1
        )
    return _deepfake_model


def detect_deepfake(audio_path: str) -> Dict:
    """
    Detect if audio is real or fake (deepfake/synthesized).
    
    Args:
        audio_path: Path to audio file
        
    Returns:
        Dictionary with label, confidence, and explanation
    """
    model = get_deepfake_model()
    
    waveform, sample_rate = preprocess_audio(audio_path)
    
    audio_array = waveform.squeeze().numpy()
    
    results = model(audio_array, sampling_rate=sample_rate)
    
    top_result = max(results, key=lambda x: x['score'])
    
    label = map_label(top_result['label'])
    confidence = float(top_result['score'])
    explanation = generate_explanation(label, confidence)
    
    return {
        "label": label,
        "confidence": confidence,
        "explanation": explanation
    }


def map_label(raw_label: str) -> str:
    """
    Map model output label to standardized Real/Fake format.
    
    Args:
        raw_label: Raw label from model
        
    Returns:
        "Real" or "Fake"
    """
    raw_label_lower = raw_label.lower()
    
    if any(keyword in raw_label_lower for keyword in ['fake', 'spoof', 'synth', 'generated', 'bonafide']):
        if 'bonafide' in raw_label_lower:
            return "Real"
        return "Fake"
    elif any(keyword in raw_label_lower for keyword in ['real', 'genuine', 'authentic', 'human']):
        return "Real"
    
    return "Real" if raw_label_lower == "label_0" else "Fake"


def generate_explanation(label: str, confidence: float) -> str:
    """
    Generate human-readable explanation based on detection result.
    
    Args:
        label: Detection label (Real/Fake)
        confidence: Confidence score (0-1)
        
    Returns:
        Explanation string
    """
    if label == "Real":
        if confidence >= 0.8:
            return "Audio shows strong characteristics of genuine human speech."
        else:
            return "Audio appears human but confidence is limited."
    else:
        if confidence >= 0.8:
            return "Audio shows strong indicators of synthesis or voice conversion."
        else:
            return "Possible manipulation detected. Manual review recommended."
