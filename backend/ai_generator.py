import os
import json
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


def generate_ai_dishes(products, goal, dislikes):

    client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY")
        )

    prompt = f"""
    Створи 3 корисні страви ВИКЛЮЧНО з цих продуктів:

    {', '.join(products)}
    НЕ використовуй ці продукти:
    {', '.join(dislikes)}

    ВАЖЛИВО:
    - використовуй ТІЛЬКИ продукти зі списку
    - не додавай інших інгредієнтів
    - для кожного інгредієнта вкажи грами
    - додай короткий рецепт
    - поверни ТІЛЬКИ JSON
    - без пояснень
    - без markdown
    - без тексту поза JSON

    Формат:

    [
    {{
        "name": "Назва страви",

        "ingredients": [
            {{
                "name": "Куряче філе",
                "grams": 150
            }},
            {{
                "name": "Броколі",
                "grams": 80
            }}
        ],

        "recipe": "Короткий рецепт приготування",
    }}
    ]

    Ціль:
    {goal}
    """

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    content = response.choices[0].message.content

    content = content.replace("```json", "")
    content = content.replace("```", "")
    content = content.strip()

    try:
        return json.loads(content)

    except Exception as e:

        print("ПОМИЛКА JSON:")
        print(content)

        raise e

