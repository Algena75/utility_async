from aiohttp import web
from aiohttp.web_request import Request
from datetime import datetime
from dbase.core.config import settings
from dbase.services import commands as cmd


async def get_building_details(request: Request, id: int) -> dict:
    db = request.app[settings.DB_KEY]
    result = await db.fetch(cmd.GET_BUILDING, id)
    if len(result) == 0:
        raise web.HTTPNotFound(text=f'Здание с id {id} не найдено')
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


async def validate_bill_data(request: Request) -> list[int]:
    db = request.app[settings.DB_KEY]
    building_id = int(request.match_info['building_id'])
    year = int(request.match_info['year'])
    month = int(request.match_info['month'])
    result = await db.fetch(cmd.GET_BUILDING, building_id)
    if len(result) == 0:
        raise web.HTTPNotFound(text=f'Здание с id {building_id} не найдено')
    if month < 1 or month > 12:
        raise web.HTTPBadRequest(text=f'Месяц не может быть {month}')
    dt = datetime.now()
    if year < 1990 or year > dt.year:
        raise web.HTTPBadRequest(
            text=f'Год должен быть в интервале 1990-{dt.year}'
        )
    if year == dt.year and month > dt.month:
        raise web.HTTPBadRequest(text='Период не может быть в будущем')
    check_period = await db.fetch(
        "SELECT count(*) FROM periods WHERE year=$1 AND month=$2;",
        year, month
    )
    if check_period[0][0] == 0:
        await db.fetch(
            "INSERT INTO periods (year, month) VALUES ($1, $2);", year, month
        )
    row = dict(result[0])
    building = dict(id=row.get('id'), street=row.get('street'),
                    house_number=row.get('house_number'),
                    bld_number=row.get('bld_number'))
    return building, year, month
