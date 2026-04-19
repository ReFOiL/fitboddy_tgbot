"""Кастомные исключения приложения (доменные и прикладные)."""


class SystemQuestionMutationError(Exception):
    """Попытка изменить контрактный системный вопрос (ключ `system:*`) недопустимым способом."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)
