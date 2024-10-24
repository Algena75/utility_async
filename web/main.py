import uvicorn
from fastapi import FastAPI

from web.api.routers import main_router
from web.core.config import settings

app = FastAPI(title=settings.APP_TITLE, description=settings.APP_DESCRIPTION)
app.include_router(main_router)


def run():
    """Функция программного запуска проекта для poetry."""
    uvicorn.run("web.main:app", host="0.0.0.0", port=8000, reload=True)


if __name__ == '__main__':
    run()
