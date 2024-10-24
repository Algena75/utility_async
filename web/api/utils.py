import json
from http import HTTPStatus
from typing import Dict

from aiohttp import ClientResponse


async def get_json_response(resp: ClientResponse) -> Dict:
    """
    Формирует ответ микросервиса dbase в JSON.
    """
    if resp.status == HTTPStatus.OK or resp.status == HTTPStatus.CREATED:
        response = await resp.json()
    else:
        response = await resp.text()
        response = json.loads(response)
    return response
