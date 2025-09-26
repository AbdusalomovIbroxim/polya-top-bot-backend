from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
import logging

logger = logging.getLogger(__name__)

def custom_exception_handler(exc, context):
    """
    Глобальный обработчик ошибок DRF
    """
    # Используем стандартный handler DRF
    response = exception_handler(exc, context)

    if response is not None:
        # Добавляем стандартный вид ошибки
        return Response(
            {
                "error": True,
                "message": response.data.get("detail", "An error occurred"),
                "details": response.data,
            },
            status=response.status_code,
        )

    # Если ошибка не стандартная (например, KeyError, ValueError и т.д.)
    logger.error(f"Unhandled exception: {exc}", exc_info=True)

    return Response(
        {
            "error": True,
            "message": "Internal server error",
            "details": str(exc),
        },
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
