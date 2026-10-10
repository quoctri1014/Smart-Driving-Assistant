from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    MAX_FRAME_SIZE_MB: int = 5
    DEFAULT_SPEED_LIMIT: float = 60.0
    WEBSOCKET_VERSION: str = "v1"
    LOG_LEVEL: str = "INFO"
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]
    MAX_STREAM_CONNECTIONS: int = 64
    MAX_STREAMS_PER_USER: int = 10
    MAX_INFLIGHT_INFERENCE: int = 8
    
settings = Settings()

