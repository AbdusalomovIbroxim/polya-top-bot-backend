# Используем официальный Python (через зеркало Google, чтобы обойти rate limit Docker Hub)
FROM mirror.gcr.io/library/python:3.12

# Устанавливаем зависимости
RUN apt-get update && apt-get install -y gcc libpq-dev

# Создаем директорию
WORKDIR /app

# Копируем зависимости
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Копируем проект
COPY . /app/

# Запускаем через gunicorn
CMD ["gunicorn", "djangoProject.wsgi:application", "--bind", "0.0.0.0:8000"]
