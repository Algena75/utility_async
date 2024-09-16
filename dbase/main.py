import asyncio
import asyncpg
import uvicorn
from dbase.core.config import settings
from dbase.core.db import create_database_if_not_exists


async def main():
    """Функция программного запуска проекта для poetry."""
    await create_database_if_not_exists()

    # uvicorn.run("dbase.main:app", host="0.0.0.0", port=8001, reload=True)


if __name__ == '__main__':
    asyncio.run(main())
