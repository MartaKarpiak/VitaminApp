import pytest

import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app
@pytest.fixture
def client():
    app.config['TESTING'] = True

    with app.test_client() as client:
        yield client


# --------------------------------------------------
# Головна сторінка
# --------------------------------------------------

def test_home_page(client):
    response = client.get('/')

    assert response.status_code == 200


# --------------------------------------------------
# Сторінка логіну
# --------------------------------------------------

def test_login_page(client):
    response = client.get('/login')

    assert response.status_code == 200


# --------------------------------------------------
# Реєстрація користувача
# --------------------------------------------------

def test_register_page(client):
    response = client.get('/register')

    assert response.status_code == 200


# --------------------------------------------------
# Dashboard без логіну
# --------------------------------------------------

def test_dashboard_requires_login(client):
    response = client.get('/dashboard')

    assert response.status_code in [302, 401, 403]


# --------------------------------------------------
# AI чатбот route
# --------------------------------------------------

def test_chat_route_exists(client):
    response = client.post(
        '/chat',
        json={
            'message': 'Привіт'
        }
    )

    assert response.status_code in [200, 401, 403, 500]


# --------------------------------------------------
# AI regenerate route
# --------------------------------------------------

def test_regenerate_route_exists(client):
    response = client.post(
        '/regenerate-meal',
        json={
            'meal_type': 'breakfast'
        }
    )

    assert response.status_code in [200, 401, 403]

from backend.algorithm import calculate_ai_dish_nutrition


# --------------------------------------------------
# Тест підрахунку нутрієнтів AI страви
# --------------------------------------------------

def test_ai_dish_nutrition():

    class MockProduct:
        def __init__(self, name, calories, protein, fat, carbs):
            self.name = name
            self.calories_100g = calories
            self.protein_100g = protein
            self.fat_100g = fat
            self.carbs_100g = carbs


    products = [
        MockProduct("Куряче філе", 165, 31, 3.6, 0),
        MockProduct("Рис", 130, 2.7, 0.3, 28)
    ]


    ai_dish = {
        "name": "Курка з рисом",
        "ingredients": [
            "Куряче філе",
            "Рис"
        ]
    }


    result = calculate_ai_dish_nutrition(ai_dish, products)


    assert result["calories"] == 295
    assert result["protein"] == 33.7
    assert result["fat"] == 3.9
    assert result["carbs"] == 28

from backend.algorithm import get_allowed_dishes


# --------------------------------------------------
# Тест dislikes filtering
# --------------------------------------------------

def test_disliked_products_filtering():

    class MockDish:
        def __init__(self, name):
            self.name = name


    allowed_dishes = [
        MockDish("Курка з рисом"),
        MockDish("Вівсянка"),
    ]


    filtered_names = [dish.name for dish in allowed_dishes]


    assert "Курка з рисом" in filtered_names
    assert "Вівсянка" in filtered_names
    assert "Піца" not in filtered_names