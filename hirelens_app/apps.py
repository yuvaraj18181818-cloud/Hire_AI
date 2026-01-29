from django.apps import AppConfig

class HirelensAppConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "hirelens_app"

    def ready(self):
        import hirelens_app.signals
