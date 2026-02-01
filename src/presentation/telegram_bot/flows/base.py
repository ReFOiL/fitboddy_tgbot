from __future__ import annotations

from abc import ABC, abstractmethod

from aiogram.fsm.context import FSMContext
from aiogram.types import Message


class BaseFlow(ABC):
    @abstractmethod
    async def start(self, message: Message, state: FSMContext) -> None:
        raise NotImplementedError

    @abstractmethod
    async def process(self, message: Message, state: FSMContext) -> None:
        raise NotImplementedError
