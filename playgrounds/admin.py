from django.contrib import admin
from django.utils.html import format_html
from .models import SportVenue, SportVenueImage, SportVenueType, Region


class SportVenueImageInline(admin.TabularInline):
    model = SportVenueImage
    extra = 1
    fields = ('image', 'preview_image', 'created_at')
    readonly_fields = ('preview_image', 'created_at')

    def preview_image(self, obj):
        if obj.image:
            return f'<img src="{obj.image.url}" style="max-height: 100px;"/>'
        return 'Нет изображения'
    preview_image.short_description = 'Предпросмотр'
    preview_image.allow_tags = True


@admin.register(SportVenue)
class SportVenueAdmin(admin.ModelAdmin):
    list_display = ('name', 'company', 'price_per_hour', 'image_preview', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at', 'price_per_hour', 'company')
    search_fields = ('name', 'description', 'company__username', 'company__email')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [SportVenueImageInline]
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'description', 'price_per_hour', 'company', 'sport_venue_type', 'deposit_amount')
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


@admin.register(SportVenueType)
class SportVenueTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at', 'updated_at')
    search_fields = ('name',)
    list_filter = ('created_at', 'updated_at')
    ordering = ('name',)


@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    list_display = ('id', 'name_ru', 'name_uz', 'name_en', 'slug', 'created_at', 'updated_at')
    search_fields = ('name_ru', 'name_uz', 'name_en', 'slug')
    ordering = ('name_ru',)
