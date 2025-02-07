
from django.urls import path
from .views import niveles_view, matriculas_parvulo_view

urlpatterns = [
        path('niveles/', niveles_view, name='niveles'),
        path('niveles/parvulo_matricula/', matriculas_parvulo_view, name='parvulo-matricula')

]