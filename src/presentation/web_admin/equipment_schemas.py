from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict, field_validator


class EquipmentBase(BaseModel):
    name: str = Field(..., max_length=50, pattern=r'^[a-z_]+$')
    display_name: str = Field(..., max_length=100)
    category: str = Field(..., max_length=50)
    is_home_friendly: bool = False
    is_active: bool = True

    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Валидация: только латиница, нижнее подчёркивание."""
        if not v.replace('_', '').isalnum() or not v.islower():
            raise ValueError('Name must contain only lowercase letters, numbers, and underscores')
        return v


class EquipmentCreate(EquipmentBase):
    pass


class EquipmentUpdate(BaseModel):
    display_name: str | None = Field(default=None, max_length=100)
    category: str | None = Field(default=None, max_length=50)
    is_home_friendly: bool | None = None
    is_active: bool | None = None


class EquipmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    display_name: str
    category: str
    is_home_friendly: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime
