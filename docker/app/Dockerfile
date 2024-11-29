FROM python:3.12-slim

COPY pyproject.toml poetry.lock /opt/app/

WORKDIR /opt/app

# Устанавливаем Poetry
RUN pip install --no-cache-dir poetry==1.8.3

# Настройка Poetry для использования глобального окружения (без создания виртуального окружения)
RUN poetry config virtualenvs.create false

# Устанавливаем зависимости проекта
RUN poetry install

VOLUME ["/opt/app"]
EXPOSE 8000
