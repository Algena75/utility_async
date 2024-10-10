import asyncio

from aiohttp import web

from dbase.api.endpoints import routes
from dbase.core.config import settings
from dbase.core.db import (create_database_if_not_exists,
                           create_database_pool,
                           destroy_database_pool)

app = web.Application()
app.on_startup.append(create_database_pool)
app.on_cleanup.append(destroy_database_pool)
app.add_routes(routes)


def main():
    """Функция программного запуска проекта для poetry."""
    asyncio.run(create_database_if_not_exists())

    web.run_app(app,
                host=settings.DB_SERVER,
                port=settings.DB_PORT)


if __name__ == '__main__':
    main()
