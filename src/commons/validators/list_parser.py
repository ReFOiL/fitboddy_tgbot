from __future__ import annotations


class CommaListParser:
    def parse(self, value: str) -> list[str]:
        value_norm = value.strip().lower()
        if value_norm in {"нет", "none", "no"}:
            return []
        return [item.strip() for item in value.split(",") if item.strip()]
