from django.utils.html import format_html
from unfold.admin import ModelAdmin
from django.contrib import admin
from .models import SportVenue, SportVenueImage, SportVenueType, Region, FavoriteSportVenue


class SportVenueImageInline(admin.TabularInline):
    model = SportVenueImage
    extra = 1
    fields = ('image', 'preview_image', 'created_at')
    readonly_fields = ('preview_image', 'created_at')

    def preview_image(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="max-height:100px; border-radius:8px;"/>', obj.image.url)
        return 'Нет изображения'

    preview_image.short_description = 'Превью'


@admin.register(SportVenue)
class SportVenueAdmin(ModelAdmin):  # <— Unfold admin
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
            return format_html('<img src="{}" style="max-height:100px; border-radius:8px;"/>', obj.images.first().image.url)
        return 'Нет изображений'

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.role == 'owner':
            qs = qs.filter(owner=request.user)
        return qs


@admin.register(SportVenueType)
class SportVenueTypeAdmin(ModelAdmin):  # <— Unfold admin
    list_display = ('id', 'name', 'slug', 'created_at', 'updated_at')
    search_fields = ('name',)
    list_filter = ('created_at', 'updated_at')
    ordering = ('name',)


@admin.register(Region)
class RegionAdmin(ModelAdmin):  # <— Unfold admin
    list_display = ('id', 'name', 'slug', 'created_at', 'updated_at')
    search_fields = ('name',)
    ordering = ('id',)


# @admin.register(FavoriteSportVenue)
# class FavoriteSportVenueAdmin(ModelAdmin):  # <— Unfold admin
#     list_display = ('user', 'sport_venue', 'created_at')
#     list_filter = ('created_at',)
#     search_fields = ('user__username', 'sport_venue__name')
