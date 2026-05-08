from flask_sqlalchemy import SQLAlchemy

# Ініціалізуємо порожній об'єкт БД. 
# Ми підключимо його до Flask пізніше в app.py
db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

class PasswordReset(db.Model):
    __tablename__ = 'password_resets'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    code = db.Column(db.String(6), nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    failed_attempts = db.Column(db.Integer, default=0)

    # Зв'язок для зручного доступу до об'єкта User
    user = db.relationship('User', backref=db.backref('reset_requests', lazy=True))

class UserDetails(db.Model):
    __tablename__ = 'user_details'

    # id користувача; одночасно є primary key і зв'язком з таблицею users
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), primary_key=True)

    # фізичні параметри користувача для розрахунку калорійності раціону
    weight = db.Column(db.Float, nullable=False)
    height = db.Column(db.Float, nullable=False)
    age = db.Column(db.Integer, nullable=False)
    sex = db.Column(db.Enum('male', 'female'), nullable=False, default='male')
    activity_level = db.Column(db.Float, default=1.2)

    # дефіцити вітамінів
    def_vit_a = db.Column(db.Boolean, default=False)
    def_vit_c = db.Column(db.Boolean, default=False)
    def_vit_d = db.Column(db.Boolean, default=False)
    def_vit_e = db.Column(db.Boolean, default=False)
    def_vit_k = db.Column(db.Boolean, default=False)
    def_vit_b1 = db.Column(db.Boolean, default=False)
    def_vit_b2 = db.Column(db.Boolean, default=False)
    def_vit_b6 = db.Column(db.Boolean, default=False)
    def_vit_b12 = db.Column(db.Boolean, default=False)

    # дефіцити мінералів
    def_iron = db.Column(db.Boolean, default=False)
    def_calcium = db.Column(db.Boolean, default=False)
    def_magnesium = db.Column(db.Boolean, default=False)
    def_zinc = db.Column(db.Boolean, default=False)

class Product(db.Model):
    __tablename__ = 'products'

    # ===== ОСНОВНЕ =====
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)

    # ===== КАЛОРІЇ І БЖВ =====
    calories_100g = db.Column(db.Float, nullable=False)
    protein_100g = db.Column(db.Float, nullable=False)
    fat_100g = db.Column(db.Float, nullable=False)
    carbs_100g = db.Column(db.Float, nullable=False)

    # ===== ВІТАМІНИ =====

    # жиророзчинні
    vit_a_mcg = db.Column(db.Float, default=0)
    vit_d_mcg = db.Column(db.Float, default=0)
    vit_e_mg = db.Column(db.Float, default=0)
    vit_k_mcg = db.Column(db.Float, default=0)

    # водорозчинні
    vit_c_mg = db.Column(db.Float, default=0)

    vit_b1_mg = db.Column(db.Float, default=0)
    vit_b2_mg = db.Column(db.Float, default=0)
    vit_b6_mg = db.Column(db.Float, default=0)
    vit_b12_mcg = db.Column(db.Float, default=0)

    # ===== МІНЕРАЛИ =====
    iron_mg = db.Column(db.Float, default=0)
    calcium_mg = db.Column(db.Float, default=0)
    magnesium_mg = db.Column(db.Float, default=0)
    zinc_mg = db.Column(db.Float, default=0)

class Dish(db.Model):
    __tablename__ = 'dishes'

    # Унікальний ідентифікатор страви
    id = db.Column(db.Integer, primary_key=True)

    # Назва готової страви
    name = db.Column(db.String(100), nullable=False)

    # Загальні калорії та БЖВ для всієї порції страви
    total_calories = db.Column(db.Float, nullable=False)
    total_protein = db.Column(db.Float, nullable=False)
    total_fat = db.Column(db.Float, nullable=False)
    total_carbs = db.Column(db.Float, nullable=False)

    # Загальна кількість вітамінів у порції страви
    vit_a_total = db.Column(db.Float, default=0)
    vit_c_total = db.Column(db.Float, default=0)
    vit_d_total = db.Column(db.Float, default=0)
    vit_e_total = db.Column(db.Float, default=0)
    vit_k_total = db.Column(db.Float, default=0)
    vit_b1_total = db.Column(db.Float, default=0)
    vit_b2_total = db.Column(db.Float, default=0)
    vit_b6_total = db.Column(db.Float, default=0)
    vit_b12_total = db.Column(db.Float, default=0)

    # Загальна кількість мінералів у порції страви
    iron_total = db.Column(db.Float, default=0)
    calcium_total = db.Column(db.Float, default=0)
    magnesium_total = db.Column(db.Float, default=0)
    zinc_total = db.Column(db.Float, default=0)

class DishIngredient(db.Model):
    __tablename__ = 'dish_ingredients'
    dish_id = db.Column(db.Integer, db.ForeignKey('dishes.id', ondelete='CASCADE'), primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id', ondelete='CASCADE'), primary_key=True)
    weight_g = db.Column(db.Float, nullable=False)

class UserDislike(db.Model):
    __tablename__ = 'user_dislikes'
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id', ondelete='CASCADE'), primary_key=True)