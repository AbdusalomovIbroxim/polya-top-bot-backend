# import logging

# from django.contrib import admin
# from .models import Event, EventParticipant, Payment

# logger = logging.getLogger(__name__)


# class EventParticipantInline(admin.TabularInline):
#     model = EventParticipant
#     extra = 0
#     readonly_fields = ("user", "payment_method", "payment_status", "joined_at")
#     can_delete = True


# @admin.register(Event)
# class EventAdmin(admin.ModelAdmin):
#     list_display = ("id", "creator", "field", "game_time", "rounds", "is_private", "created_at")
#     list_filter = ("is_private", "game_time", "rounds")
#     search_fields = ("creator__username", "field__name")
#     inlines = [EventParticipantInline]
#     readonly_fields = ("location", "created_at")


# @admin.register(EventParticipant)
# class EventParticipantAdmin(admin.ModelAdmin):
#     list_display = ("id", "event", "user", "payment_method", "payment_status", "joined_at")
#     search_fields = ("user__username", "event__id")


# @admin.register(Payment)
# class PaymentAdmin(admin.ModelAdmin):
#     list_display = ("id", "event_participant", "amount", "method", "status", "created_at")
#     search_fields = ("event_participant__user__username",)

from django.contrib import admin
from .models import Booking, Transaction

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    """
    Админка для модели Booking.
    Настраивает отображение, фильтрацию и поиск броней.
    """
    # Список полей, которые будут отображаться на странице списка броней
    list_display = ('user', 'stadium', 'start_time', 'end_time', 'amount', 'status', 'payment_method', 'created_at')
    
    # Поля, по которым можно фильтровать брони
    list_filter = ('status', 'payment_method', 'stadium', 'start_time')
    
    # Поля для поиска
    search_fields = ('user__username', 'stadium__name', 'status')
    
    # Поля, доступные только для чтения в форме редактирования
    readonly_fields = ('created_at',)
    
    # Группировка полей в форме редактирования
    fieldsets = (
        (None, {
            'fields': ('user', 'stadium', 'amount', 'status', 'payment_method')
        }),
        ('Временные данные', {
            'fields': ('start_time', 'end_time', 'created_at')
        }),
    )

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    """
    Админка для модели Transaction.
    Настраивает отображение, фильтрацию и поиск транзакций.
    """
    # Список полей для отображения
    list_display = ('id', 'booking', 'user', 'provider', 'amount', 'status', 'created_at')
    
    # Поля для фильтрации
    list_filter = ('status', 'provider', 'created_at')
    
    # Поля для поиска
    search_fields = ('booking__id', 'user__username', 'provider')
    
    # Поля, доступные только для чтения
    readonly_fields = ('created_at', 'updated_at')