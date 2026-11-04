# AI-помощник для подготовки товарных описаний (B2B КИПиА)
Локальный сервис на Python для автоматической генерации структурированных SEO-карточек промышленного оборудования (контрольно-измерительных приборов) с валидацией через Pydantic и защитой от галлюцинаций.

## Возможности
- **Строгая структура данных (Pydantic):** валидация JSON-ответа (`seo_title`, `seo_description`, `structured_specs`, `search_queries`, `commercial_block`, `missing_data_warning`).
- **Отказоустойчивость (Fallback):** автоматический подбор доступных бесплатных моделей через OpenRouter API (`openrouter/free` и резервные LLM).
- **Защита от дубликатов и потери прогресса:** проверка уже существующих товаров в `products_output.json` до отправки запроса к API и мгновенное сохранение каждой сгенерированной карточки на диск.

## Требования
- Python 3.9+
- Аккаунт на [OpenRouter](https://openrouter.ai/) и бесплатный API-ключ (`OPENROUTER_API_KEY`).

## Установка и запуск

1. Клонируйте репозиторий или распакуйте проект в рабочую директорию.
2. Создайте файл .env в корне проекта (по образцу .env.example) и укажите ваш ключ OpenRouter: 
    ```ini
    OPENROUTER_API_KEY=ваш_ключ
    ```
3. Создайте и активируйте виртуальное окружение:
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```
4. Установите зависимости:
   ```powershell
   pip install -r requirements.txt
   ```
5. Поместите входные данные в `products_input.json` и запустите скрипт:
   ```powershell
   python main.py
   ```
   Готовые карточки будут автоматически сохранены в файл `products_output.json`.

