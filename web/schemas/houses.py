from typing import Optional

from pydantic import BaseModel


class Counter(BaseModel):
    number: Optional[str | None] = None


class Apartment(BaseModel):
    number: int
    square: float
    counters: Optional[list[Counter | str]] | None = None


class HouseBase(BaseModel):
    id: int


class HouseCreate(BaseModel):
    street: str
    house_number: int
    bld_number: int | None = None
    apartments: list[Apartment] | None = None

    class Config:
        none = "ignore"


class HouseRead(HouseCreate, HouseBase):
    apartments: list[Apartment | int] | None = None
