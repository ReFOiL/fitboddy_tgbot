from __future__ import annotations

from src.shared.di.containers import Container


def build_container() -> Container:
    container = Container()
    container.wire(packages=["src.presentation.telegram_bot.handlers", "src.presentation.web_admin"])
    return container

