from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://cobranzas:cobranzas@db:5432/cobranzas"
    secret_key: str = "clave-insegura-solo-para-desarrollo"
    access_token_expire_minutes: int = 480
    upload_dir: str = "/data/uploads"
    backend_port: int = 8000


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()