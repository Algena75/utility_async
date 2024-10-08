import os

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    POSTGRES_USER: str = os.getenv("POSTGRES_USER")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD")
    POSTGRES_SERVER: str = os.getenv("POSTGRES_SERVER", "localhost")
    POSTGRES_PORT: str | int = os.getenv("POSTGRES_PORT", 5432)
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "tdd")
    CONNECTION_DATA: dict = dict(host=POSTGRES_SERVER,
                                 port=POSTGRES_PORT,
                                 user=POSTGRES_USER,
                                 database=POSTGRES_DB,
                                 password=POSTGRES_PASSWORD)
    DB_KEY: str = 'database'
    DB_SERVER: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: int = os.getenv("DB_PORT", 8001)

    class Config:
        env_file = '.env'
        extra = 'allow'


settings = Settings()
