from http import HTTPStatus
from typing import Dict

from aiohttp import ClientSession
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse

from web.api.utils import get_json_response
from web.core.client import get_client_session
from web.core.config import settings as st
from web.schemas.bills import BillCreate, BillRead

router = APIRouter(tags=['bills'])


@router.post('/bills/{building_id}/{year}/{month}', response_model=BillCreate)
async def create_new_task(
    building_id: int, year: int, month: int,
    session: ClientSession = Depends(get_client_session)
) -> BillCreate | Dict:
    """
    Создаёт и возвращает задачу по расчёту квартплаты в указанный период.
    """
    try:
        async with session.post(f'{st.DBASE_URL}/bills/{building_id}/{year}/{month}',
                                data={}) as resp:
            response = await get_json_response(resp)
        return JSONResponse(content=response, status_code=resp.status)
    except:
        raise HTTPException(
            status_code=HTTPStatus.SERVICE_UNAVAILABLE,
            detail='Сервис недоступен.'
        )


@router.get('/bills/{building_id}/{year}/{month}', response_model=BillRead)
async def get_bill_list(
    building_id: int, year: int, month: int,
    session: ClientSession = Depends(get_client_session)
) -> BillRead | Dict:
    """
    Возвращает список счетов по дому в указанный период.
    """
    try:
        async with session.get(
            f'{st.DBASE_URL}/bills/{building_id}/{year}/{month}'
        ) as resp:
            response = await get_json_response(resp)
        return JSONResponse(content=response, status_code=resp.status)
    except:
        raise HTTPException(
            status_code=HTTPStatus.SERVICE_UNAVAILABLE,
            detail='Сервис недоступен.'
        )
