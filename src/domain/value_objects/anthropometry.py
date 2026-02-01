from dataclasses import dataclass

@dataclass(frozen=True, slots=True)
class Anthropometry:
    gender: str
    age: int
    height_cm: int
    weight_kg: float
    body_fat_percentage: float | None = None

