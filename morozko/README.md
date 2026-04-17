# Morozko Telegram Bot (MVP)

Python-бот для Telegram с Excel-driven логикой и интеграцией Bitrix24.

## Что реализовано
- Ветвящаяся анкета по `business_group`.
- Подбор сценария из `result_texts` по fit-кодам и приоритету.
- Подбор оборудования из `catalog_equipment` с сортировкой `required_class + priority_score`.
- До 4 последовательных перерасчётов в рамках одной сессии (счётчик инкрементируется при подтверждённом изменении ответа).
- Передача результата в Bitrix24 (`crm.lead.add / crm.lead.update`) через inbound webhook.
- `/reload` для перезагрузки Excel (для админов).

## Быстрый старт

Подробная русская инструкция и переносимый архив: `README_SETUP_RU.md`.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
cp .env.example .env
python -m morozko_bot.bot
```

## Excel
Обязательные листы:
- `businesses`
- `questions`
- `question_options`
- `result_texts`
- `catalog_equipment`
- `settings`

Если какие-то листы/колонки отсутствуют — бот остановится на старте с ошибкой валидации.

## Bitrix
Укажите `BITRIX_WEBHOOK_BASE` вида:
`https://<portal>.bitrix24.ru/rest/<user_id>/<webhook_code>`

В MVP используется лид-модель:
- создание: `crm.lead.add`
- обновление: `crm.lead.update`

## Тесты
```bash
pytest
```
