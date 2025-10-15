# Makefile for NASA Image Explorer

.PHONY: help setup install migrate run worker superuser clean

# ==============================================================================
#  Определение переменных
# ==============================================================================
PYTHON = python

# ==============================================================================
#  Основные команды
# ==============================================================================

# help: ## ✨ Показывает эту справку
# 	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

setup: ## 🚀 Полная настройка проекта: создает venv и устанавливает зависимости
	$(PYTHON) -m venv .venv
	@/bin/sh -c '. venv/bin/activate; pip install -r requirements.txt'

install: setup ## 📦 Псевдоним для 'setup'

migrate: ## 🗄️ Создает и применяет миграции базы данных
	$(PYTHON) manage.py makemigrations
	$(PYTHON) manage.py migrate

run: ## ▶️ Запускает Django development server на 0.0.0.0:5757
	$(PYTHON) manage.py runserver 0.0.0.0:8000

superuser: ## 👤 Создает аккаунт администратора
	$(PYTHON) manage.py createsuperuser

collectstatic: ## 🎨 Собирает статические файлы
	$(PYTHON) manage.py collectstatic --noinput

clean: ## 🧹 Удаляет временные файлы, кэш и базу данных SQLite
	find . -type f -name "*.py[co]" -delete
	find . -type d -name "__pycache__" -delete
	rm -f db.sqlite3
	rm -rf media/*
	rm -rf static/*