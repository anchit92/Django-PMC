from django.urls import path
from .views import alb_health_check

app_name = "django_pmc"

urlpatterns = [
    path("health/", alb_health_check, name="health_check"),
]
