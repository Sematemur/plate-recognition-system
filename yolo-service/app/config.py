from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    yolo_model_path: str = "models/best.pt"
    yolo_confidence_threshold: float = 0.25
    max_image_size_bytes: int = 10 * 1024 * 1024  # 10 MB

    class Config:
        env_prefix = ""


settings = Settings()
