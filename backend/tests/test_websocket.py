import pytest
from starlette.testclient import TestClient
from starlette.websockets import WebSocketDisconnect
from backend.app.main import app

client = TestClient(app)

def test_websocket_stream():
    with client.websocket_connect("/ws/v1/stream") as websocket:
        init_msg = websocket.receive_json()
        assert init_msg.get("type") == "session_started"
        # Gửi dữ liệu bytes mẫu (không phải ảnh hợp lệ)
        websocket.send_bytes(b"dummy_image_data")
        data = websocket.receive_json()
        assert "type" in data
        assert data["type"] == "error"

