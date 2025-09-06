from django.apps import AppConfig


class PlaygroundsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'playgrounds'

    def ready(self):
        from django.db.models.signals import post_migrate
        from .models import Region, SportVenueType, SportVenue
        def fill_test_data(sender, **kwargs):
            Region.ensure_test_regions()
            SportVenueType.ensure_test_types()
        post_migrate.connect(fill_test_data, sender=self)
