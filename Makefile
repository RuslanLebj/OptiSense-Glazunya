# Параметры для docker-compose
DOCKER_COMPOSE = docker compose -f docker/docker-compose.yaml -p glazunya

up: # поднять контейнеры
	$(DOCKER_COMPOSE) up -d --force-recreate --remove-orphans || true

restart: # перезапустить контейнеры
	$(DOCKER_COMPOSE) restart

down: # остановить и удалить контейнеры
	$(DOCKER_COMPOSE) down

build: # сборка контейнеров (если нужно пересобрать)
	$(DOCKER_COMPOSE) build