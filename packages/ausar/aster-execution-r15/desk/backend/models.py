from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Input(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


def finite(value: Decimal) -> Decimal:
    if not value.is_finite():
        raise ValueError("Value must be finite")
    return value


class Funding(Input):
    amount: Decimal = Field(gt=0, le=Decimal("1000000000"), decimal_places=2)
    client_id: str = Field(min_length=1, max_length=100)
    _amount_finite = field_validator("amount")(finite)


class Watch(Input):
    symbol: str = Field(min_length=1, max_length=15)


class Quote(Watch):
    price: Decimal = Field(gt=0, le=Decimal("1000000000"), decimal_places=6)
    as_of: datetime
    source: str = Field(min_length=1, max_length=160)
    _price_finite = field_validator("price")(finite)

    @field_validator("as_of")
    @classmethod
    def timezone_required(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("as_of must include a timezone")
        return value


class Order(Watch):
    side: Literal["buy", "sell"]
    quantity: Decimal = Field(gt=0, le=Decimal("1000000000"), decimal_places=6)
    type: Literal["market"] = "market"
    client_id: str = Field(min_length=1, max_length=100)
    _quantity_finite = field_validator("quantity")(finite)


class Task(Input):
    kind: Literal["desk_brief", "data_audit", "reconcile", "research_note"]
    title: str | None = Field(default=None, max_length=160)
    instructions: str | None = Field(default=None, max_length=12000)
    symbol: str | None = Field(default=None, max_length=15)


class Runtime(Input):
    running: bool


class Settings(Input):
    quote_max_age_seconds: int | None = Field(default=None, ge=1, le=86400)
    heartbeat_seconds: int | None = Field(default=None, ge=1, le=60)
    cycle_interval_seconds: int | None = Field(default=None, ge=5, le=86400)
