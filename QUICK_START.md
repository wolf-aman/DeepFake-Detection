# Quick Start Guide - Submission Ready

## 🚀 For Evaluators: Getting Started in 2 Minutes

### Step 1: Install Dependencies
```bash
cd speaker-demo
uv sync
```

### Step 2: Run the Application
```bash
uv run uvicorn app.main:app --reload
```

### Step 3: Open Browser
Navigate to: **http://localhost:8000**

## 📱 Demo Features

### Main Demo (`/`)
1. **Enroll Speaker**: Upload 2-3 audio samples with a speaker name
2. **View Speakers**: See list of enrolled speakers
3. **Verify Speaker**: Test against enrolled voice
4. **Detect Deepfake**: Check if audio is real or fake

### Voice KYC (`/kyc`)
- Real-world mutual fund account opening workflow
- Demonstrates practical biometric authentication
- Shows deepfake detection for compliance

## 🎯 Key Features Implemented

| Feature | Status | Details |
|---------|--------|---------|
| Speaker Enrollment | ✅ | Extract and store voice embeddings |
| Speaker Verification | ✅ | Cosine similarity with 0.75 threshold |
| Deepfake Detection | ✅ | Classification with confidence scores |
| Web Interface | ✅ | Fully functional HTML/CSS/JavaScript |
| API Endpoints | ✅ | RESTful endpoints for all features |
| Database | ✅ | SQLite with metadata + .npy embeddings |
| Error Handling | ✅ | Comprehensive validation and feedback |
| Documentation | ✅ | Complete README with examples |

## 🤖 Models Used

| Task | Model | Source | Status |
|------|-------|--------|--------|
| Speaker Verification | `speechbrain/spkrec-ecapa-voxceleb` | HuggingFace | ✅ Working |
| Deepfake Detection | `mo-thecreator/audio-deepfake-detection` | HuggingFace | ✅ Working |

## 📊 Example Outputs

### Speaker Verification Response
```json
{
  "similarity": 0.87,
  "verified": true,
  "threshold": 0.75,
  "explanation": "Voice matches enrolled speaker with high confidence."
}
```

### Deepfake Detection Response
```json
{
  "label": "Real",
  "confidence": 0.94,
  "explanation": "Audio shows strong characteristics of genuine human speech."
}
```

## 🔧 Configuration

Edit `app/config.py` to customize:
- **VERIFICATION_THRESHOLD**: Default 0.75 (for speaker verification)
- **SAMPLE_RATE**: Default 16000 Hz
- Model IDs and storage paths

## 📚 Documentation Structure

1. **README.md**: Complete project documentation
   - Setup and installation
   - API endpoint descriptions
   - Model explanations
   - Threshold justification
   - Known limitations

2. **SUBMISSION_CHECKLIST.md**: Verification against all requirements
   - Core requirements met
   - Code quality standards
   - Bonus features implemented

3. **Code Comments**: Inline documentation in all services

## 🏆 Bonus Feature: Voice KYC

Demonstrates real-world application in financial services:
- Customer enrollment with voice biometrics
- Deepfake liveness detection
- Identity verification workflow
- Transaction authorization use case

## ⚠️ Important Notes

### Audio Files for Testing
- Format: WAV, MP3, FLAC, or OGG
- Sample Rate: Automatically resampled to 16kHz
- Duration: 3-10 seconds recommended per sample
- Quality: Clear speech without excessive background noise

### Enrollment Recommendations
- Enroll with **3-5 samples** for robustness
- Vary speaking style slightly (natural variation)
- Use consistent audio equipment if possible
- Avoid excessive background noise

### Verification Notes
- Similarity scores are normalized (0-1)
- Default threshold 0.75 balances security and usability
- Same speaker typically scores 0.80-0.95
- Different speakers typically score 0.40-0.70

## 🎓 For Interview Preparation

Key talking points:
1. **Why ECAPA-TDNN?** State-of-the-art speaker recognition, fixed-size embeddings
2. **Why Cosine Similarity?** Angular distance metric, robust to magnitude, computationally efficient
3. **Why 0.75 Threshold?** Empirical balance between false positives and false negatives
4. **Storage Architecture?** SQLite for metadata + .npy files for efficient embedding storage
5. **Deepfake Detection Approach?** Spectrogram-based classification using transformers

## 🐛 Troubleshooting Quick Fixes

| Issue | Solution |
|-------|----------|
| Models not downloading | Check internet, ensure 500MB+ disk space |
| Audio upload fails | Verify file format, check file size <50MB |
| Low verification accuracy | Add more enrollment samples, improve audio quality |
| Database errors | Delete `app/storage/speakers.db`, restart app |

## 📦 Files Structure

```
speaker-demo/
├── README.md                    ← Main documentation
├── SUBMISSION_CHECKLIST.md      ← Requirements verification
├── pyproject.toml               ← Dependencies (uv sync)
├── uv.lock                      ← Locked versions
├── app/
│   ├── main.py                  ← FastAPI app + routes
│   ├── config.py                ← Configuration
│   ├── services/
│   │   ├── speaker_service.py   ← Speaker verification logic
│   │   ├── deepfake_service.py  ← Deepfake detection logic
│   │   └── audio_utils.py       ← Audio preprocessing
│   ├── storage/
│   │   ├── db.py                ← SQLite database
│   │   └── embeddings/          ← .npy embedding files
│   ├── templates/
│   │   ├── index.html           ← Main demo
│   │   └── kyc.html             ← Voice KYC workflow
│   └── static/
│       ├── app.js               ← Frontend logic
│       └── style.css            ← Styling
```

## ✅ Verification Checklist for Evaluators

- [ ] App starts without errors: `uv sync && uv run uvicorn app.main:app --reload`
- [ ] Homepage loads: http://localhost:8000
- [ ] Can enroll a speaker (upload 2-3 audio files)
- [ ] Can view enrolled speakers in list
- [ ] Can verify against enrolled speaker (should match own voice)
- [ ] Can detect deepfake (test with real/synthetic audio)
- [ ] Voice KYC workflow accessible at `/kyc`
- [ ] All API endpoints respond correctly
- [ ] Error handling works (try invalid inputs)
- [ ] README comprehensive and accurate

---

**Ready for evaluation! 🎉**

For any questions about the implementation, refer to README.md or inline code comments.
