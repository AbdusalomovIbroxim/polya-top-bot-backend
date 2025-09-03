## Деплой и управление сервисом (Docker Compose v2)

Ниже краткие команды для запуска, остановки, обновления после `git pull`, просмотр логов и типичные действия.

### Предварительно
- На сервере установлен Docker и Docker Compose v2 (команда `docker compose`).
- Проект расположен в `/var/www/polya-top-bot-backend`.
- В `docker-compose.yml` публикация порта настроена как `80:8080` (nginx внутри слушает 8080).
- Переменная `hlz` опциональна. Если видите предупреждение — можно задать: `export hlz=prod`.

### Запуск
```bash
cd /var/www/polya-top-bot-backend
export hlz=prod   # опционально, чтобы убрать WARN
docker compose up -d
```

### Остановка
```bash
cd /var/www/polya-top-bot-backend
docker compose down
```

### Полная остановка с очисткой томов и «сирот» (редко нужно)
```bash
cd /var/www/polya-top-bot-backend
docker compose down -v --remove-orphans
```

### Обновление кода и перезапуск после `git pull`
```bash
cd /var/www/polya-top-bot-backend
git pull

# Вариант А (стандартный): пересобрать и поднять
docker compose up -d --build

# Вариант Б (если сборка из-за DNS/лимитов не нужна):
# предварительно один раз соберите вручную образ backend нужным тегом
# docker build --network=host -t polya-top-bot-backend-backend:latest .
# затем поднимайте без сборки
# docker compose up -d --no-build
```

### Миграции БД
```bash
cd /var/www/polya-top-bot-backend
docker compose exec backend python manage.py migrate
```

### Создание суперпользователя (при необходимости)
```bash
cd /var/www/polya-top-bot-backend
docker compose exec backend python manage.py createsuperuser
```

### Просмотр логов
```bash
cd /var/www/polya-top-bot-backend
# последние строки логов каждого сервиса
docker compose logs --tail=50
# только backend
docker compose logs backend --tail=100
# только nginx
docker compose logs nginx --tail=100
```

### Проверка статуса контейнеров
```bash
cd /var/www/polya-top-bot-backend
docker compose ps
```

### Траблшутинг
- Порт 80 занят:
  - Остановить системный nginx: `sudo systemctl stop nginx && sudo systemctl disable nginx`
  - Либо временно поменять публикацию порта в `docker-compose.yml` на `8080:8080` и открыть `http://SERVER_IP:8080`

- Предупреждение про переменную `hlz`:
  - Задайте перед запуском: `export hlz=prod`, или удалите её использование в `docker-compose.yml` (если она не нужна).

- Ошибка лимитов Docker Hub при сборке (429 Too Many Requests):
  - В `Dockerfile` уже используется зеркальный образ `mirror.gcr.io/library/python:3.12`.
  - Если всё равно упирается в сетевые проблемы, соберите так: `docker build --network=host -t polya-top-bot-backend-backend:latest .`, затем `docker compose up -d --no-build`.

- DNS проблемы при установке зависимостей (pip):
  - Часто решается сборкой с сетью хоста (см. пункт выше).

### Полезное
- Войти в контейнер backend:
```bash
cd /var/www/polya-top-bot-backend
docker compose exec backend bash
```
- Перезапуск только одного сервиса:
```bash
docker compose restart backend
```

Если что-то не работает — сначала смотрите логи (`docker compose logs`). Затем проверяйте миграции и подключение к БД в логах `backend`. 