from datetime import timedelta
from django.db.models import Sum, Q
from django.utils.timezone import now
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from bookings.models import Booking
from playgrounds.models import Playground
from ..permissions import IsOwnerOrSuperAdmin


class DashboardView(APIView):
    """
    Дашборд владельцев и супер-админов.
    Возвращает статистику по броням, площадкам и доходу за выбранный период.
    """
    permission_classes = [IsOwnerOrSuperAdmin]

    @swagger_auto_schema(
        operation_summary="Получить статистику дашборда",
        operation_description="""
        Возвращает статистику по бронированиям, площадкам и доходу за выбранный период.

        Доступно только для владельцев площадок и супер-админов.
        """,
        manual_parameters=[
            openapi.Parameter(
                name="period",
                in_=openapi.IN_QUERY,
                description="Период выборки: day | week | month | year (по умолчанию — day)",
                type=openapi.TYPE_STRING,
                required=False,
                example="week",
            ),
        ],
        responses={
            200: openapi.Response(
                description="Успешный ответ со статистикой",
                examples={
                    "application/json": {
                        "period": "week",
                        "stats": {
                            "total_bookings": 42,
                            "change_bookings": 8,
                            "total_playgrounds": 5,
                            "total_revenue": 2450000
                        },
                        "top_fields": [
                            {"playground__name": "Стадион №1", "total_income": 1500000},
                            {"playground__name": "Стадион №2", "total_income": 950000}
                        ]
                    }
                }
            ),
            400: openapi.Response(description="Неверное значение периода"),
            403: openapi.Response(description="Доступ запрещён"),
        },
    )
    def get(self, request):
        user = request.user
        period_param = request.query_params.get("period", "day")

        # --- Определяем период ---
        period_map = {
            "day": 1,
            "week": 7,
            "month": 30,
            "year": 365,
        }

        if period_param not in period_map:
            return Response(
                {"detail": "Неверный параметр 'period'. Используйте: day, week, month или year."},
                status=status.HTTP_400_BAD_REQUEST
            )

        period_days = period_map[period_param]
        end_date = now()
        start_date = end_date - timedelta(days=period_days)
        prev_start_date = start_date - timedelta(days=period_days)
        prev_end_date = start_date

        # --- Фильтр по ролям ---
        filters = Q()
        if getattr(user, "role", None) == "owner":
            filters &= Q(playground__owner=user)

        # --- Текущий и предыдущий периоды ---
        current_bookings = Booking.objects.filter(created_at__range=(start_date, end_date)).filter(filters)
        previous_bookings = Booking.objects.filter(created_at__range=(prev_start_date, prev_end_date)).filter(filters)

        # --- Статистика ---
        total_bookings = current_bookings.count()
        prev_total_bookings = previous_bookings.count()
        change_bookings = total_bookings - prev_total_bookings

        total_playgrounds = Playground.objects.filter(is_active=True, **({"owner": user} if user.role == "owner" else {})).count()
        total_revenue = current_bookings.filter(status="paid").aggregate(sum=Sum("price"))["sum"] or 0

        top_fields = (
            current_bookings.filter(status="paid")
            .values("playground__name")
            .annotate(total_income=Sum("price"))
            .order_by("-total_income")[:5]
        )

        return Response({
            "period": period_param,
            "stats": {
                "total_bookings": total_bookings,
                "change_bookings": change_bookings,
                "total_playgrounds": total_playgrounds,
                "total_revenue": total_revenue,
            },
            "top_fields": list(top_fields),
        })
