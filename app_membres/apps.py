from django.apps import AppConfig


class AppMembresConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app_membres'

    def ready(self):
        import app_membres.signals  

