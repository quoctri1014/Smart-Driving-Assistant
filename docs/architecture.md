# System Architecture — Smart Driving Assistant

> **Tài liệu kiến trúc hệ thống tổng thể**
> Phiên bản: 1.0 | Người thực hiện: Thành viên 2 (Backend/System Engineer)

---

## 1. Sơ Đồ Kiến Trúc Tổng Thể

```
┌──────────────────────────────────────────────────────────────────────┐
│                       CLIENT LAYER                                   │
│                                                                      │
│  ┌─────────────────────┐          ┌────────────────────────────┐     │
│  │   Web App (Next.js) │          │  Mobile App (Expo RN)      │     │
│  │   localhost:3000    │          │  Expo Go / Device          │     │
│  │                     │          │                            │     │
│  │ • Dashboard         │          │ • Drive Mode (Camera)      │     │
│  │ • Simulator         │          │ • Alert HUD                │     │
│  │ • Live Monitor      │          │ • Trip Summary             │     │
│  │ • Sessions/Violations│         │                            │     │
│  └──────────┬──────────┘          └──────────────┬─────────────┘     │
└─────────────┼────────────────────────────────────┼───────────────────┘
              │ HTTP/REST                            │ WebSocket (binary)
              │ WebSocket (binary)                   │ LAN IP
              ▼                                      ▼
┌──────────────────────────────────────────────────────────────────────┐
│                       BACKEND LAYER (FastAPI)                        │
│                       localhost:8000                                 │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐     │
│  │                    API Routers                              │     │
│  │  POST /api/v1/auth/login     GET /api/v1/violations         │     │
│  │  POST /api/v1/auth/register  GET /api/v1/sessions           │     │
│  └──────────────────────────────────────┬──────────────────────┘     │
│                                         │ JWT Auth (Bearer Token)    │
│  ┌─────────────────────────────────────────────────────────────┐     │
│  │                 WebSocket Handlers                          │     │
│  │  /ws/v1/stream         →  Road AI Pipeline                  │     │
│  │  /ws/v1/driver-stream  →  Driver Monitor Pipeline           │     │
│  └──────────────────────────────────────┬──────────────────────┘     │
│                                         │ asyncio.to_thread          │
│  ┌──────────────────────────────────────▼──────────────────────┐     │
│  │                     AI Engine Layer                         │     │
│  │  PipelineSession (per-connection)                           │     │
│  │  SharedAIModels (singleton)                                 │     │
│  │                                                             │     │
│  │  VehicleDetector → Tracker → ZoneManager                    │     │
│  │  CollisionWarning → SpeedAdvisor → SignRecognition          │     │
│  │  PlateReader → HelmetChecker                                │     │
│  │  DriverPipelineSession → DrowsinessDetector + Seatbelt      │     │
│  └──────────────────────────────────────┬──────────────────────┘     │
│                                         │ SQLAlchemy Async            │
└─────────────────────────────────────────┼────────────────────────────┘
                                          │
              ┌───────────────────────────▼───────────────────────┐
              │                  DATA LAYER                       │
              │                                                   │
              │  PostgreSQL :5432                                 │
              │  ┌─────────┐ ┌───────────────┐ ┌─────────────┐  │
              │  │ drivers │ │driving_sessions│ │ violations  │  │
              │  └─────────┘ └───────────────┘ └─────────────┘  │
              │  ┌──────────────────────────────────────────┐    │
              │  │ Storage: ./storage/*.jpg (violation imgs) │    │
              │  └──────────────────────────────────────────┘    │
              └───────────────────────────────────────────────────┘
```

---

## 2. Cấu Trúc Thư Mục Dự Án

```
traffic_ai_project/
│
├── ai_engine/                  # AI modules & standalone runner
│   ├── modules/
│   │   ├── detector.py         # YOLOv8 vehicle/person detection
│   │   ├── tracker.py          # SimpleTracker (IoU-based)
│   │   ├── zone_manager.py     # Polygon zone counting
│   │   ├── collision_warning.py # BBox growth-rate collision
│   │   ├── speed_advisor.py    # Speed recommendation logic
│   │   ├── sign_recognition.py # Traffic sign detection
│   │   ├── plate_reader.py     # EasyOCR license plate
│   │   ├── helmet_checker.py   # Helmet detection (needs model)
│   │   ├── driver_monitor.py   # MediaPipe drowsiness + seatbelt
│   │   └── utils.py
│   ├── models/                 # Fine-tuned model files (gitignored)
│   │   ├── helmet_yolov8.pt    # ⚠️ Chưa có – cần train
│   │   ├── sign_yolov8.pt      # ⚠️ Chưa có – cần train
│   │   └── seatbelt_yolov8.pt  # ⚠️ Chưa có – cần train
│   ├── sample_videos/
│   │   └── traffic.mp4         # Demo video
│   ├── yolov8n.pt              # COCO pretrained (tự tải khi chạy)
│   ├── config.py               # Cấu hình trung tâm AI
│   ├── main.py                 # Standalone runner (không cần backend)
│   ├── train.py                # Script huấn luyện custom model
│   └── benchmark.py            # Đo hiệu năng pipeline
│
├── backend/                    # FastAPI server
│   └── app/
│       ├── api/                # REST endpoints
│       │   ├── auth_routes.py  # POST /auth/login, /auth/register
│       │   ├── violation_routes.py
│       │   └── session_routes.py
│       ├── auth/               # JWT security
│       │   ├── security.py
│       │   └── dependencies.py
│       ├── core/
│       │   └── pipeline_runner.py  # PipelineSession + SharedAIModels
│       ├── crud/               # Database operations
│       ├── database/           # SQLAlchemy engine + session
│       ├── models_db/          # ORM models (Driver, Violation, Session)
│       ├── schemas/            # Pydantic schemas (DetectionResult, etc.)
│       ├── storage/            # Violation image storage handler
│       ├── websocket/
│       │   ├── stream_handler.py  # WS endpoints
│       │   └── connection_manager.py
│       ├── config.py           # Backend settings (Pydantic Settings)
│       └── main.py             # FastAPI app entry point
│
├── web-app/                    # Next.js frontend
│   └── src/
│       ├── app/                # App Router pages
│       │   ├── (auth)/login/   # Login page
│       │   ├── (dashboard)/    # Protected routes
│       │   │   ├── dashboard/  # Overview stats
│       │   │   ├── simulator/  # Video → AI stream
│       │   │   ├── live/       # Webcam → AI stream
│       │   │   ├── sessions/   # Drive history
│       │   │   ├── violations/ # Violation history
│       │   │   └── ...
│       ├── components/ui/      # Button, Card, Badge, AlertBanner...
│       ├── hooks/              # useRoadDrivingSocket, useDriverMonitorSocket
│       ├── lib/driving/        # alert-engine.ts (priority logic)
│       ├── services/           # apiClient, authService
│       └── types/              # TypeScript detection types
│
├── mobile-app/                 # React Native (Expo)
│   └── app/
│       ├── (auth)/login.tsx    # Login screen
│       ├── (tabs)/             # Tab navigation
│       │   ├── history.tsx     # Session history
│       │   └── profile.tsx     # Driver profile
│       ├── drive.tsx           # Full-screen driving mode
│       └── trip-summary.tsx    # Post-trip summary
│   └── lib/
│       ├── useDrivingSocket.ts # WebSocket hook với reconnect + stale
│       ├── buffer-util.ts      # base64 → ArrayBuffer (base64-js)
│       ├── driving/alert-engine.ts  # Shared alert priority logic
│       └── theme.ts            # Design tokens
│
├── docs/                       # Tài liệu dự án
│   ├── ai_architecture_plan.md # Kiến trúc AI (file này)
│   ├── architecture.md         # Kiến trúc hệ thống tổng thể
│   ├── api-spec.md             # API specification
│   ├── dataset_catalog.md      # Danh mục dataset
│   ├── demo-checklist.md       # Checklist demo
│   └── e2e-validation-report.md
│
├── docker-compose.yml          # PostgreSQL + Backend + Web (Docker)
├── requirements.txt            # Python dependencies
├── .env.example                # Template biến môi trường
└── README.md                   # Quick Start guide
```

---

## 3. Database Schema (ERD)

```
┌─────────────────────┐       ┌──────────────────────────┐
│       drivers       │       │     driving_sessions     │
├─────────────────────┤       ├──────────────────────────┤
│ id (PK)             │──┐    │ id (PK)                  │
│ email (UNIQUE)      │  │    │ driver_id (FK→drivers)   │
│ password_hash       │  └───▶│ start_time               │
│ full_name           │       │ end_time                 │
│ role (admin/driver) │       │ duration_minutes         │
│ created_at          │       │ avg_speed                │
└─────────────────────┘       └──────────────────────────┘
                                          │
                                          │ 1:N
                                          ▼
                              ┌──────────────────────────┐
                              │       violations         │
                              ├──────────────────────────┤
                              │ id (PK)                  │
                              │ driver_id (FK→drivers)   │
                              │ session_id (FK→sessions) │
                              │ violation_type           │
                              │  (collision/no_helmet/   │
                              │   drowsy/no_seatbelt)    │
                              │ severity (critical/warn) │
                              │ image_path               │
                              │ timestamp                │
                              └──────────────────────────┘
```

**Index được tạo trên**:
- `violations.timestamp` — tìm kiếm theo thời gian
- `violations.violation_type` — filter theo loại vi phạm
- `violations.driver_id` — lọc theo tài xế

---

## 4. Bảo Mật

| Thành phần | Cơ chế |
|---|---|
| Authentication | JWT (JSON Web Token) |
| Token lifespan | 1440 phút (24 giờ) |
| Password hashing | bcrypt (passlib) |
| Authorization | Role-based (admin / driver) |
| CORS | Chỉ cho phép `http://localhost:3000` |
| WebSocket auth | Token qua query param `?token=` |

---

## 5. Công Nghệ Sử Dụng

### Backend
| Package | Version | Mục đích |
|---|---|---|
| FastAPI | ≥0.110 | Web framework + WebSocket |
| uvicorn[standard] | ≥0.29 | ASGI server |
| SQLAlchemy[asyncio] | ≥2.0 | ORM async |
| asyncpg | ≥0.29 | PostgreSQL driver |
| passlib[bcrypt] | ≥1.7 | Password hashing |
| python-jose | ≥3.3 | JWT tokens |
| pydantic-settings | ≥2.2 | Config management |

### AI Engine
| Package | Version | Mục đích |
|---|---|---|
| ultralytics | ≥8.2 | YOLOv8 inference |
| opencv-python | ≥4.9 | Image processing |
| mediapipe | ≥0.10 | Face Mesh (DMS) |
| easyocr | ≥1.7 | License plate OCR |
| numpy | ≥1.26 | Array operations |
| supervision | ≥0.21 | Tracking utilities |

### Frontend (Web)
| Package | Mục đích |
|---|---|
| Next.js 15 (App Router) | React framework |
| TypeScript | Type safety |
| Tailwind CSS v4 | Styling |
| lucide-react | Icons |

### Mobile
| Package | Mục đích |
|---|---|
| Expo SDK 57 | React Native framework |
| expo-camera | Camera access |
| expo-router | File-based routing |
| base64-js | Binary frame conversion |

---

## 6. Môi Trường Chạy (Start Commands)

```bash
# Terminal 1 — Backend (từ project root)
.\venv\Scripts\uvicorn.exe backend.app.main:app --host 0.0.0.0 --port 8000

# Terminal 2 — Web App
cd web-app && npm run dev

# Terminal 3 — Mobile App
cd mobile-app && npx expo start
```

Chi tiết hơn: xem [README.md](../README.md)
