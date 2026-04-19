from __future__ import annotations


class TrainingLoadPolicy:
    """Правила трансформации effort в difficulty и изменения load-множителя."""

    MULT_MIN = 0.7
    MULT_MAX = 1.5
    STEP = 0.1

    @classmethod
    def normalize_effort(cls, effort: str) -> str:
        return {"easy": "easy", "ok": "normal", "hard": "hard"}.get(
            effort.strip().lower(), "normal"
        )

    @classmethod
    def next_multiplier(cls, current: float, recent_difficulties: list[str]) -> float:
        """
        По последним до 3 записям (от новых к старым): easy / normal / hard.
        >2 easy за последние 3 → +0.1; >2 hard → −0.1.
        """
        if len(recent_difficulties) < 3:
            return current
        window = recent_difficulties[:3]
        easy_n = sum(1 for x in window if x == "easy")
        hard_n = sum(1 for x in window if x == "hard")
        if easy_n > 2:
            return min(cls.MULT_MAX, round(current + cls.STEP, 2))
        if hard_n > 2:
            return max(cls.MULT_MIN, round(current - cls.STEP, 2))
        return current
