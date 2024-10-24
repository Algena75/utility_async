import json
from http import HTTPStatus
from typing import Dict, List

from aiohttp import ClientSession
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse

from web.api.utils import get_json_response
from web.core.client import get_client_session
from web.core.config import settings as st
from web.schemas.houses import HouseCreate, HouseRead

router = APIRouter(tags=['bildings'])


@router.get('/houses', response_model=List[HouseRead])
async def get_houses_list(
    session: ClientSession = Depends(get_client_session)
) -> List[HouseRead] | Dict:
    """Возвращает список домов."""
    try:
        async with session.get(f'{st.DBASE_URL}/buildings') as resp:
            response = await get_json_response(resp)
        return JSONResponse(content=response, status_code=resp.status)
    except:
        raise HTTPException(
            status_code=HTTPStatus.SERVICE_UNAVAILABLE,
            detail='Сервис недоступен.'
        )


@router.get('/houses/{id}', response_model=HouseRead)
async def get_house(
    id: int,
    session: ClientSession = Depends(get_client_session)
) -> HouseRead:
    """Возвращает выбранный дом."""
    try:
        async with session.get(f'{st.DBASE_URL}/buildings/{id}') as resp:
            response = await get_json_response(resp)
        return JSONResponse(content=response, status_code=resp.status)
    except Exception:
        raise HTTPException(
            status_code=HTTPStatus.SERVICE_UNAVAILABLE,
            detail='Сервис недоступен.'
        )


@router.post('/houses', response_model=HouseRead)
async def create_new_house(
    new_obj: HouseCreate,
    session: ClientSession = Depends(get_client_session)
) -> HouseRead:
    """
    Создаёт и возвращает новый дом. Если дом уже создан, то проверяет
    квартиру или список счётчиков.
    """
    new_obj = new_obj.model_dump()
    try:
        async with session.post(f'{st.DBASE_URL}/buildings',
                                data=json.dumps(new_obj)) as resp:
            response = await get_json_response(resp)
        return JSONResponse(content=response, status_code=resp.status)
    except:
        raise HTTPException(
            status_code=HTTPStatus.SERVICE_UNAVAILABLE,
            detail='Сервис недоступен.'
        )
