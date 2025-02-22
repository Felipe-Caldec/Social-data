from django.urls import path
from .views import dependencia_view


urlpatterns = [
    path('dependencia/', dependencia_view, name='dependencia-salud')
]