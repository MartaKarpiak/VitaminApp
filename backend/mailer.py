"""
Модуль інтеграції з поштовими сервісами (SMTP).

Відповідає за безпечне відправлення транзакційних електронних листів 
(наприклад, кодів відновлення пароля) користувачам системи. 
Для роботи вимагає налаштованих змінних середовища MAIL_USERNAME та MAIL_PASSWORD.
"""

import smtplib
import os
from email.message import EmailMessage

def send_reset_email(to_email: str, code: str) -> bool:
    """
    Відправляє електронний лист з кодом відновлення пароля через SMTP сервер.

    Функція використовує протокол SMTP_SSL (за замовчуванням порт 465) для 
    гарантовано зашифрованого з'єднання (End-to-End Encryption) з поштовим сервером 
    ще до етапу авторизації.

    Args:
        to_email (str): Електронна адреса отримувача.
        code (str): Згенерований 6-значний код відновлення.

    Returns:
        bool: True, якщо лист успішно відправлено поштовим сервером. 
        False, якщо виникла помилка (наприклад, невірний пароль SMTP, 
        відсутність мережі або блокування з боку провайдера).

    Environment Variables:
        MAIL_USERNAME (str): Адреса відправника (наприклад, your.app@gmail.com).
        MAIL_PASSWORD (str): App Password (Пароль додатка), згенерований в налаштуваннях Google/іншого провайдера.
        MAIL_SERVER (str, optional): Адреса SMTP сервера. За замовчуванням 'smtp.gmail.com'.
        MAIL_PORT (str, optional): Порт SMTP сервера. За замовчуванням '465'.
    """
    # Отримання конфігурації з середовища (.env)
    sender_email = os.getenv('MAIL_USERNAME')
    sender_password = os.getenv('MAIL_PASSWORD')
    smtp_server = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    smtp_port = int(os.getenv('MAIL_PORT', 465))
    
    # Формування структури та заголовків листа
    msg = EmailMessage()
    msg['Subject'] = 'Код відновлення пароля - Vitamin App'
    msg['From'] = sender_email
    msg['To'] = to_email
    
    # Тіло листа (Plain Text)
    msg.set_content(
        f"Вітаємо!\n\n"
        f"Ваш код для відновлення пароля: {code}\n\n"
        f"Цей код дійсний протягом 5 хвилин.\n"
        f"Якщо ви не робили цей запит, просто проігноруйте цей лист."
    )

    try:
        # Створення безпечного контексту та відправка
        with smtplib.SMTP_SSL(smtp_server, smtp_port) as server:
            server.login(sender_email, sender_password)
            server.send_message(msg)
        return True
        
    except Exception as e:
        # Логування помилки (ізолює падіння пошти від падіння всього веб-додатка)
        print(f"[SMTP ERROR] Не вдалося відправити лист на {to_email}: {e}")
        return False