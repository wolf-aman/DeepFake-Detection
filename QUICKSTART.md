# Quick Start Guide

## Installation

1. **Install uv** (if not already installed):
   ```bash
   # Windows (PowerShell)
   powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
   
   # macOS/Linux
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. **Navigate to project directory**:
   ```bash
   cd speaker-demo
   ```

3. **Install dependencies**:
   ```bash
   uv sync
   ```
   
   This will:
   - Create a virtual environment
   - Install all required Python packages
   - Set up the project

## Running the Application

Start the FastAPI server:

```bash
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Access the application:
- Main Demo: http://localhost:8000
- Voice KYC: http://localhost:8000/kyc

## First Time Setup

The first time you use the application:
1. Models will be automatically downloaded (~500MB)
2. Database will be automatically created
3. Embeddings directory will be created

This may take a few minutes on first run.

## Basic Usage

### Speaker Enrollment
1. Go to http://localhost:8000
2. Enter a speaker name (e.g., "john_doe")
3. Upload 3-5 audio files of the same person
4. Click "Enroll Speaker"

### Speaker Verification
1. Select an enrolled speaker from dropdown
2. Upload an audio file to verify
3. Click "Verify Speaker"
4. View similarity score and verification result

### Deepfake Detection
1. Upload any audio file
2. Click "Detect Deepfake"
3. View Real/Fake classification with confidence

### Voice KYC Workflow
1. Go to http://localhost:8000/kyc
2. Complete all three steps:
   - Voice Enrollment
   - Identity Verification
   - Deepfake/Liveness Check
3. View final KYC decision

## Troubleshooting

### Models not downloading
- Check internet connection
- Ensure at least 1GB free disk space
- Check HuggingFace is accessible

### Audio file errors
- Supported formats: WAV, MP3, FLAC, OGG
- Ensure files are not corrupted
- Try converting to WAV format

### Port already in use
Change the port:
```bash
uv run uvicorn app.main:app --reload --port 8001
```

## API Documentation

Once running, access interactive API docs:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Sample Audio for Testing

You can use any audio recording app to create test samples:
- Windows: Voice Recorder app
- macOS: QuickTime Player (File > New Audio Recording)
- Linux: GNOME Sound Recorder or Audacity
- Mobile: Built-in voice recorder apps

Record yourself saying any phrase for 5-10 seconds per sample.

## Production Considerations

Before deploying to production:
1. Change default threshold if needed (in `app/config.py`)
2. Add authentication and authorization
3. Enable HTTPS
4. Set up proper logging
5. Configure rate limiting
6. Use production ASGI server (gunicorn + uvicorn)
7. Consider cloud storage for embeddings at scale

## Support

For issues, refer to:
- Full README.md for detailed documentation
- API docs at /docs endpoint
- Error messages in terminal output
