from __future__ import annotations

import importlib
import pkgutil
from types import ModuleType


def import_submodules(package_name: str) -> None:
    package = importlib.import_module(package_name)
    if not isinstance(package, ModuleType) or not hasattr(package, "__path__"):
        return
    for _, module_name, _ in pkgutil.walk_packages(package.__path__, package.__name__ + "."):
        importlib.import_module(module_name)


def import_handlers() -> None:
    import_submodules("src.presentation.telegram_bot.handlers")
