
from django.urls import path
from .views import establecimientos_view

urlpatterns = [
        path('establecimientos/', establecimientos_view, name='establecimientos')
]