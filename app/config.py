from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "fast-api-crc32"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    log_level: str = "info"
    environment: str = "development"
    max_upload_size_mb: int = 50

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
