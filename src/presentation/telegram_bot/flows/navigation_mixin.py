from __future__ import annotations


class NavigationMixin:
    BACK_BUTTON = "⬅️ Назад"
    EXIT_BUTTON = "🚪 Выход"

    @classmethod
    def _with_nav(cls, options: list[str], include_back: bool, include_exit: bool = True) -> list[str]:
        nav: list[str] = []
        if include_back:
            nav.append(cls.BACK_BUTTON)
        if include_exit:
            nav.append(cls.EXIT_BUTTON)
        return options + nav

    @classmethod
    def _is_back(cls, text: str) -> bool:
        text_raw = text.strip()
        text_norm = text_raw.lower()
        return text_raw == cls.BACK_BUTTON or text_norm in {"назад", "предыдущий шаг"}

    @classmethod
    def _is_exit(cls, text: str) -> bool:
        text_raw = text.strip()
        text_norm = text_raw.lower()
        return text_raw == cls.EXIT_BUTTON or text_norm in {"выход", "отмена", "закрыть"}
