from aiohttp import web
from aiohttp.web_request import Request
from aiohttp.web_response import Response

from dbase.core.config import settings
from dbase.services import commands as cmd
from dbase.services.utils import get_building_details, validate_data

routes = web.RouteTableDef()


@routes.get('/buildings')
async def get_buildings(request: Request) -> Response:
    db = request.app[settings.DB_KEY]
    result = await db.fetch(cmd.GET_BUILDINGS)
    if len(result) == 0:
        raise web.HTTPNotFound(text='Данные не обнаружены')
    return web.json_response([dict(record) for record in result])


@routes.get('/buildings/{id}')
async def get_apartments(request: Request) -> Response:
    id = int(request.match_info['id'])
    result = await get_building_details(request, id)
    return web.json_response(result)


@routes.post('/buildings')
async def new_building(request: Request) -> Response:
    data = await request.json()
    await validate_data(data)
    db = request.app[settings.DB_KEY]
    bld_number = (
        None if not data.get('bld_number') else data.get('bld_number')
    )
    building = await db.fetch(cmd.GET_BUILDING_ID, data.get('street'),
                              int(data.get('house_number')), int(bld_number))
    status = 200
    if not building:
        building = await db.fetch(cmd.NEW_BUILDING, data.get('street'),
                                  int(data.get('house_number')),
                                  int(bld_number))
        status = 201
    building_id = dict(building[0]).get('id')
    apartments = data.get('apartments')
    if apartments:
        for apartment in apartments:
            new_apartment = await db.fetch(cmd.NEW_APARTMENT, building_id,
                                           apartment.get('number'),
                                           apartment.get('square'))
            counters = apartment.get('counters')
            if counters:
                values = [counter.get('number') for counter in counters]
            qty = await db.fetch(f"""INSERT INTO counters (apartment,
                                                           counter_number)
                                 SELECT $1, x
                                 FROM unnest(ARRAY{values}) x
                                 ON CONFLICT DO NOTHING
                                 RETURNING *;
                                 """, new_apartment[0].get('id'))
            status = 201 if qty else status
    result = await get_building_details(request, building_id)
    return web.json_response(result, status=status)
