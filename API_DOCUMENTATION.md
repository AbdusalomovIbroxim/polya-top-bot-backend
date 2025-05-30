# API Documentation - Playground Booking System

## Содержание
1. [Общая информация](#общая-информация)
2. [Аутентификация](#аутентификация)
3. [Пользователи](#пользователи)
4. [Игровые поля](#игровые-поля)
5. [Бронирования](#бронирования)
6. [Избранное](#избранное)

## Общая информация

### Базовый URL
```
http://your-domain.com/api/
```

### Форматы данных
- Все даты и время: `YYYY-MM-DD HH:MM:SS`
- Цены: десятичные числа с двумя знаками после запятой
- Изображения: `multipart/form-data`
- JSON для всех остальных данных

### Заголовки
```http
Content-Type: application/json
Authorization: Bearer <token>  # где <token> - JWT токен
```

### Пагинация
Все списки поддерживают пагинацию:
- `page`: номер страницы (по умолчанию 1)
- `page_size`: количество элементов на странице (по умолчанию 10, максимум 100)

### Роли пользователей
- `USER`: обычный пользователь
- `SELLER`: владелец полей
- `ADMIN`: администратор системы

## Аутентификация

### Регистрация
```http
POST /api/users/
```
Создает нового пользователя.

**Тело запроса:**
```json
{
    "username": "string",     // уникальное имя пользователя
    "email": "string",        // email
    "password": "string",     // пароль
    "role": "USER"           // роль (USER, SELLER, ADMIN)
}
```

### Вход
```http
POST /api/token/
```
Получение JWT токенов.

**Тело запроса:**
```json
{
    "username": "string",
    "password": "string"
}
```

**Ответ:**
```json
{
    "access": "string",   // токен для доступа
    "refresh": "string"   // токен для обновления
}
```

### Обновление токена
```http
POST /api/token/refresh/
```
Получение нового access токена.

**Тело запроса:**
```json
{
    "refresh": "string"  // refresh токен
}
```

## Пользователи

### Получение профиля
```http
GET /api/users/me/
```
Получение данных текущего пользователя.

### Обновление профиля
```http
PATCH /api/users/update_me/
```
Обновление данных пользователя.

**Тело запроса:**
```json
{
    "first_name": "string",
    "last_name": "string",
    "phone": "string",
    "address": "string"
}
```

## Игровые поля

### Получение списка полей
```http
GET /api/playgrounds/
```

**Параметры фильтрации:**
- `city`: фильтр по городу
- `type`: тип поля (FOOTBALL, BASKETBALL, TENNIS, VOLLEYBALL, OTHER)
- `min_price`: минимальная цена
- `max_price`: максимальная цена
- `company`: ID компании

### Создание поля (SELLER)
```http
POST /api/playgrounds/
```

**Тело запроса:**
```json
{
    "name": "string",
    "description": "string",
    "price_per_hour": "decimal",
    "city": "string",
    "address": "string",
    "type": "string",
    "deposit_amount": "decimal",
    "images": ["file1", "file2"]  // изображения
}
```

### Проверка доступности
```http
GET /api/playgrounds/{id}/check_availability/
```

**Параметры:**
- `date`: дата для проверки (YYYY-MM-DD)

**Ответ:**
```json
{
    "date": "2024-03-20",
    "working_hours": {
        "start": "08:00",
        "end": "22:30"
    },
    "time_points": [
        {
            "time": "08:00",
            "is_available": true
        }
    ]
}
```

## Бронирования

### Создание бронирования
```http
POST /api/bookings/
```

**Тело запроса:**
```json
{
    "playground": "integer",
    "start_time": "datetime",
    "end_time": "datetime"
}
```

**Важно:**
- Время должно быть кратно 30 минутам
- Рабочие часы: 8:00 - 22:30
- Максимальная длительность: 24 часа
- Нельзя бронировать прошедшее время
- Нельзя бронировать занятое время

### Получение списка бронирований
```http
GET /api/bookings/
```

**Параметры фильтрации:**
- `start_date`: дата начала
- `end_date`: дата окончания
- `status`: статус (PENDING, CONFIRMED, CANCELLED, COMPLETED)
- `playground`: ID поля
- `user`: ID пользователя

### Подтверждение бронирования (SELLER/ADMIN)
```http
POST /api/bookings/{id}/confirm/
```

### Отмена бронирования
```http
POST /api/bookings/{id}/cancel/
```

## Избранное

### Добавление в избранное
```http
POST /api/favorites/
```

**Тело запроса:**
```json
{
    "playground": "integer"  // ID поля
}
```

### Получение избранного
```http
GET /api/favorites/
```

### Удаление из избранного
```http
DELETE /api/favorites/{id}/
```

## Коды ошибок

### 400 Bad Request
Некорректные данные в запросе
```json
{
    "detail": "string",
    "field_name": ["string"]
}
```

### 401 Unauthorized
Требуется аутентификация
```json
{
    "detail": "Authentication credentials were not provided."
}
```

### 403 Forbidden
Нет прав на действие
```json
{
    "detail": "У вас нет прав на выполнение этого действия"
}
```

### 404 Not Found
Ресурс не найден
```json
{
    "detail": "Not found."
}
```

## Примеры использования

### Пример создания бронирования
```javascript
// Получение токена
const response = await fetch('/api/token/', {
    method: 'POST',
    body: JSON.stringify({
        username: 'user',
        password: 'password'
    })
});
const { access } = await response.json();

// Создание бронирования
const booking = await fetch('/api/bookings/', {
    method: 'POST',
    headers: {
        'Authorization': `Bearer ${access}`,
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        playground: 1,
        start_time: '2024-03-20 10:00:00',
        end_time: '2024-03-20 11:00:00'
    })
});
```

### Пример загрузки изображений
```javascript
const formData = new FormData();
formData.append('name', 'Новое поле');
formData.append('price_per_hour', '1000');
formData.append('images', file1);
formData.append('images', file2);

const response = await fetch('/api/playgrounds/', {
    method: 'POST',
    headers: {
        'Authorization': `Bearer ${access}`
    },
    body: formData
});
``` 