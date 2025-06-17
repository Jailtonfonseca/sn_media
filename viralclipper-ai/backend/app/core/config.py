from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    PROJECT_NAME: str = "ViralClipper AI"
    DATABASE_URL: str = "postgresql://user:password@db:5432/viralclipperdb"
    CELERY_BROKER_URL: str = "amqp://user:password@rabbitmq:5672//"
    CELERY_RESULT_BACKEND: str = "rpc://"

    # JWT Settings
    JWT_SECRET_KEY: str = "supersecretkey"  # Mudar isso em produção!
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 # 1 dia

    # Google OAuth Settings (placeholders - preencher com credenciais reais)
    GOOGLE_CLIENT_ID: str = "YOUR_GOOGLE_CLIENT_ID"
    GOOGLE_CLIENT_SECRET: str = "YOUR_GOOGLE_CLIENT_SECRET"
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/api/v1/auth/google/callback" # Ajustar conforme necessário

    API_V1_STR: str = "/api/v1"

    MEDIA_ROOT_PATH: str = "/app/media" # Dentro do container Docker

    YOUTUBE_API_SCOPES: List[str] = [
        "https://www.googleapis.com/auth/youtube.upload",
        "https://www.googleapis.com/auth/youtube.readonly" # Para verificar status, etc.
    ]

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
