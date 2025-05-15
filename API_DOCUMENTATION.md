# API Documentation - Playground Booking System

## Содержание
1. [Аутентификация](#аутентификация)
2. [Пользователи](#пользователи)
3. [Игровые поля](#игровые-поля)
4. [Бронирования](#бронирования)
5. [Общие примечания](#общие-примечания)

## Аутентификация

### Регистрация пользователя
```http
POST /api/users/
```

**Тело запроса:**
```json
{
    "username": "string",
    "email": "string",
    "password": "string",
    "role": "USER"
}
```

**Ответ (201 Created):**
```json
{
    "id": "integer",
    "username": "string",
    "email": "string",
    "role": "string"
}
```

### Вход в систему (JWT)
```http
POST /api/token/
```

**Тело запроса:**
```json
{
    "username": "string",
    "password": "string"
}
```

**Ответ (200 OK):**
```json
{
    "access": "string",
    "refresh": "string"
}
```

### Обновление токена
```http
POST /api/token/refresh/
```

**Тело запроса:**
```json
{
    "refresh": "string"
}
```

**Ответ (200 OK):**
```json
{
    "access": "string"
}
```

### Проверка токена
```http
POST /api/token/verify/
```

**Тело запроса:**
```json
{
    "token": "string"
}
```

**Ответ (200 OK):**
```json
{}
```

## Пользователи

### Получение списка пользователей
```http
GET /api/users/
```

**Заголовки:**
```
Authorization: Bearer <token>
```

**Ответ (200 OK):**
```json
{
    "count": "integer",
    "next": "string",
    "previous": "string",
    "results": [
        {
            "id": "integer",
            "username": "string",
            "email": "string",
            "first_name": "string",
            "last_name": "string",
            "role": "string",
            "phone": "string",
            "address": "string",
            "date_joined": "datetime"
        }
    ]
}
```

### Получение информации о пользователе
```http
GET /api/users/{id}/
```

**Заголовки:**
```
Authorization: Bearer <token>
```

**Ответ (200 OK):**
```json
{
    "id": "integer",
    "username": "string",
    "email": "string",
    "first_name": "string",
    "last_name": "string",
    "role": "string",
    "phone": "string",
    "address": "string",
    "date_joined": "datetime"
}
```

### Получение текущего пользователя
```http
GET /api/users/me/
```

**Заголовки:**
```
Authorization: Bearer <token>
```

**Ответ (200 OK):**
```json
{
    "id": "integer",
    "username": "string",
    "email": "string",
    "first_name": "string",
    "last_name": "string",
    "role": "string",
    "phone": "string",
    "address": "string",
    "date_joined": "datetime"
}
```

### Обновление данных текущего пользователя
```http
PUT/PATCH /api/users/update_me/
```

**Заголовки:**
```
Authorization: Bearer <token>
```

**Тело запроса:**
```json
{
    "username": "string",
    "email": "string",
    "first_name": "string",
    "last_name": "string",
    "phone": "string",
    "address": "string"
}
```

**Ответ (200 OK):**
```json
{
    "id": "integer",
    "username": "string",
    "email": "string",
    "first_name": "string",
    "last_name": "string",
    "role": "string",
    "phone": "string",
    "address": "string",
    "date_joined": "datetime"
}
```

## Игровые поля

### Получение списка полей
```http
GET /api/playgrounds/
```

**Параметры запроса:**
- `city` - фильтр по городу
- `type` - фильтр по типу поля (FOOTBALL, BASKETBALL, TENNIS, VOLLEYBALL, OTHER)
- `min_price` - минимальная цена
- `max_price` - максимальная цена
- `company` - ID компании

**Ответ (200 OK):**
```json
{
    "count": "integer",
    "next": "string",
    "previous": "string",
    "results": [
        {
            "id": "integer",
            "name": "string",
            "description": "string",
            "price_per_hour": "decimal",
            "city": "string",
            "address": "string",
            "type": "string",
            "deposit_amount": "decimal",
            "images": [
                {
                    "id": "integer",
                    "image": "string"
                }
            ],
            "company": {
                "id": "integer",
                "username": "string",
                "email": "string"
            }
        }
    ]
}
```

### Создание поля (только для продавцов)
```http
POST /api/playgrounds/
```

**Заголовки:**
```
Authorization: Bearer <token>
Content-Type: multipart/form-data
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
    "images": ["file1", "file2"]
}
```

**Ответ (201 Created):**
```json
{
    "id": "integer",
    "name": "string",
    "description": "string",
    "price_per_hour": "decimal",
    "city": "string",
    "address": "string",
    "type": "string",
    "deposit_amount": "decimal",
    "images": [
        {
            "id": "integer",
            "image": "string"
        }
    ],
    "company": {
        "id": "integer",
        "username": "string",
        "email": "string"
    }
}
```

### Получение деталей поля
```http
GET /api/playgrounds/{id}/
```

**Ответ (200 OK):**
```json
{
    "id": "integer",
    "name": "string",
    "description": "string",
    "price_per_hour": "decimal",
    "city": "string",
    "address": "string",
    "type": "string",
    "deposit_amount": "decimal",
    "images": [
        {
            "id": "integer",
            "image": "string"
        }
    ],
    "company": {
        "id": "integer",
        "username": "string",
        "email": "string"
    }
}
```

### Обновление поля (только для владельца)
```http
PUT/PATCH /api/playgrounds/{id}/
```

**Заголовки:**
```
Authorization: Bearer <token>
Content-Type: multipart/form-data
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
    "images": ["file1", "file2"]
}
```

**Ответ (200 OK):**
```json
{
    "id": "integer",
    "name": "string",
    "description": "string",
    "price_per_hour": "decimal",
    "city": "string",
    "address": "string",
    "type": "string",
    "deposit_amount": "decimal",
    "images": [
        {
            "id": "integer",
            "image": "string"
        }
    ],
    "company": {
        "id": "integer",
        "username": "string",
        "email": "string"
    }
}
```

### Удаление поля (только для владельца)
```http
DELETE /api/playgrounds/{id}/
```

**Заголовки:**
```
Authorization: Bearer <token>
```

**Ответ (204 No Content):**
```json
{}
```

### Добавление изображения к полю (только для владельца)
```http
POST /api/playgrounds/{id}/add_image/
```

**Заголовки:**
```
Authorization: Bearer <token>
Content-Type: multipart/form-data
```

**Тело запроса:**
```json
{
    "image": "file"
}
```

**Ответ (201 Created):**
```json
{
    "id": "integer",
    "image": "string"
}
```

### Удаление изображения поля (только для владельца)
```http
DELETE /api/playgrounds/{id}/remove_image/
```

**Заголовки:**
```
Authorization: Bearer <token>
```

**Тело запроса:**
```json
{
    "image_id": "integer"
}
```

**Ответ (204 No Content):**
```json
{}
```

### Проверка доступности поля
```http
GET /api/playgrounds/{id}/check_availability/
```

**Параметры запроса:**
- `date` - дата для проверки (YYYY-MM-DD)

**Ответ (200 OK):**
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
        },
        {
            "time": "08:30",
            "is_available": true
        }
    ]
}
```

### Избранные поля

#### Получение списка избранных полей
```http
GET /api/favorites/
```

**Заголовки:**
```
Authorization: Bearer <token>
```

**Ответ (200 OK):**
```json
{
    "count": "integer",
    "next": "string",
    "previous": "string",
    "results": [
        {
            "id": "integer",
            "playground": "integer",
            "playground_details": {
                "id": "integer",
                "name": "string",
                "description": "string",
                "price_per_hour": "decimal",
                "city": "string",
                "address": "string",
                "type": "string",
                "deposit_amount": "decimal",
                "images": [
                    {
                        "id": "integer",
                        "image": "string"
                    }
                ],
                "company": {
                    "id": "integer",
                    "username": "string",
                    "email": "string"
                }
            },
            "created_at": "datetime"
        }
    ]
}
```

#### Добавление поля в избранное
```http
POST /api/favorites/
```

**Заголовки:**
```
Authorization: Bearer <token>
```

**Тело запроса:**
```json
{
    "playground": "integer"
}
```

**Ответ (201 Created):**
```json
{
    "id": "integer",
    "playground": "integer",
    "playground_details": {
        "id": "integer",
        "name": "string",
        "description": "string",
        "price_per_hour": "decimal",
        "city": "string",
        "address": "string",
        "type": "string",
        "deposit_amount": "decimal",
        "images": [
            {
                "id": "integer",
                "image": "string"
            }
        ],
        "company": {
            "id": "integer",
            "username": "string",
            "email": "string"
        }
    },
    "created_at": "datetime"
}
```

#### Удаление поля из избранного
```http
DELETE /api/favorites/{id}/
```

**Заголовки:**
```
Authorization: Bearer <token>
```

**Ответ (204 No Content):**
```json
{}
```

## Бронирования

### Получение списка бронирований
```http
GET /api/bookings/
```

**Заголовки (опционально):**
```
Authorization: Bearer <token>
```

**Параметры запроса:**
- `start_date` - дата начала (YYYY-MM-DD HH:MM:SS)
- `end_date` - дата окончания (YYYY-MM-DD HH:MM:SS)
- `status` - статус бронирования (PENDING, CONFIRMED, CANCELLED, COMPLETED)
- `playground` - ID поля
- `user` - ID пользователя

**Ответ (200 OK):**
```json
{
    "count": "integer",
    "next": "string",
    "previous": "string",
    "results": [
        {
            "id": "integer",
            "playground": "integer",
            "playground_details": {
                "id": "integer",
                "name": "string",
                "description": "string",
                "price_per_hour": "decimal",
                "city": "string",
                "address": "string",
                "type": "string",
                "deposit_amount": "decimal",
                "images": [
                    {
                        "id": "integer",
                        "image": "string"
                    }
                ]
            },
            "user": "integer",
            "user_details": {
                "id": "integer",
                "username": "string",
                "email": "string"
            },
            "start_time": "datetime",
            "end_time": "datetime",
            "status": "string",
            "payment_status": "string",
            "payment_url": "string",
            "qr_code": "string",
            "total_price": "decimal",
            "deposit_amount": "decimal",
            "created_at": "datetime",
            "updated_at": "datetime",
            "session_key": "string"
        }
    ]
}
```

### Создание бронирования
```http
POST /api/bookings/
```

**Заголовки (опционально):**
```
Authorization: Bearer <token>
```

**Тело запроса:**
```json
{
    "playground": "integer",
    "start_time": "datetime", // YYYY-MM-DD HH:MM:SS
    "end_time": "datetime"    // YYYY-MM-DD HH:MM:SS
}
```

**Важные замечания:**
- Время должно быть кратно 30 минутам
- Бронирование возможно только с 8:00 до 22:30
- Максимальная длительность бронирования - 24 часа
- Нельзя бронировать время в прошлом
- Нельзя бронировать уже забронированное время
- Для неавторизованных пользователей бронирование будет привязано к сессии
- Для авторизованных пользователей бронирование будет привязано к их аккаунту

**Ответ (201 Created):**
```json
{
    "id": "integer",
    "playground": "integer",
    "playground_details": {
        "id": "integer",
        "name": "string",
        "description": "string",
        "price_per_hour": "decimal",
        "city": "string",
        "address": "string",
        "type": "string",
        "deposit_amount": "decimal",
        "images": [
            {
                "id": "integer",
                "image": "string"
            }
        ]
    },
    "user": "integer",
    "user_details": {
        "id": "integer",
        "username": "string",
        "email": "string"
    },
    "start_time": "datetime",
    "end_time": "datetime",
    "status": "PENDING",
    "payment_status": "PENDING",
    "payment_url": "string",
    "qr_code": "string",
    "total_price": "decimal",
    "deposit_amount": "decimal",
    "created_at": "datetime",
    "updated_at": "datetime",
    "session_key": "string"
}
```

### Подтверждение бронирования (для продавцов и админов)
```http
POST /api/bookings/{id}/confirm/
```

**Заголовки:**
```
Authorization: Bearer <token>
```

**Ответ (200 OK):**
```json
{
    "id": "integer",
    "status": "CONFIRMED",
    // ... остальные поля бронирования
}
```

### Отмена бронирования
```http
POST /api/bookings/{id}/cancel/
```

**Заголовки (опционально):**
```
Authorization: Bearer <token>
```

**Ответ (200 OK):**
```json
{
    "id": "integer",
    "status": "CANCELLED",
    // ... остальные поля бронирования
}
```

## Общие примечания

### Аутентификация
1. Большинство эндпоинтов требуют аутентификации через JWT токен
2. Токен нужно передавать в заголовке `Authorization: Bearer <token>`
3. Некоторые эндпоинты (просмотр полей, проверка доступности) доступны без аутентификации
4. Создание бронирования доступно как авторизованным, так и неавторизованным пользователям

### Форматы данных
1. Все даты и время передаются в формате ISO 8601 (YYYY-MM-DD HH:MM:SS)
2. Время работы полей: с 8:00 до 22:30
3. Все цены передаются в виде десятичных чисел с двумя знаками после запятой
4. Изображения передаются как multipart/form-data

### Бронирования
1. Слоты разбиты по 30 минут
2. Нельзя бронировать время в прошлом
3. Нельзя бронировать уже забронированное время
4. Максимальная длительность бронирования - 24 часа
5. Бронирования неавторизованных пользователей привязываются к сессии
6. Бронирования авторизованных пользователей привязываются к их аккаунту

### Пагинация
1. Пагинация включена по умолчанию (10 элементов на страницу)
2. Можно изменить количество элементов через параметр `page_size`
3. Максимальный размер страницы - 100 элементов

### Роли пользователей
1. `USER` - обычный пользователь
2. `SELLER` - продавец (владелец полей)
3. `ADMIN` - администратор системы

### Ограничения
1. Продавцы могут управлять только своими полями
2. Админы имеют доступ ко всем данным
3. Пользователи видят только свои бронирования
4. Неавторизованные пользователи видят только свои бронирования по сессии

## Коды ошибок

### 400 Bad Request
```json
{
    "detail": "string",
    "field_name": ["string"]
}
```

### 401 Unauthorized
```json
{
    "detail": "Authentication credentials were not provided."
}
```

### 403 Forbidden
```json
{
    "detail": "У вас нет прав на выполнение этого действия"
}
```

### 404 Not Found
```json
{
    "detail": "Not found."
}
``` 