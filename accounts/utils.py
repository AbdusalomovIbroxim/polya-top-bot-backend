import hmac
import hashlib
import json
import time
import logging
from urllib.parse import parse_qs

logger = logging.getLogger(__name__)

def check_telegram_auth(init_data: str, bot_token: str):
    """
    Проверяет подлинность данных инициализации (initData), полученных от Telegram Web App.

    Args:
        init_data: Строка initData, полученная из window.Telegram.WebApp.initData.
        bot_token: Токен вашего Telegram-бота.

    Returns:
        Словарь с данными пользователя и другой информацией в случае успеха,
        иначе None.
    """
    try:
        if not bot_token:
            logger.error("Токен бота (TELEGRAM_BOT_TOKEN) не предоставлен.")
            return None

        # initData представляет собой строку запроса (query string)
        parsed_data = parse_qs(init_data)
        
        if "hash" not in parsed_data:
            logger.warning("В initData отсутствует поле 'hash'.")
            return None

        # Извлекаем хэш для проверки. parse_qs возвращает список значений для каждого ключа.
        hash_from_telegram = parsed_data.pop("hash")[0]

        # Проверяем, что данные не устарели. Срок жизни - 1 час (3600 секунд).
        # Это защищает от атак повторного воспроизведения.
        auth_date = int(parsed_data.get("auth_date", [0])[0])
        if time.time() - auth_date > 3600:
            logger.warning("Данные initData устарели. Возраст: %s сек.", time.time() - auth_date)
            return None

        # Формируем строку для проверки.
        # Все пары ключ=значение, отсортированные по алфавиту, соединяются через '\n'.
        data_check_pairs = []
        for key in sorted(parsed_data.keys()):
            # Значение извлекается как первый элемент списка
            value = parsed_data[key][0]
            data_check_pairs.append(f"{key}={value}")
        
        data_check_string = "\n".join(data_check_pairs)
        logger.debug("Строка для проверки (data_check_string):\n%s", data_check_string)

        # ЭТО КЛЮЧЕВОЕ ИСПРАВЛЕНИЕ:
        # Секретный ключ вычисляется как HMAC-SHA256 от токена бота с ключом "WebAppData".
        secret_key = hmac.new("WebAppData".encode(), bot_token.encode(), hashlib.sha256).digest()
        
        # Вычисляем хэш от строки проверки с использованием секретного ключа.
        calculated_hash = hmac.new(
            secret_key, data_check_string.encode(), hashlib.sha256
        ).hexdigest()
        
        logger.debug("Хэш от Telegram: %s", hash_from_telegram)
        logger.debug("Вычисленный хэш: %s", calculated_hash)

        # Безопасно сравниваем хэши.
        if not hmac.compare_digest(calculated_hash, hash_from_telegram):
            logger.error("Проверка подписи не удалась. Хэши не совпадают.")
            return None

        logger.info("✅ Аутентификация Telegram Web App прошла успешно.")
        
        # Преобразуем данные в удобный формат и парсим JSON-поля
        result_data = {k: v[0] for k, v in parsed_data.items()}
        if "user" in result_data:
            try:
                result_data["user"] = json.loads(result_data["user"])
            except json.JSONDecodeError:
                logger.error("Не удалось декодировать JSON из поля 'user'.")
                return None
        
        return result_data

    except Exception as e:
        logger.exception("Неожиданная ошибка при проверке авторизации Telegram: %s", e)
        return None
