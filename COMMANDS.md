# Command Reference

## Installation Commands

### Install uv Package Manager

**Windows (PowerShell):**
```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**macOS/Linux:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Using pip:**
```bash
pip install uv
```

### Install Project Dependencies

```bash
cd speaker-demo
uv sync
```

## Running the Application

### Development Server (with auto-reload)
```bash
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Production Server (without reload)
```bash
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Custom Port
```bash
uv run uvicorn app.main:app --reload --port 8001
```

### Localhost Only
```bash
uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

## Testing API with curl

### List Enrolled Speakers
```bash
curl http://localhost:8000/speakers
```

### Enroll a Speaker
```bash
curl -X POST http://localhost:8000/enroll \
  -F "name=john_doe" \
  -F "files=@audio1.wav" \
  -F "files=@audio2.wav" \
  -F "files=@audio3.wav"
```

### Verify a Speaker
```bash
curl -X POST http://localhost:8000/verify \
  -F "name=john_doe" \
  -F "file=@test_audio.wav"
```

### Detect Deepfake
```bash
curl -X POST http://localhost:8000/detect-deepfake \
  -F "file=@audio_sample.wav"
```

### Delete a Speaker
```bash
curl -X DELETE http://localhost:8000/speakers/john_doe
```

## Python Commands

### Run in Python Interpreter
```bash
uv run python
```

Then test components:
```python
from app.services.speaker_service import extract_embedding
from app.storage.db import list_speakers

# List speakers
speakers = list_speakers()
print(speakers)

# Extract embedding
embedding = extract_embedding("path/to/audio.wav")
print(embedding.shape)
```

### Check Python Version
```bash
uv run python --version
```

## Utility Commands

### Clear Database (start fresh)
```bash
# Windows
del app\storage\speakers.db
del app\storage\embeddings\*.npy

# macOS/Linux
rm app/storage/speakers.db
rm app/storage/embeddings/*.npy
```

### Check Installed Packages
```bash
uv pip list
```

### Update Dependencies
```bash
uv sync --upgrade
```

## Audio Recording Commands

### Windows (using PowerShell)
```powershell
# Open Voice Recorder app
start ms-winsoundevent:
```

### macOS
```bash
# Open QuickTime Player
open -a "QuickTime Player"
# Then: File > New Audio Recording
```

### Linux (with ffmpeg)
```bash
# Record for 10 seconds
ffmpeg -f alsa -i default -t 10 output.wav

# Or use GNOME Sound Recorder
gnome-sound-recorder
```

## Development Commands

### Format Code (if black is installed)
```bash
uv run black app/
```

### Type Checking (if mypy is installed)
```bash
uv run mypy app/
```

### Run with Custom Config
```python
# Edit app/config.py and restart server
# No additional commands needed
```

## Docker Commands (Optional)

If you want to add Docker support later:

**Dockerfile example:**
```dockerfile
FROM python:3.10-slim

WORKDIR /app

RUN pip install uv
COPY pyproject.toml .
RUN uv sync

COPY app/ app/

CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Build and run:**
```bash
docker build -t speaker-demo .
docker run -p 8000:8000 speaker-demo
```

## Troubleshooting Commands

### Clear Python Cache
```bash
# Windows
del /s /q __pycache__
del /s /q *.pyc

# macOS/Linux
find . -type d -name __pycache__ -exec rm -r {} +
find . -type f -name "*.pyc" -delete
```

### Check Port Usage
```bash
# Windows
netstat -ano | findstr :8000

# macOS/Linux
lsof -i :8000
```

### Kill Process on Port
```bash
# Windows
# Find PID first, then:
taskkill /F /PID <pid>

# macOS/Linux
kill -9 $(lsof -ti:8000)
```

### Check Disk Space
```bash
# Windows
dir

# macOS/Linux
df -h
```

## Quick Test Sequence

```bash
# 1. Install
cd speaker-demo
uv sync

# 2. Run server
uv run uvicorn app.main:app --reload

# 3. In another terminal, test API
curl http://localhost:8000/speakers

# 4. Open browser
# Windows
start http://localhost:8000

# macOS
open http://localhost:8000

# Linux
xdg-open http://localhost:8000
```

## Environment Variables (Optional)

Create `.env` file for custom settings:
```bash
SPEAKER_MODEL_ID=speechbrain/spkrec-ecapa-voxceleb
DEEPFAKE_MODEL_ID=mo-thecreator/audio-deepfake-detection
VERIFICATION_THRESHOLD=0.75
SAMPLE_RATE=16000
```

Load in app:
```python
from dotenv import load_dotenv
load_dotenv()
```

## Access URLs

- Main Demo: http://localhost:8000
- Voice KYC: http://localhost:8000/kyc
- API Docs (Swagger): http://localhost:8000/docs
- API Docs (ReDoc): http://localhost:8000/redoc
- OpenAPI JSON: http://localhost:8000/openapi.json

## Common Workflows

### First Time Setup
```bash
cd speaker-demo
uv sync
uv run uvicorn app.main:app --reload
```
Then open http://localhost:8000

### Daily Development
```bash
cd speaker-demo
uv run uvicorn app.main:app --reload
```

### Testing Changes
```bash
# Server auto-reloads when files change
# Just edit code and refresh browser
```

### Starting Fresh
```bash
# Clear data
rm app/storage/speakers.db
rm app/storage/embeddings/*.npy

# Restart server
uv run uvicorn app.main:app --reload
```

## Production Deployment

### Using Gunicorn (Linux/macOS)
```bash
uv pip install gunicorn
uv run gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Using systemd Service (Linux)
Create `/etc/systemd/system/speaker-demo.service`:
```ini
[Unit]
Description=Speaker Demo API
After=network.target

[Service]
User=www-data
WorkingDirectory=/path/to/speaker-demo
ExecStart=/usr/local/bin/uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

Then:
```bash
sudo systemctl enable speaker-demo
sudo systemctl start speaker-demo
```

## Performance Monitoring

### Check Memory Usage
```bash
# Windows
tasklist | findstr python

# macOS/Linux
ps aux | grep python
```

### Monitor Logs
```bash
# If using systemd
journalctl -u speaker-demo -f

# Or add logging to app
uv run uvicorn app.main:app --log-level debug
```

---

**Need Help?**
- Check README.md for detailed documentation
- Check QUICKSTART.md for setup guide
- Check TROUBLESHOOTING section in README.md
