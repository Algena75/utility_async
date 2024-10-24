from pydantic import BaseModel

from web.schemas.houses import HouseRead


class Bill(BaseModel):
    number: int
    water: float
    community_property: float
    total: float


class BuildingCreate(HouseRead):
    year: int
    month: int


class BillRead(HouseRead):
    period: str
    bills: list[Bill]


class BillCreate(BaseModel):
    message: str
    building: BuildingCreate
