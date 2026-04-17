FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml README.md README_SETUP_RU.md .
COPY morozko_bot ./morozko_bot
COPY .env.example .

RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir .

CMD ["python", "-m", "morozko_bot.bot"]
