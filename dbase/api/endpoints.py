from aiohttp import web
from aiohttp.web_request import Request
from aiohttp.web_response import Response

from dbase.core.config import constants, settings
from dbase.services import commands as cmd
from dbase.services.utils import (get_building_details, validate_bill_data,
                                  validate_data)

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
        None if not data.get('bld_number') else int(data.get('bld_number'))
    )
    building = await db.fetch(cmd.GET_BUILDING_ID,
                              data.get('street'),
                              int(data.get('house_number')),
                              bld_number)
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
    building, year, month = await validate_bill_data(request)
    db = request.app[settings.DB_KEY]
    bills = await db.fetch(cmd.GET_BILLS, building.get('id'), year, month)
    if not bills:
        raise web.HTTPNotFound(text='Данные не обнаружены')
    bill_list = list()
    for bill in bills:
        str_bill = dict()
        for key in bill.keys():
            str_bill[key] = str(bill.get(key))
        bill_list.append(str_bill)
    building.update(period=f'{year}-{month}', bills=bill_list)
    return web.json_response(building)


@routes.post('/bills/{building_id}/{year}/{month}')
async def calculate_bills(request: Request) -> Response:
    building, year, month = await validate_bill_data(request)
    db = request.app[settings.DB_KEY]
    apartment_list = await db.fetch(cmd.GET_BUILDING, building.get('id'))
    tariffs = await db.fetch(cmd.GET_TARIFFS, year, month)
    for row in tariffs:
        if dict(row).get('tariff_name') == 'WA':
            water_tariff = dict(row).get('value')
        elif dict(row).get('tariff_name') == 'CP':
            cp_tariff = dict(row).get('value')
    for apartment in apartment_list:
        counters = apartment.get('counters')
        water_difference = 0
        if counters:
            for counter in counters:
                counter_values = await db.fetch(cmd.GET_COUNTER_VALUES,
                                                counter, year, month)
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
        else:
            water_difference += constants.NORMA
        water =  round(float(water_difference) * float(water_tariff), 2)
        community_property = round(float(apartment[6]) * float(cp_tariff), 2)
        await db.fetch(cmd.SET_BILL,
                       apartment[4], year, month,
                       water, community_property, water + community_property)
