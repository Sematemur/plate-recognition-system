from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # LiteLLM connection
    litellm_base_url: str = "http://litellm:4000"
    litellm_model: str = "glm-ocr"
    litellm_api_key: str = ""
    litellm_timeout: float = 120.0

    # AI guardrail thresholds
    high_confidence_threshold: float = 0.9
    medium_confidence_threshold: float = 0.6
    low_confidence_threshold: float = 0.3

    # Plate validation
    max_plate_length: int = 12

    class Config:
        env_prefix = ""


settings = Settings()
