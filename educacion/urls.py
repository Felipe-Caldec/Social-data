
from django.urls import path
from .views import niveles_view, matriculas_parvulo_view,estudiantes_tabla_view 
from .views import grafico_matricula_parvulo_2021, grafico_matricula_parvulo_2022
from .views import grafico_matricula_parvulo_2023, grafico_matricula_parvulo_2024 
from .views import grafico_matricula_parvulo_2020, grafico_matricula_por_ano

urlpatterns = [
        path('niveles/', niveles_view, name='niveles'),
        path('niveles/parvulo_matricula/', matriculas_parvulo_view, name='parvulo-matricula'),
        path('niveles/parvulo_matricula/<str:subtema>/', estudiantes_tabla_view, name='tabla-matricula'),
        path('niveles/graficos_2021/', grafico_matricula_parvulo_2021, name='graficos-2021'),
        path('niveles/graficos_2022/', grafico_matricula_parvulo_2022, name='graficos-2022'),
        path('niveles/graficos_2023/', grafico_matricula_parvulo_2023, name='graficos-2023'),
        path('niveles/graficos_2024/', grafico_matricula_parvulo_2024, name='graficos-2024'),
        path('niveles/graficos_2020/', grafico_matricula_parvulo_2020, name='graficos-2020'),
        path('niveles/graficos_por_ano/', grafico_matricula_por_ano, name='graficos-por-ano'),

]