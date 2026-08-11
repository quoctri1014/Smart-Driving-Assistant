from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    MAX_FRAME_SIZE_MB: int = 5
    DEFAULT_SPEED_LIMIT: float = 60.0
    WEBSOCKET_VERSION: str = "v1"
    LOG_LEVEL: str = "INFO"
    
settings = Settings()
