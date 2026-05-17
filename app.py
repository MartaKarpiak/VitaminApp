import os
from flask import Flask, render_template, session, request, redirect, url_for, flash
from dotenv import load_dotenv
from backend.models import db, User, UserDetails
from backend.models import db
from backend.auth import auth_bp
from backend.algorithm import calculate_ai_dish_nutrition
from backend.ai_generator import generate_ai_dishes
from backend.models import Product
from flask_migrate import Migrate

# 1. Завантаження .env тепер просте, бо файли лежать поруч
load_dotenv()

# 2. Ініціалізація додатку. Відносний шлях 'frontend' працює ідеально з кореня
app = Flask(__name__, template_folder='frontend')

# 3. Налаштування з'єднання з базою даних
db_user = os.getenv('DB_USER')
db_pass = os.getenv('DB_PASSWORD')
db_host = os.getenv('DB_HOST')
db_name = os.getenv('DB_NAME')

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

if os.getenv("GITHUB_ACTIONS") == "true":
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = (
        f'mysql+pymysql://{db_user}:{db_pass}@{db_host}/{db_name}'
    )

    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        "connect_args": {
            "ssl": {}
        }
    }

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate-ai-dishes')
def generate_ai_dishes_route():

    products = [
        "Куряче філе",
        "Рис бурий",
        "Броколі",
        "Яйце куряче"
    ]

    goal = "high protein and vitamin D"

    ai_dishes = generate_ai_dishes(products, goal)

    all_products = Product.query.all()

    calculated_dishes = []

    for dish in ai_dishes:

        nutrition = calculate_ai_dish_nutrition(
            dish,
            all_products
        )

        calculated_dishes.append(nutrition)

    return render_template(
        'ai_dishes.html',
        dishes=calculated_dishes
    )


# 4. Прив'язка бази даних до нашого Flask-додатку
db.init_app(app)
migrate = Migrate(app, db)

# 5. Реєстрація Blueprint (підключення маршрутів з auth.py)
app.register_blueprint(auth_bp)

# 6. Створення таблиць у базі (якщо їх ще немає)
with app.app_context():
    db.create_all()


if __name__ == '__main__':
    # Запуск сервера
    app.run(debug=True)
