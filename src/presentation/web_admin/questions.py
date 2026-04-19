from __future__ import annotations

from fastapi import APIRouter, Depends
from dependency_injector.wiring import Provide, inject

from src.presentation.web_admin.auth import get_current_admin
from src.presentation.web_admin.question_controller import QuestionController
from src.presentation.web_admin.question_schemas import (
    CustomQuestionCreate,
    CustomQuestionOut,
    CustomQuestionUpdate,
    MessageOut,
    QuestionCreatedOut,
    QuestionOrderUpdate,
    ScoringWeightCreate,
    ScoringWeightOut,
)
from src.shared.di.containers import Container


router = APIRouter()


@router.post("/admin/questions", response_model=QuestionCreatedOut)
@inject
async def create_question(
    question_data: CustomQuestionCreate,
    _admin: str = Depends(get_current_admin),
    controller: QuestionController = Depends(Provide[Container.question_controller]),
) -> QuestionCreatedOut:
    return (await controller.create(question_data)).unwrap()


@router.get("/admin/questions", response_model=list[CustomQuestionOut])
@inject
async def list_questions(
    _admin: str = Depends(get_current_admin),
    controller: QuestionController = Depends(Provide[Container.question_controller]),
) -> list[CustomQuestionOut]:
    return (await controller.list_all()).unwrap()


@router.put("/admin/questions/{question_id}", response_model=MessageOut)
@inject
async def update_question(
    question_id: int,
    question_data: CustomQuestionUpdate,
    _admin: str = Depends(get_current_admin),
    controller: QuestionController = Depends(Provide[Container.question_controller]),
) -> MessageOut:
    return (await controller.update(question_id, question_data)).unwrap()


@router.delete("/admin/questions/{question_id}", response_model=MessageOut)
@inject
async def delete_question(
    question_id: int,
    _admin: str = Depends(get_current_admin),
    controller: QuestionController = Depends(Provide[Container.question_controller]),
) -> MessageOut:
    return (await controller.deactivate(question_id)).unwrap()


@router.put("/admin/questions/{question_id}/order", response_model=MessageOut)
@inject
async def update_question_order(
    question_id: int,
    order_data: QuestionOrderUpdate,
    _admin: str = Depends(get_current_admin),
    controller: QuestionController = Depends(Provide[Container.question_controller]),
) -> MessageOut:
    return (await controller.update_order(question_id, order_data)).unwrap()


@router.post("/admin/questions/{question_id}/link-template/{template_id}", response_model=MessageOut)
@inject
async def link_question_to_template(
    question_id: int,
    template_id: int,
    _admin: str = Depends(get_current_admin),
    controller: QuestionController = Depends(Provide[Container.question_controller]),
) -> MessageOut:
    return (await controller.link_template(question_id, template_id)).unwrap()


@router.get("/admin/questions/{question_id}/scoring-weights", response_model=list[ScoringWeightOut])
@inject
async def list_scoring_weights(
    question_id: int,
    _admin: str = Depends(get_current_admin),
    controller: QuestionController = Depends(Provide[Container.question_controller]),
) -> list[ScoringWeightOut]:
    return (await controller.list_scoring_weights(question_id)).unwrap()


@router.post("/admin/questions/{question_id}/scoring-weights", response_model=ScoringWeightOut)
@inject
async def create_or_update_scoring_weight(
    question_id: int,
    data: ScoringWeightCreate,
    _admin: str = Depends(get_current_admin),
    controller: QuestionController = Depends(Provide[Container.question_controller]),
) -> ScoringWeightOut:
    return (await controller.create_or_update_scoring_weight(question_id, data)).unwrap()


@router.delete("/admin/questions/{question_id}/scoring-weights/{answer_value}", response_model=MessageOut)
@inject
async def delete_scoring_weight(
    question_id: int,
    answer_value: str,
    _admin: str = Depends(get_current_admin),
    controller: QuestionController = Depends(Provide[Container.question_controller]),
) -> MessageOut:
    return (await controller.delete_scoring_weight(question_id, answer_value)).unwrap()
