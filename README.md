# Speaker Verification & Audio Deepfake Detection Demo

This is a cleaned and refactored FastAPI web demo for:

1. Speaker enrollment
2. Speaker verification
3. Audio deepfake / spoof detection
4. A bonus voice-KYC style workflow

The app uses pretrained models only. It does **not** train any model from scratch.

## Project structure

```text
speaker-deepfake-demo/
├── app/
│   ├── main.py                  # FastAPI routes and app wiring
│   ├── config.py                # Central settings
│   ├── core/
│   │   └── exceptions.py        # Typed application errors
│   ├── services/
│   │   ├── audio.py             # Upload validation + audio preprocessing
│   │   ├── speaker.py           # Enrollment and verification logic
│   │   └── deepfake.py          # Audio authenticity detection logic
│   ├── storage/
│   │   ├── db.py                # SQLite repository
│   │   └── embeddings/          # Speaker .npy embeddings
│   ├── templates/
│   │   ├── index.html           # Main demo UI
│   │   └── kyc.html             # Bonus KYC UI
│   └── static/
│       ├── app.js               # Frontend interactions
│       └── style.css            # Light professional UI
├── pyproject.toml
└── README.md
```

## Setup

Install `uv` if it is not already installed:

```bash
pip install uv
```

Create the environment and install dependencies:

```bash
uv sync
```

The first model call will download model weights into `pretrained_models/`.

## Run

```bash
uv run fastapi dev app/main.py
```

Open:

```text
http://127.0.0.1:8000
```

KYC demo:

```text
http://127.0.0.1:8000/kyc
```

Health check:

```text
http://127.0.0.1:8000/health
```

## API endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/` | Main web interface |
| `GET` | `/kyc` | Voice KYC interface |
| `GET` | `/health` | Basic health check |
| `POST` | `/enroll` | Enroll a speaker using `name` and one or more `files` |
| `GET` | `/speakers` | List enrolled speakers |
| `DELETE` | `/speakers/{name}` | Delete an enrolled speaker by name or slug |
| `POST` | `/verify` | Verify a test audio file against an enrolled speaker |
| `POST` | `/detect-deepfake` | Classify audio as real/fake/unknown |

Example `curl` commands:

```bash
curl -X POST http://127.0.0.1:8000/enroll \
  -F "name=John Doe" \
  -F "files=@sample1.wav" \
  -F "files=@sample2.wav"

curl -X POST http://127.0.0.1:8000/verify \
  -F "name=john_doe" \
  -F "file=@test.wav"

curl -X POST http://127.0.0.1:8000/detect-deepfake \
  -F "file=@test.wav"
```

## Model choices

### Speaker verification

- Model: `speechbrain/spkrec-ecapa-voxceleb`
- Why: ECAPA-TDNN speaker embeddings are widely used for speaker verification demos.
- Input: mono speech audio, converted internally to 16 kHz.
- Output: a speaker embedding vector.
- Comparison: cosine similarity between enrolled and test embeddings.

### Deepfake / spoof detection

- Model: `mo-thecreator/Deepfake-audio-detection`
- Why: Hugging Face audio-classification model intended for real/fake audio detection.
- Input: mono audio array at 16 kHz.
- Output: predicted model label, confidence, and explanation.

## Storage choice

The app stores:

- Speaker metadata in SQLite: `app/storage/speakers.db`
- Speaker embeddings as `.npy` files: `app/storage/embeddings/{speaker_slug}.npy`

This keeps the demo simple, transparent, and easy to inspect. SQLite handles metadata querying while NumPy files store numeric embedding vectors efficiently.

## Verification threshold

The default threshold is `0.75` cosine similarity.

Reasoning:

- For a demo, `0.75` is a practical starting point for ECAPA-style embeddings.
- It is not a production-calibrated threshold.
- For real deployment, collect validation audio from target users, evaluate genuine/impostor score distributions, and choose a threshold based on target false accept / false reject rates.

## Important fixes and improvements made

- Added proper `app/` package structure.
- Added application startup database initialization.
- Added typed app errors instead of exposing raw tracebacks to users.
- Added upload validation: file extension, max upload size, empty-file checks, short/silent audio checks.
- Replaced direct speaker-name file paths with sanitized speaker slugs.
- Added repository pattern for SQLite storage.
- Added service classes for speaker verification and deepfake detection.
- Added thread-safe lazy model loading.
- Improved temporary-file cleanup.
- Rewrote frontend DOM rendering to avoid injecting user-controlled speaker names through `innerHTML`.
- Added `encodeURIComponent` for speaker delete calls.
- Added raw model labels to deepfake responses for transparency.

## Known limitations

- This is still a local demo, not a production KYC system.
- Verification threshold is not calibrated on your target population.
- Deepfake model reliability depends heavily on audio quality, language, codec, and recording conditions.
- No authentication, authorization, audit trail, or rate limiting is included.
- Browser `accept="audio/*"` is only a UI hint; backend validation is still required and included.
- Very noisy, very short, or silent recordings are rejected.

## Screenshots / sample outputs

Enrollment response:

```json
{
  "message": "Speaker enrolled successfully",
  "name": "John Doe",
  "slug": "john_doe",
  "samples_used": 3
}
```

Verification response:

```json
{
  "name": "John Doe",
  "similarity": 0.812345,
  "verified": true,
  "threshold": 0.75
}
```

Deepfake response:

```json
{
  "label": "Real",
  "confidence": 0.934321,
  "raw_label": "bonafide",
  "explanation": "The model classifies this as natural speech with high confidence (93.4%)."
}
```
