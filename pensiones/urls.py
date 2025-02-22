
from django.urls import path
from .views import rentabilidad_view,Cal_Rentabi_View, rentabilidad_fondos_view

urlpatterns = [
    path('rentabilidad/', rentabilidad_view, name='rentabilidad'),
    path('rentabilidad/calculo/', Cal_Rentabi_View, name = 'rentabi-cal'),
    path('rentabilidad/afp/', rentabilidad_fondos_view, name='fecha'),


]