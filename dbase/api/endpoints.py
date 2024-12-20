from aiohttp import web
from aiohttp.web_request import Request
from aiohttp.web_response import Response

from dbase.core.celery import calculate_bills
from dbase.core.config import settings
from dbase.services import commands as cmd
from dbase.services.utils import (get_building_details, validate_bill_data,
                                  validate_data)

routes = web.RouteTableDef()


@routes.get('/buildings')
async def get_buildings(request: Request) -> Response:
    """
    Функция делает запрос к БД и возвращает список объектов в JSON.
    """
    db = request.app[settings.DB_KEY]
    result = await db.fetch(cmd.GET_BUILDINGS)
    if len(result) == 0:
        raise web.HTTPNotFound(text='{"detail": "Данные не обнаружены"}')
    return web.json_response([dict(record) for record in result])


@routes.get('/buildings/{id}')
async def get_apartments(request: Request) -> Response:
    """
    Функция делает запрос к БД и возвращает запрашиваемый объект в JSON.
    """
    id = int(request.match_info['id'])
    result = await get_building_details(request, id)
    return web.json_response(result)


@routes.post('/buildings')
async def new_building(request: Request) -> Response:
    """
    Функция создаёт/обновляет новый объект в БД и возвращает его в JSON.
    """
    data = await request.json()
    await validate_data(data)
    db = request.app[settings.DB_KEY]
    bld_number = (
        None if not data.get('bld_number') else int(data.get('bld_number'))
    )
    end = f' AND b.bld_number = {bld_number};' if bld_number else ';'
    building = await db.fetch(f'{cmd.GET_BUILDING_ID}{end}',
                              data.get('street'),
                              int(data.get('house_number')))
    status = 200
    if not building:
        building = await db.fetch(cmd.NEW_BUILDING,
                                  data.get('street'),
                                  int(data.get('house_number')),
                                  bld_number)
        status = 201
    building_id = dict(building[0]).get('id')
    apartments = data.get('apartments')
    if apartments:
        for apartment in apartments:
            new_apartment = await db.fetch(cmd.NEW_APARTMENT,
                                           building_id,
                                           apartment.get('number'),
                                           apartment.get('square'))
            counters = apartment.get('counters')
            if counters:
                values = [counter.get('number') for counter in counters]
                qty = await db.fetch(cmd.NEW_COUNTERS.format(values=values),
                                     new_apartment[0].get('id'))
                status = 201 if qty else status
    result = await get_building_details(request, building_id)
    return web.json_response(result, status=status)


@routes.get('/bills/{building_id}/{year}/{month}')
async def get_bills(request: Request) -> Response:
    """
    Функция возвращает список счетов для запрошенного объекта в указанный
    период.
    """
    building, year, month = await validate_bill_data(request)
    db = request.app[settings.DB_KEY]
    bills = await db.fetch(cmd.GET_BILLS, building.get('id'), year, month)
    if not bills:
        raise web.HTTPNotFound(text='{"detail": "Данные не обнаружены"}')
    bill_list = list()
    for bill in bills:
        str_bill = dict()
        for key in bill.keys():
            str_bill[key] = str(bill.get(key))
        bill_list.append(str_bill)
    building.update(period=f'{year}-{month}', bills=bill_list)
    return web.json_response(building)


@routes.post('/bills/{building_id}/{year}/{month}')
async def add_task_bills_calculation(request: Request) -> Response:
    """
    Функция создаёт задачу для расчёта счетов для запрошенного объекта в
    указанный период.
    """
    building, year, month = await validate_bill_data(request)
    building.update(year=year, month=month)
    try:
        calculate_bills.delay(building)
    except Exception:
        raise Exception()
    return web.json_response({'message': 'Сформирована задача для дома:',
                              'building': building})
