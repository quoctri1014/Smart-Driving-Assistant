# Smart Driving Assistant — Demo Checklist

## Pre-Demo Setup

- [ ] Backend terminal started: `.\venv\Scripts\uvicorn.exe backend.app.main:app --host 0.0.0.0 --port 8000`
- [ ] `Shared AI Models loaded successfully.` confirmed in backend log
- [ ] Health endpoint: `curl http://localhost:8000/health` returns `{"status":"ok"}`
- [ ] Web app started: `cd web-app && npm run dev`
- [ ] Web opened at: `http://localhost:3000`
- [ ] (Optional) PostgreSQL running for login/sessions/violations

---

## Web Simulator Demo

- [ ] Open `/simulator` page
- [ ] Upload a sample video file
- [ ] Click **Start Session**
- [ ] Road WebSocket status shows **CONNECTED**
- [ ] Speed slider adjusts (e.g. set to 20 km/h)
- [ ] Backend receives correct speed in metadata (`vehicle_speed: 20`)
- [ ] JPEG frames stream to backend (check backend logs for frame processing)
- [ ] Detection result returned from backend (`detection_result` event)
- [ ] Bounding boxes render on canvas overlay
- [ ] Recommended speed updates from backend response
- [ ] Alert banner changes state based on collision/speed result

### Stale Data Test
- [ ] Pause/stop the video
- [ ] After ~2.5 seconds: UI shows **AI Data Unavailable** or **Reconnecting**
- [ ] Recommended speed and collision state are cleared

### Reconnect Test
- [ ] Stop backend process
- [ ] UI shows **Disconnected / Reconnecting**
- [ ] Restart backend
- [ ] WebSocket reconnects automatically without page reload

---

## Web Live Monitor Demo

- [ ] Open `/live` page
- [ ] Road camera (webcam) connected
- [ ] Road WebSocket shows **CONNECTED**
- [ ] Driver Monitor section shows **External Driver Camera Required** (expected on single display)
- [ ] Detection results render as road frames are sent

---

## Mobile Demo

> **Primary fallback**: If mobile network fails, use **Web Simulator** as demo main.

### Setup
- [ ] Backend LAN IP configured in `mobile-app/.env.local` (`EXPO_PUBLIC_WS_URL=ws://192.168.x.x:8000`)
- [ ] Phone and PC on the same Wi-Fi network
- [ ] `npx expo start` running in Terminal 3

### Camera & Permissions
- [ ] Scan QR code with Expo Go app
- [ ] On first launch: camera permission requested
- [ ] Permission granted → camera preview appears
- [ ] Permission denied → UI shows error message (no crash)

### Driving Session
- [ ] Tap **START DRIVE** button
- [ ] Status badge shows **CONNECTING** → **AI ACTIVE**
- [ ] Backend log shows new WebSocket connection
- [ ] Frames streaming (backend log: `frame received`, `imdecode success`)
- [ ] Detection result returned to mobile
- [ ] Speed displayed as **Simulated Speed** (not GPS)
- [ ] Alert banner changes based on detection result

### Collision Takeover
- [ ] When `collision_warning.level = "danger"` received: full-screen red overlay shows **BRAKE NOW!**
- [ ] No button overlap in danger state
- [ ] Safe area respected (status bar not covered by danger overlay)

### Stale State
- [ ] Stop backend while session active
- [ ] After >2.5s: UI shows **AI Connection Lost / Reconnecting...**
- [ ] Recommended speed disappears
- [ ] Collision state clears

### End Trip
- [ ] Tap **END TRIP**
- [ ] Navigation to **Trip Summary** screen
- [ ] Trip Summary shows local session data (no fake metrics)
- [ ] **RETURN TO HOME** button works

### DMS Status
- [ ] No "DMS Normal" displayed (DMS is unsupported on single-device mobile)
- [ ] If any DMS UI exists, it shows **Driver Monitoring Unavailable** or **External Driver Camera Required**

---

## Known Limitations (Not Demo Blockers)

| Item | Status | Notes |
|---|---|---|
| PostgreSQL for REST | Required separately | Use `docker compose up -d postgres` or native install |
| Helmet model | Not included | `[HelmetChecker] model not found` log is expected |
| Mobile DMS | Not supported | Requires external device / dedicated hardware |
| Mobile FPS | ~2 FPS | Prototype rate; production needs `react-native-vision-camera` |
| GPU acceleration | Not available | CPU inference only; warning from easyocr is expected |

---

## Expo Go Compatibility

| Feature | Expo Go |
|---|---|
| Camera preview | ✅ |
| Permission request | ✅ |
| `takePictureAsync` | ✅ |
| WebSocket binary send | ✅ |
| Alert UI | ✅ |
| Trip Summary | ✅ |

**Status: Expo Go Compatible** — no Development Build required for current feature set.

---

## Fallback Demo Strategy

If mobile device cannot connect to backend over LAN:

1. Use **Web Simulator** as primary demo (upload test video, stream to backend)
2. Show **Mobile UI screenshots/recording** for mobile flow demonstration
3. Show **TypeScript check** (`npx tsc --noEmit` → 0 errors) as code quality proof
