from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str = "Glazunya App"
    api_version: str = "1.0.0"

    class Config:
        env_file = ".env"  # Можно оставить, если хотите использовать .env в локальной разработке, но не обязательно для Docker


settings = Settings()
