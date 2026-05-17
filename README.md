# VitaminApp

Веб-застосунок для персоналізованого підбору харчування з використанням Flask, MySQL та OpenAI API.

---

# Опис проєкту

VitaminApp — це система рекомендації харчування, яка допомагає користувачам формувати персоналізоване меню на основі:

- добової потреби у калоріях
- білків, жирів та вуглеводів
- дефіцитів вітамінів та мікроелементів
- небажаних продуктів
- AI-рекомендацій страв

Система автоматично розраховує нутрієнти та генерує меню з урахуванням потреб користувача.

---

# Основні можливості

- реєстрація та авторизація користувачів
- персональні рекомендації харчування
- AI генерація страв
- AI чат-асистент з порадами щодо харчування
- автоматичний підбір меню під дефіцити вітамінів
- фільтрація небажаних продуктів
- підрахунок калорій та БЖВ
- автоматичне тестування за допомогою pytest
- CI/CD через GitHub Actions

---

# Використані технології

## Backend
- Python
- Flask
- SQLAlchemy
- MySQL
- pytest
- Flask-Migrate

## Frontend
- HTML
- CSS
- JavaScript

## AI інтеграція
- OpenAI API

## Автоматизоване тестування та CI/CD
- pytest
- GitHub Actions
- SQLite (для CI тестування)

---

# Запуск проєкту

## 1. Клонування репозиторію

```bash
git clone https://github.com/MartaKarpiak/VitaminApp.git
```

## 2. Перехід у папку проєкту

```bash
cd VitaminApp
```

## 3. Створення та активація віртуального середовища

```bash
python -m venv venv
venv\Scripts\activate
```

## 4. Встановлення необхідних бібліотек

```bash
pip install -r requirements.txt
```

## 5. Створення файлу .env

У корені проєкту необхідно створити файл .env з такими параметрами:
DB_USER=root
DB_PASSWORD=your_password
DB_HOST=localhost
DB_NAME=vitamin_db

SECRET_KEY=your_secret_key

OPENAI_API_KEY=your_openai_api_key

MAIL_USERNAME=your_email
MAIL_PASSWORD=your_password

## 6. Ініціалізація бази даних

```bash
python init_db.py
```

## 7. Запуск веб-застосунку

```bash
python app.py
```