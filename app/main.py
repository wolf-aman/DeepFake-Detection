from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.requests import Request
from typing import List
from pathlib import Path
import app.config as config
from app.services.audio_utils import save_temp_audio, cleanup_temp_file
from app.services.speaker_service import enroll_speaker, verify_speaker, delete_speaker, get_all_speakers
from app.services.deepfake_service import detect_deepfake

app = FastAPI(title="Speaker Verification & Deepfake Detection")

templates = Jinja2Templates(directory=str(config.BASE_DIR / "templates"))
app.mount("/static", StaticFiles(directory=str(config.BASE_DIR / "static")), name="static")


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Main demo interface."""
    return templates.TemplateResponse(request=request, name="index.html")


@app.get("/kyc", response_class=HTMLResponse)
async def kyc(request: Request):
    """Voice KYC workflow interface."""
    return templates.TemplateResponse(request=request, name="kyc.html")


@app.post("/enroll")
async def enroll_endpoint(name: str = Form(...), files: List[UploadFile] = File(...)):
    """Enroll a new speaker with one or more audio samples."""
    if not files:
        raise HTTPException(status_code=400, detail="At least one audio file is required")
    
    temp_files = []
    try:
        for uploaded_file in files:
            file_bytes = await uploaded_file.read()
            temp_path = save_temp_audio(file_bytes, suffix=Path(uploaded_file.filename).suffix)
            temp_files.append(temp_path)
        
        result = enroll_speaker(name, temp_files)
        return JSONResponse(content=result)
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Enrollment failed: {str(e)}")
    finally:
        for temp_file in temp_files:
            cleanup_temp_file(temp_file)


@app.post("/verify")
async def verify_endpoint(name: str = Form(...), file: UploadFile = File(...)):
    """Verify if the uploaded audio matches the enrolled speaker."""
    temp_file = None
    try:
        file_bytes = await file.read()
        temp_file = save_temp_audio(file_bytes, suffix=Path(file.filename).suffix)
        
        result = verify_speaker(name, temp_file)
        return JSONResponse(content=result)
    
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Verification failed: {str(e)}")
    finally:
        if temp_file:
            cleanup_temp_file(temp_file)


@app.get("/speakers")
async def get_speakers():
    """List all enrolled speakers."""
    try:
        speakers = get_all_speakers()
        return JSONResponse(content=speakers)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list speakers: {str(e)}")


@app.delete("/speakers/{name}")
async def delete_speaker_endpoint(name: str):
    """Delete an enrolled speaker and their embedding."""
    try:
        result = delete_speaker(name)
        return JSONResponse(content=result)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete speaker: {str(e)}")


@app.post("/detect-deepfake")
async def detect_deepfake_endpoint(file: UploadFile = File(...)):
    """Detect if the uploaded audio is real or deepfake/synthesized."""
    temp_file = None
    try:
        file_bytes = await file.read()
        temp_file = save_temp_audio(file_bytes, suffix=Path(file.filename).suffix)
        
        result = detect_deepfake(temp_file)
        return JSONResponse(content=result)
    
    except Exception as e:
        import traceback
        print("ERROR in deepfake detection endpoint:")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Deepfake detection failed: {str(e)}")
    finally:
        if temp_file:
            cleanup_temp_file(temp_file)
