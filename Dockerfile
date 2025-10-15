# Используем официальный Python через зеркало Google
FROM mirror.gcr.io/library/python:3.12

# Устанавливаем рабочую директорию
WORKDIR /app

COPY requirements.txt /app/

RUN ls -n /app/

# Устанавливаем системные зависимости и gettext
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    gettext \
    curl \
    wget \
    make \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь проект
COPY . /app/

# Собираем статические файлы (опционально)
# RUN python manage.py collectstatic --noinput
RUN make collectstatic

# Экспонируем порт
EXPOSE 8000

# Запуск приложения через gunicorn
CMD ["gunicorn", "djangoProject.wsgi:application", "--bind", "0.0.0.0:8000", "--log-level", "debug", "--access-logfile", "-", "--error-logfile", "-"]
# CMD ["make", "run"]