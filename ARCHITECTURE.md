# System Architecture

## 🏗️ High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Web Browser                           │
│  ┌──────────────────┐          ┌──────────────────┐        │
│  │   Main Demo UI   │          │   Voice KYC UI   │        │
│  │  (index.html)    │          │   (kyc.html)     │        │
│  └──────────────────┘          └──────────────────┘        │
│           │                              │                   │
│           └──────────────┬───────────────┘                  │
│                          │                                   │
│                    app.js (Frontend Logic)                   │
│                          │                                   │
└──────────────────────────┼───────────────────────────────────┘
                           │ HTTP/JSON
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                   FastAPI Backend (main.py)                  │
│  ┌────────────┐  ┌────────────┐  ┌────────────────────┐   │
│  │  /enroll   │  │  /verify   │  │ /detect-deepfake   │   │
│  └────────────┘  └────────────┘  └────────────────────┘   │
│  ┌────────────┐  ┌────────────────────────────────────┐   │
│  │ /speakers  │  │  /speakers/{name} [DELETE]         │   │
│  └────────────┘  └────────────────────────────────────┘   │
└─────────────────────────┬─────┬─────────────────────────────┘
                          │     │
          ┌───────────────┘     └───────────────┐
          ▼                                      ▼
┌──────────────────────┐              ┌──────────────────────┐
│   Services Layer     │              │   Storage Layer      │
│                      │              │                      │
│ ┌──────────────────┐ │              │ ┌────────────────┐ │
│ │ speaker_service  │ │◄─────────────┤►│   SQLite DB    │ │
│ │  - enroll        │ │              │ │  (metadata)    │ │
│ │  - verify        │ │              │ └────────────────┘ │
│ │  - delete        │ │              │                    │
│ └──────────────────┘ │              │ ┌────────────────┐ │
│                      │              │ │  .npy files    │ │
│ ┌──────────────────┐ │              │ │  (embeddings)  │ │
│ │ deepfake_service │ │              │ └────────────────┘ │
│ │  - detect        │ │              │                    │
│ └──────────────────┘ │              └──────────────────────┘
│                      │
│ ┌──────────────────┐ │
│ │  audio_utils     │ │
│ │  - preprocess    │ │
│ │  - temp files    │ │
│ └──────────────────┘ │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────────────┐
│      AI Models (cached)      │
│                              │
│ ┌──────────────────────────┐│
│ │  ECAPA-TDNN Encoder      ││
│ │  (Speaker Embeddings)    ││
│ └──────────────────────────┘│
│                              │
│ ┌──────────────────────────┐│
│ │  Audio Deepfake          ││
│ │  Detection Model         ││
│ └──────────────────────────┘│
└──────────────────────────────┘
```

## 📦 Component Breakdown

### Frontend Layer

#### **Templates**
- `index.html` - Main demo interface with 4 sections
- `kyc.html` - Professional KYC workflow interface

#### **Static Assets**
- `style.css` - Professional styling without external frameworks
- `app.js` - All JavaScript logic (fetch, DOM manipulation, state)

**Responsibilities:**
- User interface rendering
- Form handling and validation
- API communication via fetch
- Dynamic content updates
- Loading states and error handling

---

### Backend Layer

#### **FastAPI Application (main.py)**
Entry point and routing layer

**Endpoints:**
- `GET /` → Main UI
- `GET /kyc` → KYC UI
- `POST /enroll` → Enroll speaker
- `POST /verify` → Verify speaker
- `GET /speakers` → List speakers
- `DELETE /speakers/{name}` → Delete speaker
- `POST /detect-deepfake` → Detect deepfakes

**Responsibilities:**
- HTTP request/response handling
- Input validation
- Error handling with proper status codes
- Temporary file management
- Calling service layer

---

### Services Layer

#### **speaker_service.py**
Speaker verification business logic

**Functions:**
- `get_speaker_model()` → Load model (singleton)
- `extract_embedding(audio)` → Generate embedding
- `enroll_speaker(name, files)` → Register new speaker
- `verify_speaker(name, audio)` → Verify identity
- `cosine_similarity(v1, v2)` → Compute similarity
- `delete_speaker(name)` → Remove speaker

**Algorithm:**
1. Load audio → preprocess
2. Extract ECAPA-TDNN embedding (192-dim vector)
3. For enrollment: average multiple embeddings
4. For verification: compute cosine similarity
5. Compare against threshold (0.75)

#### **deepfake_service.py**
Audio deepfake detection logic

**Functions:**
- `get_deepfake_model()` → Load model (singleton)
- `detect_deepfake(audio)` → Classify audio
- `map_label(raw)` → Standardize label
- `generate_explanation(label, conf)` → Human-readable result

**Algorithm:**
1. Load audio → preprocess
2. Run audio classification pipeline
3. Map output to Real/Fake
4. Generate confidence-based explanation

#### **audio_utils.py**
Audio preprocessing utilities

**Functions:**
- `preprocess_audio(path)` → Convert, resample, normalize
- `save_temp_audio(bytes)` → Save uploaded file
- `cleanup_temp_file(path)` → Delete temp file

**Processing Pipeline:**
1. Load audio with torchaudio
2. Convert to mono (if stereo)
3. Resample to 16kHz
4. Normalize amplitude
5. Return tensor + sample rate

---

### Storage Layer

#### **db.py**
SQLite database operations

**Schema:**
```sql
CREATE TABLE speakers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    embedding_path TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

**Functions:**
- `init_db()` → Create table
- `insert_speaker(name, path)` → Add speaker
- `get_speaker(name)` → Retrieve speaker
- `list_speakers()` → All speakers
- `delete_speaker(name)` → Remove speaker

**Features:**
- Automatic initialization
- Parameterized queries (SQL injection protection)
- Row factory for dict results

#### **Embeddings Storage**
- Format: NumPy `.npy` files
- Location: `app/storage/embeddings/`
- Naming: `{speaker_name}.npy`
- Content: Float32 array (192 dimensions)

**Why .npy?**
- Efficient binary format
- Fast load/save with NumPy
- No serialization overhead
- Easy to transfer to cloud storage

---

### AI Models Layer

#### **ECAPA-TDNN (Speaker Verification)**
- Source: SpeechBrain
- Model ID: `speechbrain/spkrec-ecapa-voxceleb`
- Input: 16kHz audio waveform
- Output: 192-dimensional embedding
- Loading: Lazy (on first use)
- Caching: Singleton pattern

**Architecture:**
- Time Delay Neural Network (TDNN)
- Emphasized Channel Attention
- Propagation and Aggregation
- Trained on VoxCeleb dataset

#### **Audio Deepfake Detection**
- Source: HuggingFace
- Model ID: `mo-thecreator/audio-deepfake-detection`
- Input: 16kHz audio array
- Output: Classification scores
- Loading: Lazy (on first use)
- Caching: Singleton pattern

**Classification:**
- Real/Bonafide audio
- Fake/Spoofed audio
- Confidence scores

---

## 🔄 Data Flow

### Enrollment Flow
```
User uploads 3-5 audio files
        ↓
FastAPI receives multipart form
        ↓
Save to temp files
        ↓
For each audio:
  - Preprocess (mono, 16kHz, normalize)
  - Extract ECAPA-TDNN embedding
        ↓
Average all embeddings
        ↓
Save to embeddings/{name}.npy
        ↓
Insert metadata to SQLite
        ↓
Delete temp files
        ↓
Return success response
```

### Verification Flow
```
User uploads audio + selects speaker
        ↓
FastAPI receives multipart form
        ↓
Save to temp file
        ↓
Load enrolled embedding from .npy
        ↓
Preprocess test audio
        ↓
Extract ECAPA-TDNN embedding
        ↓
Compute cosine similarity
        ↓
Compare against threshold (0.75)
        ↓
Delete temp file
        ↓
Return similarity + verified boolean
```

### Deepfake Detection Flow
```
User uploads audio
        ↓
FastAPI receives file
        ↓
Save to temp file
        ↓
Preprocess audio (mono, 16kHz, normalize)
        ↓
Run deepfake detection model
        ↓
Map output to Real/Fake
        ↓
Generate explanation based on confidence
        ↓
Delete temp file
        ↓
Return label + confidence + explanation
```

### Voice KYC Flow
```
Step 1: Voice Enrollment
  - User provides name + 3-5 samples
  - Standard enrollment flow
  - Enable Step 2
        ↓
Step 2: Identity Verification
  - User uploads verification audio
  - Standard verification flow
  - Store result in frontend state
  - Enable Step 3
        ↓
Step 3: Deepfake Check
  - User uploads audio
  - Standard deepfake detection flow
  - Store result in frontend state
        ↓
Final Decision:
  IF verified == true AND deepfake == Real:
    → ACCESS GRANTED
  ELSE:
    → ACCESS DENIED
```

---

## 🔐 Security Architecture

### Input Validation
- File type checking (audio/* only)
- Name validation (prevent SQL injection)
- File size limits (implicit)
- Empty file checks

### Temporary Files
- Created in system temp directory
- Unique filenames with tempfile
- Cleaned up in finally blocks
- No file path traversal vulnerabilities

### Database Security
- Parameterized queries (no string interpolation)
- Unique constraints on speaker names
- Transaction safety

### Error Handling
- Generic error messages to users
- Detailed errors in server logs
- Proper HTTP status codes
- No sensitive data leakage

---

## ⚡ Performance Optimizations

### Model Loading
- **Singleton Pattern**: Models loaded once globally
- **Lazy Loading**: Only loaded when first needed
- **Memory Efficiency**: Shared across all requests

### Database
- **Connection Pooling**: SQLite handles automatically
- **Indexed Queries**: Name field indexed (UNIQUE)
- **Efficient Schema**: Minimal columns

### Embeddings
- **Binary Format**: Fast NumPy .npy format
- **On-Demand Loading**: Only load when needed
- **Small Size**: 192 floats ≈ 768 bytes per speaker

### Audio Processing
- **PyTorch Operations**: GPU acceleration if available
- **Batch Processing**: Can process multiple files
- **Efficient Resampling**: torchaudio transforms

### Frontend
- **No Heavy Frameworks**: Vanilla JS is fast
- **Minimal HTTP Requests**: Only when needed
- **Cached Dropdown**: Speaker list updated on change

---

## 📈 Scalability Considerations

### Current Scale
- **Users**: Single-user or small team
- **Speakers**: Hundreds to thousands
- **Storage**: Local filesystem
- **Database**: SQLite

### Scaling Path

#### To 10,000+ Speakers:
- Keep current architecture
- Consider database indexing optimization
- Monitor disk space for embeddings

#### To 100,000+ Speakers:
- Migrate embeddings to cloud storage (S3/Azure Blob)
- Use PostgreSQL instead of SQLite
- Add caching layer (Redis) for frequent lookups
- Consider vector database for similarity search

#### To Production:
- Add authentication and authorization
- Implement rate limiting
- Use production ASGI server (Gunicorn + Uvicorn)
- Add logging and monitoring
- Enable HTTPS
- Add health check endpoints
- Use environment variables for config

---

## 🧩 Extension Points

### Easy to Add:
- **New Models**: Swap model IDs in config.py
- **Custom Thresholds**: Per-speaker or adaptive thresholds
- **Audio Formats**: Already support most via torchaudio
- **Additional Endpoints**: Follow existing patterns in main.py
- **UI Customization**: Modify style.css and templates

### Moderate Effort:
- **Multi-language Support**: Add i18n to frontend
- **Batch Processing**: Process multiple verifications
- **Audio Quality Check**: Pre-validate audio before processing
- **User Management**: Add user auth system
- **Cloud Storage**: Migrate from .npy to S3/Azure

### Significant Changes:
- **Real-time Streaming**: WebRTC integration
- **Mobile App**: Need separate native apps or React Native
- **Multi-modal**: Combine voice with face/fingerprint
- **Distributed System**: Microservices architecture

---

## 🎯 Design Principles

1. **Separation of Concerns**: Routes → Services → Storage
2. **Single Responsibility**: Each module does one thing well
3. **DRY**: Reusable functions (audio_utils, model loaders)
4. **Fail-Safe**: Comprehensive error handling
5. **Performance**: Lazy loading, caching, efficient operations
6. **Maintainability**: Clear names, minimal comments, logical structure
7. **Extensibility**: Easy to add features without major refactoring

---

## 📊 Technology Choices Rationale

| Technology | Reason |
|------------|--------|
| **FastAPI** | Modern, fast, auto-documentation, async support |
| **SQLite** | Zero-config, reliable, perfect for metadata |
| **NumPy .npy** | Efficient binary format for embeddings |
| **SpeechBrain** | State-of-the-art pretrained models |
| **HuggingFace** | Easy model access and usage |
| **PyTorch** | Industry standard, GPU support |
| **Vanilla JS** | No build step, fast, educational |
| **Jinja2** | Simple templating, FastAPI integration |
| **uv** | Fast, modern Python package manager |

---

This architecture provides a solid foundation for production use while remaining simple enough to understand and extend.
