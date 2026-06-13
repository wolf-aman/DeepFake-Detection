from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.config import settings
from app.core.exceptions import AppError
from app.services.audio import cleanup_temp_file, save_upload_to_temp
from app.services.deepfake import HuggingFaceDeepfakeDetector
from app.services.speaker import SpeakerVerificationService, SpeechBrainECAPAEmbedder
from app.storage.db import SpeakerRepository

logger = logging.getLogger(__name__)

repository = SpeakerRepository(settings.database_path)
speaker_service = SpeakerVerificationService(repository, SpeechBrainECAPAEmbedder(settings), settings)
deepfake_detector = HuggingFaceDeepfakeDetector(settings)
templates = Jinja2Templates(directory=str(settings.templates_dir))


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings.create_directories()
    repository.init_schema()
    yield


app = FastAPI(title="Speaker Verification & Deepfake Detection", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=str(settings.static_dir)), name="static")


@app.exception_handler(AppError)
async def handle_app_error(_: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})


@app.exception_handler(Exception)
async def handle_unexpected_error(_: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unexpected API error", exc_info=exc)
    return JSONResponse(status_code=500, content={"detail": "Unexpected server error. Check backend logs."})


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")


@app.get("/kyc", response_class=HTMLResponse)
async def kyc(request: Request):
    return templates.TemplateResponse(request=request, name="kyc.html")


@app.post("/enroll")
async def enroll_endpoint(name: str = Form(...), files: list[UploadFile] = File(...)):
    temp_files: list[Path] = []
    try:
        for uploaded_file in files:
            temp_files.append(await save_upload_to_temp(uploaded_file, settings))
        return speaker_service.enroll(name, temp_files)
    finally:
        for temp_file in temp_files:
            cleanup_temp_file(temp_file)


@app.get("/speakers")
async def get_speakers():
    return speaker_service.list_speakers()


@app.delete("/speakers/{name}")
async def delete_speaker_endpoint(name: str):
    return speaker_service.delete(name)


@app.post("/verify")
async def verify_endpoint(name: str = Form(...), file: UploadFile = File(...)):
    temp_file: Path | None = None
    try:
        temp_file = await save_upload_to_temp(file, settings)
        return speaker_service.verify(name, temp_file)
    finally:
        cleanup_temp_file(temp_file)


@app.post("/detect-deepfake")
async def detect_deepfake_endpoint(file: UploadFile = File(...)):
    temp_file: Path | None = None
    try:
        temp_file = await save_upload_to_temp(file, settings)
        return deepfake_detector.detect(temp_file)
    finally:
        cleanup_temp_file(temp_file)
