import logging

from django.contrib import admin
from .models import Event, EventParticipant, Payment

logger = logging.getLogger(__name__)


class EventParticipantInline(admin.TabularInline):
    model = EventParticipant
    extra = 0
    readonly_fields = ("user", "payment_method", "payment_status", "joined_at")
    can_delete = True


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ("id", "creator", "field", "game_time", "rounds", "is_private", "created_at")
    list_filter = ("is_private", "game_time", "rounds")
    search_fields = ("creator__username", "field__name")
    inlines = [EventParticipantInline]
    readonly_fields = ("location", "created_at")


@admin.register(EventParticipant)
class EventParticipantAdmin(admin.ModelAdmin):
    list_display = ("id", "event", "user", "payment_method", "payment_status", "joined_at")
    search_fields = ("user__username", "event__id")


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("id", "event_participant", "amount", "method", "status", "created_at")
    search_fields = ("event_participant__user__username",)
