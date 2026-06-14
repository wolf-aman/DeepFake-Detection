# Speaker Verification & Audio Deepfake Detection Demo

A local FastAPI web demo for **speaker enrollment**, **speaker verification**, and **audio deepfake / spoof detection** using pretrained models. The project also includes a bonus **Voice KYC** workflow, hidden from the frontend by default and easy to enable when required.

---

## 1. Features

- **Speaker enrollment** with one or more uploaded audio samples.
- **Speaker verification** using speaker embeddings and cosine similarity.
- **Audio deepfake / spoof detection** using a pretrained Hugging Face audio-classification model.
- **SQLite local storage** for speaker metadata.
- **`.npy` embedding storage** for speaker voice profiles.
- **Simple HTML/CSS/JavaScript frontend** for enrollment, speaker listing, verification, and deepfake detection.
- **Bonus Voice KYC workflow** for a real-world financial onboarding use case.
- **KYC hidden by default** so the main demo stays focused and clean.
- **Local-first implementation** with no paid APIs and no hard-coded results.

---

## 2. Project structure

```text
speaker-deepfake-demo/
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI routes and app wiring
│   ├── config.py                  # Paths, thresholds, model IDs, feature flags
│   ├── services/
│   │   ├── __init__.py
│   │   ├── audio_utils.py         # Audio loading, temp-file handling, preprocessing
│   │   ├── speaker_service.py     # Speaker enrollment and verification logic
│   │   └── deepfake_service.py    # Audio deepfake / spoof detection logic
│   ├── storage/
│   │   ├── __init__.py
│   │   ├── db.py                  # SQLite database helper functions
│   │   ├── speakers.db            # Created automatically at runtime
│   │   └── embeddings/            # Stored speaker embedding .npy files
│   ├── templates/
│   │   ├── index.html             # Main demo UI
│   │   └── kyc.html               # Bonus Voice KYC UI
│   └── static/
│       ├── app.js                 # Frontend API calls and UI behavior
│       └── style.css              # Responsive light UI styling
├── pyproject.toml
├── uv.lock
└── README.md
```

Important package note:

```text
app/__init__.py
app/services/__init__.py
app/storage/__init__.py
```

These files are required so Python can import modules like `app.services.audio_utils` correctly.

---

## 3. Requirements

Recommended environment:

- Python 3.11
- `uv` package manager
- Windows, macOS, or Linux
- Internet connection on first model run, because pretrained model weights are downloaded automatically

Install `uv` if needed:

```bash
pip install uv
```

For Windows PowerShell users:

```powershell
uv python install 3.11
uv venv --python 3.11
uv sync
```

For macOS / Linux users:

```bash
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

The first time you use speaker verification or deepfake detection, the pretrained models may download and cache locally. This can take some time depending on your internet speed.

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

Open API docs:

```text
http://127.0.0.1:8000/docs
```

---

## 6. Voice KYC feature flag

The Voice KYC page is kept in the project as a bonus real-world use case, but it is **disabled by default** so it does not appear in the main frontend demo.

When disabled:

- The **Voice KYC** link is hidden from the main page.
- Directly opening `/kyc` returns `404`.
- The KYC implementation remains in the code and can be enabled later.

### Enable KYC on Windows PowerShell

```powershell
$env:ENABLE_KYC_DEMO="true"
uv run fastapi dev app/main.py
```

### Enable KYC on Windows CMD

```cmd
set ENABLE_KYC_DEMO=true && uv run fastapi dev app/main.py
```

### Enable KYC on macOS / Linux

```bash
ENABLE_KYC_DEMO=true uv run fastapi dev app/main.py
```

After enabling it, open:

```text
http://127.0.0.1:8000/kyc
```

---

## 7. API endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/` | Main web interface |
| `GET` | `/kyc` | Bonus Voice KYC interface, available only when `ENABLE_KYC_DEMO=true` |
| `POST` | `/enroll` | Enroll a speaker using `name` and one or more audio `files` |
| `GET` | `/speakers` | List all enrolled speakers |
| `DELETE` | `/speakers/{name}` | Delete an enrolled speaker and its stored embedding |
| `POST` | `/verify` | Verify an uploaded audio file against an enrolled speaker |
| `POST` | `/detect-deepfake` | Classify uploaded audio as real or fake |

### Example: enroll a speaker

```bash
curl -X POST http://127.0.0.1:8000/enroll \
  -F "name=John Doe" \
  -F "files=@sample1.wav" \
  -F "files=@sample2.wav"
```

### Example: verify a speaker

```bash
curl -X POST http://127.0.0.1:8000/verify \
  -F "name=John Doe" \
  -F "file=@test.wav"
```

### Example: detect deepfake audio

```bash
curl -X POST http://127.0.0.1:8000/detect-deepfake \
  -F "file=@test.wav"
```

---

## 8. How the system works

### 8.1 Speaker enrollment

1. User uploads one or more enrollment audio samples and enters a speaker name.
2. `main.py` receives the upload through `POST /enroll`.
3. Uploaded audio is temporarily saved using `save_temp_audio()`.
4. `speaker_service.py` extracts speaker embeddings using SpeechBrain ECAPA.
5. If multiple samples are provided, embeddings are averaged into one speaker profile.
6. The final embedding is saved as a `.npy` file under `app/storage/embeddings/`.
7. Speaker metadata is inserted into SQLite using `db.py`.
8. Temporary uploaded audio files are deleted after processing.

### 8.2 Speaker verification

1. User selects an enrolled speaker and uploads a test audio file.
2. `main.py` receives the request through `POST /verify`.
3. The stored embedding for that speaker is loaded from disk.
4. A new embedding is extracted from the uploaded test audio.
5. The system computes cosine similarity between the stored embedding and test embedding.
6. If the similarity is greater than or equal to `VERIFICATION_THRESHOLD`, the user is marked as verified.

### 8.3 Deepfake / spoof detection

1. User uploads an audio file.
2. The backend preprocesses audio to mono 16 kHz format.
3. `deepfake_service.py` loads the Hugging Face audio-classification model lazily.
4. The model returns logits for the audio classes.
5. Softmax converts logits into class probabilities.
6. The highest-scoring class is mapped to the standard demo labels: `Real` or `Fake`.
7. The API returns label, confidence, raw model label, and explanation.

### 8.4 Bonus Voice KYC workflow

The KYC workflow combines both APIs into a practical onboarding demo:

1. Enroll the user's voice.
2. Verify a fresh voice sample against the enrolled profile.
3. Run a deepfake / liveness-style authenticity check.
4. Approve only when the speaker is verified and the audio is classified as real.

Final decision logic:

```text
APPROVED = speaker_verified AND audio_is_real
REJECTED = speaker_not_verified OR audio_is_fake
```

---

## 9. Model choices

### 9.1 Speaker verification model

- **Model:** `speechbrain/spkrec-ecapa-voxceleb`
- **Library:** SpeechBrain
- **Task:** Speaker embedding extraction and speaker verification
- **Input format:** Mono speech waveform, resampled to 16 kHz
- **Output:** Speaker embedding vector
- **Scoring:** Cosine similarity between enrollment and test embeddings

Reference:

```text
https://huggingface.co/speechbrain/spkrec-ecapa-voxceleb
```

Why this model was chosen:

- It is a strong pretrained speaker-recognition model.
- It runs locally and does not require a paid API.
- It is simple to explain during an interview.
- It produces embeddings that can be stored efficiently and compared with cosine similarity.

### 9.2 Audio deepfake / spoof detection model

- **Model:** `mo-thecreator/Deepfake-audio-detection`
- **Library:** Hugging Face Transformers
- **Task:** Audio classification for real/fake speech detection
- **Input format:** Mono waveform, resampled to 16 kHz
- **Output:** Classification logits/probabilities

Reference:

```text
https://huggingface.co/mo-thecreator/Deepfake-audio-detection
```

Implementation note:

The deepfake detector uses:

```python
AutoFeatureExtractor
AutoModelForAudioClassification
```

It does **not** use `AutoProcessor` as the primary loader, because some audio-classification models do not ship with a text tokenizer. Using `AutoProcessor` can trigger errors such as:

```text
Can't load tokenizer for 'mo-thecreator/Deepfake-audio-detection'
```

Using `AutoFeatureExtractor` matches the model's audio-classification use case and avoids tokenizer-related loading errors.

Important limitation:

The detector should be treated as a **demo-level pretrained classifier**, not a production-grade spoofing system. Deepfake detection performance can vary heavily across datasets, microphones, noise conditions, compression, and unknown generation methods.

---

## 10. Storage design

The project uses two forms of local storage:

| Data | Storage location | Reason |
|---|---|---|
| Speaker metadata | `app/storage/speakers.db` | Easy querying, deletion, and timestamps |
| Speaker embeddings | `app/storage/embeddings/{name}.npy` | Efficient binary storage for NumPy vectors |

The SQLite database stores:

```text
id
name
embedding_path
created_at
```

The embedding vector is stored separately as a `.npy` file. This keeps the database simple and avoids storing large numeric arrays directly inside SQL rows.

### Inspect stored speakers

```powershell
uv run python -c "import sqlite3; from pathlib import Path; db=Path('app/storage/speakers.db'); con=sqlite3.connect(db); con.row_factory=sqlite3.Row; print([dict(r) for r in con.execute('SELECT * FROM speakers').fetchall()])"
```

### Inspect embedding vectors

```powershell
uv run python -c "import sqlite3, numpy as np; from pathlib import Path; storage=Path('app/storage'); con=sqlite3.connect(storage/'speakers.db'); con.row_factory=sqlite3.Row; rows=con.execute('SELECT name, embedding_path FROM speakers').fetchall(); [print('\nSpeaker:', r['name'], '\nPath:', storage/r['embedding_path'], '\nShape:', np.load(storage/r['embedding_path']).shape, '\nFirst 10 values:', np.load(storage/r['embedding_path'])[:10]) for r in rows]"
```

---

## 11. Verification threshold explanation

The default verification threshold is:

```text
0.75 cosine similarity
```

Reasoning for this demo:

- Speaker verification compares two embedding vectors.
- Cosine similarity measures how close the two voice embeddings are in embedding space.
- Higher similarity means the voices are more likely to belong to the same speaker.
- `0.75` is used as a practical starting threshold for controlled demo recordings.
- The threshold is intentionally easy to explain and tune.

Production note:

This threshold is **not production-calibrated**. In a real deployment, the threshold should be selected using a labeled validation set with:

- same-speaker pairs
- different-speaker pairs
- noisy recordings
- different microphones
- different languages or accents if relevant
- different recording sessions
- replayed or synthetic attack samples if security is important

A production system should evaluate:

- False Acceptance Rate, FAR
- False Rejection Rate, FRR
- ROC curve
- Equal Error Rate, EER
- threshold sensitivity across devices and environments

---

## 12. Sample API responses

### Enrollment response

```json
{
  "message": "Speaker enrolled successfully",
  "name": "John Doe"
}
```

### Speaker list response

```json
[
  {
    "id": 1,
    "name": "John Doe",
    "embedding_path": "embeddings/John Doe.npy",
    "created_at": "2026-06-14T18:00:00.000000"
  }
]
```

### Verification response

```json
{
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
  "explanation": "Audio appears to be natural human speech with no strong synthesis artifacts detected."
}
```

---

## 13. Known limitations

- The demo is not a production authentication system.
- Short or silent audio can reduce reliability.
- Noisy recordings can reduce both speaker verification and deepfake detection accuracy.
- The speaker threshold is manually chosen and not calibrated on a large validation set.
- Deepfake detection confidence is model confidence, not a guaranteed real-world probability.
- Deepfake models can fail on unseen synthesis methods or heavy compression.
- The KYC workflow is a demonstration of API usage, not a legally compliant KYC product.
- The app stores data locally and does not include user authentication, encryption, audit logging, or consent management.

---

## 14. Troubleshooting

### Error: `No module named 'app.services.audio_utils'`

This usually means the folder structure is wrong or `__init__.py` files are missing.

Check that your project has:

```text
app/__init__.py
app/services/__init__.py
app/services/audio_utils.py
app/storage/__init__.py
```

Also run the app from the project root:

```bash
uv run fastapi dev app/main.py
```

Do not run it from inside the `app/` folder.

### Error: `Can't load tokenizer for 'mo-thecreator/Deepfake-audio-detection'`

This happens when the loader tries to find a tokenizer for an audio-classification model.

Fix used in this project:

```python
from transformers import AutoFeatureExtractor, AutoModelForAudioClassification
```

The deepfake service should load the model like this:

```python
_feature_extractor = AutoFeatureExtractor.from_pretrained(config.DEEPFAKE_MODEL_ID)
_model = AutoModelForAudioClassification.from_pretrained(config.DEEPFAKE_MODEL_ID)
```

Also make sure you do not have a local folder named `mo-thecreator` inside the project, because Transformers may accidentally try to load from that local path.

### First request is slow

The first speaker verification or deepfake detection request may be slow because the model is downloaded and loaded into memory. Later requests are faster because the models are cached and lazy-loaded.

---

## 15. Interview explanation points

You should be ready to explain:

- What speaker embeddings are.
- Why cosine similarity is used.
- Why multiple enrollment samples are averaged.
- Why audio is converted to mono 16 kHz.
- What the threshold means and why it needs calibration.
- Why deepfake detection is harder than speaker verification.
- Why model confidence is not always a calibrated probability.
- Why KYC is a bonus workflow and hidden by default in the main demo.
- Why SQLite plus `.npy` files is a simple and explainable storage choice.

---

## 16. Quick run checklist

```bash
uv sync
uv run fastapi dev app/main.py
```

Then test in the browser:

```text
http://127.0.0.1:8000
```

Recommended demo flow:

1. Enroll a speaker with 3 short `.wav` files.
2. Refresh the speaker list.
3. Select the enrolled speaker and verify a fresh test sample.
4. Upload an audio sample for deepfake detection.
5. Enable KYC only if you want to show the bonus workflow.
