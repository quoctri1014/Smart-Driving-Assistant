from fastapi import WebSocket
from typing import Dict
from backend.app.core.pipeline_runner import PipelineSession
from modules.driver_monitor import DriverPipelineSession
import logging
import secrets
import time
import asyncio

logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[WebSocket, PipelineSession] = {}
        self.active_driver_connections: Dict[WebSocket, DriverPipelineSession] = {}
        self.client_metadata: Dict[WebSocket, dict] = {}
        self.driver_timers = {}  # Opaque resume token -> timer, disconnect time, active

    async def connect(self, websocket: WebSocket):
        # Initialize a new pipeline session per connection
        self.active_connections[websocket] = await asyncio.to_thread(PipelineSession)
        self.client_metadata[websocket] = {"vehicle_speed": None}
        logger.info(f"Client connected. Active connections: {len(self.active_connections)}")

    async def connect_driver(self, websocket: WebSocket, owner=None):
        now = time.monotonic()
        self.driver_timers = {key: value for key, value in self.driver_timers.items()
                              if value[2] or now - value[1] < 86400}
        token = websocket.query_params.get("timer_token")
        previous = self.driver_timers.get(token)
        session = await asyncio.to_thread(DriverPipelineSession)
        if previous is not None and not previous[2] and previous[3] == owner:
            session.driving_timer = previous[0]
        else:
            token = secrets.token_urlsafe(32)
        session.timer_token = token
        session.timer_owner = owner
        self.driver_timers[token] = (session.driving_timer, now, True, owner)
        self.active_driver_connections[websocket] = session
        await websocket.send_json({"type": "driver_session", "timer_token": token})
        logger.info(f"Driver Client connected. Active driver connections: {len(self.active_driver_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            del self.active_connections[websocket]
        if websocket in self.active_driver_connections:
            session = self.active_driver_connections[websocket]
            self.driver_timers[session.timer_token] = (session.driving_timer, time.monotonic(), False, session.timer_owner)
            session.close()
            del self.active_driver_connections[websocket]
        if websocket in self.client_metadata:
            del self.client_metadata[websocket]
        logger.info(f"Client disconnected. Active connections: {len(self.active_connections)}, Driver: {len(self.active_driver_connections)}")

    def get_session(self, websocket: WebSocket) -> PipelineSession:
        return self.active_connections.get(websocket)

    def get_driver_session(self, websocket: WebSocket) -> DriverPipelineSession:
        return self.active_driver_connections.get(websocket)
        
    def update_metadata(self, websocket: WebSocket, metadata: dict):
        if websocket in self.client_metadata:
            self.client_metadata[websocket].update(metadata)
            
    def get_metadata(self, websocket: WebSocket) -> dict:
        return self.client_metadata.get(websocket, {})

    async def broadcast_alert(self, message: dict):
        """Broadcast alert or notification to all active WebSocket clients"""
        all_sockets = list(set(list(self.active_connections.keys()) + list(self.active_driver_connections.keys())))
        for ws in all_sockets:
            try:
                await ws.send_json(message)
            except Exception:
                pass

manager = ConnectionManager()
