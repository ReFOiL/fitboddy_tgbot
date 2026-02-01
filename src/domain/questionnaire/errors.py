from __future__ import annotations

import enum


class ValidationErrorCode(str, enum.Enum):
    REQUIRED = "required"
    INVALID = "invalid"
    FORMAT_INVALID = "format_invalid"
    MAX_LENGTH = "max_length"
    NUMBER_INVALID = "number_invalid"
    NUMBER_RANGE = "number_range"
    BOOLEAN_INVALID = "boolean_invalid"
    CHOICE_INVALID = "choice_invalid"
    CHOICE_REQUIRED = "choice_required"
    OPTIONS_NOT_CONFIGURED = "options_not_configured"
    ANSWER_TYPE_INVALID = "answer_type_invalid"


_RU_MESSAGES: dict[ValidationErrorCode, str] = {
    ValidationErrorCode.REQUIRED: "Ответ обязателен.",
    ValidationErrorCode.INVALID: "Некорректное значение.",
    ValidationErrorCode.FORMAT_INVALID: "Неверный формат ответа.",
    ValidationErrorCode.MAX_LENGTH: "Превышена максимальная длина.",
    ValidationErrorCode.NUMBER_INVALID: "Введите число.",
    ValidationErrorCode.NUMBER_RANGE: "Число вне допустимого диапазона.",
    ValidationErrorCode.BOOLEAN_INVALID: "Введите да/нет.",
    ValidationErrorCode.CHOICE_INVALID: "Выберите вариант из списка.",
    ValidationErrorCode.CHOICE_REQUIRED: "Выберите варианты из списка.",
    ValidationErrorCode.OPTIONS_NOT_CONFIGURED: "Варианты ответа не настроены.",
    ValidationErrorCode.ANSWER_TYPE_INVALID: "Некорректный тип ответа.",
}


def get_error_message(code: ValidationErrorCode, locale: str = "ru") -> str:
    if locale == "ru":
        return _RU_MESSAGES.get(code, _RU_MESSAGES[ValidationErrorCode.INVALID])
    return _RU_MESSAGES.get(code, _RU_MESSAGES[ValidationErrorCode.INVALID])
