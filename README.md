# Speaker Verification & Audio Deepfake Detection Demo

A FastAPI-based web demo for speaker enrollment, speaker verification, audio deepfake/spoof detection, and a bonus voice-KYC workflow.

The project uses pretrained models and local storage. It does **not** train a large model from scratch and does **not** require paid APIs.

---

## 1. Features

- **Speaker enrollment** using one or more audio samples.
- **Speaker verification** using speaker embeddings and cosine similarity.
- **Audio deepfake/spoof detection** using a pretrained Hugging Face audio-classification model.
- **SQLite-backed local metadata storage** with `.npy` files for embedding vectors.
- **Simple HTML/CSS/JavaScript frontend** for enrollment, verification, speaker management, and deepfake detection.
- **Bonus Voice KYC workflow** showing a practical use case for mutual-fund or financial onboarding.
- **Local-first design**: no paid APIs are required for the core demo.

---

## 2. Project structure

```text
speaker-deepfake-demo/
├── app/
│   ├── __init__.py
│   ├── main.py                  # FastAPI routes and app wiring
│   ├── config.py                # Central settings and model IDs
│   ├── core/
│   │   └── exceptions.py        # Typed application exceptions
│   ├── services/
│   │   ├── audio.py             # Audio loading, validation, preprocessing
│   │   ├── speaker.py           # Speaker enrollment and verification logic
│   │   └── deepfake.py          # Audio authenticity / spoof detection logic
│   ├── storage/
│   │   ├── db.py                # SQLite repository layer
│   │   └── embeddings/          # Stored speaker embedding .npy files
│   ├── templates/
│   │   ├── index.html           # Main demo UI
│   │   └── kyc.html             # Bonus voice-KYC UI
│   └── static/
│       ├── app.js               # Frontend API calls and UI behavior
│       └── style.css            # Responsive light UI styling
├── scripts/
│   └── evaluate_deepfake_dataset.py  # Optional local evaluation script
├── pyproject.toml
├── uv.lock
└── README.md
```

---

## 3. Requirements

Recommended environment:

- Python 3.11
- `uv` package manager
- Windows, macOS, or Linux
- Internet connection on first run, because pretrained model weights are downloaded automatically

Install `uv` if needed:

```bash
pip install uv
```

For Windows PowerShell users, the project was tested with commands like:

```powershell
uv python install 3.11
uv venv --python 3.11
uv sync
```

---

## 4. Setup

From the project root:

```bash
uv sync
```

This installs dependencies from `pyproject.toml` and `uv.lock`.

The first time speaker verification or deepfake detection is used, model weights may be downloaded and cached locally. This can take time depending on internet speed.

---

## 5. Run the app

Start the FastAPI development server:

```bash
uv run fastapi dev app/main.py
```

Open the main demo:

```text
http://127.0.0.1:8000
```

Open the bonus voice-KYC workflow:

```text
http://127.0.0.1:8000/kyc
```

Open API docs:

```text
http://127.0.0.1:8000/docs
```

Health check:

```text
http://127.0.0.1:8000/health
```

---

## 6. API endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/` | Main web interface |
| `GET` | `/kyc` | Bonus voice-KYC interface |
| `GET` | `/health` | Basic backend health check |
| `POST` | `/enroll` | Enroll a speaker using `name` and one or more audio `files` |
| `GET` | `/speakers` | List all enrolled speakers |
| `DELETE` | `/speakers/{name}` | Delete an enrolled speaker by name or slug |
| `POST` | `/verify` | Verify an uploaded audio file against an enrolled speaker |
| `POST` | `/detect-deepfake` | Classify uploaded audio as real/fake/unknown |

Example API calls:

```bash
curl -X POST http://127.0.0.1:8000/enroll \
  -F "name=John Doe" \
  -F "files=@sample1.wav" \
  -F "files=@sample2.wav"
```

```bash
curl -X POST http://127.0.0.1:8000/verify \
  -F "name=john_doe" \
  -F "file=@test.wav"
```

```bash
curl -X POST http://127.0.0.1:8000/detect-deepfake \
  -F "file=@test.wav"
```

---

## 7. How the system works

### 7.1 Speaker enrollment

1. User uploads one or more enrollment audio samples and provides a speaker name.
2. The backend validates the uploaded files.
3. Each audio file is loaded, converted to mono, and resampled to 16 kHz.
4. A pretrained speaker model extracts an embedding from each sample.
5. Enrollment embeddings are combined into a speaker profile.
6. The speaker metadata is stored in SQLite.
7. The embedding vector is saved as a `.npy` file.

### 7.2 Speaker verification

1. User selects an enrolled speaker and uploads a test audio file.
2. The same speaker embedding model extracts an embedding from the test audio.
3. The stored enrollment embedding and test embedding are compared using cosine similarity.
4. If the similarity is greater than or equal to the threshold, the speaker is marked as verified.

### 7.3 Deepfake / spoof detection

1. User uploads an audio file.
2. Audio is converted to the expected input format for the detector.
3. A pretrained audio-classification model predicts whether the audio appears real or fake.
4. The API returns the predicted label, confidence score, raw model label, and explanation.

### 7.4 Bonus voice-KYC workflow

The `/kyc` page demonstrates a practical financial onboarding flow:

1. Enroll the user's voice.
2. Verify a fresh voice sample against the enrolled profile.
3. Run an audio authenticity/deepfake check.
4. Show a final approve/reject decision based on both checks.

---

## 8. Model choices

### 8.1 Speaker verification model

- **Model:** `speechbrain/spkrec-ecapa-voxceleb`
- **Library:** SpeechBrain
- **Task:** Speaker embedding extraction and speaker verification
- **Training source:** VoxCeleb-style speaker recognition data, as described on the model card
- **Input:** Mono speech waveform, internally resampled to 16 kHz
- **Output:** Fixed-dimensional speaker embedding vector
- **Scoring:** Cosine similarity between enrolled and test embeddings

Reference:

```text
https://huggingface.co/speechbrain/spkrec-ecapa-voxceleb
```

Why this model was chosen:

- It is simple to use locally.
- It is a common pretrained baseline for speaker verification demos.
- It avoids paid APIs and keeps the project reproducible.
- It produces embeddings that can be stored and compared efficiently.

### 8.2 Audio deepfake / spoof detection model

The deepfake detector is configurable through `app/config.py` or an environment variable if enabled in the service.

Models tested during development included:

```text
mo-thecreator/Deepfake-audio-detection
garystafford/wav2vec2-deepfake-voice-detector
```

The current detector should be treated as a **demo-level pretrained classifier**, not a production-grade spoofing system.

Recommended future model direction:

- Prefer models trained or evaluated on ASVspoof-style datasets.
- ASVspoof 2019 Logical Access includes speech synthesis and voice-conversion attacks.
- ASVspoof 2021 includes more challenging evaluation conditions for fake/spoofed speech.

References:

```text
https://www.asvspoof.org/index2019.html
https://www.asvspoof.org/asvspoof2019/ASRU-2019-special-session.html
https://huggingface.co/garystafford/wav2vec2-deepfake-voice-detector
```

Why this approach was used:

- The assignment requires a pretrained model suitable for audio spoof/deepfake detection.
- Hugging Face audio classifiers are easy to run locally.
- The API returns an interpretable label, confidence score, and explanation.

Important note:

Deepfake detection is a harder and less stable task than speaker verification. A model can perform well on one dataset but fail on another fake-generation method. For this reason, the README documents limitations clearly and includes an evaluation script for testing model behavior on labeled real/fake data.

---

## 9. Storage design

The project uses two forms of local storage:

| Data | Storage location | Reason |
|---|---|---|
| Speaker metadata | `app/storage/speakers.db` | Easy querying, deletion, timestamps, speaker names/slugs |
| Speaker embeddings | `app/storage/embeddings/{speaker_slug}.npy` | Efficient binary storage for NumPy vectors |

The SQLite database stores metadata such as:

```text
id
name
slug
embedding_path
created_at
```

The actual embedding vector is stored separately as a `.npy` file. This keeps the database readable and avoids storing large numeric arrays directly inside SQL rows.

### Inspect stored speakers

```powershell
uv run python -c "import sqlite3; from pathlib import Path; db=Path('app/storage/speakers.db'); con=sqlite3.connect(db); con.row_factory=sqlite3.Row; print([dict(r) for r in con.execute('SELECT * FROM speakers').fetchall()])"
```

### Inspect embedding vectors

```powershell
uv run python -c "import sqlite3, numpy as np; from pathlib import Path; storage=Path('app/storage'); con=sqlite3.connect(storage/'speakers.db'); con.row_factory=sqlite3.Row; rows=con.execute('SELECT name, embedding_path FROM speakers').fetchall(); [print('\nSpeaker:', r['name'], '\nPath:', storage/r['embedding_path'], '\nShape:', np.load(storage/r['embedding_path']).shape, '\nFirst 10 values:', np.load(storage/r['embedding_path'])[:10]) for r in rows]"
```

---

## 10. Verification threshold explanation

The default speaker verification threshold is:

```text
0.75 cosine similarity
```

Reasoning for this demo:

- Speaker verification compares two embedding vectors using cosine similarity.
- Higher similarity means the voices are more likely to belong to the same speaker.
- `0.75` is used as a practical demo threshold for controlled recordings.
- This threshold is easy to explain and works as a starting point for manual testing.

Production note:

This is **not** a production-calibrated threshold. In a real deployment, the threshold should be selected using a labeled validation set containing:

- same-speaker pairs
- different-speaker pairs
- noisy recordings
- different microphones
- different recording sessions

A production system would analyze false acceptance rate, false rejection rate, ROC curves, and equal error rate before selecting a threshold.

---

## 11. Evaluation and calibration

An optional evaluation script can be used to test real/fake performance on labeled folders:

```powershell
uv run python scripts/evaluate_deepfake_dataset.py --real-dir "PATH_TO_REAL_FOLDER" --fake-dir "PATH_TO_FAKE_FOLDER" --limit-per-class 5 --output deepfake_eval.csv
```

Example with a dataset structured as `AUDIO/REAL` and `AUDIO/FAKE`:

```powershell
uv run python scripts/evaluate_deepfake_dataset.py --real-dir "C:\Users\amanr\Downloads\code\asr-project\sample_audio\AUDIO\REAL" --fake-dir "C:\Users\amanr\Downloads\code\asr-project\sample_audio\AUDIO\FAKE" --limit-per-class 5 --output deepfake_eval_5_real_5_fake.csv
```

The script reports:

- overall accuracy
- real-class accuracy
- fake-class accuracy
- false positives
- false negatives
- per-file confidence scores
- chunk-level fake/real scores if chunking is enabled

This is useful because raw softmax confidence from transformer classifiers is not always a calibrated probability.

---

## 12. Sample responses

### Enrollment response

```json
{
  "message": "Speaker enrolled successfully",
  "name": "John Doe",
  "slug": "john_doe",
  "samples_used": 3
}
```

### Verification response

```json
{
  "name": "John Doe",
  "similarity": 0.812345,
  "verified": true,
  "threshold": 0.75
}
```

### Deepfake detection response

```json
{
  "label": "Real",
  "confidence": 0.934321,
  "raw_label": "real",
  "class_probabilities": {
    "fake": 0.065679,
    "real": 0.934321
  },
  "model_id": "configured-model-id",
  "explanation": "The model classifies this as natural speech with high confidence (93.4%)."
}
```

---

## 13. Screenshots

Add screenshots before submission if available:

```text
screenshots/
├── 01-home-page.png
├── 02-enrollment-success.png
├── 03-speaker-verification-score.png
├── 04-deepfake-result.png
└── 05-kyc-final-decision.png
```

Recommended screenshot checklist:

- Main dashboard loaded
- Speaker enrollment success
- Enrolled speaker list
- Speaker verification result with similarity score
- Deepfake detection result with label/confidence
- Bonus KYC approval/rejection screen

---

## 14. Error handling and validation

The backend includes practical checks such as:

- empty file validation
- supported audio extension validation
- temporary file cleanup
- short/silent audio handling
- typed application errors
- JSON error responses for frontend display
- sanitized speaker slugs for safer filenames

Frontend behavior includes:

- loading states
- success/error messages
- speaker dropdown refresh
- delete confirmation
- result cards for verification and deepfake detection

---

## 15. Known limitations

This demo is not a production authentication system.

Current limitations:

- Speaker threshold is manually selected and not fully calibrated.
- No formal EER/ROC calibration is included.
- Speaker embeddings may degrade with noisy, short, or silence-heavy audio.
- Deepfake detection accuracy depends strongly on the training data of the selected model.
- A deepfake model trained on one attack type may fail on another attack type.
- Raw softmax confidence can be overconfident and should not be interpreted as a perfect probability.
- No authentication, authorization, audit logging, or rate limiting is included.
- No database encryption or secure user identity management is included.
- The KYC page is a demo workflow, not a legally compliant KYC product.

---

## 16. Future improvements

Recommended improvements for a more production-like system:

1. Store individual enrollment embeddings and compare against each sample instead of relying only on one averaged embedding.
2. Add voice activity detection or silence trimming before speaker embedding extraction.
3. Calibrate speaker threshold using genuine/impostor validation pairs.
4. Evaluate multiple ASVspoof-trained deepfake models and choose based on measured performance.
5. Add confidence calibration for deepfake scores using a validation set.
6. Add persistent logging of verification/deepfake attempts for later analysis.
7. Add authentication and role-based access for admin functions.
8. Add rate limiting and upload-size controls for safer deployment.
9. Add Docker packaging for easier reproducibility.
10. Add automated tests for API endpoints and service functions.

---

## 17. Questions to be ready to answer

### What is a speaker embedding?

A speaker embedding is a numerical vector representing voice characteristics of a speaker. Similar voices should produce vectors that are close in embedding space.

### How does cosine similarity work here?

Cosine similarity measures the angle between two embedding vectors. A higher score means the enrolled voice and test voice are more similar.

### Why use SQLite and `.npy` files?

SQLite stores metadata cleanly, while `.npy` files store numeric embedding vectors efficiently. This keeps the project simple and transparent.

### Why is the threshold 0.75?

It is a demo threshold chosen as a practical starting point for controlled recordings. In production it should be calibrated using validation data, ROC curves, false accept rate, false reject rate, and EER.

### What are the limitations of the deepfake detector?

Deepfake detection depends heavily on model training data. A detector may work on one dataset but fail on another fake-generation method such as voice conversion, TTS, replay, or codec-degraded audio.

---

## 18. Submission checklist

Before submitting, ensure the repository or ZIP includes:

- [ ] `README.md`
- [ ] `pyproject.toml`
- [ ] `uv.lock`
- [ ] `app/main.py`
- [ ] `app/templates/`
- [ ] `app/static/`
- [ ] `app/services/`
- [ ] `app/storage/`
- [ ] Example screenshots or sample outputs
- [ ] Clear setup and run instructions
- [ ] Known limitations section

---

## 19. Final note

This project is intended as a clear, local, explainable demo of speaker verification and audio authenticity checking. It demonstrates the full flow from upload to preprocessing, embedding extraction, scoring, local storage, frontend display, and a practical KYC-style use case.
