"""
Модуль ядра алгоритму Vitamin App.

Відповідає за розрахунок фізіологічних норм користувача (калорії, макро- та мікронутрієнти)
та виконання комбінаторної оптимізації для підбору ідеального щоденного меню
на основі бази даних страв та індивідуальних преференцій (чорного списку).
"""

import itertools
from typing import List, Dict, Any, Optional, Tuple
from backend.models import db, Dish, DishIngredient, UserDislike


# Константна таблиця норм (RDA - Recommended Dietary Allowances)
# Структура: { "стать": { "нутрієнт": базова_добова_норма } }
RDA_STANDARDS: Dict[str, Dict[str, float]] = {
    "male": {
        "vit_a_mcg": 900.0,
        "vit_c_mg": 90.0,
        "vit_d_mcg": 15.0,
        "vit_e_mg": 15.0,
        "vit_k_mcg": 120.0,
        "vit_b1_mg": 1.2,
        "vit_b2_mg": 1.3,
        "vit_b6_mg": 1.3,
        "vit_b12_mcg": 2.4,
        "iron_mg": 8.0,
        "calcium_mg": 1000.0,
        "magnesium_mg": 400.0,
        "zinc_mg": 11.0
    },
    "female": {
        "vit_a_mcg": 700.0,
        "vit_c_mg": 75.0,
        "vit_d_mcg": 15.0,
        "vit_e_mg": 15.0,
        "vit_k_mcg": 90.0,
        "vit_b1_mg": 1.1,
        "vit_b2_mg": 1.1,
        "vit_b6_mg": 1.3,
        "vit_b12_mcg": 2.4,
        "iron_mg": 18.0,
        "calcium_mg": 1000.0,
        "magnesium_mg": 310.0,
        "zinc_mg": 8.0
    }
}


# Коефіцієнт збільшення норми нутрієнта при підтвердженому дефіциті
THERAPEUTIC_MULTIPLIER: float = 1.5


def calculate_daily_targets(user_id: int) -> Dict[str, Any]:
    """
    Розраховує добову норму калорій, макронутрієнтів (БЖВ) та мікронутрієнтів.

    Використовує формулу Міффліна-Сан Жеора для визначення базового метаболізму (BMR),
    який потім множиться на коефіцієнт активності (TDEE).

    Args:
        user_id (int): Унікальний ідентифікатор користувача.

    Returns:
        Dict[str, Any]: Словник із розрахованими цілями.
    """

    # Локальний імпорт для уникнення циклічних залежностей
    from backend.models import UserDetails

    user_info = UserDetails.query.get(user_id)

    if not user_info:
        raise ValueError(f"Дані користувача з ID {user_id} не знайдено.")

    # ===== 1. РОЗРАХУНОК КАЛОРІЙ =====
    # Формула Міффліна-Сан Жеора:
    # чоловіки: 10*вага + 6.25*зріст - 5*вік + 5
    # жінки:    10*вага + 6.25*зріст - 5*вік - 161
    bmr_base = (10 * user_info.weight) + (6.25 * user_info.height) - (5 * user_info.age)

    if user_info.sex == "male":
        bmr = bmr_base + 5
    else:
        bmr = bmr_base - 161

    # TDEE — добова потреба в калоріях з урахуванням активності
    tdee = bmr * user_info.activity_level

    # ===== 2. РОЗРАХУНОК БЖВ =====
    # 1 г білка = 4 ккал
    # 1 г жиру = 9 ккал
    # 1 г вуглеводів = 4 ккал
    # Пропорція маси: 1 : 1 : 4
    # 4x + 9x + 4*(4x) = 29x
    x = tdee / 29.0

    # ===== 3. БАЗОВІ НОРМИ МІКРОНУТРІЄНТІВ =====
    # Беремо добові норми залежно від статі користувача
    base_rda = RDA_STANDARDS.get(user_info.sex, RDA_STANDARDS["male"])

    def apply_deficiency(nutrient_name: str, deficiency_flag: bool) -> float:
        """
        Повертає добову норму нутрієнта.

        Якщо користувач позначив дефіцит,
        базова норма множиться на THERAPEUTIC_MULTIPLIER.
        """
        base_value = base_rda[nutrient_name]
        multiplier = THERAPEUTIC_MULTIPLIER if deficiency_flag else 1.0
        return round(base_value * multiplier, 2)

    # ===== 4. РОЗРАХУНОК НОРМ З УРАХУВАННЯМ ДЕФІЦИТІВ =====
    target_micronutrients = {
        "vit_a_mcg": apply_deficiency("vit_a_mcg", user_info.def_vit_a),
        "vit_c_mg": apply_deficiency("vit_c_mg", user_info.def_vit_c),
        "vit_d_mcg": apply_deficiency("vit_d_mcg", user_info.def_vit_d),
        "vit_e_mg": apply_deficiency("vit_e_mg", user_info.def_vit_e),
        "vit_k_mcg": apply_deficiency("vit_k_mcg", user_info.def_vit_k),
        "vit_b1_mg": apply_deficiency("vit_b1_mg", user_info.def_vit_b1),
        "vit_b2_mg": apply_deficiency("vit_b2_mg", user_info.def_vit_b2),
        "vit_b6_mg": apply_deficiency("vit_b6_mg", user_info.def_vit_b6),
        "vit_b12_mcg": apply_deficiency("vit_b12_mcg", user_info.def_vit_b12),
        "iron_mg": apply_deficiency("iron_mg", user_info.def_iron),
        "calcium_mg": apply_deficiency("calcium_mg", user_info.def_calcium),
        "magnesium_mg": apply_deficiency("magnesium_mg", user_info.def_magnesium),
        "zinc_mg": apply_deficiency("zinc_mg", user_info.def_zinc),
    }

    return {
        "tdee_kcal": round(tdee, 2),
        "macros": {
            "protein_g": round(x, 2),
            "fat_g": round(x, 2),
            "carbs_g": round(4 * x, 2)
        },
        "micronutrients": target_micronutrients
    }


def get_allowed_dishes(user_id: int) -> List[Dish]:
    """
    Формує список дозволених страв, виключаючи ті, що містять небажані продукти.
    """

    # 1. Знаходимо ID продуктів, які користувач не їсть
    disliked_products = db.session.query(UserDislike.product_id)\
                                  .filter(UserDislike.user_id == user_id).subquery()

    # 2. Знаходимо ID страв, які містять хоча б один небажаний продукт
    banned_dishes = db.session.query(DishIngredient.dish_id)\
                              .filter(DishIngredient.product_id.in_(disliked_products)).subquery()

    # 3. Повертаємо тільки ті страви, які НЕ входять до заборонених
    allowed_dishes = db.session.query(Dish)\
                               .filter(~Dish.id.in_(banned_dishes)).all()

    return allowed_dishes


def find_best_menu(targets: Dict[str, Any], allowed_dishes: List[Dish]) -> Optional[Tuple[Dish, ...]]:
    """
    Виконує пошук оптимальної комбінації з 3 страв.

    Алгоритм перебирає всі можливі комбінації по 3 страви
    та обирає ту, яка найкраще наближена до цільових БЖВ і калорій.
    """

    best_menu = None
    lowest_penalty = float("inf")

    # Перебір усіх комбінацій по 3 страви
    for combo in itertools.combinations(allowed_dishes, 3):
        current_p = sum(d.total_protein for d in combo)
        current_f = sum(d.total_fat for d in combo)
        current_c = sum(d.total_carbs for d in combo)
        current_kcal = sum(d.total_calories for d in combo)

        # Функція штрафу: чим більше відхилення від цілей, тим гірша комбінація
        penalty = (
            abs(targets["macros"]["protein_g"] - current_p) +
            abs(targets["macros"]["fat_g"] - current_f) +
            abs(targets["macros"]["carbs_g"] - current_c)
        )

        # Якщо калорійність сильно відрізняється від цілі — додаємо великий штраф
        if abs(targets["tdee_kcal"] - current_kcal) > targets["tdee_kcal"] * 0.1:
            penalty += 500

        # Запам'ятовуємо найкращу комбінацію
        if penalty < lowest_penalty:
            lowest_penalty = penalty
            best_menu = combo

    return best_menu