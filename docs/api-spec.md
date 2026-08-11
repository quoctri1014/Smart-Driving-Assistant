# Smart Driving Assistant API Specification

## 1. HTTP Endpoints
### GET /health
Returns server status.
**Response**: `{"status": "ok"}`

## 2. WebSocket Endpoint
**URL**: `/ws/v1/stream`

### 2.1 Client to Server Messages

**a) Metadata (JSON Text)**
Used to update vehicle state.
```json
{
  "type": "metadata",
  "vehicle_speed": 42.5
}
```
*Note*: `vehicle_speed` is in km/h.

**b) Ping (JSON Text)**
```json
{
  "type": "ping"
}
```

**c) Frame (Binary)**
Send a single video frame encoded as JPEG or WebP bytes. Maximum size: 5MB.

### 2.2 Server to Client Messages

**a) Detection Result (JSON Text)**
```json
{
  "type": "detection_result",
  "data": {
    "frame_id": 1,
    "timestamp": 1690000000.123,
    "vehicles": [
      {
        "id": 1,
        "bbox": {"x1": 0.0, "y1": 0.0, "x2": 100.0, "y2": 100.0},
        "class": "car",
        "zone": "Zone 1"
      }
    ],
    "plates": [],
    "helmet_violations": [],
    "collision_warning": null,
    "speed_advice": {
      "current_speed": 42.5,
      "recommended_speed": 40.0,
      "reason": "Mật độ giao thông cao"
    },
    "traffic_signs": [],
    "processing_time_ms": 15.4
  }
}
```

**b) Error (JSON Text)**
```json
{
  "type": "error",
  "code": "FRAME_TOO_LARGE",
  "message": "Frame exceeds size limit"
}
```

## 3. REST API Endpoints (Phase 3)

### 3.1 Authentication
**POST /api/v1/auth/register**
- Body: `{"email": "...", "password": "...", "full_name": "..."}`
- Returns: `{"access_token": "...", "token_type": "bearer"}`

**POST /api/v1/auth/login**
- Body (Form Data): `username=...&password=...`
- Returns: `{"access_token": "...", "token_type": "bearer"}`

### 3.2 Violations (Requires Bearer Token)
**GET /api/v1/violations**
- Headers: `Authorization: Bearer <token>`
- Query Params: `skip=0`, `limit=50`, `violation_type=drowsy`
- Returns: List of violations for the logged-in driver.

### 3.3 Sessions (Requires Bearer Token)
**GET /api/v1/sessions**
- Headers: `Authorization: Bearer <token>`
- Query Params: `skip=0`, `limit=50`
- Returns: List of driving sessions for the logged-in driver.

> **Note**: REST endpoints (auth, violations, sessions) require a running PostgreSQL instance.
> Configure `DATABASE_URL` in `.env` before using them. See `docker-compose.yml` for easy setup.

## 4. Driver WebSocket Endpoint
**URL**: `/ws/v1/driver-stream`

> **Correct endpoint is `/ws/v1/driver-stream`** — not `/ws/v1/stream_driver`.

### 4.1 Client to Server Messages

**a) Ping (JSON Text)**
```json
{
  "type": "ping"
}
```

**b) Frame (Binary)**
Send a JPEG-encoded binary frame of the driver's face. Maximum size: 5MB.

### 4.2 Server to Client Messages

**a) Driver Monitor Result (JSON Text)**
```json
{
  "type": "driver_monitor_result",
  "data": {
    "drowsiness": {
      "is_drowsy": false,
      "alert_level": "normal"
    },
    "seatbelt": {
      "seatbelt_on": true
    }
  }
}
```
