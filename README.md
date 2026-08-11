# Smart Driving Assistant System

Hệ thống ADAS (Advanced Driver Assistance System) thời gian thực, gồm AI nhận diện biển báo, cảnh báo va chạm, giám sát tài xế và giải trợ lý lái xe thông minh.

## Architecture

```
backend/         FastAPI + WebSocket AI pipeline (uvicorn)
web-app/         Next.js dashboard + Simulator + Live Monitor
mobile-app/      React Native (Expo) mobile driving mode
ai_engine/       YOLOv8 + EasyOCR + MediaPipe AI modules
docs/            API specification and demo checklist
docker-compose.yml  PostgreSQL database setup
```

## Prerequisites

| Requirement | Version |
|---|---|
| Python venv | `venv/` inside project root |
| Node.js | >= 18 |
| PostgreSQL | Required for REST (Auth/Sessions/Violations) — optional for WebSocket-only demo |
| Expo CLI | Installed via `mobile-app/` |

> **WebSocket-only demo** (Simulator, Live Monitor) works **without** PostgreSQL.  
> Login, Sessions, Violations pages require PostgreSQL running.

---

## DEMO QUICK START

Run these in 3 separate terminals **from the project root** (`d:\traffic_ai_project`):

### TERMINAL 1 — Backend (AI + WebSocket + REST)

```powershell
# Activate virtualenv and start FastAPI
.\venv\Scripts\uvicorn.exe backend.app.main:app --host 0.0.0.0 --port 8000
```

Wait for: `Application startup complete. Uvicorn running on http://0.0.0.0:8000`

AI model load output (expected on first run):
- `Loading Shared AI Models...`
- `Shared AI Models loaded successfully.`
- `[HelmetChecker] model not found` → helmet detection disabled (non-blocker for demo)

**Health check**: `curl http://localhost:8000/health` → `{"status":"ok"}`

#### Optional: Start PostgreSQL for REST features

```powershell
# If Docker Desktop is installed:
docker compose up -d postgres

# Then create .env from template:
copy .env.example .env
# Edit .env if needed (default creds already match docker-compose.yml)
```

### TERMINAL 2 — Web App

```powershell
cd web-app
npm run dev
```

Open: **http://localhost:3000**

#### Environment Variables (web-app/.env.local)

```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

### TERMINAL 3 — Mobile App (Optional)

```powershell
cd mobile-app
npx expo start
```

#### Environment Variables for Physical Device (mobile-app/.env.local)

```env
# Replace 192.168.x.x with your PC's LAN IP (must be on same Wi-Fi)
EXPO_PUBLIC_API_URL=http://192.168.x.x:8000/api/v1
EXPO_PUBLIC_WS_URL=ws://192.168.x.x:8000
```

> **Android Emulator**: Leave `EXPO_PUBLIC_WS_URL` unset — fallback is `ws://10.0.2.2:8000` automatically.
> **iOS Simulator**: Leave unset — fallback is `ws://localhost:8000` automatically.

**Expo Go compatibility**: Scan QR code with Expo Go app (v50+). Camera + WebSocket streaming works in Expo Go on physical device.

---

## WebSocket Endpoints

| Purpose | Endpoint |
|---|---|
| Road AI (vehicle detection, speed, collision) | `ws://host:8000/ws/v1/stream` |
| Driver Monitor (drowsiness, seatbelt) | `ws://host:8000/ws/v1/driver-stream` |

---

## REST Endpoints (requires PostgreSQL)

| Method | Path | Description |
|---|---|---|
| GET | `/health` | Server health (no DB required) |
| POST | `/api/v1/auth/register` | Register driver account |
| POST | `/api/v1/auth/login` | Login → returns JWT token |
| GET | `/api/v1/violations` | List violations (Bearer token) |
| GET | `/api/v1/sessions` | List sessions (Bearer token) |

---

## Mobile Camera Streaming — Architecture Note

The mobile app streams Road Camera frames to `/ws/v1/stream` using:
1. `expo-camera` `takePictureAsync` at ~2 FPS (prototype rate)
2. `base64-js` decodes JPEG base64 → binary `Uint8Array`
3. WebSocket sends binary `ArrayBuffer` directly to FastAPI backend
4. FastAPI uses `cv2.imdecode()` to decode and run the AI pipeline

**Limitation**: Standard `expo-camera` does not support continuous frame extraction at high FPS without native modules (e.g. `react-native-vision-camera`). This is a prototype implementation.

**DMS (Driver Monitoring)**: Mobile single-device DMS is not supported. Most smartphones cannot simultaneously stream both front and rear cameras via standard APIs. An external device or dedicated hardware is required for DMS in production.

---

## Project Status: DEMO READY

See `docs/demo-checklist.md` for full validation checklist.
