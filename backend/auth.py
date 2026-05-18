import re
import secrets
from flask import jsonify, request
from openai import OpenAI
import os
import random
from datetime import datetime, timedelta
from typing import Tuple

from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.wrappers import Response

from backend.models import db, User, UserDetails, PasswordReset, Product, UserDislike
from backend.algorithm import calculate_daily_targets, get_allowed_dishes, find_best_menu
from backend.mailer import send_reset_email
from backend.models import Dish
from backend.ai_generator import generate_ai_dishes


auth_bp = Blueprint('auth', __name__)

MAX_FAILED_ATTEMPTS: int = 3


def generate_secure_code() -> str:
    return ''.join(str(secrets.randbelow(10)) for _ in range(6))


def validate_password(password: str) -> Tuple[bool, str]:
    if len(password) <= 8:
        return False, "Пароль має містити більше 8 символів."
    if not re.search(r'[A-Z]', password):
        return False, "Пароль має містити хоча б одну велику літеру."
    if not re.search(r'\d', password):
        return False, "Пароль має містити хоча б одну цифру."
    if not re.search(r'[\W_]', password):
        return False, "Пароль має містити хоча б один спеціальний символ."
    return True, "Пароль відповідає вимогам."


def is_mail_valid(email: str) -> bool:
    email_regex = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(email_regex, email) is not None


@auth_bp.route('/register', methods=['GET', 'POST'])
def register() -> str | Response:
    if request.method == 'POST':
        username = request.form.get('login')
        email = request.form.get('email')
        password = request.form.get('password')
        password_confirm = request.form.get('password_confirm')

        if password != password_confirm:
            flash("Помилка: Паролі не співпадають!", "error")
            return render_template('register.html')

        if not is_mail_valid(email):
            flash("Помилка: Невірний формат email!", "error")
            return render_template('register.html')

        is_valid, error_message = validate_password(password)
        if not is_valid:
            flash(f"Помилка: {error_message}", "error")
            return render_template('register.html')

        existing_user = User.query.filter((User.username == username) | (User.email == email)).first()
        if existing_user:
            flash("Помилка: Користувач з таким логіном або поштою вже існує!", "error")
            return render_template('register.html')

        hashed_password = generate_password_hash(password)
        new_user = User(username=username, email=email, password_hash=hashed_password)

        db.session.add(new_user)
        db.session.commit()

        flash("Реєстрація успішна! Тепер ви можете увійти.", "success")
        return redirect(url_for('auth.login'))

    return render_template('register.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login() -> str | Response:
    if request.method == 'POST':
        username = request.form.get('login')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            flash(f"Успішний вхід! Вітаємо, {user.username}.", "success")
            return redirect(url_for('auth.dashboard'))

        flash("Помилка: Невірний логін або пароль!", "error")
        return render_template('login.html')

    return render_template('login.html')


@auth_bp.route('/logout')
def logout() -> Response:
    session.pop('user_id', None)
    flash("Ви вийшли з облікового запису.", "success")
    return redirect(url_for('auth.login'))


@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password() -> str | Response:
    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()

        if user:
            PasswordReset.query.filter_by(user_id=user.id).delete()
            db.session.commit()

            code = generate_secure_code()
            expires = datetime.utcnow() + timedelta(minutes=5)

            reset_request = PasswordReset(user_id=user.id, code=code, expires_at=expires)
            db.session.add(reset_request)
            db.session.commit()

            send_reset_email(user.email, code)

        flash("Якщо така пошта існує, ми надіслали на неї код відновлення.", "success")
        return redirect(url_for('auth.verify_reset_code', email=email))

    return render_template('forgot_password.html')


@auth_bp.route('/verify-reset-code', methods=['GET', 'POST'])
def verify_reset_code() -> str | Response:
    email = request.args.get('email')

    if request.method == 'POST':
        email_form = request.form.get('email')
        code_input = request.form.get('code')
        new_password = request.form.get('new_password')
        password_confirm = request.form.get('password_confirm')

        if new_password != password_confirm:
            flash("Помилка: Нові паролі не співпадають!", "error")
            return render_template('verify_code.html', email=email_form)

        is_valid, error_msg = validate_password(new_password)
        if not is_valid:
            flash(f"Помилка: {error_msg}", "error")
            return render_template('verify_code.html', email=email_form)

        user = User.query.filter_by(email=email_form).first()
        if not user:
            flash("Помилка: Користувача не знайдено.", "error")
            return redirect(url_for('auth.forgot_password'))

        reset_request = PasswordReset.query.filter_by(user_id=user.id).first()

        if not reset_request:
            flash("Помилка: Запит на відновлення не знайдено або він застарів.", "error")
            return redirect(url_for('auth.forgot_password'))

        if datetime.utcnow() > reset_request.expires_at:
            db.session.delete(reset_request)
            db.session.commit()
            flash("Помилка: Час дії коду минув (5 хвилин).", "error")
            return redirect(url_for('auth.forgot_password'))

        if reset_request.code != code_input:
            reset_request.failed_attempts += 1
            db.session.commit()

            if reset_request.failed_attempts >= MAX_FAILED_ATTEMPTS:
                db.session.delete(reset_request)
                db.session.commit()
                flash("Помилка: Перевищено ліміт спроб. Запит анульовано.", "error")
                return redirect(url_for('auth.forgot_password'))

            attempts_left = MAX_FAILED_ATTEMPTS - reset_request.failed_attempts
            flash(f"Помилка: Невірний код. Залишилось спроб: {attempts_left}", "error")
            return render_template('verify_code.html', email=email_form)

        user.password_hash = generate_password_hash(new_password)
        db.session.delete(reset_request)
        db.session.commit()

        flash("Пароль успішно змінено. Тепер ви можете увійти.", "success")
        return redirect(url_for('auth.login'))

    return render_template('verify_code.html', email=email)


@auth_bp.route('/dashboard')
def dashboard() -> str | Response:
    user_id = session.get('user_id')

    if not user_id:
        flash("Будь ласка, увійдіть у систему.", "error")
        return redirect(url_for('auth.login'))

    user = User.query.get(user_id)
    user_details = UserDetails.query.filter_by(user_id=user_id).first()

    targets = None
    best_menu = None
    dish_reasons = {}
    product_recommendations = {}

    all_products = Product.query.all()

    dislike_records = UserDislike.query.filter_by(user_id=user_id).all()
    user_dislikes = [record.product_id for record in dislike_records]

    if user_details:
        nutrient_map = {
            "Вітамін A": ("def_vit_a", "vit_a_mcg", "мкг"),
            "Вітамін C": ("def_vit_c", "vit_c_mg", "мг"),
            "Вітамін D": ("def_vit_d", "vit_d_mcg", "мкг"),
            "Вітамін E": ("def_vit_e", "vit_e_mg", "мг"),
            "Вітамін K": ("def_vit_k", "vit_k_mcg", "мкг"),
            "Вітамін B1": ("def_vit_b1", "vit_b1_mg", "мг"),
            "Вітамін B2": ("def_vit_b2", "vit_b2_mg", "мг"),
            "Вітамін B6": ("def_vit_b6", "vit_b6_mg", "мг"),
            "Вітамін B12": ("def_vit_b12", "vit_b12_mcg", "мкг"),
            "Залізо": ("def_iron", "iron_mg", "мг"),
            "Кальцій": ("def_calcium", "calcium_mg", "мг"),
            "Магній": ("def_magnesium", "magnesium_mg", "мг"),
            "Цинк": ("def_zinc", "zinc_mg", "мг"),
        }

        for nutrient_name, (def_field, product_field, unit) in nutrient_map.items():
            if getattr(user_details, def_field):
                top_products = sorted(
                    all_products,
                    key=lambda product: getattr(product, product_field) or 0,
                    reverse=True
                )[:4]

                product_recommendations[nutrient_name] = {
                    "unit": unit,
                    "field": product_field,
                    "products": top_products
                }

        try:
            targets = calculate_daily_targets(user_id)
            allowed_dishes = get_allowed_dishes(user_id)

            if len(allowed_dishes) >= 3:
                if 'saved_menu' in session:

                    best_menu = session['saved_menu']

                else:

                    best_menu = find_best_menu(targets, allowed_dishes)

                    temp_menu = {}

                    for meal_type, dish in best_menu.items():

                        temp_menu[meal_type] = {
                            "id": dish.id,
                            "name": dish.name,
                            "recipe": dish.recipe,

                            "ingredients": [
                                {
                                    "name": ingredient.product.name,
                                    "grams": ingredient.weight_g
                                }
                                for ingredient in dish.ingredients
                            ],

                            "total_calories": dish.total_calories,
                            "total_protein": dish.total_protein,
                            "total_fat": dish.total_fat,
                            "total_carbs": dish.total_carbs,

                            "vit_a_total": dish.vit_a_total,
                            "vit_c_total": dish.vit_c_total,
                            "vit_d_total": dish.vit_d_total,
                            "vit_e_total": dish.vit_e_total,
                            "vit_k_total": dish.vit_k_total,
                            "vit_b1_total": dish.vit_b1_total,
                            "vit_b2_total": dish.vit_b2_total,
                            "vit_b6_total": dish.vit_b6_total,
                            "vit_b12_total": dish.vit_b12_total,

                            "iron_total": dish.iron_total,
                            "calcium_total": dish.calcium_total,
                            "magnesium_total": dish.magnesium_total,
                            "zinc_total": dish.zinc_total
                        }

                    best_menu = temp_menu

                    session['saved_menu'] = best_menu

                if best_menu:
                    for dish in best_menu.values():

                        reasons = []

                        if dish["vit_a_total"] >= targets["micronutrients"]["vit_a_mcg"] * 0.2:
                            reasons.append("містить багато вітаміну A")

                        if dish["vit_c_total"] >= targets["micronutrients"]["vit_c_mg"] * 0.2:
                            reasons.append("є хорошим джерелом вітаміну C")

                        if dish["vit_d_total"] >= targets["micronutrients"]["vit_d_mcg"] * 0.2:
                            reasons.append("допомагає підвищити рівень вітаміну D")

                        if dish["vit_e_total"] >= targets["micronutrients"]["vit_e_mg"] * 0.2:
                            reasons.append("містить вітамін E")

                        if dish["vit_k_total"] >= targets["micronutrients"]["vit_k_mcg"] * 0.2:
                            reasons.append("містить вітамін K")

                        if dish["vit_b1_total"] >= targets["micronutrients"]["vit_b1_mg"] * 0.2:
                            reasons.append("підтримує норму вітаміну B1")

                        if dish["vit_b2_total"] >= targets["micronutrients"]["vit_b2_mg"] * 0.2:
                            reasons.append("містить вітамін B2")

                        if dish["vit_b6_total"] >= targets["micronutrients"]["vit_b6_mg"] * 0.2:
                            reasons.append("містить вітамін B6")

                        if dish["vit_b12_total"] >= targets["micronutrients"]["vit_b12_mcg"] * 0.2:
                            reasons.append("є джерелом вітаміну B12")

                        if dish["iron_total"] >= targets["micronutrients"]["iron_mg"] * 0.2:
                            reasons.append("містить залізо")

                        if dish["calcium_total"] >= targets["micronutrients"]["calcium_mg"] * 0.2:
                            reasons.append("підтримує норму кальцію")

                        if dish["magnesium_total"] >= targets["micronutrients"]["magnesium_mg"] * 0.2:
                            reasons.append("містить магній")

                        if dish["zinc_total"] >= targets["micronutrients"]["zinc_mg"] * 0.2:
                            reasons.append("містить цинк")

                        if not reasons:
                            reasons.append("добре доповнює раціон за калоріями та БЖВ")

                        dish_reasons[dish["id"]] = reasons

                else:
                    flash("У базі недостатньо страв для формування меню (потрібно мінімум 3).", "error")

        except Exception as e:
            print(f"Algorithm Error: {e}")
            flash("Виникла помилка при розрахунку меню.", "error")

    if best_menu:
        session['best_menu'] = {
            meal_type: dish["id"] if isinstance(dish, dict) else dish.id
            for meal_type, dish in best_menu.items()
        }

        regenerated_meal = session.get('regenerated_meal')

        if regenerated_meal and regenerated_meal in best_menu:

                    products = [
                        product.name
                        for product in all_products
                    ]

                    goal_parts = []

                    if user_details.def_vit_d:
                        goal_parts.append("rich in vitamin D")

                    if user_details.def_iron:
                        goal_parts.append("rich in iron")

                    if user_details.def_magnesium:
                        goal_parts.append("rich in magnesium")

                    if user_details.def_zinc:
                        goal_parts.append("rich in zinc")

                    if user_details.def_vit_b12:
                        goal_parts.append("rich in vitamin B12")

                    if user_details.def_vit_c:
                        goal_parts.append("rich in vitamin C")

                    if user_details.def_vit_a:
                        goal_parts.append("rich in vitamin A")

                    goal = ", ".join(goal_parts)

                    if not goal:
                        goal = "healthy balanced meal"

                    disliked_products = [
                        product.name
                        for product in all_products
                        if product.id in user_dislikes
                    ]

                    ai_dishes = generate_ai_dishes(
                        products,
                        goal,
                        disliked_products
                    )

                    if ai_dishes:

                        ai_dish = ai_dishes[0]
                        total_calories = 0
                        total_protein = 0
                        total_fat = 0
                        total_carbs = 0

                        for ingredient in ai_dish["ingredients"]:

                            product = Product.query.filter_by(
                                name=ingredient["name"]
                            ).first()

                            if product:

                                grams = ingredient["grams"]
                                factor = grams / 100

                                total_calories += product.calories_100g * factor
                                total_protein += product.protein_100g * factor
                                total_fat += product.fat_100g * factor
                                total_carbs += product.carbs_100g * factor

                        best_menu[regenerated_meal] = {
                            "id": -1,

                            "name": ai_dish["name"],

                            "ingredients": ai_dish["ingredients"],

                            "recipe": ai_dish["recipe"],

                            "total_calories": round(total_calories, 1),
                            "total_protein": round(total_protein, 1),
                            "total_fat": round(total_fat, 1),
                            "total_carbs": round(total_carbs, 1),

                            "vit_a_total": 0,
                            "vit_c_total": 0,
                            "vit_d_total": 0,
                            "vit_e_total": 0,
                            "vit_k_total": 0,
                            "vit_b1_total": 0,
                            "vit_b2_total": 0,
                            "vit_b6_total": 0,
                            "vit_b12_total": 0,

                            "iron_total": 0,
                            "calcium_total": 0,
                            "magnesium_total": 0,
                            "zinc_total": 0
                        }
                        session['saved_menu'] = best_menu

        session.pop('regenerated_meal', None)

    return render_template(
            'dashboard.html',
            user=user,
            user_details=user_details,
            targets=targets,
            best_menu=best_menu,
            all_products=all_products,
            user_dislikes=user_dislikes,
            dish_reasons=dish_reasons,
            product_recommendations=product_recommendations
        )


@auth_bp.route('/update-profile', methods=['POST'])
def update_profile() -> Response:
    user_id = session.get('user_id')

    if not user_id:
        return redirect(url_for('auth.login'))

    sex = request.form.get('sex')
    age = int(request.form.get('age'))
    weight = float(request.form.get('weight'))
    height = float(request.form.get('height'))
    activity_level = float(request.form.get('activity_level'))

    def_vit_a = bool(request.form.get('def_vit_a'))
    def_vit_c = bool(request.form.get('def_vit_c'))
    def_vit_d = bool(request.form.get('def_vit_d'))
    def_vit_e = bool(request.form.get('def_vit_e'))
    def_vit_k = bool(request.form.get('def_vit_k'))

    def_vit_b1 = bool(request.form.get('def_vit_b1'))
    def_vit_b2 = bool(request.form.get('def_vit_b2'))
    def_vit_b6 = bool(request.form.get('def_vit_b6'))
    def_vit_b12 = bool(request.form.get('def_vit_b12'))

    def_iron = bool(request.form.get('def_iron'))
    def_calcium = bool(request.form.get('def_calcium'))
    def_magnesium = bool(request.form.get('def_magnesium'))
    def_zinc = bool(request.form.get('def_zinc'))

    disliked_product_ids = request.form.getlist('dislikes')

    try:
        user_details = UserDetails.query.filter_by(user_id=user_id).first()

        if user_details:
            user_details.sex = sex
            user_details.age = age
            user_details.weight = weight
            user_details.height = height
            user_details.activity_level = activity_level

            user_details.def_vit_a = def_vit_a
            user_details.def_vit_c = def_vit_c
            user_details.def_vit_d = def_vit_d
            user_details.def_vit_e = def_vit_e
            user_details.def_vit_k = def_vit_k

            user_details.def_vit_b1 = def_vit_b1
            user_details.def_vit_b2 = def_vit_b2
            user_details.def_vit_b6 = def_vit_b6
            user_details.def_vit_b12 = def_vit_b12

            user_details.def_iron = def_iron
            user_details.def_calcium = def_calcium
            user_details.def_magnesium = def_magnesium
            user_details.def_zinc = def_zinc

        else:
            new_details = UserDetails(
                user_id=user_id,
                sex=sex,
                age=age,
                weight=weight,
                height=height,
                activity_level=activity_level,
                def_vit_a=def_vit_a,
                def_vit_c=def_vit_c,
                def_vit_d=def_vit_d,
                def_vit_e=def_vit_e,
                def_vit_k=def_vit_k,
                def_vit_b1=def_vit_b1,
                def_vit_b2=def_vit_b2,
                def_vit_b6=def_vit_b6,
                def_vit_b12=def_vit_b12,
                def_iron=def_iron,
                def_calcium=def_calcium,
                def_magnesium=def_magnesium,
                def_zinc=def_zinc
            )

            db.session.add(new_details)

        UserDislike.query.filter_by(user_id=user_id).delete()

        for p_id in disliked_product_ids:
            new_dislike = UserDislike(
                user_id=user_id,
                product_id=int(p_id)
            )
            db.session.add(new_dislike)

        db.session.commit()
        flash("Параметри успішно збережено!", "success")

    except Exception as e:
        db.session.rollback()
        print(f"Database Error in update_profile: {e}")
        flash("Виникла помилка при збереженні даних.", "error")
        session.pop('saved_menu', None)

    return redirect(url_for('auth.dashboard'))

@auth_bp.route('/regenerate-meal', methods=['POST'])
def regenerate_meal():

    data = request.get_json()

    meal_type = data.get("meal_type")

    session['regenerated_meal'] = meal_type

    return jsonify({
        "success": True
    })

@auth_bp.route("/chat", methods=["POST"])
def chat():

    if "user_id" not in session:
        return jsonify({
            "reply": "Користувач не авторизований."
        })

    user_id = session["user_id"]

    user_details = UserDetails.query.get(user_id)

    data = request.get_json()

    user_message = data.get("message")

    dislikes = []

    user_dislikes = UserDislike.query.filter_by(user_id=user_id).all()

    for dislike in user_dislikes:

        product = Product.query.get(dislike.product_id)

        if product:
            dislikes.append(product.name)

    deficiencies = []

    if user_details.def_vit_d:
        deficiencies.append("vitamin D")

    if user_details.def_iron:
        deficiencies.append("iron")

    if user_details.def_magnesium:
        deficiencies.append("magnesium")

    if user_details.def_zinc:
        deficiencies.append("zinc")

    if user_details.def_vit_b12:
        deficiencies.append("vitamin B12")

    system_prompt = f"""
    You are an AI nutrition assistant.

    User deficiencies:
    {', '.join(deficiencies)}

    User disliked products:
    {', '.join(dislikes)}

    Give short, useful, personalized nutrition advice.
    """
    client = OpenAI(
        api_key=os.getenv("OPENAI_API_KEY")
    )

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": user_message
            }
        ]
    )

    reply = response.choices[0].message.content

    return jsonify({
        "reply": reply
    })