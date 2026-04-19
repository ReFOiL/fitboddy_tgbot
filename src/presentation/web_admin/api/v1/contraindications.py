"""API v1: CRUD справочника противопоказаний."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from dependency_injector.wiring import Provide, inject

from src.presentation.web_admin.auth import AdminPrincipal, get_current_admin
from src.presentation.web_admin.contraindication_controller import ContraindicationController
from src.presentation.web_admin.workout_schemas import (
    ContraindicationCreate,
    ContraindicationOut,
    ContraindicationUpdate,
    MessageOut,
)
from src.shared.di.containers import Container

router = APIRouter()


@router.get("/contraindications", response_model=list[ContraindicationOut])
@inject
async def list_contraindications(
    _admin: AdminPrincipal = Depends(get_current_admin),
    controller: ContraindicationController = Depends(Provide[Container.contraindication_controller]),
) -> list[ContraindicationOut]:
    return (await controller.list_all()).unwrap()


@router.get("/contraindications/{contraindication_id}", response_model=ContraindicationOut)
@inject
async def get_contraindication(
    contraindication_id: int,
    _admin: AdminPrincipal = Depends(get_current_admin),
    controller: ContraindicationController = Depends(Provide[Container.contraindication_controller]),
) -> ContraindicationOut:
    return (await controller.get(contraindication_id)).unwrap()


@router.post("/contraindications", response_model=ContraindicationOut)
@inject
async def create_contraindication(
    data: ContraindicationCreate,
    _admin: AdminPrincipal = Depends(get_current_admin),
    controller: ContraindicationController = Depends(Provide[Container.contraindication_controller]),
) -> ContraindicationOut:
    return (await controller.create(data)).unwrap()


@router.put("/contraindications/{contraindication_id}", response_model=ContraindicationOut)
@inject
async def update_contraindication(
    contraindication_id: int,
    data: ContraindicationUpdate,
    _admin: AdminPrincipal = Depends(get_current_admin),
    controller: ContraindicationController = Depends(Provide[Container.contraindication_controller]),
) -> ContraindicationOut:
    return (await controller.update(contraindication_id, data)).unwrap()


@router.delete("/contraindications/{contraindication_id}", response_model=MessageOut)
@inject
async def delete_contraindication(
    contraindication_id: int,
    _admin: AdminPrincipal = Depends(get_current_admin),
    controller: ContraindicationController = Depends(Provide[Container.contraindication_controller]),
) -> MessageOut:
    return (await controller.delete(contraindication_id)).unwrap()
