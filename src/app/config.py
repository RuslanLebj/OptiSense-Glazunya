import os
from typing import ClassVar
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "Glazunya App"
    API_VERSION: str = "1.0.0"
    BASE_DIR: str = os.path.dirname(os.path.abspath(__file__))

    # OptiSense API credentials
    OPTISENSE_API_URL: str
    OPTISENSE_API_KEY: str

    # Redis credentials
    REDIS_URL: str
    REDIS_POOL_MAX_SIZE: int = 15

    # Queue params
    QUEUE_NAME: str = "stream_processing_task"

    # YOLO model
    MODEL_PATH: ClassVar[str] = '/opt/app/artifacts/models/yolo11n_int8_openvino_model/yolo11n.xml'

    # Yandex Cloud S3 credentials
    STORAGE_ACCESS_KEY_ID: str | None = None
    STORAGE_SECRET_ACCESS_KEY: str | None = None
    STORAGE_ENDPOINT_URL: str | None = None
    STORAGE_REGION_NAME: str | None = None
    STORAGE_BUCKET_NAME: str | None = None

    class Config:
        env_file = ".env"  # Можно оставить, если хотите использовать .env в локальной разработке, но не обязательно для Docker


settings = Settings()
