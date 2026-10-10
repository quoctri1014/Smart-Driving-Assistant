import asyncio
import json
import time
from pathlib import Path
from datetime import datetime
import cv2
import numpy as np
from fastapi import APIRouter, WebSocket, HTTPException
from sqlalchemy import select
from backend.app.auth.dependencies import resolve_user
from backend.app.websocket.connection_manager import manager
from backend.app.config import settings
from backend.app.database.session import async_session_maker
from backend.app.crud.session_crud import create_session
from backend.app.crud.violation_crud import create_violation
from backend.app.models_db.driving_session import DrivingSession
from backend.app.storage.image_storage import image_storage
import logging

router = APIRouter()
logger = logging.getLogger(__name__)
_slots = asyncio.Semaphore(settings.MAX_INFLIGHT_INFERENCE)
_connections = {}  # Reservations include model initialization.

async def stream(websocket, cabin=False):
    await websocket.accept()
    token = websocket.query_params.get("token")
    try:
        async with async_session_maker() as db:
            user = await resolve_user(token, db)
    except HTTPException:
        logger.error("WebSocket rejected: User resolution failed (HTTPException)")
        await websocket.close(code=1008, reason="Unauthorized")
        return
    except Exception as e:
        logger.exception(f"Unexpected error resolving user: {e}")
        await websocket.close(code=1011, reason="Internal Server Error")
        return

    # Prune disconnected or stale websockets from _connections
    stale_ws = [ws for ws in list(_connections.keys()) if getattr(ws, "client_state", None) and ws.client_state.name == "DISCONNECTED"]
    for ws in stale_ws:
        _connections.pop(ws, None)

    if len(_connections) >= settings.MAX_STREAM_CONNECTIONS or sum(v == user.id for v in _connections.values()) >= settings.MAX_STREAMS_PER_USER:
        logger.warning(f"Connection limit exceeded for user {user.id}")
        await websocket.close(code=1013, reason="Too many connections")
        return
    _connections[websocket] = user.id
    session_id = None
    last_auth = time.monotonic()
    last_frame_time = 0.0
    last_saved = {}
    try:
        if cabin:
            await manager.connect_driver(websocket, owner=(user.organization_id, user.id))
            pipeline = manager.get_driver_session(websocket)
        else:
            await manager.connect(websocket)
            pipeline = manager.get_session(websocket)
            directory = Path("output") / str(user.organization_id) / str(user.id)
            directory.mkdir(parents=True, exist_ok=True)
            if hasattr(pipeline, "violation_manager") and pipeline.violation_manager and hasattr(pipeline.violation_manager, "export_path"):
                try:
                    pipeline.violation_manager.export_path = str(directory / Path(pipeline.violation_manager.export_path).name)
                except Exception as exp_err:
                    logger.warning(f"Could not set violation_manager export path: {exp_err}")
        async with async_session_maker() as db:
            session_id = (await create_session(db, user.id, user.organization_id)).id
        await websocket.send_json({"type": "session_started", "session_id": session_id})

        while True:
            message = await websocket.receive()
            if message.get("type") == "websocket.disconnect":
                break
            if time.monotonic() - last_auth >= 30:
                async with async_session_maker() as db:
                    user = await resolve_user(token, db)
                last_auth = time.monotonic()
            if message.get("text") is not None:
                try:
                    data = json.loads(message["text"])
                    if not isinstance(data, dict):
                        raise ValueError()
                    if data.get("type") == "ping":
                        await websocket.send_json({"type": "pong"})
                    elif not cabin and data.get("type") == "metadata":
                        manager.update_metadata(websocket, {key: data[key] for key in ("vehicle_speed", "estimated_distance_m") if key in data})
                    elif cabin and data.get("type") in ("break_started", "break_ended"):
                        if data["type"] == "break_started":
                            pipeline.notify_break_started()
                        else:
                            pipeline.notify_break_ended()
                        await websocket.send_json({"type": "break_status", "data": pipeline.driving_timer.update()})
                except (ValueError, TypeError):
                    await websocket.send_json({"type": "error", "code": "INVALID_JSON"})
                continue
            raw = message.get("bytes")
            if not raw or len(raw) > settings.MAX_FRAME_SIZE_MB * 1024 * 1024:
                await websocket.send_json({"type": "error", "code": "INVALID_FRAME_SIZE"})
                continue

            # Token Bucket / Frame rate limiter: Drop frames exceeding 35 FPS per client connection
            now_mono = time.monotonic()
            if (now_mono - last_frame_time) < (1.0 / 35.0):
                continue
            last_frame_time = now_mono

            frame = cv2.imdecode(np.frombuffer(raw, np.uint8), cv2.IMREAD_COLOR)
            if frame is None:
                await websocket.send_json({"type": "error", "code": "DECODE_FAILED"})
                continue
            try:
                await asyncio.wait_for(_slots.acquire(), timeout=0.1)
            except asyncio.TimeoutError:
                await websocket.send_json({"type": "error", "code": "BUSY", "message": "Retry with a newer frame"})
                continue
            try:
                if cabin:
                    result = await asyncio.to_thread(pipeline.process_driver_frame, frame, session_id=session_id, driver_id=user.id)
                    payload = result
                else:
                    metadata = manager.get_metadata(websocket)
                    result = await asyncio.to_thread(
                        pipeline.process_frame, 
                        frame, 
                        metadata.get("vehicle_speed"), 
                        metadata.get("estimated_distance_m"),
                        session_id=session_id,
                        driver_id=user.id
                    )
                    payload = result.model_dump(by_alias=True)
            except Exception:
                logger.exception("Frame inference failed")
                await websocket.send_json({"type": "error", "code": "PIPELINE_ERROR"})
                continue
            finally:
                _slots.release()
            await websocket.send_json({"type": "driver_monitor_result" if cabin else "detection_result", "data": payload})
            
            # Ghi nhận vi phạm theo phán quyết của DecisionEngine
            decision = getattr(pipeline, "last_decision", None)
            if decision and decision.should_record_violation and decision.violation_type:
                try:
                    image = await asyncio.to_thread(image_storage.save_violation_image, frame, decision.violation_type)
                    async with async_session_maker() as db:
                        await create_violation(
                            db, 
                            event_type=decision.violation_type, 
                            severity=decision.violation_severity or "warning", 
                            image_path=image, 
                            session_id=session_id,
                            organization_id=user.organization_id, 
                            driver_id=user.id
                        )
                except Exception:
                    logger.exception("Could not persist authenticated violation event from DecisionEngine")
    except HTTPException:
        await websocket.close(code=1008)
    except Exception:
        logger.exception("Stream disconnected")
    finally:
        manager.disconnect(websocket)
        _connections.pop(websocket, None)
        if session_id is not None:
            try:
                async with async_session_maker() as db:
                    item = await db.get(DrivingSession, session_id)
                    item.end_time = datetime.utcnow()
                    item.total_minutes = (item.end_time - item.start_time).total_seconds() / 60
                    await db.commit()
            except Exception:
                logger.exception("Could not finalize driving session")

@router.websocket("/ws/v1/stream")
@router.websocket("/ws/stream")
@router.websocket("/ws/driving-stream")
async def websocket_stream(websocket: WebSocket):
    await stream(websocket)

@router.websocket("/ws/v1/driver-stream")
@router.websocket("/ws/driver-stream")
@router.websocket("/ws/driver-monitor")
async def websocket_driver_stream(websocket: WebSocket):
    await stream(websocket, cabin=True)

