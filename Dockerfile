FROM python:3.11-slim

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    nginx \
    supervisor \
    && rm -rf /var/lib/apt/lists/*

# Создание рабочей директории
WORKDIR /app

# Копирование файлов зависимостей
COPY requirements.txt .

# Установка зависимостей Python
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install gunicorn

# Копирование проекта
COPY . .

# Создание директорий для статических и медиа файлов
RUN mkdir -p /app/static /app/media

# Сборка статических файлов
RUN python manage.py collectstatic --noinput

# Копирование конфигурационных файлов
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Открытие портов
EXPOSE 80

# Запуск supervisor
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]