from aiohttp import ClientSession, TCPConnector


async def get_client_session():
    """
    Возвращает объект сессии для создания http-запроса к микросервису dbase.
    """
    async with ClientSession(connector=TCPConnector(verify_ssl=False),
                             trust_env=True) as client_session:
        yield client_session
