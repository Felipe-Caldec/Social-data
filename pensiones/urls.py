
from django.urls import path
from .views import rentabilidad_view

urlpatterns = [
    path('rentabilidad/', rentabilidad_view, name='rentabilidad')

]