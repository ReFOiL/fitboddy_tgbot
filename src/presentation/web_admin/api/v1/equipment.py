"""API v1: CRUD справочника оборудования."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from dependency_injector.wiring import Provide, inject

from src.presentation.web_admin.auth import AdminPrincipal, get_current_admin
from src.presentation.web_admin.equipment_controller import EquipmentController
from src.presentation.web_admin.equipment_schemas import EquipmentCreate, EquipmentOut, EquipmentUpdate
from src.presentation.web_admin.admin_schemas import MessageOut
from src.shared.di.containers import Container

router = APIRouter()


@router.get("/equipment", response_model=list[EquipmentOut])
@inject
async def list_equipment(
    is_active: bool | None = Query(default=None, description="Filter by active status"),
    category: str | None = Query(default=None, description="Filter by category"),
    _admin: AdminPrincipal = Depends(get_current_admin),
    controller: EquipmentController = Depends(Provide[Container.equipment_controller]),
) -> list[EquipmentOut]:
    return (await controller.list_all(is_active=is_active, category=category)).unwrap()


@router.get("/equipment/{equipment_id}", response_model=EquipmentOut)
@inject
async def get_equipment(
    equipment_id: int,
    _admin: AdminPrincipal = Depends(get_current_admin),
    controller: EquipmentController = Depends(Provide[Container.equipment_controller]),
) -> EquipmentOut:
    return (await controller.get(equipment_id)).unwrap()


@router.post("/equipment", response_model=EquipmentOut)
@inject
async def create_equipment(
    data: EquipmentCreate,
    _admin: AdminPrincipal = Depends(get_current_admin),
    controller: EquipmentController = Depends(Provide[Container.equipment_controller]),
) -> EquipmentOut:
    return (await controller.create(data)).unwrap()


@router.put("/equipment/{equipment_id}", response_model=EquipmentOut)
@inject
async def update_equipment(
    equipment_id: int,
    data: EquipmentUpdate,
    _admin: AdminPrincipal = Depends(get_current_admin),
    controller: EquipmentController = Depends(Provide[Container.equipment_controller]),
) -> EquipmentOut:
    return (await controller.update(equipment_id, data)).unwrap()


@router.delete("/equipment/{equipment_id}", response_model=MessageOut)
@inject
async def delete_equipment(
    equipment_id: int,
    _admin: AdminPrincipal = Depends(get_current_admin),
    controller: EquipmentController = Depends(Provide[Container.equipment_controller]),
) -> MessageOut:
    return (await controller.delete(equipment_id)).unwrap()
