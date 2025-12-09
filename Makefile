.PHONY: help build up down restart logs clean

help: ## Mostrar esta ayuda
	@echo "Comandos disponibles:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

build: ## Construir las imágenes Docker
	docker-compose build

up: ## Iniciar todos los servicios
	docker-compose up -d

down: ## Detener todos los servicios
	docker-compose down

restart: ## Reiniciar todos los servicios
	docker-compose restart

logs: ## Ver logs de todos los servicios
	docker-compose logs -f

logs-backend: ## Ver logs del backend
	docker-compose logs -f backend

logs-frontend: ## Ver logs del frontend
	docker-compose logs -f frontend

logs-db: ## Ver logs de la base de datos
	docker-compose logs -f postgres

clean: ## Limpiar contenedores, volúmenes e imágenes
	docker-compose down -v
	docker system prune -f

ps: ## Ver estado de los servicios
	docker-compose ps

shell-backend: ## Abrir shell en el contenedor del backend
	docker-compose exec backend bash

shell-frontend: ## Abrir shell en el contenedor del frontend
	docker-compose exec frontend sh

shell-db: ## Abrir psql en la base de datos
	docker-compose exec postgres psql -U fyntra_user -d fyntra

migrate: ## Aplicar migraciones de base de datos
	docker-compose exec backend alembic upgrade head

migrate-create: ## Crear nueva migración (uso: make migrate-create MESSAGE="descripción")
	docker-compose exec backend alembic revision --autogenerate -m "$(MESSAGE)"

init-data: ## Crear datos iniciales de prueba
	docker-compose exec backend sh -c "PYTHONPATH=/app python /app/scripts/init_data.py"

test-backend: ## Ejecutar tests del backend
	docker-compose exec backend pytest

test-frontend: ## Ejecutar tests del frontend
	docker-compose exec frontend npm test

