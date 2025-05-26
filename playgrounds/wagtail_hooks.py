from wagtail.contrib.modeladmin.options import ModelAdmin, modeladmin_register
from wagtail.contrib.modeladmin.views import CreateView, EditView
from .models import Playground, PlaygroundType

class PlaygroundAdmin(ModelAdmin):
    model = Playground
    menu_label = 'Игровые поля'
    menu_icon = 'site'
    list_display = ('name', 'company', 'price_per_hour', 'type', 'city')
    list_filter = ('type', 'city', 'company')
    search_fields = ('name', 'description', 'address')
    ordering = ('name',)

class PlaygroundTypeAdmin(ModelAdmin):
    model = PlaygroundType
    menu_label = 'Типы полей'
    menu_icon = 'tag'
    list_display = ('name', 'description')
    search_fields = ('name', 'description')
    ordering = ('name',)

modeladmin_register(PlaygroundAdmin)
modeladmin_register(PlaygroundTypeAdmin) 