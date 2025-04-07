.PHONY: venv install run test migrate makemigrations shell clean docker-build docker-up docker-down docker-logs docker-restart

# Создание виртуального окружения
venv:
	python3 -m venv venv
	. venv/bin/activate && pip install --upgrade pip

# Установка зависимостей
install: venv
	. venv/bin/activate && pip install -r requirements.txt

# Запуск сервера разработки
run:
	. venv/bin/activate && python manage.py runserver 0.0.0.0:8000

# Запуск тестов
test:
	. venv/bin/activate && python manage.py test

# Применение миграций
migrate:
	. venv/bin/activate && python manage.py migrate

# Создание миграций
makemigrations:
	. venv/bin/activate && python manage.py makemigrations

# Запуск shell Django
shell:
	. venv/bin/activate && python manage.py shell

# Очистка кэша и временных файлов
clean:
	find . -type d -name "__pycache__" -exec rm -r {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type f -name ".coverage" -delete
	find . -type d -name "*.egg-info" -exec rm -r {} +
	find . -type d -name "*.egg" -exec rm -r {} +
	find . -type d -name ".pytest_cache" -exec rm -r {} +
	find . -type d -name "htmlcov" -exec rm -r {} +
	rm -rf venv

# Docker команды
docker-build:
	docker-compose build

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f

docker-restart:
	docker-compose restart

# Полная установка и запуск проекта
setup: install migrate docker-build docker-up

# Полная пересборка и перезапуск
rebuild: docker-down docker-build docker-up

# Помощь
help:
	@echo "Доступные команды:"
	@echo "  make venv           - Создание виртуального окружения"
	@echo "  make install        - Установка зависимостей"
	@echo "  make run           - Запуск сервера разработки"
	@echo "  make test          - Запуск тестов"
	@echo "  make migrate       - Применение миграций"
	@echo "  make makemigrations - Создание миграций"
	@echo "  make shell         - Запуск shell Django"
	@echo "  make clean         - Очистка кэша и временных файлов"
	@echo "  make docker-build  - Сборка Docker образа"
	@echo "  make docker-up     - Запуск Docker контейнеров"
	@echo "  make docker-down   - Остановка Docker контейнеров"
	@echo "  make docker-logs   - Просмотр логов Docker"
	@echo "  make docker-restart - Перезапуск Docker контейнеров"
	@echo "  make setup         - Полная установка и запуск проекта"
	@echo "  make rebuild       - Полная пересборка и перезапуск"
	@echo "  make help          - Показать эту справку" 