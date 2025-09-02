# Используем официальный Python
FROM python:3.11-slim

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
