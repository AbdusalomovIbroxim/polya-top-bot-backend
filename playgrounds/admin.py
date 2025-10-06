from django.contrib import admin
from django.utils.html import format_html
from .models import SportVenue, SportVenueImage, SportVenueType, Region, FavoriteSportVenue

# Inline для изображений
class SportVenueImageInline(admin.TabularInline):
    model = SportVenueImage
    extra = 1
    fields = ('image', 'preview_image', 'created_at')
    readonly_fields = ('preview_image', 'created_at')

    def preview_image(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="max-height:100px;"/>', obj.image.url)
        return 'Нет изображения'
    preview_image.short_description = 'Превью'

# Админ для площадок
@admin.register(SportVenue)
class SportVenueAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'price_per_hour', 'region', 'owner', 'image_preview', 'created_at'
    )
    list_filter = ('region', 'sport_venue_type', 'created_at', 'updated_at')
    search_fields = ('name', 'description', 'address')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [SportVenueImageInline]
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'description', 'price_per_hour', 'sport_venue_type', 'owner')
        }),
        ('Локация', {
            'fields': ('region', 'address', 'latitude', 'longitude', 'yandex_map_url')
        }),
    )

    @admin.display(description='Превью')
    def image_preview(self, obj):
        if obj.images.exists():
            return format_html('<img src="{}" style="max-height:100px;"/>', obj.images.first().image.url)
        return 'Нет изображений'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.role == 'owner':
            qs = qs.filter(owner=request.user)
        return qs

# Админ для типов площадок
@admin.register(SportVenueType)
class SportVenueTypeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'slug', 'created_at', 'updated_at')
    search_fields = ('name',)
    list_filter = ('created_at', 'updated_at')
    ordering = ('name',)

# Админ для регионов
@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'slug', 'created_at', 'updated_at')
    search_fields = ('name',)
    ordering = ('id',)

# Админ для избранного
@admin.register(FavoriteSportVenue)
class FavoriteSportVenueAdmin(admin.ModelAdmin):
    list_display = ('user', 'sport_venue', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'sport_venue__name')
