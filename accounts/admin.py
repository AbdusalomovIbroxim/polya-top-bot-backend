from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Role, FootballExperience, FootballFrequency, FootballFormat, FootballPosition

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    # Поля, отображаемые в списке пользователей
    list_display = (
        'id', 'username', 'telegram_id', 'email', 'phone', 'first_name', 
        'last_name', 'role', 'is_active', 'is_staff'
    )
    
    # Поля для фильтрации
    list_filter = (
        'role', 
        'is_active', 
        'is_staff', 
        'is_superuser', 
        'date_joined',
        'football_experience',
        'football_frequency',
        'football_competitions',
        # 'city'
    )
    
    # Поля для поиска
    search_fields = (
        'username', 
        'email', 
        'phone', 
        'first_name', 
        'last_name', 
        'telegram_id'
    )
    
    # Сортировка по умолчанию
    ordering = ('-date_joined',)
    
    # Группировка полей для страницы редактирования пользователя
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
    
    # Группировка полей для страницы создания нового пользователя
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

    # Управляет отображением полей в зависимости от роли пользователя
    def get_list_display(self, request):
        list_display = super().get_list_display(request)
        if not request.user.is_superuser:
            return [field for field in list_display if field not in ('is_superuser', 'is_staff')]
        return list_display

    def get_fieldsets(self, request, obj=None):
        fieldsets = super().get_fieldsets(request, obj)
        if not request.user.is_superuser:
            # Скрываем поле is_superuser для не-суперпользователей
            fieldsets = [fieldset for fieldset in fieldsets if 'is_superuser' not in fieldset[1]['fields']]
            
            # Скрываем поле is_staff для не-суперпользователей, если оно находится в том же наборе полей
            for fs in fieldsets:
                if 'is_staff' in fs[1]['fields'] and not request.user.is_superuser:
                    fs[1]['fields'] = tuple(f for f in fs[1]['fields'] if f != 'is_staff')
        return fieldsets