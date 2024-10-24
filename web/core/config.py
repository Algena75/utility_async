import os

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_TITLE: str = 'Сервис расчёта квартплаты'
    APP_DESCRIPTION: str = 'Тестовое задание'
    DBASE_URL: str = os.getenv('DBASE_URL', 'http://127.0.0.1:8001')

    class Config:
        env_file = '.env'
        extra = 'allow'


settings = Settings()
