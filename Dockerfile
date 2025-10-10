# Используем официальный Python через зеркало Google
FROM mirror.gcr.io/library/python:3.12

# Устанавливаем системные зависимости и gettext
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    gettext \
    curl \
    wget \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем зависимости
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь проект
COPY . /app/

# Собираем статические файлы (опционально)
RUN python manage.py collectstatic --noinput

# Компилируем переводы (если они есть)
RUN python manage.py compilemessages || echo "No translations to compile yet"

# Экспонируем порт
EXPOSE 8000

# Запуск приложения через gunicorn
CMD ["gunicorn", "djangoProject.wsgi:application", "--bind", "0.0.0.0:8000"]
