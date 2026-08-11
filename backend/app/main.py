import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "ai_engine"))

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from backend.app.websocket.stream_handler import router as stream_router
from backend.app.core.pipeline_runner import SharedAIModels
from backend.app.config import settings

from backend.app.api.auth_routes import router as auth_router
from backend.app.api.violation_routes import router as violation_router
from backend.app.api.session_routes import router as session_router

logging.basicConfig(level=getattr(logging, settings.LOG_LEVEL))
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Application startup: Loading AI models...")
    # Initialize shared models before accepting requests
    SharedAIModels()
    yield
    logger.info("Application shutdown.")

app = FastAPI(title="Smart Driving Assistant API", lifespan=lifespan)

# Add CORS middleware for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount storage for images
import os
os.makedirs("./storage", exist_ok=True)
app.mount("/storage", StaticFiles(directory="./storage"), name="storage")

app.include_router(stream_router)
app.include_router(auth_router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(violation_router, prefix="/api/v1/violations", tags=["violations"])
app.include_router(session_router, prefix="/api/v1/sessions", tags=["sessions"])

@app.get("/health")
def health_check():
    return {"status": "ok"}
