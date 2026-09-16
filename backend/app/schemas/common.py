from datetime import datetime
from typing import Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator

T = TypeVar("T")


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    @field_validator("*", mode="before")
    @classmethod
    def _uuid_a_str(cls, v):
        if isinstance(v, UUID):
            return str(v)
        return v


class IdSchema(ORMModel):
    id: str


class MessageOut(BaseModel):
    detalle: str = "ok"


class CreatedAtMixin(ORMModel):
    created_at: datetime


class Paginated(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int
    pages: int