from aiohttp import web
from aiohttp.web_request import Request

from dbase.core.config import settings
from dbase.services import commands as cmd


async def get_building_details(request: Request, id: int) -> dict:
    db = request.app[settings.DB_KEY]
    result = await db.fetch(cmd.GET_BUILDING, id)
    if len(result) == 0:
        raise web.HTTPNotFound(text='Данные не обнаружены')
    res_dict = dict(id=result[0][0],
                    street=result[0][1],
                    house_number=result[0][2],
                    bld_number=result[0][3])
    if result[0][4]:
        res_dict.update(apartments=[dict(
            number=record[4], square=record[5], counters=record[6]
        ) for record in result])
    return res_dict


async def validate_data(data: dict) -> None:
    if not data.get('street') or not data.get('house_number'):
        raise web.HTTPBadRequest(text='Некорректные поля')
