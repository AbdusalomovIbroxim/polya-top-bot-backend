from django.contrib import admin
from .models import Booking, Transaction
from django.utils import timezone
from datetime import timedelta


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    """
    Админка для модели Booking.
    Настраивает отображение, фильтрацию и поиск броней.
    """

    list_display = (
        'user',
        'stadium',
        'formatted_start',
        'formatted_end',
        'amount',
        'status',
        'payment_method',
    )
    list_filter = ('status', 'payment_method', 'stadium', 'start_time')
    search_fields = ('user__username', 'stadium__name')
    readonly_fields = ('created_at',)
    fieldsets = (
        (None, {
            'fields': ('user', 'stadium', 'amount', 'status', 'payment_method')
        }),
        ('Временные данные', {
            'fields': ('start_time', 'end_time', 'created_at')
        }),
    )

    def formatted_start(self, obj):
        return self._format_datetime(obj.start_time)
    formatted_start.short_description = "Начало"

    def formatted_end(self, obj):
        return self._format_datetime(obj.end_time)
    formatted_end.short_description = "Окончание"

    def _format_datetime(self, dt):
        """Форматирует дату: 'Сегодня, 19:00', 'Завтра, 21:30', '15.10.2025 19:00'."""
        local_dt = timezone.localtime(dt)
        now = timezone.localtime(timezone.now()).date()
        date = local_dt.date()

        if date == now:
            prefix = "Сегодня"
        elif date == now + timedelta(days=1):
            prefix = "Завтра"
        else:
            prefix = local_dt.strftime("%d.%m.%Y")

        return f"{prefix}, {local_dt.strftime('%H:%M')}"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.role == 'owner':
            qs = qs.filter(stadium__owner=request.user)
        return qs


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    """
    Админка для модели Transaction.
    Доступна только суперадминам.
    """

    list_display = ('id', 'booking', 'user', 'amount', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('booking__id', 'user__username')
    readonly_fields = ('created_at', 'updated_at')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.role == 'owner':
            qs = qs.filter(booking__stadium__owner=request.user)
        return qs

    # --- доступ только суперадминам ---
    def has_module_permission(self, request):
        """Скрывает раздел 'Транзакции' для всех, кроме суперадминов."""
        return request.user.is_superuser

    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser
