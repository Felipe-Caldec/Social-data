
from django.urls import path
from .views import niveles_view, matriculas_parvulo_view,estudiantes_tabla_view 
from .views import grafico_matricula_parvulo_2021, grafico_matricula_parvulo_2022
from .views import grafico_matricula_parvulo_2023, grafico_matricula_parvulo_2024 
from .views import grafico_matricula_parvulo_2020, grafico_matricula_por_ano, grafico_matricula_basica_2023
from .views import grafico_matricula_basica_2022, grafico_matricula_media_2023, grafico_matricula_media_2022
from .views import grafico_matricula_basica_2021, grafico_matricula_media_2021
from .views import grafico_matricula_basica_2020, grafico_matricula_media_2020, lista_view
from .views import lista_simce_view, grafico_resultados_simce_4, grafico_resultados_simce_2
from .views import grafico_resultados_idps22_4

urlpatterns = [
        path('niveles/', niveles_view, name='niveles'),
        path('niveles/parvulo_matricula/', matriculas_parvulo_view, name='parvulo-matricula'),
        path('niveles/parvulo_matricula/<str:subtema>/', estudiantes_tabla_view, name='tabla-matricula'),
        path('niveles/graficos_par_2021/', grafico_matricula_parvulo_2021, name='graficos-par-2021'),
        path('niveles/graficos_par_2022/', grafico_matricula_parvulo_2022, name='graficos-par-2022'),
        path('niveles/graficos_par_2023/', grafico_matricula_parvulo_2023, name='graficos-par-2023'),
        path('niveles/graficos_par_2024/', grafico_matricula_parvulo_2024, name='graficos-par-2024'),
        path('niveles/graficos_par_2020/', grafico_matricula_parvulo_2020, name='graficos-par-2020'),
        path('niveles/graficos_por_ano/', grafico_matricula_por_ano, name='graficos-por-ano'),
        path('niveles/graficos_bas_2023/', grafico_matricula_basica_2023, name='graficos-bas-2023'),
        path('niveles/graficos_med_2023/', grafico_matricula_media_2023, name='graficos-med-2023'),
        path('niveles/graficos_bas_2022/', grafico_matricula_basica_2022, name='graficos-bas-2022'),
        path('niveles/graficos_med_2022/', grafico_matricula_media_2022, name='graficos-med-2022'),
        path('niveles/graficos_med_2021/', grafico_matricula_media_2021, name='graficos-med-2021'),
        path('niveles/graficos_bas_2021/', grafico_matricula_basica_2021, name='graficos-bas-2021'),
        path('niveles/graficos_med_2020/', grafico_matricula_media_2020, name='graficos-med-2020'),
        path('niveles/graficos_bas_2020/', grafico_matricula_basica_2020, name='graficos-bas-2020'),
        path('niveles/lista_matriculas/', lista_view, name='lista-matriculas-view'),
        path('niveles/lista_simce/', lista_simce_view, name='lista-simce-view'),
        path('niveles/graficos_sim_4/', grafico_resultados_simce_4, name='graficos-sim-4'),
        path('niveles/graficos_sim_2/', grafico_resultados_simce_2, name='graficos-sim-2'),
        path('niveles/graficos_idps22_4/', grafico_resultados_idps22_4, name='graficos-idps22-4'),
]