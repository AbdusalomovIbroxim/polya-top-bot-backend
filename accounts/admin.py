from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from unfold.admin import ModelAdmin  # 🌈 важно!
from .models import User


class UnfoldUserAdmin(UserAdmin, ModelAdmin):
    """Комбинированный UserAdmin с поддержкой Unfold-стилей"""
    pass


@admin.register(User)
class CustomUserAdmin(UnfoldUserAdmin):
    list_display = (
        'username', 'phone', 'first_name', 'last_name'
    )

    search_fields = (
        'username', 'first_name', 'last_name', 'telegram_id'
    )

    ordering = ('-date_joined',)

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Персональная информация', {
            'fields': (
                'first_name', 'last_name', 'email', 'phone', 'photo',
                'telegram_id', 'language', 'city'
            ),
            'classes': ('wide',)
        }),
        ('Футбольная информация', {
            'fields': (
                'football_experience', 'football_frequency',
                'football_competitions', 'football_formats', 'football_position'
            ),
            'classes': ('wide',)
        }),
        ('Роли и разрешения', {
            'fields': ('role', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        ('Важные даты', {
            'fields': ('last_login', 'date_joined'),
            'classes': ('collapse',)
        }),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'username', 'password1', 'password2', 'role', 'telegram_id', 'first_name',
                'last_name', 'email', 'phone', 'photo', 'language', 'city',
                'football_experience', 'football_frequency', 'football_competitions',
                'football_formats', 'football_position'
            ),
        }),
    )

    def get_list_display(self, request):
        list_display = super().get_list_display(request)
        if not request.user.is_superuser:
            return [field for field in list_display if field not in ('is_superuser', 'is_staff')]
        return list_display

    def get_fieldsets(self, request, obj=None):
        fieldsets = super().get_fieldsets(request, obj)
        if not request.user.is_superuser:
            fieldsets = [fieldset for fieldset in fieldsets if 'is_superuser' not in fieldset[1]['fields']]

            for fs in fieldsets:
                if 'is_staff' in fs[1]['fields'] and not request.user.is_superuser:
                    fs[1]['fields'] = tuple(f for f in fs[1]['fields'] if f != 'is_staff')
        return fieldsets

    def has_module_permission(self, request):
        return request.user.is_superuser or getattr(request.user, 'role', None) == 'superadmin'
