from fastapi import WebSocket
from typing import Dict
from backend.app.core.pipeline_runner import PipelineSession
from modules.driver_monitor import DriverPipelineSession
import logging

logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[WebSocket, PipelineSession] = {}
        self.active_driver_connections: Dict[WebSocket, DriverPipelineSession] = {}
        self.client_metadata: Dict[WebSocket, dict] = {}

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        # Initialize a new pipeline session per connection
        self.active_connections[websocket] = PipelineSession()
        self.client_metadata[websocket] = {"vehicle_speed": None}
        logger.info(f"Client connected. Active connections: {len(self.active_connections)}")

    async def connect_driver(self, websocket: WebSocket):
        await websocket.accept()
        self.active_driver_connections[websocket] = DriverPipelineSession()
        logger.info(f"Driver Client connected. Active driver connections: {len(self.active_driver_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            del self.active_connections[websocket]
        if websocket in self.active_driver_connections:
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

manager = ConnectionManager()
