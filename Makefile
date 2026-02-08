.PHONY: help build up down restart logs clean start

help: ## Mostrar esta ayuda
	@echo "Comandos disponibles:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

build: ## Construir las imágenes Docker
	docker-compose build

up: ## Iniciar todos los servicios
	docker-compose up -d

start: build up ## Arrancar todo desde cero (tras make clean): build + up. Luego: make init-data y abrir http://localhost
	@echo "Servicios iniciados. Espera a que estén listos (make ps) y ejecuta: make init-data"
	@echo "Abre en el navegador: http://localhost  (no uses el puerto 4200 directamente)"

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

frontend-local: ## Detener contenedores y levantar solo el frontend en Docker (conectado a backend en Render)
	@echo "Deteniendo contenedores Docker..."
	docker-compose down
	@echo "Levantando frontend en Docker..."
	@echo "El frontend se conectará a: https://fyntra-backend-6yvt.onrender.com/api"
	@echo "Abre en el navegador: http://localhost:4200"
	@echo "Nota: El frontend en Docker no necesita postgres ni redis (usa backend en Render)"
	docker-compose up -d --no-deps frontend || docker-compose up -d frontend
	docker-compose logs -f frontend

frontend-local-npm: ## Levantar frontend localmente con npm (requiere Node.js instalado)
	@echo "Deteniendo contenedores Docker..."
	docker-compose down
	@echo "Verificando Node.js/npm..."
	@if ! command -v npm > /dev/null 2>&1; then \
		echo "❌ Error: npm no encontrado."; \
		echo ""; \
		echo "Para instalar Node.js, ejecuta:"; \
		echo "  brew install node"; \
		echo ""; \
		echo "O visita: https://nodejs.org/"; \
		echo ""; \
		echo "Alternativamente, usa: make frontend-local (usa Docker)"; \
		exit 1; \
	fi
	@echo "✅ Node.js/npm encontrado"
	@echo "Levantando frontend localmente..."
	@echo "El frontend se conectará a: https://fyntra-backend-6yvt.onrender.com/api"
	@echo "Abre en el navegador: http://localhost:4200"
	cd frontend && npm start

frontend-local-prod: ## Levantar frontend localmente usando configuración de producción (backend en Render)
	@echo "Deteniendo contenedores Docker..."
	docker-compose down
	@echo "Levantando frontend localmente con configuración de producción..."
	@echo "El frontend se conectará a: https://fyntra-backend-6yvt.onrender.com/api"
	@echo "Abre en el navegador: http://localhost:4200"
	cd frontend && npm start -- --configuration=production
