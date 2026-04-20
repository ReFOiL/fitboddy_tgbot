from __future__ import annotations


class EffortNormalizationPolicy:
    def normalize(self, effort: str) -> str:
        return {"easy": "easy", "ok": "normal", "hard": "hard"}.get(
            effort.strip().lower(), "normal"
        )


class TrainingLoadProgressionPolicy:
    """Правила изменения load-множителя по истории сложности."""

    MULT_MIN = 0.7
    MULT_MAX = 1.5
    STEP = 0.1

    def next_multiplier(self, current: float, recent_difficulties: list[str]) -> float:
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
            return min(self.MULT_MAX, round(current + self.STEP, 2))
        if hard_n > 2:
            return max(self.MULT_MIN, round(current - self.STEP, 2))
        return current
