import sys
import os
import uuid
import time
from pathlib import Path

# Add ai_engine to sys.path - reloaded for multi-vehicle ALPR vision
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "ai_engine"))

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from backend.app.websocket.stream_handler import router as stream_router
from backend.app.core.pipeline_runner import SharedAIModels
from backend.app.config import settings
from backend.app.database.session import AsyncSessionLocal

from backend.app.api.auth_routes import router as auth_router
from backend.app.api.violation_routes import router as violation_router
from backend.app.api.session_routes import router as session_router
from backend.app.api.fleet_routes import router as fleet_router
from backend.app.api.organization_routes import router as org_router
from backend.app.api.system_routes import router as system_router
from backend.app.api.journey_routes import router as journey_router
from backend.app.api.coaching_routes import router as coaching_router
from backend.app.api.report_routes import router as report_router
from backend.app.api.license_plate_routes import router as license_plate_router
from backend.app.api.traffic_sign_routes import router as traffic_sign_router
from backend.app.api.helmet_routes import router as helmet_router
from backend.app.api.traffic_density_routes import router as traffic_density_router

from backend.app.database.seed_rbac import initialize_database

logging.basicConfig(level=getattr(logging, settings.LOG_LEVEL))
logger = logging.getLogger("trafficguard.api")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Application startup: Checking database connection...")
    try:
        from backend.app.database.session import engine
        from backend.app.database.base import Base
        import backend.app.models_db  # Ensure all models are loaded
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        await initialize_database()
    except Exception as e:
        logger.error(f"Error initializing database & RBAC: {e}")

    logger.info("Application startup: Loading AI models...")
    # Initialize shared models before accepting requests
    SharedAIModels()
    try:
        from backend.app.api.traffic_sign_routes import get_sign_onnx_session, get_qcvn_classifier, get_ocr_reader
        from backend.app.api.helmet_routes import get_helmet_session
        from backend.app.api.traffic_density_routes import get_vehicle_model
        import numpy as np

        from backend.app.services.sign_template_matcher import SignTemplateMatcher

        get_sign_onnx_session()
        get_qcvn_classifier()
        SignTemplateMatcher.get_instance()
        v_model = get_vehicle_model()
        if v_model:
            v_model(np.zeros((64, 64, 3), dtype=np.uint8), conf=0.35, imgsz=384, verbose=False)
        shared_m = SharedAIModels()
        if shared_m.plate_reader and shared_m.plate_reader.detector:
            shared_m.plate_reader.detector(np.zeros((64, 64, 3), dtype=np.uint8), conf=0.35, imgsz=384, verbose=False)
        reader = get_ocr_reader()
        if reader:
            dummy = np.zeros((32, 32), dtype=np.uint8)
            reader.readtext(dummy, allowlist='0123456789', detail=0)
        logger.info("All AI models, OCR, and QCVN template matcher pre-warmed successfully.")
    except Exception as e:
        logger.warning(f"Model pre-warm warning: {e}")
    yield
    logger.info("Application shutdown.")

app = FastAPI(title="TRAFFICGUARD Enterprise API", lifespan=lifespan)

# Correlation ID and Request Timing Middleware
@app.middleware("http")
async def correlation_and_timing_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    start_time = time.time()
    
    response: Response = await call_next(request)
    
    duration = round((time.time() - start_time) * 1000, 2)
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Response-Time-Ms"] = str(duration)
    
    # Structured log line without logging credentials or auth tokens
    logger.info(
        f"[{request_id}] {request.method} {request.url.path} -> {response.status_code} ({duration}ms)"
    )
    return response

from backend.app.middleware.rate_limiter import TokenBucketRateLimiter

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID", "X-Response-Time-Ms"]
)

# Token Bucket Rate Limiting (Section 6.3)
app.add_middleware(TokenBucketRateLimiter, rate_per_minute=60)

# Ensure storage directory exists for evidence
os.makedirs(os.path.abspath(os.getenv("STORAGE_PATH", "./storage")), exist_ok=True)

app.include_router(stream_router)

# Support /api/v1 routes
app.include_router(auth_router, prefix="/api/v1/auth", tags=["auth-v1"])
app.include_router(violation_router, prefix="/api/v1/violations", tags=["violations-v1"])
app.include_router(session_router, prefix="/api/v1/sessions", tags=["sessions-v1"])
app.include_router(fleet_router, prefix="/api/v1/fleet", tags=["fleet-v1"])
app.include_router(org_router, prefix="/api/v1", tags=["organization-v1"])
app.include_router(system_router, prefix="/api/v1", tags=["system-v1"])
app.include_router(journey_router, prefix="/api/v1/journeys", tags=["journeys-v1"])
app.include_router(coaching_router, prefix="/api/v1/coaching", tags=["coaching-v1"])
app.include_router(report_router, prefix="/api/v1/reports", tags=["reports-v1"])
app.include_router(license_plate_router, prefix="/api/v1", tags=["license-plate-v1"])
app.include_router(traffic_sign_router, prefix="/api/v1", tags=["traffic-signs-v1"])
app.include_router(helmet_router, prefix="/api/v1", tags=["helmets-v1"])
app.include_router(traffic_density_router, prefix="/api/v1", tags=["traffic-density-v1"])

# Support /api routes for backwards compatibility
app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
app.include_router(violation_router, prefix="/api/violations", tags=["violations"])
app.include_router(session_router, prefix="/api/sessions", tags=["sessions"])
app.include_router(fleet_router, prefix="/api/fleet", tags=["fleet"])
app.include_router(org_router, prefix="/api", tags=["organization"])
app.include_router(system_router, prefix="/api", tags=["system"])
app.include_router(journey_router, prefix="/api/journeys", tags=["journeys"])
app.include_router(coaching_router, prefix="/api/coaching", tags=["coaching"])
app.include_router(report_router, prefix="/api/reports", tags=["reports"])
app.include_router(license_plate_router, prefix="/api", tags=["license-plate"])
app.include_router(traffic_sign_router, prefix="/api", tags=["traffic-signs"])
app.include_router(helmet_router, prefix="/api", tags=["helmets"])
app.include_router(traffic_density_router, prefix="/api", tags=["traffic-density"])

@app.get("/health")
def health_check():
    """Liveness probe: Trả về trạng thái tiến trình API đang hoạt động"""
    return {"status": "healthy", "service": "trafficguard-api", "timestamp": time.time()}

@app.get("/ready")
async def readiness_check():
    """Readiness probe: Kiểm tra khả năng kết nối cơ sở dữ liệu"""
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
        return {"status": "ready", "database": "connected"}
    except Exception as e:
        logger.error(f"Readiness probe failed: {e}")
        return Response(
            content='{"status": "unhealthy", "database": "disconnected"}',
            status_code=503,
            media_type="application/json"
        )
