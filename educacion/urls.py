
from django.urls import path
from .views import niveles_view, matriculas_parvulo_view,estudiantes_tabla_view 
from .views import grafico_matricula_parvulo_2021, grafico_matricula_parvulo_2022
from .views import grafico_matricula_parvulo_2023, grafico_matricula_parvulo_2024 
from .views import grafico_matricula_parvulo_2020, grafico_matricula_por_ano, grafico_matricula_basica_2023
from .views import grafico_matricula_basica_2022, grafico_matricula_media_2023, grafico_matricula_media_2022
from .views import grafico_matricula_basica_2021, grafico_matricula_media_2021
from .views import grafico_matricula_basica_2020, grafico_matricula_media_2020, lista_view
from .views import lista_simce_view, grafico_resultados_simce_4, grafico_resultados_simce_2
from .views import grafico_resultados_idps22_4, grafico_resultados_idps22_2
from .views import grafico_resultados_idps23_4, grafico_resultados_idps23_2, dotacion_docente_20
from .views import dotacion_docente_21, dotacion_docente_22, dotacion_docente_23, dotacion_docente_24,lista_docentes_view
from .views import grafico_matricula_superior_2024,grafico_matricula_superior_2023,grafico_matricula_superior_2022
from .views import grafico_matricula_superior_2021,grafico_matricula_superior_2020, lista_rendimiento_view
from .views import grafico_rendimiento_20, grafico_rendimiento_21, grafico_rendimiento_22, grafico_rendimiento_23


urlpatterns = [
        path('niveles/', niveles_view, name='niveles'),
        path('niveles/lista_matriculas/', lista_view, name='lista-matriculas-view'),
        path('niveles/lista_simce/', lista_simce_view, name='lista-simce-view'),
        path('niveles/lista_docente/', lista_docentes_view, name='lista-docentes-view'),
        path('niveles/lista_rendimiento/', lista_rendimiento_view, name='lista-rendimiento-view'),
        path('niveles/parvulo_matricula/', matriculas_parvulo_view, name='parvulo-matricula'),
        path('niveles/parvulo_matricula/<str:subtema>/', estudiantes_tabla_view, name='tabla-matricula'),
        path('niveles/lista_matriculas/graficos_par_2021/', grafico_matricula_parvulo_2021, name='graficos-par-2021'),
        path('niveles/lista_matriculas/graficos_par_2022/', grafico_matricula_parvulo_2022, name='graficos-par-2022'),
        path('niveles/lista_matriculas/graficos_par_2023/', grafico_matricula_parvulo_2023, name='graficos-par-2023'),
        path('niveles/lista_matriculas/graficos_par_2024/', grafico_matricula_parvulo_2024, name='graficos-par-2024'),
        path('niveles/lista_matriculas/graficos_par_2020/', grafico_matricula_parvulo_2020, name='graficos-par-2020'),
        path('niveles/lista_matriculas/graficos_por_ano/', grafico_matricula_por_ano, name='graficos-por-ano'),
        path('niveles/lista_matriculas/graficos_bas_2023/', grafico_matricula_basica_2023, name='graficos-bas-2023'),
        path('niveles/lista_matriculas/graficos_med_2023/', grafico_matricula_media_2023, name='graficos-med-2023'),
        path('niveles/lista_matriculas/graficos_bas_2022/', grafico_matricula_basica_2022, name='graficos-bas-2022'),
        path('niveles/lista_matriculas/graficos_med_2022/', grafico_matricula_media_2022, name='graficos-med-2022'),
        path('niveles/lista_matriculas/graficos_med_2021/', grafico_matricula_media_2021, name='graficos-med-2021'),
        path('niveles/lista_matriculas/graficos_bas_2021/', grafico_matricula_basica_2021, name='graficos-bas-2021'),
        path('niveles/lista_matriculas/graficos_med_2020/', grafico_matricula_media_2020, name='graficos-med-2020'),
        path('niveles/lista_matriculas/graficos_bas_2020/', grafico_matricula_basica_2020, name='graficos-bas-2020'),
        path('niveles/lista_simce/graficos_sim_4/', grafico_resultados_simce_4, name='graficos-sim-4'),
        path('niveles/lista_simce/graficos_sim_2/', grafico_resultados_simce_2, name='graficos-sim-2'),
        path('niveles/lista_simce/graficos_idps22_4/', grafico_resultados_idps22_4, name='graficos-idps22-4'),
        path('niveles/lista_simce/graficos_idps22_2/', grafico_resultados_idps22_2, name='graficos-idps22-2'),
        path('niveles/lista_simce/graficos_idps23_4/', grafico_resultados_idps23_4, name='graficos-idps23-4'),
        path('niveles/lista_simce/graficos_idps23_2/', grafico_resultados_idps23_2, name='graficos-idps23-2'),
        path('niveles/lista_docente/graficos_doc20/', dotacion_docente_20, name='graficos-doc20'),
        path('niveles/lista_docente/graficos_doc21/', dotacion_docente_21, name='graficos-doc21'),
        path('niveles/lista_docente/graficos_doc22/', dotacion_docente_22, name='graficos-doc22'),
        path('niveles/lista_docente/graficos_doc23/', dotacion_docente_23, name='graficos-doc23'),
        path('niveles/lista_docente/graficos_doc24/', dotacion_docente_24, name='graficos-doc24'),
        path('niveles/lista_matriculas/graficos_sup_2024/', grafico_matricula_superior_2024, name='graficos-sup-24'),
        path('niveles/lista_matriculas/graficos_sup_2023/', grafico_matricula_superior_2023, name='graficos-sup-23'),
        path('niveles/lista_matriculas/graficos_sup_2022/', grafico_matricula_superior_2022, name='graficos-sup-22'),
        path('niveles/lista_matriculas/graficos_sup_2021/', grafico_matricula_superior_2021, name='graficos-sup-21'),
        path('niveles/lista_matriculas/graficos_sup_2020/', grafico_matricula_superior_2020, name='graficos-sup-20'),
        path('niveles/lista_rendimiento/graficos_ren_2020/', grafico_rendimiento_20, name='graficos-ren-20'),
        path('niveles/lista_rendimiento/graficos_ren_2021/', grafico_rendimiento_21, name='graficos-ren-21'),
        path('niveles/lista_rendimiento/graficos_ren_2022/', grafico_rendimiento_22, name='graficos-ren-22'),
        path('niveles/lista_rendimiento/graficos_ren_2023/', grafico_rendimiento_23, name='graficos-ren-23'),
]  