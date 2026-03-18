from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    database_url: str

    # Service URLs
    yolo_service_url: str = "http://localhost:8001"
    ocr_service_url: str = "http://localhost:8002"

    # Timeouts (seconds)
    yolo_timeout: float = 30.0
    ocr_timeout: float = 120.0
    health_check_timeout: float = 3.0

    # Feed
    feed_interval: int = 3
    sample_data_dir: str = "sample-data"

    # Image validation
    max_image_size_bytes: int = 10 * 1024 * 1024  # 10 MB
    allowed_content_types: list[str] = [
        "image/jpeg",
        "image/png",
        "image/webp",
    ]

    # Pagination
    default_page_size: int = 50
    max_page_size: int = 200

    # CORS
    cors_allowed_origins: list[str] = ["http://localhost:3001"]

    class Config:
        env_prefix = ""


settings = Settings()
