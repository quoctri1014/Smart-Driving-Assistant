import json
import cv2
import numpy as np
import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from backend.app.websocket.connection_manager import manager
from backend.app.config import settings
from backend.app.storage.image_storage import image_storage
from backend.app.database.session import async_session_maker
from backend.app.crud.violation_crud import create_violation
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.websocket("/ws/v1/stream")
async def websocket_stream(websocket: WebSocket):
    await manager.connect(websocket)
    session = manager.get_session(websocket)
    
    try:
        while True:
            # Handle both text (metadata) and bytes (frame)
            message = await websocket.receive()
            
            if "text" in message:
                try:
                    data = json.loads(message["text"])
                    if data.get("type") == "metadata":
                        manager.update_metadata(websocket, data)
                    elif data.get("type") == "ping":
                        await websocket.send_json({"type": "pong"})
                except json.JSONDecodeError:
                    await websocket.send_json({"type": "error", "code": "INVALID_JSON", "message": "Invalid JSON format"})
                    
            elif "bytes" in message:
                frame_bytes = message["bytes"]
                
                # Check size
                if len(frame_bytes) > settings.MAX_FRAME_SIZE_MB * 1024 * 1024:
                    await websocket.send_json({"type": "error", "code": "FRAME_TOO_LARGE", "message": "Frame exceeds size limit"})
                    continue
                    
                if not frame_bytes:
                    await websocket.send_json({"type": "error", "code": "EMPTY_FRAME", "message": "Empty frame received"})
                    continue

                # Decode
                np_arr = np.frombuffer(frame_bytes, np.uint8)
                frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
                
                if frame is None:
                    await websocket.send_json({"type": "error", "code": "DECODE_FAILED", "message": "Failed to decode image"})
                    continue
                    
                metadata = manager.get_metadata(websocket)
                vehicle_speed = metadata.get("vehicle_speed")
                
                try:
                    # Run inference in a thread pool so it doesn't block asyncio loop
                    result = await asyncio.to_thread(
                        session.process_frame,
                        frame,
                        vehicle_speed
                    )
                    
                    # Async task để lưu DB (ví dụ: cảnh báo va chạm, mũ bảo hiểm)
                    if result.collision_warning:
                        image_path = await asyncio.to_thread(image_storage.save_violation_image, frame, "collision")
                        async def save_col():
                            async with async_session_maker() as db:
                                await create_violation(db, violation_type="collision", severity=result.collision_warning.level, image_path=image_path)
                        asyncio.create_task(save_col())
                        
                    if result.helmet_violations:
                        image_path = await asyncio.to_thread(image_storage.save_violation_image, frame, "no_helmet")
                        async def save_helm():
                            async with async_session_maker() as db:
                                await create_violation(db, violation_type="no_helmet", severity="critical", image_path=image_path)
                        asyncio.create_task(save_helm())
                        
                    await websocket.send_json({
                        "type": "detection_result",
                        "data": result.model_dump(by_alias=True)
                    })
                except Exception as e:
                    logger.error(f"Inference error: {e}", exc_info=True)
                    await websocket.send_json({"type": "error", "code": "PIPELINE_ERROR", "message": "Error processing frame"})
                    
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"Unexpected websocket error: {e}", exc_info=True)
        manager.disconnect(websocket)

@router.websocket("/ws/v1/driver-stream")
async def websocket_driver_stream(websocket: WebSocket):
    await manager.connect_driver(websocket)
    session = manager.get_driver_session(websocket)
    
    try:
        while True:
            message = await websocket.receive()
            
            if "text" in message:
                try:
                    data = json.loads(message["text"])
                    if data.get("type") == "ping":
                        await websocket.send_json({"type": "pong"})
                except json.JSONDecodeError:
                    await websocket.send_json({"type": "error", "code": "INVALID_JSON", "message": "Invalid JSON format"})
                    
            elif "bytes" in message:
                frame_bytes = message["bytes"]
                
                if len(frame_bytes) > settings.MAX_FRAME_SIZE_MB * 1024 * 1024:
                    await websocket.send_json({"type": "error", "code": "FRAME_TOO_LARGE", "message": "Frame exceeds size limit"})
                    continue
                    
                if not frame_bytes:
                    await websocket.send_json({"type": "error", "code": "EMPTY_FRAME", "message": "Empty frame received"})
                    continue

                np_arr = np.frombuffer(frame_bytes, np.uint8)
                frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
                
                if frame is None:
                    await websocket.send_json({"type": "error", "code": "DECODE_FAILED", "message": "Failed to decode image"})
                    continue
                    
                try:
                    result = await asyncio.to_thread(
                        session.process_driver_frame,
                        frame
                    )
                    
                    # Async task để lưu DB
                    if result["drowsiness"]["alert_level"] != "normal":
                        image_path = await asyncio.to_thread(image_storage.save_violation_image, frame, "drowsy")
                        async def save_drowsy():
                            async with async_session_maker() as db:
                                await create_violation(db, violation_type="drowsy", severity=result["drowsiness"]["alert_level"], image_path=image_path)
                        asyncio.create_task(save_drowsy())
                        
                    if not result["seatbelt"]["seatbelt_on"]:
                        image_path = await asyncio.to_thread(image_storage.save_violation_image, frame, "no_seatbelt")
                        async def save_seatbelt():
                            async with async_session_maker() as db:
                                await create_violation(db, violation_type="no_seatbelt", severity="critical", image_path=image_path)
                        asyncio.create_task(save_seatbelt())
                        
                    await websocket.send_json({
                        "type": "driver_monitor_result",
                        "data": result
                    })
                except Exception as e:
                    logger.error(f"Driver inference error: {e}", exc_info=True)
                    await websocket.send_json({"type": "error", "code": "PIPELINE_ERROR", "message": "Error processing driver frame"})
                    
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"Unexpected driver websocket error: {e}", exc_info=True)
        manager.disconnect(websocket)
