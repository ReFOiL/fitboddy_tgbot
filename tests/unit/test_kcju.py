from src.application.use_cases.questionnaire.calculate_kcju import calculate_kcju
from src.domain.value_objects.anthropometry import Anthropometry


def test_calculate_kcju_weight_loss() -> None:
    anthropometry = Anthropometry(gender="male", age=30, height_cm=180, weight_kg=80)
    kcju = calculate_kcju(anthropometry, activity_multiplier=1.55, goal="weight_loss")
    assert kcju.calories > 0
    assert kcju.protein_g > 0
    assert kcju.fat_g > 0
    assert kcju.carbs_g >= 0

