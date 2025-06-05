FROM python:3.12-slim

# Устанавливаем системные библиотеки, необходимые для работы OpenCV (cv2)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        libgl1-mesa-glx \
        libglib2.0-0 \
        libsm6 \
        libxext6 \
        libxrender1 \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml poetry.lock /opt/app/

WORKDIR /opt/app

# Устанавливаем Poetry
RUN pip install --no-cache-dir poetry==1.8.3

# Настройка Poetry для использования глобального окружения (без создания виртуального окружения)
RUN poetry config virtualenvs.create false

# Устанавливаем зависимости проекта
RUN poetry install

VOLUME ["/opt/app"]
EXPOSE 8100
