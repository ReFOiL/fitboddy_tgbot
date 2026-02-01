from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Kcju:
    calories: int
    protein_g: int
    fat_g: int
    carbs_g: int

