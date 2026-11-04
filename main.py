from __future__ import annotations

import json
import os
import urllib.request
from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel, Field

load_dotenv()


class ProductCardResponse(BaseModel):
    seo_title: str = Field(description="SEO-заголовок карточки товара, строго до 70 символов")
    seo_description: str = Field(description="SEO-описание товара от 800 до 1200 символов")
    structured_specs: dict = Field(description="Список характеристик из входных данных")
    search_queries: list[str] = Field(description="3–5 поисковых запросов")
    commercial_block: str = Field(description="Краткий блок для менеджера")
    missing_data_warning: list[str] = Field(description="Список отсутствующих параметров")


def get_available_free_models() -> list[str]:
    """Автоматически получает список работающих бесплатных моделей с OpenRouter."""
    models = ["openrouter/free"]
    try:
        req = urllib.request.Request("https://openrouter.ai/api/v1/models")
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode("utf-8"))
            for item in data.get("data", []):
                model_id = item.get("id", "")
                if model_id.endswith(":free") and any(
                    k in model_id for k in ("qwen", "llama", "deepseek", "mistral", "gemma")
                ):
                    models.append(model_id)
    except Exception:
        pass
    return models[:6]


def generate_product_card(product_data: dict, free_models: list[str]) -> ProductCardResponse | None:
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("Ошибка: Не найден OPENROUTER_API_KEY в файле .env")
        return None

    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
    )

    system_instruction = (
        "Ты — профессиональный контент-менеджер и SEO-специалист B2B интернет-магазина КИПиА.\n"
        "КРИТИЧЕСКИ ВАЖНЫЕ ПРАВИЛА:\n"
        "1. Пиши СТРОГО на чистом русском языке. Запрещено переводить русские слова из названия товара на английский "
        "(например, слово 'показывающий') или вставлять иностранные (английские, арабские, китайские) слова в текст.\n"
        "2. Запрещено выдумывать технические характеристики, материалы корпуса/механизма (сталь, латунь, медь) "
        "или способы монтажа (например, DIN-рейка) как в structured_specs, так и в самом тексте seo_description, "
        "если их нет во входном JSON. Используй только факты из входных данных.\n"
        "3. В поле missing_data_warning указывай только реально отсутствующие параметры (если диапазон задан как 0–1,6 МПа, "
        "то нижний и верхний пределы уже известны).\n"
        "4. Отвечай ИСКЛЮЧИТЕЛЬНО валидным JSON-объектом без markdown-оберток."
    )

    prompt = f"""
    Сформируй черновик карточки товара на основе входных данных:
    {json.dumps(product_data, ensure_ascii=False, indent=2)}
    
    Верни строго JSON со следующими ключами:
    - seo_title (строка, до 70 символов, сохраняй точное русское название прибора)
    - seo_description (строка, 800-1200 символов, технически грамотный B2B-текст строго без выдуманных материалов и свойств)
    - structured_specs (объект с характеристиками на русском языке)
    - search_queries (массив из 3-5 поисковых фраз на русском языке)
    - commercial_block (строка: кому подходит и какие задачи решает)
    - missing_data_warning (массив строк: каких важных характеристик реально не хватает во входных данных)
    """

    for model_name in free_models:
        print(f"Запрос к модели {model_name}...")
        try:
            response = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.1,
            )

            raw_text = response.choices[0].message.content
            if not raw_text:
                continue

            clean_text = raw_text.strip()
            if clean_text.startswith("```json"):
                clean_text = clean_text[7:]
            elif clean_text.startswith("```"):
                clean_text = clean_text[3:]
            if clean_text.endswith("```"):
                clean_text = clean_text[:-3]

            result = ProductCardResponse.model_validate_json(clean_text.strip())
            print(f"Успешно сгенерировано ({model_name})!")
            return result

        except Exception as e:
            print(f"Модель {model_name} вернула ошибку: {e}. Пробуем следующую...")

    print("Не удалось получить ответ ни от одной модели.")
    return None


def main():
    print("Запуск AI-помощника подготовки товарных описаний...\n")

    if not os.path.exists("products_input.json"):
        print("Файл products_input.json не найден!")
        return

    with open("products_input.json", "r", encoding="utf-8") as f:
        try:
            products = json.load(f)
        except json.JSONDecodeError:
            print("Ошибка: products_input.json содержит некорректный JSON.")
            return

    free_models = get_available_free_models()
    results = []

    for idx, product in enumerate(products, 1):
        product_name = product.get("name", f"Товар #{idx}")
        print(f"--- Обработка товара {idx}: {product_name} ---")
        card = generate_product_card(product, free_models)

        if card:
            card_dict = card.model_dump()
            print(json.dumps(card_dict, ensure_ascii=False, indent=2))
            results.append({
                "input_name": product_name,
                "generated_card": card_dict,
            })
        else:
            print("Не удалось сгенерировать карточку для данного товара.")
        print("=" * 60 + "\n")

    if results:
        output_filename = "products_output.json"
        with open(output_filename, "w", encoding="utf-8") as out_f:
            json.dump(results, out_f, ensure_ascii=False, indent=2)
        print(f"Успешно сохранено карточек ({len(results)} шт.) в файл {output_filename}")


if __name__ == "__main__":
    main()