# Быстрый запуск «Морозко» (RU)

Ниже два варианта: с установленным Python и без Python (через Docker).

## Вариант A — локально с Python

1. Установи **Python 3.11+** с https://www.python.org/downloads/  
   Во время установки поставь галочку **Add Python to PATH**.

2. Открой терминал в папке проекта и выполни:

```bash
python -m venv .venv
# Linux/macOS
source .venv/bin/activate
# Windows PowerShell
# .\.venv\Scripts\Activate.ps1

pip install --upgrade pip
pip install -e .
cp .env.example .env
```

3. Открой `.env` и заполни:
- `TELEGRAM_BOT_TOKEN`
- `BITRIX_WEBHOOK_BASE`
- `MOROZKO_EXCEL_PATH`
- `BOT_ADMIN_IDS`

4. Положи Excel-файл по пути `MOROZKO_EXCEL_PATH`.

5. Запуск:

```bash
python -m morozko_bot.bot
```

## Вариант B — без локального Python (через Docker)

Требуется Docker Desktop.

```bash
docker build -t morozko-bot .
docker run --rm -it --env-file .env -v $(pwd)/data:/app/data morozko-bot
```

> Для Windows PowerShell вместо `$(pwd)` используй `${PWD}`.

## Готовый архив

Собрать переносимый архив:

```bash
bash scripts/build_ready_bundle.sh
```

Архив будет в `dist/Morozko_ready_package.zip`.
