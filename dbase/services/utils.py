from datetime import datetime

import asyncpg
from aiohttp import web
from aiohttp.web_request import Request
from asyncpg.connection import Connection

from dbase.core.config import constants, settings
from dbase.services import commands as cmd


async def get_building_details(request: Request, id: int) -> dict:
    """
    Функция возвращает из БД объект здания по его id.
    """
    db = request.app[settings.DB_KEY]
    result = await db.fetch(cmd.GET_BUILDING, id)
    if len(result) == 0:
        message = '{"detail": "' + f'Здание с id {id} не найдено"' + '}'
        raise web.HTTPNotFound(text=message)
    res_dict = dict(id=result[0][0],
                    street=result[0][1],
                    house_number=result[0][2],
                    bld_number=result[0][3])
    if result[0][4]:
        res_dict.update(apartments=[dict(
            number=record[5], square=record[6], counters=record[7]
        ) for record in result])
    return res_dict


async def validate_data(data: dict) -> None:
    """
    Валидатор обязательных полей при создании нового объекта.
    """
    if not data.get('street') or not data.get('house_number'):
        raise web.HTTPBadRequest(text='{"detail": "Некорректные поля"}')


async def validate_bill_data(request: Request) -> list[int]:
    """
    Валидатор обязательных полей при создании нового объекта.
    """
    db = request.app[settings.DB_KEY]
    building_id = int(request.match_info['building_id'])
    year = int(request.match_info['year'])
    month = int(request.match_info['month'])
    result = await db.fetch(cmd.GET_BUILDING, building_id)
    if len(result) == 0:
        message = ('{"detail": "' +
                   f'Здание с id {building_id} не найдено' + '"}')
        raise web.HTTPNotFound(text=message)
    if month < 1 or month > 12:
        message = ('{"detail": "' +
                   f'Месяц не может быть {month}' + '"}')
        raise web.HTTPBadRequest(text=message)
    dt = datetime.now()
    if year < 1990 or year > dt.year:
        message = ('{"detail": "' +
                   f'Год должен быть в интервале 1990-{dt.year}' + '"}')
        raise web.HTTPBadRequest(text=message)
    if year == dt.year and month > dt.month:
        message = '{"detail": "Период не может быть в будущем"}'
        raise web.HTTPBadRequest(text=message)
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


async def calculate_bill(building_id: int, month: int, year: int) -> None:
    """
    Функция расчёта коммунальных платежей.
    """
    db = await asyncpg.connect(**settings.CONNECTION_DATA)
    apartment_list = await db.fetch(cmd.GET_BUILDING, building_id)
    tariffs = await db.fetch(cmd.GET_TARIFFS, year, month)
    for row in tariffs:
        if dict(row).get('tariff_name') == 'WA':
            water_tariff = dict(row).get('value')
        elif dict(row).get('tariff_name') == 'CP':
            cp_tariff = dict(row).get('value')
    for apartment in apartment_list:
        counters = apartment.get('counters')
        if counters:
            water_difference = await get_water_difference(counters, year, month, db)
        else:
            water_difference += constants.NORMA
        water = round(float(water_difference) * float(water_tariff), 2)
        community_property = round(float(apartment[6]) * float(cp_tariff), 2)
        await db.execute(cmd.SET_BILL,
                         apartment[4], year, month, water,
                         community_property, water + community_property)
    await db.close()


async def get_water_difference(counters: list, year: int, month: int,
                               db: Connection):
    """
    Вспомогательная функция для расчёта расхода воды.
    """
    water_difference = 0
    for counter in counters:
        counter_values = await db.fetch(cmd.GET_COUNTER_VALUES,
                                        counter, year, month)
        if len(counter_values) > 0:
            if all([len(counter_values) == 2,
                    counter_values[0][2] == year,
                    counter_values[0][1] == month]):
                water_difference += (counter_values[0][3] -
                                     counter_values[1][3])
            elif all([len(counter_values) == 1,
                      counter_values[0][2] == year,
                      counter_values[0][1] == month]):
                water_difference += counter_values[0][3]
            elif len(counter_values) == 2 or len(counter_values) == 1:
                water_difference += constants.NORMA
                await db.fetch(cmd.SET_COUNTER_VALUES,
                               counter, year, month,
                               counter_values[0][3] + constants.NORMA)
        else:
            water_difference += constants.NORMA
            await db.fetch(cmd.SET_COUNTER_VALUES,
                           counter, year, month,
                           constants.NORMA)
    return water_difference
