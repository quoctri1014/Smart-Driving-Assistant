import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_websocket_stream():
    with client.websocket_connect("/ws/v1/stream") as websocket:
        # Gửi dữ liệu base64 mẫu
        websocket.send_bytes(b"dummy_image_data")
        data = websocket.receive_json()
        assert "type" in data
        assert data["type"] == "error" # dummy data should return error
