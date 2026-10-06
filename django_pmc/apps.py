from django.apps import AppConfig


class DjangoPmcConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "django_pmc"
    verbose_name = "Django Poor Man's Cron"
