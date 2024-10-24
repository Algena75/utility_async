from fastapi import APIRouter

from web.api.endpoints import bill_router, house_router

main_router = APIRouter()
main_router.include_router(bill_router)
main_router.include_router(house_router)
