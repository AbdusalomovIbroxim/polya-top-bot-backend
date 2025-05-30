from django.contrib import admin
from django.utils.html import format_html
from .models import Playground, PlaygroundImage, PlaygroundType


class PlaygroundImageInline(admin.TabularInline):
    model = PlaygroundImage
    extra = 1
    fields = ('image', 'preview_image', 'created_at')
    readonly_fields = ('preview_image', 'created_at')

    def preview_image(self, obj):
        if obj.image:
            return f'<img src="{obj.image.url}" style="max-height: 100px;"/>'
        return 'Нет изображения'
    preview_image.short_description = 'Предпросмотр'
    preview_image.allow_tags = True


@admin.register(Playground)
class PlaygroundAdmin(admin.ModelAdmin):
    list_display = ('name', 'company', 'price_per_hour', 'image_preview', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at', 'price_per_hour', 'company')
    search_fields = ('name', 'description', 'company__username', 'company__email')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [PlaygroundImageInline]
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'description', 'price_per_hour', 'company', 'type', 'deposit_amount')
        }),
        ('Локация', {
            'fields': ('city', 'address', 'latitude', 'longitude', 'yandex_map_url')
        }),
    )

    @admin.display(description='Превью')
    def image_preview(self, obj):
        if obj.images.exists():
            return format_html(
                '<img src="{}" style="max-height: 100px;"/>',
                obj.images.first().image.url
            )
        return 'Нет изображений'


@admin.register(PlaygroundType)
class PlaygroundTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'created_at', 'updated_at')
    search_fields = ('name', 'description')
    list_filter = ('created_at', 'updated_at')
    ordering = ('name',)
