from django.shortcuts import render
from .models import matricula_parvulo, matricula_basica, matricula_media, resultados_simce, resultados_simce_idps
from .models import dotacion_docente, matricula_superior, rendimiento_academico
from django.http import HttpResponse
from django.core.paginator import Paginator
from .forms import Estudiantes_filtro
from .admin import MatriculaParvuloResource
from django.db.models import Q
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from scipy.stats import chi2_contingency
import numpy as np


def niveles_view (request):
    return render (request, 'educacion/niveles.html')

def matriculas_parvulo_view (request):
    return render (request, 'educacion/matriculas.html')

def estudiantes_tabla_view(request, subtema=None):

    form = Estudiantes_filtro(request.GET)
    estudiante = matricula_parvulo.objects.all()

    # Aplicar filtro basado en el subtema seleccionado
    filtros = Q()
    
    if subtema:
        filtros &= Q(agno=subtema) # Ajusta el campo según tu modelo

    if form.is_valid():
        gen_alu = form.cleaned_data.get('gen_alu') # NOMBRAR IGUAL LAS VARIABLES EN FORM, VIEW, MODEL, INCLUYE MAYUSCULAS
        nom_reg_estab = form.cleaned_data.get('nom_reg_estab')

        if nom_reg_estab:
            filtros &= Q(nom_reg_estab=nom_reg_estab)
        if gen_alu:
            filtros &= Q(gen_alu=gen_alu)

    estudiante = estudiante.filter(filtros)

    if 'exportar' in request.GET:
        parvulo_resource = MatriculaParvuloResource()
        dataset = parvulo_resource.export(estudiante)  # Exportar solo los datos filtrados
        # dataset = parvulo_resource.export(Parvulo.objects.all()) ---Exportar todos

        response = HttpResponse(dataset.xlsx, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachment; filename="parvulos_{subtema or "filtrados"}.xlsx"'
        return response

# Crear un paginador con 50 registros por página
    paginator = Paginator(estudiante, 20)
# Obtener el número de página desde la solicitud (por defecto es la página 1)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    query_params = request.GET.urlencode()

    return render (request, 'educacion/matriculas_2024.html', {'page_obj': page_obj, 'form': form, 
                                                     'query_params': query_params,
                                                     # Codifica los parámetros para la URL
                                                     'subtema':subtema
                                                     })

def lista_view (request):
    return render (request, 'educacion/lista_matriculas.html')

def lista_simce_view (request):
    return render (request, 'educacion/lista_simce.html')

def lista_docentes_view (request):
    return render (request, 'educacion/lista_docente.html')

def lista_rendimiento_view (request):
    return render (request, 'educacion/lista_rendimiento.html')


##############################  GRAFICOS MATRICULA PARVULO  ############################################

def grafico_matricula_parvulo_2021 (request):

    categorias_genero = {
        1: "Masculino",
        2: "Femenino",
    }

    categorias_rural = {
        0:"Urbano",
        1:"Rural",
    }

    categorias_dependencia = {
        1:"Municipal",
        2:"Particular Subvencionado",
        3:"Particular Pagado",
        4:"JUNJI",
        5:"INTEGRA",
        6:"SLE",
    }

    categorias_tipo = {
        1: "Ed. Parvularia",
        4: "Ed. Espacial"
    }

    categorias_nivel = {
        1:"Sala cuna menor",
        2:"Sala cuna mayor",
        3:"Medio menor", 
        4:"Medio mayor",
        5:"Transición menor",
        6:"Transición mayor"
    }

    # Obtener la región seleccionada desde la URL (por defecto muestra todos)
    region_seleccionada = request.GET.get('nom_reg_a_estab', "RM")

    datos = matricula_parvulo.objects.filter(agno=2021, gen_alu__in= [1, 2])
    
    # Obtener datos del modelo, filtrando por región si se especifica
    if region_seleccionada:
        datos = datos.filter(nom_reg_a_estab=region_seleccionada)

    datos= datos.values('gen_alu','rural_estab','dependencia','cod_ense2_m', 'nivel1')
    df = pd.DataFrame(datos)

    df['gen_alu'] = df['gen_alu'].map(categorias_genero)
    df['rural_estab'] = df['rural_estab'].map(categorias_rural)
    df['dependencia'] = df['dependencia'].map(categorias_dependencia)
    df['cod_ense2_m'] = df['cod_ense2_m'].map(categorias_tipo)
    df['nivel1'] = df['nivel1'].map(categorias_nivel)


     # Contar cuántos hay de cada género
    conteo = df.groupby(['gen_alu','rural_estab']).size().reset_index(name='Cantidad')
    conteo.columns = ['Género','Zona','Cantidad']
    
    # Convertir "Género" a tipo string (para que no sea numérico)
    conteo['Género'] = conteo['Género'].astype(str)
    conteo['Zona'] = conteo['Zona'].astype(str)
    conteo = conteo.dropna(subset=['Zona'])

    # Calcular el total por zona para obtener porcentajes
    totales_por_zona = conteo.groupby('Género')['Cantidad'].transform('sum')
    conteo['Porcentaje'] = (conteo['Cantidad'] / totales_por_zona) * 100

# Crear la figura manualmente

    fig= go.Figure()

    for zona in conteo['Zona'].unique():
        df_filtrado = conteo[conteo['Zona'] == zona]
        if zona == 'Urbano':
            color_relleno = 'skyblue'
            color_borde = 'deepskyblue'  # Más oscuro que skyblue
        else: 
            color_relleno = 'salmon'
            color_borde = 'indianred' 
        fig.add_trace(go.Bar(
            x=df_filtrado['Género'],
            y=df_filtrado['Porcentaje'],
            name=zona,  # Esto agrupará las barras por zona
            text=df_filtrado['Porcentaje'].apply(lambda x: f"{x:.2f}%"),  # Muestra los valores en las barras
            textposition='auto',
            marker=dict(color=color_relleno,line=dict(color=color_borde, width=1.5))
        ))

    fig.update_layout(
        barmode='group', 
        title="Gráfico género según zona",
        title_font= dict(weight="bold"),
        title_x=0.5,
        yaxis=dict(title="Porcentaje", ticksuffix="%", range=[0, 100], gridcolor='lightgray',
                   zerolinecolor='lightgray'),
        xaxis_title="Género",
        plot_bgcolor='white', # fondo del grafico
        bargap=0.2, 
        bargroupgap=0.1,  
        autosize= True
    )

### **Gráfico 2: Distribución género segun dependencia**

    conteo_dependencia = df.groupby(['gen_alu','dependencia']).size().reset_index(name='Cantidad')
    conteo_dependencia.columns = ['Género','Dependencia', 'Cantidad']

# Calcular porcentaje total
    totales_por_dependencia = conteo_dependencia.groupby('Género')['Cantidad'].transform('sum')
    conteo_dependencia['Porcentaje'] = (conteo_dependencia['Cantidad'] / totales_por_dependencia) * 100

    fig2 = go.Figure()

    fig2 = make_subplots(
        rows=2, cols=1, 
        specs=[[{'type': 'domain'}], [{'type': 'domain'}]],
        subplot_titles=[
            'Distribución por dependencia - Mujeres', 
            'Distribución por dependencia - Hombres'
        ]
    )

# Filtrar por género
    generos = conteo_dependencia['Género'].unique()

    for i, genero in enumerate(generos):
        df_genero = conteo_dependencia[conteo_dependencia['Género'] == genero]
        
        fig2.add_trace(
            go.Pie(
                labels=df_genero['Dependencia'],
                values=df_genero['Cantidad'],
                name=genero,
                textinfo='percent',
                hoverinfo='percent+value'
            ),
            row=i+1, col=1
        )

    fig2.update_layout(
        title_text="Distribución por dependencia administrativa según género",
        title_font=dict(weight="bold"),
        title_x=0.5,
        showlegend=True,
        autosize=True,
        height=650,
        legend=dict(orientation="h", yanchor="bottom", y=-0.4, xanchor="center", x=0.5) 
    )

### **Gráfico 3: Distribución género segun tipo**

    conteo_tipo = df.groupby(['gen_alu','cod_ense2_m']).size().reset_index(name='Cantidad')
    conteo_tipo.columns = ['Género','Tipo', 'Cantidad']

# Calcular porcentaje total
    totales_por_tipo = conteo_tipo.groupby('Género')['Cantidad'].transform('sum')
    conteo_tipo['Porcentaje'] = (conteo_tipo['Cantidad'] / totales_por_tipo) * 100

    fig3 = go.Figure()

    for tipo in conteo_tipo['Tipo'].unique():
        df_filtrado = conteo_tipo[conteo_tipo['Tipo'] == tipo]
        if tipo == 'Ed. Parvularia':
            color_relleno = 'skyblue'
            color_borde = 'deepskyblue'  # Más oscuro que skyblue
        else: 
            color_relleno = 'salmon'
            color_borde = 'indianred'
        fig3.add_trace(go.Bar(
            x =df_filtrado['Género'],
            y = df_filtrado['Porcentaje'],
            name= tipo, 
            text=df_filtrado['Porcentaje'].apply(lambda x: f"{x:.2f}%"),
            textposition= 'auto',
            marker=dict(color=color_relleno,line=dict(color=color_borde, width=1.5))
            ))

    fig3.update_layout(
        barmode='group',
        title="Gráfico género según tipo",
        title_font= dict(weight="bold"),
        title_x=0.5,
        yaxis=dict(title="Porcentaje", range=[0, 100], ticksuffix="%", gridcolor='lightgray',
                   zerolinecolor='lightgray'),
        xaxis_title="Género",
        bargap=0.1,
        bargroupgap=0.1,
        autosize= True,
        plot_bgcolor='white'
    )

### **Gráfico 4: Distribución género segun nivel

    conteo_nivel = df.groupby(['rural_estab','nivel1']).size().reset_index(name='Cantidad')
    conteo_nivel.columns = ['Zona','Nivel', 'Cantidad']

# Calcular porcentaje total
    totales_por_nivel = conteo_nivel.groupby('Zona')['Cantidad'].transform('sum')
    conteo_nivel['Porcentaje'] = (conteo_nivel['Cantidad'] / totales_por_nivel) * 100

# Ordenar según valor ortiginal de la categoría
    conteo_nivel = conteo_nivel.sort_values(by='Nivel', key=lambda x: x.map({v: k for k, v in categorias_nivel.items()}))

    fig4 = go.Figure()

    fig4 = make_subplots(
            rows=2, cols=1, 
            specs=[[{'type': 'domain'}], [{'type': 'domain'}]],
            subplot_titles=[
                'Distribución por nivel - Urbano', 
                'Distribución por nivel - Rural'
            ]
        )

# Filtrar por género
    zonas = conteo_nivel['Zona'].unique()

    for i, nivel in enumerate(zonas):
        df_nivel = conteo_nivel[conteo_nivel['Zona'] == nivel]
        
        fig4.add_trace(
            go.Pie(
                labels=df_nivel['Nivel'],
                values=df_nivel['Cantidad'],
                name=nivel,
                textinfo='percent',
                hoverinfo='label+percent+value'
            ),
            row=i+1, col=1
        )

    fig4.update_layout(
        title_text="Distribución por nivel educativo según género",
        title_font=dict(weight="bold"),
        title_x=0.5,
        showlegend=True,
        autosize=True,
        height=650,
        legend=dict(orientation="h", yanchor="bottom", y=-0.4, # y posiciona las leyendas
                    xanchor="center", x=0.5) 
    )

    grafico_genero_zona_html = fig.to_html()
    grafico_genero_dependencia_html = fig2.to_html()
    grafico_genero_tipo_html = fig3.to_html()
    grafico_genero_nivel_html = fig4.to_html()


    # Pruebas de chi-cuadrado 
    tabla_tipo = pd.crosstab(df['gen_alu'], df['cod_ense2_m'])
    chi2_tipo, p_tipo, _, _ = chi2_contingency(tabla_tipo)

    tabla_nivel = pd.crosstab(df['rural_estab'], df['nivel1'])
    chi2_nivel, p_nivel, _, _ = chi2_contingency(tabla_nivel)

    def v_cramer (tabla_tipo):
        n = tabla_tipo.sum().sum()
        chi2_tipo, _, _, _ = chi2_contingency(tabla_tipo)
        phi2= chi2_tipo/n
        r, k = tabla_tipo.shape
        # Corregir phi2 (phi2corr) para evitar valores negativos
        phi2corr = max(0, phi2 - ((k - 1) * (r - 1)) / (n - 1))
        k_corr = k - (k - 1) * (k - 2) / (n - 1)
        r_corr = r - (r - 1) * (r - 2) / (n - 1)
        v = np.sqrt(phi2corr / min(k_corr - 1, r_corr - 1))
        
        return v
    
    v_cramer_tipo = v_cramer(tabla_tipo)
    v_cramer_nivel = v_cramer(tabla_nivel)

    return render(request, 'educacion/graficos_parvulo_2021.html', {'grafico_html': grafico_genero_zona_html,
                                                    'grafico_dependencia_html': grafico_genero_dependencia_html,
                                                    'grafico_tipo_html': grafico_genero_tipo_html,
                                                    'grafico_nivel_html':grafico_genero_nivel_html,
                                                    'chi2_tipo': round(chi2_tipo, 2),
                                                    'p_tipo': round(p_tipo, 4),
                                                    'chi2_nivel': round(chi2_nivel, 2),
                                                    'p_nivel': round(p_nivel, 4),
                                                    'v_cramer_tipo': round(v_cramer_tipo,2),
                                                    'v_cramer_nivel': round(v_cramer_nivel,2),
                                                    'region': region_seleccionada})

def grafico_matricula_parvulo_2022(request):

    categorias_genero = {
        1: "Masculino",
        2: "Femenino",
    }

    categorias_rural = {
        0:"Urbano",
        1:"Rural",
    }

    categorias_dependencia = {
        1:"Municipal",
        2:"Particular Subvencionado",
        3:"Particular Pagado",
        4:"JUNJI",
        5:"INTEGRA",
        6:"SLE",
    }

    categorias_tipo = {
        1: "Ed. Parvularia",
        4: "Ed. Espacial"
    }

    categorias_nivel = {
        1:"Sala cuna menor",
        2:"Sala cuna mayor",
        3:"Medio menor", 
        4:"Medio mayor",
        5:"Transición menor",
        6:"Transición mayor"
    }


    # Obtener la región seleccionada desde la URL (por defecto muestra todos)
    region_seleccionada = request.GET.get('nom_reg_a_estab', "RM")

    datos = matricula_parvulo.objects.filter(agno=2022, gen_alu__in= [1, 2])
    
    # Obtener datos del modelo, filtrando por región si se especifica
    if region_seleccionada:
        datos = datos.filter(nom_reg_a_estab=region_seleccionada)

    datos= datos.values('gen_alu','rural_estab','dependencia','cod_ense2_m','nivel1')
    df = pd.DataFrame(datos)

    df['gen_alu'] = df['gen_alu'].map(categorias_genero)
    df['rural_estab'] = df['rural_estab'].map(categorias_rural)
    df['dependencia'] = df['dependencia'].map(categorias_dependencia)
    df['cod_ense2_m'] = df['cod_ense2_m'].map(categorias_tipo)
    df['nivel1'] = df['nivel1'].map(categorias_nivel)


     # Contar cuántos hay de cada género
    conteo = df.groupby(['gen_alu','rural_estab']).size().reset_index(name='Cantidad')
    conteo.columns = ['Género','Zona','Cantidad']
    

    # Convertir "Género" a tipo string (para que no sea numérico)
    conteo['Género'] = conteo['Género'].astype(str)
    conteo['Zona'] = conteo['Zona'].astype(str)
    conteo = conteo.dropna(subset=['Zona'])

    # Calcular el total por zona para obtener porcentajes
    totales_por_zona = conteo.groupby('Género')['Cantidad'].transform('sum')
    conteo['Porcentaje'] = (conteo['Cantidad'] / totales_por_zona) * 100


# Crear la figura manualmente
    fig = go.Figure()

    for zona in conteo['Zona'].unique():
        df_filtrado = conteo[conteo['Zona'] == zona]
        if zona == 'Urbano':
            color_relleno = 'skyblue'
            color_borde = 'deepskyblue'  # Más oscuro que skyblue
        else: 
            color_relleno = 'salmon'
            color_borde = 'indianred' 
        fig.add_trace(go.Bar(
            x=df_filtrado['Género'],
            y=df_filtrado['Porcentaje'],
            name=zona,  # Esto agrupará las barras por zona
            text=df_filtrado['Porcentaje'].apply(lambda x: f"{x:.2f}%"),  # Muestra los valores en las barras
            textposition='auto',
            marker=dict(color=color_relleno,line=dict(color=color_borde, width=1.5))
        ))

    fig.update_layout(
        barmode='group', 
        title="Gráfico género según zona",
        title_font= dict(weight="bold"),
        title_x=0.5,
        yaxis=dict(title="Porcentaje", ticksuffix="%", range=[0, 100], gridcolor='lightgray',
                   zerolinecolor='lightgray'),
        xaxis_title="Género",
        plot_bgcolor='white', # fondo del grafico
        bargap=0.2, 
        bargroupgap=0.1,  
        autosize= True
    )
### **Gráfico 2: Distribución género segun dependencia**

    conteo_dependencia = df.groupby(['gen_alu','dependencia']).size().reset_index(name='Cantidad')
    conteo_dependencia.columns = ['Género','Dependencia', 'Cantidad']

# Calcular porcentaje total
    totales_por_dependencia = conteo_dependencia.groupby('Género')['Cantidad'].transform('sum')
    conteo_dependencia['Porcentaje'] = (conteo_dependencia['Cantidad'] / totales_por_dependencia) * 100
# Crear figura con 2 subgráficos (2 filas, 1 columna)
    fig2 = make_subplots(
        rows=2, cols=1, 
        specs=[[{'type': 'domain'}], [{'type': 'domain'}]],
        subplot_titles=[
            'Distribución por dependencia - Mujeres', 
            'Distribución por dependencia - Hombres'
        ]
    )

# Filtrar por género
    generos = conteo_dependencia['Género'].unique()

    for i, genero in enumerate(generos):
        df_genero = conteo_dependencia[conteo_dependencia['Género'] == genero]
        
        fig2.add_trace(
            go.Pie(
                labels=df_genero['Dependencia'],
                values=df_genero['Cantidad'],
                name=genero,
                textinfo='percent',
                hoverinfo='percent+value'
            ),
            row=i+1, col=1
        )

    fig2.update_layout(
        title_text="Distribución por dependencia administrativa según género",
        title_font=dict(weight="bold"),
        title_x=0.5,
        showlegend=True,
        autosize=True,
        height=650,
        legend=dict(orientation="h", yanchor="bottom", y=-0.4, xanchor="center", x=0.5) 
    )

### **Gráfico 3: Distribución género segun tipo**

    conteo_tipo = df.groupby(['gen_alu','cod_ense2_m']).size().reset_index(name='Cantidad')
    conteo_tipo.columns = ['Género','Tipo', 'Cantidad']

# Calcular porcentaje total
    totales_por_tipo = conteo_tipo.groupby('Género')['Cantidad'].transform('sum')
    conteo_tipo['Porcentaje'] = (conteo_tipo['Cantidad'] / totales_por_tipo) * 100

    fig3 = go.Figure()

    for tipo in conteo_tipo['Tipo'].unique():
        df_filtrado = conteo_tipo[conteo_tipo['Tipo'] == tipo]
        if tipo == 'Ed. Parvularia':
            color_relleno = 'skyblue'
            color_borde = 'deepskyblue'  # Más oscuro que skyblue
        else: 
            color_relleno = 'salmon'
            color_borde = 'indianred'
        fig3.add_trace(go.Bar(
            x =df_filtrado['Género'],
            y = df_filtrado['Porcentaje'],
            name= tipo, 
            text=df_filtrado['Porcentaje'].apply(lambda x: f"{x:.2f}%"),
            textposition= 'auto',
            marker=dict(color=color_relleno,line=dict(color=color_borde, width=1.5))
            ))

    fig3.update_layout(
        barmode='group',
        title="Gráfico género según tipo",
        title_font= dict(weight="bold"),
        title_x=0.5,
        yaxis=dict(title="Porcentaje", range=[0, 100], ticksuffix="%", gridcolor='lightgray',
                   zerolinecolor='lightgray'),
        xaxis_title="Género",
        bargap=0.1,
        bargroupgap=0.1,
        autosize= True,
        plot_bgcolor='white'
    )

### **Gráfico 4: Distribución género segun nivel

    conteo_nivel = df.groupby(['rural_estab','nivel1']).size().reset_index(name='Cantidad')
    conteo_nivel.columns = ['Zona','Nivel', 'Cantidad']

# Calcular porcentaje total
    totales_por_nivel = conteo_nivel.groupby('Zona')['Cantidad'].transform('sum')
    conteo_nivel['Porcentaje'] = (conteo_nivel['Cantidad'] / totales_por_nivel) * 100

    fig4 = make_subplots(
            rows=2, cols=1, 
            specs=[[{'type': 'domain'}], [{'type': 'domain'}]],
            subplot_titles=[
                'Distribución por nivel - Urbano', 
                'Distribución por nivel - Rural'
            ]
        )

# Filtrar por género
    zonas = conteo_nivel['Zona'].unique()

    for i, nivel in enumerate(zonas):
        df_nivel = conteo_nivel[conteo_nivel['Zona'] == nivel]
        
        fig4.add_trace(
            go.Pie(
                labels=df_nivel['Nivel'],
                values=df_nivel['Cantidad'],
                name=nivel,
                textinfo='percent',
                hoverinfo='label+percent+value'
            ),
            row=i+1, col=1
        )

    fig4.update_layout(
        title_text="Distribución por nivel educativo según género",
        title_font=dict(weight="bold"),
        title_x=0.5,
        showlegend=True,
        autosize=True,
        height=650,
        legend=dict(orientation="h", yanchor="bottom", y=-0.4, # y posiciona las leyendas
                    xanchor="center", x=0.5) 
    )

    grafico_genero_zona_html = fig.to_html()
    grafico_genero_dependencia_html = fig2.to_html()
    grafico_genero_tipo_html = fig3.to_html()
    grafico_genero_nivel_html = fig4.to_html()

    # Pruebas de chi-cuadrado 
    tabla_tipo = pd.crosstab(df['gen_alu'], df['cod_ense2_m'])
    chi2_tipo, p_tipo, _, _ = chi2_contingency(tabla_tipo)

    tabla_nivel = pd.crosstab(df['rural_estab'], df['nivel1'])
    chi2_nivel, p_nivel, _, _ = chi2_contingency(tabla_nivel)

    def v_cramer (tabla_tipo):
        n = tabla_tipo.sum().sum()
        chi2_tipo, _, _, _ = chi2_contingency(tabla_tipo)
        phi2= chi2_tipo/n
        r, k = tabla_tipo.shape
        # Corregir phi2 (phi2corr) para evitar valores negativos
        phi2corr = max(0, phi2 - ((k - 1) * (r - 1)) / (n - 1))
        k_corr = k - (k - 1) * (k - 2) / (n - 1)
        r_corr = r - (r - 1) * (r - 2) / (n - 1)
        v = np.sqrt(phi2corr / min(k_corr - 1, r_corr - 1))
        
        return v
    
    v_cramer_tipo = v_cramer(tabla_tipo)
    v_cramer_nivel = v_cramer(tabla_nivel)

    return render(request, 'educacion/graficos_parvulo_2022.html', {'grafico_html': grafico_genero_zona_html,
                                                    'grafico_dependencia_html': grafico_genero_dependencia_html,
                                                    'grafico_tipo_html': grafico_genero_tipo_html,
                                                    'grafico_nivel_html':grafico_genero_nivel_html,
                                                    'chi2_tipo': round(chi2_tipo, 2),
                                                    'p_tipo': round(p_tipo, 4),
                                                    'chi2_nivel': round(chi2_nivel, 2),
                                                    'p_nivel': round(p_nivel, 4),
                                                    'v_cramer_tipo': round(v_cramer_tipo,2),
                                                    'v_cramer_nivel': round(v_cramer_nivel,2),
                                                    'region': region_seleccionada})

def grafico_matricula_parvulo_2023(request):

    categorias_genero = {
        1: "Masculino",
        2: "Femenino",
    }

    categorias_rural = {
        0:"Urbano",
        1:"Rural",
    }

    categorias_dependencia = {
        1:"Municipal",
        2:"Particular Subvencionado",
        3:"Particular Pagado",
        4:"JUNJI",
        5:"INTEGRA",
        6:"SLE",
    }

    categorias_tipo = {
        1: "Ed. Parvularia",
        4: "Ed. Espacial"
    }

    categorias_nivel = {
        1:"Sala cuna menor",
        2:"Sala cuna mayor",
        3:"Medio menor", 
        4:"Medio mayor",
        5:"Transición menor",
        6:"Transición mayor"
    }

    # Obtener la región seleccionada desde la URL (por defecto muestra todos)
    region_seleccionada = request.GET.get('nom_reg_a_estab', "RM")

    datos = matricula_parvulo.objects.filter(agno=2023, gen_alu__in= [1, 2])
    
    # Obtener datos del modelo, filtrando por región si se especifica
    if region_seleccionada:
        datos = datos.filter(nom_reg_a_estab=region_seleccionada)

    datos= datos.values('gen_alu','rural_estab','dependencia','cod_ense2_m','nivel1')
    df = pd.DataFrame(datos)

    # Reemplazar los números con los nombres de género
    df['gen_alu'] = df['gen_alu'].map(categorias_genero)
    df['rural_estab'] = df['rural_estab'].map(categorias_rural)
    df['dependencia'] = df['dependencia'].map(categorias_dependencia)
    df['cod_ense2_m'] = df['cod_ense2_m'].map(categorias_tipo)
    df['nivel1'] = df['nivel1'].map(categorias_nivel)


     # Contar cuántos hay de cada género
    conteo = df.groupby(['gen_alu','rural_estab']).size().reset_index(name='Cantidad')
    conteo.columns = ['Género','Zona','Cantidad']
    
    # Convertir "Género" a tipo string (para que no sea numérico)
    conteo['Género'] = conteo['Género'].astype(str)
    conteo['Zona'] = conteo['Zona'].astype(str)
    conteo = conteo.dropna(subset=['Zona'])

    # Calcular el total por zona para obtener porcentajes
    totales_por_zona = conteo.groupby('Género')['Cantidad'].transform('sum')
    conteo['Porcentaje'] = (conteo['Cantidad'] / totales_por_zona) * 100


# Crear la figura manualmente
    fig = go.Figure()

    for zona in conteo['Zona'].unique():
        df_filtrado = conteo[conteo['Zona'] == zona]
        if zona == 'Urbano':
            color_relleno = 'skyblue'
            color_borde = 'deepskyblue'  # Más oscuro que skyblue
        else: 
            color_relleno = 'salmon'
            color_borde = 'indianred' 
        fig.add_trace(go.Bar(
            x=df_filtrado['Género'],
            y=df_filtrado['Porcentaje'],
            name=zona,  # Esto agrupará las barras por zona
            text=df_filtrado['Porcentaje'].apply(lambda x: f"{x:.2f}%"),  # Muestra los valores en las barras
            textposition='auto',
            marker=dict(color=color_relleno,line=dict(color=color_borde, width=1.5))
        ))

    fig.update_layout(
        barmode='group', 
        title="Gráfico género según zona",
        title_font= dict(weight="bold"),
        title_x=0.5,
        yaxis=dict(title="Porcentaje", ticksuffix="%", range=[0, 100], gridcolor='lightgray',
                   zerolinecolor='lightgray'),
        xaxis_title="Género",
        plot_bgcolor='white', # fondo del grafico
        bargap=0.2, 
        bargroupgap=0.1,  
        autosize= True
    )
### **Gráfico 2: Distribución género segun dependencia**

    conteo_dependencia = df.groupby(['gen_alu','dependencia']).size().reset_index(name='Cantidad')
    conteo_dependencia.columns = ['Género','Dependencia', 'Cantidad']

# Calcular porcentaje total
    totales_por_dependencia = conteo_dependencia.groupby('Género')['Cantidad'].transform('sum')
    conteo_dependencia['Porcentaje'] = (conteo_dependencia['Cantidad'] / totales_por_dependencia) * 100

    fig2 = go.Figure()

    fig2 = make_subplots(
        rows=2, cols=1, 
        specs=[[{'type': 'domain'}], [{'type': 'domain'}]],
        subplot_titles=[
            'Distribución por dependencia - Mujeres', 
            'Distribución por dependencia - Hombres'
        ]
    )

# Filtrar por género
    generos = conteo_dependencia['Género'].unique()

    for i, genero in enumerate(generos):
        df_genero = conteo_dependencia[conteo_dependencia['Género'] == genero]
        
        fig2.add_trace(
            go.Pie(
                labels=df_genero['Dependencia'],
                values=df_genero['Cantidad'],
                name=genero,
                textinfo='percent',
                hoverinfo='percent+value'
            ),
            row=i+1, col=1
        )

    fig2.update_layout(
        title_text="Distribución por dependencia administrativa según género",
        title_font=dict(weight="bold"),
        title_x=0.5,
        showlegend=True,
        autosize=True,
        height=650,
        legend=dict(orientation="h", yanchor="bottom", y=-0.4, xanchor="center", x=0.5) 
    )
### **Gráfico 3: Distribución género segun tipo**

    conteo_tipo = df.groupby(['gen_alu','cod_ense2_m']).size().reset_index(name='Cantidad')
    conteo_tipo.columns = ['Género','Tipo', 'Cantidad']

# Calcular porcentaje total
    totales_por_tipo = conteo_tipo.groupby('Género')['Cantidad'].transform('sum')
    conteo_tipo['Porcentaje'] = (conteo_tipo['Cantidad'] / totales_por_tipo) * 100

    fig3 = go.Figure()

    for tipo in conteo_tipo['Tipo'].unique():
        df_filtrado = conteo_tipo[conteo_tipo['Tipo'] == tipo]
        if tipo == 'Ed. Parvularia':
            color_relleno = 'skyblue'
            color_borde = 'deepskyblue'  # Más oscuro que skyblue
        else: 
            color_relleno = 'salmon'
            color_borde = 'indianred'
        fig3.add_trace(go.Bar(
            x =df_filtrado['Género'],
            y = df_filtrado['Porcentaje'],
            name= tipo, 
            text=df_filtrado['Porcentaje'].apply(lambda x: f"{x:.2f}%"),
            textposition= 'auto',
            marker=dict(color=color_relleno,line=dict(color=color_borde, width=1.5))
            ))

    fig3.update_layout(
        barmode='group',
        title="Gráfico género según tipo",
        title_font= dict(weight="bold"),
        title_x=0.5,
        yaxis=dict(title="Porcentaje", range=[0, 100], ticksuffix="%", gridcolor='lightgray',
                   zerolinecolor='lightgray'),
        xaxis_title="Género",
        bargap=0.1,
        bargroupgap=0.1,
        autosize= True,
        plot_bgcolor='white'
    )
    ### **Gráfico 4: Distribución género segun nivel

    conteo_nivel = df.groupby(['rural_estab','nivel1']).size().reset_index(name='Cantidad')
    conteo_nivel.columns = ['Zona','Nivel', 'Cantidad']

# Calcular porcentaje total
    totales_por_nivel = conteo_nivel.groupby('Zona')['Cantidad'].transform('sum')
    conteo_nivel['Porcentaje'] = (conteo_nivel['Cantidad'] / totales_por_nivel) * 100

    fig4 = go.Figure()

    fig4 = make_subplots(
            rows=2, cols=1, 
            specs=[[{'type': 'domain'}], [{'type': 'domain'}]],
            subplot_titles=[
                'Distribución por nivel - Urbano', 
                'Distribución por nivel - Rural'
            ]
        )

# Filtrar por género
    zonas = conteo_nivel['Zona'].unique()

    for i, nivel in enumerate(zonas):
        df_nivel = conteo_nivel[conteo_nivel['Zona'] == nivel]
        
        fig4.add_trace(
            go.Pie(
                labels=df_nivel['Nivel'],
                values=df_nivel['Cantidad'],
                name=nivel,
                textinfo='percent',
                hoverinfo='label+percent+value'
            ),
            row=i+1, col=1
        )

    fig4.update_layout(
        title_text="Distribución por nivel educativo según género",
        title_font=dict(weight="bold"),
        title_x=0.5,
        showlegend=True,
        autosize=True,
        height=650,
        legend=dict(orientation="h", yanchor="bottom", y=-0.4, # y posiciona las leyendas
                    xanchor="center", x=0.5) 
    )


    grafico_genero_zona_html = fig.to_html()
    grafico_genero_dependencia_html = fig2.to_html()
    grafico_genero_tipo_html = fig3.to_html()
    grafico_genero_nivel_html = fig4.to_html()

    # Pruebas de chi-cuadrado 
    tabla_tipo = pd.crosstab(df['gen_alu'], df['cod_ense2_m'])
    chi2_tipo, p_tipo, _, _ = chi2_contingency(tabla_tipo)

    tabla_nivel = pd.crosstab(df['rural_estab'], df['nivel1'])
    chi2_nivel, p_nivel, _, _ = chi2_contingency(tabla_nivel)

    def v_cramer (tabla_tipo):
        n = tabla_tipo.sum().sum()
        chi2_tipo, _, _, _ = chi2_contingency(tabla_tipo)
        phi2= chi2_tipo/n
        r, k = tabla_tipo.shape
        # Corregir phi2 (phi2corr) para evitar valores negativos
        phi2corr = max(0, phi2 - ((k - 1) * (r - 1)) / (n - 1))
        k_corr = k - (k - 1) * (k - 2) / (n - 1)
        r_corr = r - (r - 1) * (r - 2) / (n - 1)
        v = np.sqrt(phi2corr / min(k_corr - 1, r_corr - 1))
        
        return v
    
    v_cramer_tipo = v_cramer(tabla_tipo)
    v_cramer_nivel = v_cramer(tabla_nivel)

    return render(request, 'educacion/graficos_parvulo_2023.html', {'grafico_html': grafico_genero_zona_html,
                                                    'grafico_dependencia_html': grafico_genero_dependencia_html,
                                                    'grafico_tipo_html': grafico_genero_tipo_html,
                                                    'grafico_nivel_html':grafico_genero_nivel_html,
                                                    'chi2_tipo': round(chi2_tipo, 2),
                                                    'p_tipo': round(p_tipo, 4),
                                                    'chi2_nivel': round(chi2_nivel, 2),
                                                    'p_nivel': round(p_nivel, 4),
                                                    'v_cramer_tipo': round(v_cramer_tipo,2),
                                                    'v_cramer_nivel': round(v_cramer_nivel,2),
                                                    'region': region_seleccionada})

def grafico_matricula_parvulo_2024(request):

    categorias_genero = {
        1: "Masculino",
        2: "Femenino",
    }

    categorias_rural = {
        0:"Urbano",
        1:"Rural",
    }

    categorias_dependencia = {
        1:"Municipal",
        2:"Particular Subvencionado",
        3:"Particular Pagado",
        4:"JUNJI",
        5:"INTEGRA",
        6:"SLE",
    }

    categorias_tipo = {
        1: "Ed. Parvularia",
        4: "Ed. Espacial"
    }

    categorias_nivel = {
        1:"Sala cuna menor",
        2:"Sala cuna mayor",
        3:"Medio menor", 
        4:"Medio mayor",
        5:"Transición menor",
        6:"Transición mayor"
    }
    # Obtener la región seleccionada desde la URL (por defecto muestra todos)
    region_seleccionada = request.GET.get('nom_reg_a_estab', "RM")

    datos = matricula_parvulo.objects.filter(agno=2024, gen_alu__in= [1, 2])
    
    # Obtener datos del modelo, filtrando por región si se especifica
    if region_seleccionada:
        datos = datos.filter(nom_reg_a_estab=region_seleccionada)

    datos= datos.values('gen_alu','rural_estab','dependencia','cod_ense2_m','nivel1')
    df = pd.DataFrame(datos)

    df['gen_alu'] = df['gen_alu'].map(categorias_genero)
    df['rural_estab'] = df['rural_estab'].map(categorias_rural)
    df['dependencia'] = df['dependencia'].map(categorias_dependencia)
    df['cod_ense2_m'] = df['cod_ense2_m'].map(categorias_tipo)
    df['nivel1'] = df['nivel1'].map(categorias_nivel)

     # Contar cuántos hay de cada género
    conteo = df.groupby(['gen_alu','rural_estab']).size().reset_index(name='Cantidad')
    conteo.columns = ['Género','Zona','Cantidad']
    
    # Convertir "Género" a tipo string (para que no sea numérico)
    conteo['Género'] = conteo['Género'].astype(str)
    conteo['Zona'] = conteo['Zona'].astype(str)
    conteo = conteo.dropna(subset=['Zona'])

    # Calcular el total por zona para obtener porcentajes
    totales_por_zona = conteo.groupby('Género')['Cantidad'].transform('sum')
    conteo['Porcentaje'] = (conteo['Cantidad'] / totales_por_zona) * 100

# Crear la figura manualmente
    fig = go.Figure()

    for zona in conteo['Zona'].unique():
        df_filtrado = conteo[conteo['Zona'] == zona]
        if zona == 'Urbano':
            color_relleno = 'skyblue'
            color_borde = 'deepskyblue'  # Más oscuro que skyblue
        else: 
            color_relleno = 'salmon'
            color_borde = 'indianred' 
        fig.add_trace(go.Bar(
            x=df_filtrado['Género'],
            y=df_filtrado['Porcentaje'],
            name=zona,  # Esto agrupará las barras por zona
            text=df_filtrado['Porcentaje'].apply(lambda x: f"{x:.2f}%"),  # Muestra los valores en las barras
            textposition='auto',
            marker=dict(color=color_relleno,line=dict(color=color_borde, width=1.5))
        ))

    fig.update_layout(
        barmode='group', 
        title="Gráfico género según zona",
        title_font= dict(weight="bold"),
        title_x=0.5,
        yaxis=dict(title="Porcentaje", ticksuffix="%", range=[0, 100], gridcolor='lightgray',
                   zerolinecolor='lightgray'),
        xaxis_title="Género",
        plot_bgcolor='white', # fondo del grafico
        bargap=0.2, 
        bargroupgap=0.1,  
        autosize= True
    )

### **Gráfico 2: Distribución género segun dependencia**

    conteo_dependencia = df.groupby(['gen_alu','dependencia']).size().reset_index(name='Cantidad')
    conteo_dependencia.columns = ['Género','Dependencia', 'Cantidad']

# Calcular porcentaje total
    totales_por_dependencia = conteo_dependencia.groupby('Género')['Cantidad'].transform('sum')
    conteo_dependencia['Porcentaje'] = (conteo_dependencia['Cantidad'] / totales_por_dependencia) * 100

    fig2 = go.Figure()

    fig2 = make_subplots(
        rows=2, cols=1, 
        specs=[[{'type': 'domain'}], [{'type': 'domain'}]],
        subplot_titles=[
            'Distribución por dependencia - Mujeres', 
            'Distribución por dependencia - Hombres'
        ]
    )

# Filtrar por género
    generos = conteo_dependencia['Género'].unique()

    for i, genero in enumerate(generos):
        df_genero = conteo_dependencia[conteo_dependencia['Género'] == genero]
        
        fig2.add_trace(
            go.Pie(
                labels=df_genero['Dependencia'],
                values=df_genero['Cantidad'],
                name=genero,
                textinfo='percent',
                hoverinfo='percent+value'
            ),
            row=i+1, col=1
        )

    fig2.update_layout(
        title_text="Distribución por dependencia administrativa según género",
        title_font=dict(weight="bold"),
        title_x=0.5,
        showlegend=True,
        autosize=True,
        height=650,
        legend=dict(orientation="h", yanchor="bottom", y=-0.4, xanchor="center", x=0.5) 
    )

### **Gráfico 3: Distribución género segun tipo**

    conteo_tipo = df.groupby(['gen_alu','cod_ense2_m']).size().reset_index(name='Cantidad')
    conteo_tipo.columns = ['Género','Tipo', 'Cantidad']

# Calcular porcentaje total
    totales_por_tipo = conteo_tipo.groupby('Género')['Cantidad'].transform('sum')
    conteo_tipo['Porcentaje'] = (conteo_tipo['Cantidad'] / totales_por_tipo) * 100

    fig3 = go.Figure()

    for tipo in conteo_tipo['Tipo'].unique():
        df_filtrado = conteo_tipo[conteo_tipo['Tipo'] == tipo]
        if tipo == 'Ed. Parvularia':
            color_relleno = 'skyblue'
            color_borde = 'deepskyblue'  # Más oscuro que skyblue
        else: 
            color_relleno = 'salmon'
            color_borde = 'indianred'
        fig3.add_trace(go.Bar(
            x =df_filtrado['Género'],
            y = df_filtrado['Porcentaje'],
            name= tipo, 
            text=df_filtrado['Porcentaje'].apply(lambda x: f"{x:.2f}%"),
            textposition= 'auto',
            marker=dict(color=color_relleno,line=dict(color=color_borde, width=1.5))
            ))

    fig3.update_layout(
        barmode='group',
        title="Gráfico género según tipo",
        title_font= dict(weight="bold"),
        title_x=0.5,
        yaxis=dict(title="Porcentaje", range=[0, 100], ticksuffix="%", gridcolor='lightgray',
                   zerolinecolor='lightgray'),
        xaxis_title="Género",
        bargap=0.1,
        bargroupgap=0.1,
        autosize= True,
        plot_bgcolor='white'
    )

    ### **Gráfico 4: Distribución género segun nivel

    conteo_nivel = df.groupby(['rural_estab','nivel1']).size().reset_index(name='Cantidad')
    conteo_nivel.columns = ['Zona','Nivel', 'Cantidad']

# Calcular porcentaje total
    totales_por_nivel = conteo_nivel.groupby('Zona')['Cantidad'].transform('sum')
    conteo_nivel['Porcentaje'] = (conteo_nivel['Cantidad'] / totales_por_nivel) * 100

    fig4 = go.Figure()


    fig4 = make_subplots(
            rows=2, cols=1, 
            specs=[[{'type': 'domain'}], [{'type': 'domain'}]],
            subplot_titles=[
                'Distribución por nivel - Urbano', 
                'Distribución por nivel - Rural'
            ]
        )

# Filtrar por género
    zonas = conteo_nivel['Zona'].unique()

    for i, nivel in enumerate(zonas):
        df_nivel = conteo_nivel[conteo_nivel['Zona'] == nivel]
        
        fig4.add_trace(
            go.Pie(
                labels=df_nivel['Nivel'],
                values=df_nivel['Cantidad'],
                name=nivel,
                textinfo='percent',
                hoverinfo='label+percent+value'
            ),
            row=i+1, col=1
        )

    fig4.update_layout(
        title_text="Distribución por nivel educativo según género",
        title_font=dict(weight="bold"),
        title_x=0.5,
        showlegend=True,
        autosize=True,
        height=650,
        legend=dict(orientation="h", yanchor="bottom", y=-0.4, # y posiciona las leyendas
                    xanchor="center", x=0.5) 
    )

    grafico_genero_zona_html = fig.to_html()
    grafico_genero_dependencia_html = fig2.to_html()
    grafico_genero_tipo_html = fig3.to_html()
    grafico_genero_nivel_html = fig4.to_html()

    # Pruebas de chi-cuadrado 
    tabla_tipo = pd.crosstab(df['gen_alu'], df['cod_ense2_m'])
    chi2_tipo, p_tipo, _, _ = chi2_contingency(tabla_tipo)

    tabla_nivel = pd.crosstab(df['rural_estab'], df['nivel1'])
    chi2_nivel, p_nivel, _, _ = chi2_contingency(tabla_nivel)

    def v_cramer (tabla_tipo):
        n = tabla_tipo.sum().sum()
        chi2_tipo, _, _, _ = chi2_contingency(tabla_tipo)
        phi2= chi2_tipo/n
        r, k = tabla_tipo.shape
        # Corregir phi2 (phi2corr) para evitar valores negativos
        phi2corr = max(0, phi2 - ((k - 1) * (r - 1)) / (n - 1))
        k_corr = k - (k - 1) * (k - 2) / (n - 1)
        r_corr = r - (r - 1) * (r - 2) / (n - 1)
        v = np.sqrt(phi2corr / min(k_corr - 1, r_corr - 1))
        
        return v
    
    v_cramer_tipo = v_cramer(tabla_tipo)
    v_cramer_nivel = v_cramer(tabla_nivel)

    return render(request, 'educacion/graficos_parvulo_2024.html', {'grafico_html': grafico_genero_zona_html,
                                                        'grafico_dependencia_html': grafico_genero_dependencia_html,
                                                        'grafico_tipo_html': grafico_genero_tipo_html,
                                                        'grafico_nivel_html':grafico_genero_nivel_html,
                                                        'chi2_tipo': round(chi2_tipo, 2),
                                                        'p_tipo': round(p_tipo, 4),
                                                        'chi2_nivel': round(chi2_nivel, 2),
                                                        'p_nivel': round(p_nivel, 4),
                                                        'v_cramer_tipo': round(v_cramer_tipo,2),
                                                        'v_cramer_nivel': round(v_cramer_nivel,2),
                                                        'region': region_seleccionada})

def grafico_matricula_parvulo_2020(request):

    categorias_genero = {
        1: "Masculino",
        2: "Femenino",
    }

    categorias_rural = {
        0:"Urbano",
        1:"Rural",
    }

    categorias_dependencia = {
        1:"Municipal",
        2:"Particular Subvencionado",
        3:"Particular Pagado",
        4:"JUNJI",
        5:"INTEGRA",
        6:"SLE",
    }

    categorias_tipo = {
        1: "Ed. Parvularia",
        4: "Ed. Espacial"
    }

    categorias_nivel = {
        1:"Sala cuna menor",
        2:"Sala cuna mayor",
        3:"Medio menor", 
        4:"Medio mayor",
        5:"Transición menor",
        6:"Transición mayor"
    }

    # Obtener la región seleccionada desde la URL 
    region_seleccionada = request.GET.get('nom_reg_a_estab', "RM")

    datos = matricula_parvulo.objects.filter(agno=2020, gen_alu__in= [1, 2])
    
    # Obtener datos del modelo, filtrando por región si se especifica
    if region_seleccionada:
        datos = datos.filter(nom_reg_a_estab=region_seleccionada)

    datos= datos.values('gen_alu','rural_estab','dependencia','cod_ense2_m','nivel1')
    df = pd.DataFrame(datos)

    df['gen_alu'] = df['gen_alu'].map(categorias_genero)
    df['rural_estab'] = df['rural_estab'].map(categorias_rural)
    df['dependencia'] = df['dependencia'].map(categorias_dependencia)
    df['cod_ense2_m'] = df['cod_ense2_m'].map(categorias_tipo)
    df['nivel1'] = df['nivel1'].map(categorias_nivel)


     # Contar cuántos hay de cada género
    conteo = df.groupby(['gen_alu','rural_estab']).size().reset_index(name='Cantidad')
    conteo.columns = ['Género','Zona','Cantidad']
    
    # Convertir "Género" a tipo string (para que no sea numérico)
    conteo['Género'] = conteo['Género'].astype(str)
    conteo['Zona'] = conteo['Zona'].astype(str)
    conteo = conteo.dropna(subset=['Zona'])

    # Calcular el total por zona para obtener porcentajes
    totales_por_zona = conteo.groupby('Género')['Cantidad'].transform('sum')
    conteo['Porcentaje'] = (conteo['Cantidad'] / totales_por_zona) * 100


# Crear la figura manualmente
    fig = go.Figure()

    for zona in conteo['Zona'].unique():
        df_filtrado = conteo[conteo['Zona'] == zona]
        if zona == 'Urbano':
            color_relleno = 'skyblue'
            color_borde = 'deepskyblue'  # Más oscuro que skyblue
        else: 
            color_relleno = 'salmon'
            color_borde = 'indianred' 
        fig.add_trace(go.Bar(
            x=df_filtrado['Género'],
            y=df_filtrado['Porcentaje'],
            name=zona,  # Esto agrupará las barras por zona
            text=df_filtrado['Porcentaje'].apply(lambda x: f"{x:.2f}%"),  # Muestra los valores en las barras
            textposition='auto',
            marker=dict(color=color_relleno,line=dict(color=color_borde, width=1.5))
        ))

    fig.update_layout(
        barmode='group', 
        title="Gráfico género según zona",
        title_font= dict(weight="bold"),
        title_x=0.5,
        yaxis=dict(title="Porcentaje", ticksuffix="%", range=[0, 100], gridcolor='lightgray',
                   zerolinecolor='lightgray'),
        xaxis_title="Género",
        plot_bgcolor='white', # fondo del grafico
        bargap=0.2, 
        bargroupgap=0.1,  
        autosize= True
    )

### **Gráfico 2: Distribución género segun dependencia**

    conteo_dependencia = df.groupby(['gen_alu','dependencia']).size().reset_index(name='Cantidad')
    conteo_dependencia.columns = ['Género','Dependencia', 'Cantidad']

# Calcular porcentaje total
    totales_por_dependencia = conteo_dependencia.groupby('Género')['Cantidad'].transform('sum')
    conteo_dependencia['Porcentaje'] = (conteo_dependencia['Cantidad'] / totales_por_dependencia) * 100

    fig2 = go.Figure()

    fig2 = make_subplots(
        rows=2, cols=1, 
        specs=[[{'type': 'domain'}], [{'type': 'domain'}]],
        subplot_titles=[
            'Distribución por dependencia - Mujeres', 
            'Distribución por dependencia - Hombres'
        ]
    )

# Filtrar por género
    generos = conteo_dependencia['Género'].unique()

    for i, genero in enumerate(generos):
        df_genero = conteo_dependencia[conteo_dependencia['Género'] == genero]
        
        fig2.add_trace(
            go.Pie(
                labels=df_genero['Dependencia'],
                values=df_genero['Cantidad'],
                name=genero,
                textinfo='percent',
                hoverinfo='percent+value'
            ),
            row=i+1, col=1
        )

    fig2.update_layout(
        title_text="Distribución por dependencia administrativa según género",
        title_font=dict(weight="bold"),
        title_x=0.5,
        showlegend=True,
        autosize=True,
        height=650,
        legend=dict(orientation="h", yanchor="bottom", y=-0.4, xanchor="center", x=0.5) 
    )
### **Gráfico 3: Distribución género segun tipo**

    conteo_tipo = df.groupby(['gen_alu','cod_ense2_m']).size().reset_index(name='Cantidad')
    conteo_tipo.columns = ['Género','Tipo', 'Cantidad']

# Calcular porcentaje total
    totales_por_tipo = conteo_tipo.groupby('Género')['Cantidad'].transform('sum')
    conteo_tipo['Porcentaje'] = (conteo_tipo['Cantidad'] / totales_por_tipo) * 100

    fig3 = go.Figure()

    for tipo in conteo_tipo['Tipo'].unique():
        df_filtrado = conteo_tipo[conteo_tipo['Tipo'] == tipo]
        if tipo == 'Ed. Parvularia':
            color_relleno = 'skyblue'
            color_borde = 'deepskyblue'  # Más oscuro que skyblue
        else: 
            color_relleno = 'salmon'
            color_borde = 'indianred'
        fig3.add_trace(go.Bar(
            x =df_filtrado['Género'],
            y = df_filtrado['Porcentaje'],
            name= tipo, 
            text=df_filtrado['Porcentaje'].apply(lambda x: f"{x:.2f}%"),
            textposition= 'auto',
            marker=dict(color=color_relleno,line=dict(color=color_borde, width=1.5))
            ))

    fig3.update_layout(
        barmode='group',
        title="Gráfico género según tipo",
        title_font= dict(weight="bold"),
        title_x=0.5,
        yaxis=dict(title="Porcentaje", range=[0, 100], ticksuffix="%", gridcolor='lightgray',
                   zerolinecolor='lightgray'),
        xaxis_title="Género",
        bargap=0.1,
        bargroupgap=0.1,
        autosize= True,
        plot_bgcolor='white'
    )
    ### **Gráfico 4: Distribución género segun nivel

    conteo_nivel = df.groupby(['rural_estab','nivel1']).size().reset_index(name='Cantidad')
    conteo_nivel.columns = ['Zona','Nivel', 'Cantidad']

# Calcular porcentaje total
    totales_por_nivel = conteo_nivel.groupby('Zona')['Cantidad'].transform('sum')
    conteo_nivel['Porcentaje'] = (conteo_nivel['Cantidad'] / totales_por_nivel) * 100
# Ordenar según valor ortiginal de la categoría
    conteo_nivel = conteo_nivel.sort_values(by='Nivel', key=lambda x: x.map({v: k for k, v in categorias_nivel.items()}))

    fig4 = go.Figure()

    fig4 = make_subplots(
            rows=2, cols=1, 
            specs=[[{'type': 'domain'}], [{'type': 'domain'}]],
            subplot_titles=[
                'Distribución por nivel - Urbano', 
                'Distribución por nivel - Rural'
            ]
        )

# Filtrar por género
    zonas = conteo_nivel['Zona'].unique()

    for i, nivel in enumerate(zonas):
        df_nivel = conteo_nivel[conteo_nivel['Zona'] == nivel]
        
        fig4.add_trace(
            go.Pie(
                labels=df_nivel['Nivel'],
                values=df_nivel['Cantidad'],
                name=nivel,
                textinfo='percent',
                hoverinfo='label+percent+value'
            ),
            row=i+1, col=1
        )

    fig4.update_layout(
        title_text="Distribución por nivel educativo según género",
        title_font=dict(weight="bold"),
        title_x=0.5,
        showlegend=True,
        autosize=True,
        height=650,
        legend=dict(orientation="h", yanchor="bottom", y=-0.4, # y posiciona las leyendas
                    xanchor="center", x=0.5) 
    )
    grafico_genero_zona_html = fig.to_html()
    grafico_genero_dependencia_html = fig2.to_html()
    grafico_genero_tipo_html = fig3.to_html()
    grafico_genero_nivel_html = fig4.to_html()

    # Pruebas de chi-cuadrado 
    tabla_tipo = pd.crosstab(df['gen_alu'], df['cod_ense2_m'])
    chi2_tipo, p_tipo, _, _ = chi2_contingency(tabla_tipo)

    tabla_nivel = pd.crosstab(df['rural_estab'], df['nivel1'])
    chi2_nivel, p_nivel, _, _ = chi2_contingency(tabla_nivel)

    def v_cramer (tabla_tipo):
        n = tabla_tipo.sum().sum()
        chi2_tipo, _, _, _ = chi2_contingency(tabla_tipo)
        phi2= chi2_tipo/n
        r, k = tabla_tipo.shape
        # Corregir phi2 (phi2corr) para evitar valores negativos
        phi2corr = max(0, phi2 - ((k - 1) * (r - 1)) / (n - 1))
        k_corr = k - (k - 1) * (k - 2) / (n - 1)
        r_corr = r - (r - 1) * (r - 2) / (n - 1)
        v = np.sqrt(phi2corr / min(k_corr - 1, r_corr - 1))
        
        return v
    
    v_cramer_tipo = v_cramer(tabla_tipo)
    v_cramer_nivel = v_cramer(tabla_nivel)


    return render(request, 'educacion/graficos_parvulo_2020.html', {'grafico_html': grafico_genero_zona_html,
                                                        'grafico_dependencia_html': grafico_genero_dependencia_html,
                                                        'grafico_tipo_html': grafico_genero_tipo_html,
                                                        'grafico_nivel_html':grafico_genero_nivel_html,
                                                        'chi2_tipo': round(chi2_tipo, 2),
                                                        'p_tipo': round(p_tipo, 4),
                                                        'chi2_nivel': round(chi2_nivel, 2),
                                                        'p_nivel': round(p_nivel, 4),
                                                        'v_cramer_tipo': round(v_cramer_tipo,2),
                                                        'v_cramer_nivel': round(v_cramer_nivel,2),
                                                        'region': region_seleccionada})

######################### GRAFICOS MATRICULA SEGUN AÑO #################################

def grafico_matricula_por_ano(request):
    
    categorias_genero = {1: "Masculino", 2: "Femenino"}
    categorias_rural = {0: "Urbano", 1: "Rural"}

    # Obtener datos (modificar según tu modelo)
    datos = matricula_parvulo.objects.all()  # Trae todos los datos de matriculas
    
    # Obtener la región seleccionada desde la URL (si aplica)
    region_seleccionada = request.GET.get('nom_reg_a_estab', None)
    
    # Filtrar por región si se seleccionó una
    if region_seleccionada:
        datos = datos.filter(nom_reg_a_estab=region_seleccionada)

    # Convertir a DataFrame
    df = pd.DataFrame(datos.values('agno','rural_estab','gen_alu'))  # Asegúrate de que 'agno' es el campo para el año

   # Reemplazar valores numéricos por nombres de categorías
    df['gen_alu'] = df['gen_alu'].map(categorias_genero)
    df['rural_estab'] = df['rural_estab'].map(categorias_rural)

    # Calcular total de matrículas por año
    total_anual = df.groupby('agno').size().reset_index(name='Total')

    # Contar el total de matrículas por año
    conteo_por_ano = df.groupby('agno').size().reset_index(name='Cantidad')
    
    # Crear el gráfico
    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=conteo_por_ano['agno'],  # Año
        y=conteo_por_ano['Cantidad'],  # Total de matrículas por año
        name='Matriculas por año',
        text=conteo_por_ano['Cantidad'],  # Mostrar la cantidad sobre cada barra
        textposition='auto',
    ))

    # Configurar el diseño
    fig.update_layout(
        title="Comparación de matriculas por año",
        title_x=0.5,
        title_font= dict(weight='bold'),
        xaxis_title="Año",
        yaxis_title="Cantidad de Matrículas",
        yaxis=dict(tickformat="d"), 
        bargap=0.2,
        bargroupgap=0.1,
        autosize=True
    )


    # --- PRIMER GRÁFICO: Comparación anual por género  ---
    conteo_anual_genero = df.groupby(['agno', 'gen_alu']).size().reset_index(name='Cantidad')
    conteo_anual_genero = conteo_anual_genero.merge(total_anual, on='agno')
    conteo_anual_genero['Porcentaje'] = (conteo_anual_genero['Cantidad'] / conteo_anual_genero['Total']) * 100
    conteo_anual_genero['gen_alu'] = conteo_anual_genero['gen_alu'].astype(str)


    fig1 = go.Figure()
    for genero in conteo_anual_genero['gen_alu'].unique():
        df_filtrado = conteo_anual_genero[conteo_anual_genero['gen_alu'] == genero]
        fig1.add_trace(go.Bar(
            x=df_filtrado['agno'],
            y=df_filtrado['Porcentaje'],
            name=str(genero),
            text=df_filtrado['Porcentaje'].apply(lambda x: f"{x:.2f}%"),
            textposition='auto'
        ))

    fig1.update_layout(
        barmode='group',
        title="Comparación de años por género",
        title_x=0.5,
        title_font= dict(weight='bold'),
        yaxis=dict(title="Porcentaje", tickformat=".2f", range=[0, 100]),
        xaxis_title="Año",
        yaxis_title="Cantidad",
        bargap=0.2,
        bargroupgap=0.1,
        autosize=True
    )

    # --- SEGUNDO GRÁFICO: Comparación de matrículas por año y zona ---
    conteo_anual_zona = df.groupby(['agno', 'rural_estab']).size().reset_index(name='Cantidad')
    conteo_anual_zona = conteo_anual_zona.merge(total_anual, on='agno')
    conteo_anual_zona['Porcentaje'] = (conteo_anual_zona['Cantidad'] / conteo_anual_zona['Total']) * 100
    conteo_anual_zona['rural_estab'] = conteo_anual_zona['rural_estab'].astype(str)

    fig2 = go.Figure()
    for zona in conteo_anual_zona['rural_estab'].unique():
        df_filtrado = conteo_anual_zona[conteo_anual_zona['rural_estab'] == zona]
        fig2.add_trace(go.Bar(
            x=df_filtrado['agno'],
            y=df_filtrado['Porcentaje'],
            name=str(zona),
            text=df_filtrado['Porcentaje'].apply(lambda x: f"{x:.2f}%"),
            textposition='auto'
        ))

    fig2.update_layout(
        barmode='group',
        title="Total de matrículas por año según zona",
        title_x=0.5,
        yaxis=dict(title="Porcentaje", tickformat=".2f", range=[0, 100]),
        xaxis_title="Año",
        yaxis_title="Cantidad",
        bargap=0.2,
        bargroupgap=0.1,
        title_font= dict(weight='bold'),
        autosize=True
    )

    # Convertir gráficos a HTML
    grafico1_html = fig1.to_html()
    grafico2_html = fig2.to_html()
    grafico_ano_html = fig.to_html()

    # Renderizar el gráfico en la vista
    return render(request, 'educacion/graficos_por_ano.html', {'grafico_html': grafico_ano_html,
                                                               'grafico1_html':grafico1_html,
                                                               'grafico2_html': grafico2_html,
                                                               'region': region_seleccionada})

#########################    GRAFICOS MATRICULA BASICA  ########################################### 

def grafico_matricula_basica_2023 (request):

    categorias_genero = {
        1: "Masculino",
        2: "Femenino",
    }

    categorias_rural = {
        0:"Urbano",
        1:"Rural",
    }

    categorias_dependencia = {
        1:"Municipal",
        2:"Particular Subvencionado",
        3:"Particular Pagado",
        4:"Corporación de Administración Delegada",
        5:"Servicio Local de Educación",
    }

    tipo_enseñanza = {
        2: "Niñas/os",
        3: "Adultas/os",
    }

    tipo2_enseñanza = {
        3: "Enseñanza Básica Regular",
        4: "Enseñanza Básica Especial",
        9: "Educación Básica Adultos"
    }

    # Obtener la región seleccionada desde la URL (por defecto muestra todos)
    region_seleccionada = request.GET.get('NOM_REG_RBD_A', "RM")

    datos = matricula_basica.objects.filter(AGNO=2023, GEN_ALU__in= [1, 2])
    
    # Obtener datos del modelo, filtrando por región si se especifica
    if region_seleccionada:
        datos = datos.filter(NOM_REG_RBD_A=region_seleccionada)

    datos= datos.values('GEN_ALU','RURAL_RBD','COD_DEPE2','COD_ENSE2','ENS')
    df = pd.DataFrame(datos)

    df['GEN_ALU'] = df['GEN_ALU'].map(categorias_genero)
    df['RURAL_RBD'] = df['RURAL_RBD'].map(categorias_rural)
    df['COD_DEPE2'] = df['COD_DEPE2'].map(categorias_dependencia)
    df['COD_ENSE2'] = df['COD_ENSE2'].map(tipo_enseñanza)
    df['ENS'] = df['ENS'].map(tipo2_enseñanza)


     # Contar cuántos hay de cada género
    conteo = df.groupby(['GEN_ALU','RURAL_RBD']).size().reset_index(name='Cantidad')
    conteo.columns = ['Género','Zona','Cantidad']
    
    # Calcular el total por zona para obtener porcentajes
    totales_por_zona = conteo.groupby('Género')['Cantidad'].transform('sum')
    conteo['Porcentaje'] = (conteo['Cantidad'] / totales_por_zona) * 100


# Crear la figura manualmente
    fig = go.Figure()

    for zona in conteo['Zona'].unique():
        df_filtrado = conteo[conteo['Zona'] == zona]
        if zona == 'Urbano':
            color_relleno = 'skyblue'
            color_borde = 'deepskyblue'  # Más oscuro que skyblue
        else: 
            color_relleno = 'salmon'
            color_borde = 'indianred' 
        fig.add_trace(go.Bar(
            x=df_filtrado['Género'],
            y=df_filtrado['Porcentaje'],
            name=zona,  # Esto agrupará las barras por zona
            text=df_filtrado['Porcentaje'].apply(lambda x: f"{x:.2f}%"),  # Muestra los valores en las barras
            textposition='auto',
            marker=dict(color=color_relleno,line=dict(color=color_borde, width=1.5))
        ))

    fig.update_layout(
        barmode='group', 
        title="Gráfico género según zona",
        title_font= dict(weight="bold"),
        title_x=0.5,
        yaxis=dict(title="Porcentaje", ticksuffix="%", range=[0, 100], gridcolor='lightgray',
                   zerolinecolor='lightgray'),
        xaxis_title="Género",
        plot_bgcolor='white', # fondo del grafico
        bargap=0.2, 
        bargroupgap=0.1,  
        autosize= True
    )

### **Gráfico 2: Distribución género segun dependencia**

    conteo_dependencia = df.groupby(['GEN_ALU','COD_DEPE2']).size().reset_index(name='Cantidad')
    conteo_dependencia.columns = ['Género','Dependencia', 'Cantidad']

# Calcular porcentaje total
    totales_por_dependencia = conteo_dependencia.groupby('Género')['Cantidad'].transform('sum')
    conteo_dependencia['Porcentaje'] = (conteo_dependencia['Cantidad'] / totales_por_dependencia) * 100

    fig2 = make_subplots(
        rows=2, cols=1, 
        specs=[[{'type': 'domain'}], [{'type': 'domain'}]],
        subplot_titles=[
            'Distribución por dependencia - Mujeres', 
            'Distribución por dependencia - Hombres'
        ]
    )

# Filtrar por género
    generos = conteo_dependencia['Género'].unique()

    for i, genero in enumerate(generos):
        df_genero = conteo_dependencia[conteo_dependencia['Género'] == genero]
        
        fig2.add_trace(
            go.Pie(
                labels=df_genero['Dependencia'],
                values=df_genero['Cantidad'],
                name=genero,
                textinfo='percent',
                hoverinfo='percent+value'
            ),
            row=i+1, col=1
        )

    fig2.update_layout(
        title_text="Distribución por dependencia administrativa según género",
        title_font=dict(weight="bold"),
        title_x=0.5,
        showlegend=True,
        autosize=True,
        height=650,
        legend=dict(orientation="h", yanchor="bottom", y=-0.4, xanchor="center", x=0.5) 
    )

### **Gráfico 3: Distribución género segun tipo**

    conteo_tipo = df.groupby(['GEN_ALU','COD_ENSE2']).size().reset_index(name='Cantidad')
    conteo_tipo.columns = ['Género','Tipo', 'Cantidad']

# Calcular porcentaje total
    totales_por_tipo = conteo_tipo.groupby('Género')['Cantidad'].transform('sum')
    conteo_tipo['Porcentaje'] = (conteo_tipo['Cantidad'] / totales_por_tipo) * 100

    fig3 = go.Figure()

    for tipo in conteo_tipo['Tipo'].unique():
        df_filtrado = conteo_tipo[conteo_tipo['Tipo'] == tipo]
        if tipo == 'Adultas/os':
            color_relleno = 'skyblue'
            color_borde = 'deepskyblue'  # Más oscuro que skyblue
        else: 
            color_relleno = 'salmon'
            color_borde = 'indianred' 
        fig3.add_trace(go.Bar(
            x=df_filtrado['Género'],
            y=df_filtrado['Porcentaje'],
            name=tipo,  # Esto agrupará las barras por zona
            text=df_filtrado['Porcentaje'].apply(lambda x: f"{x:.2f}%"),  # Muestra los valores en las barras
            textposition='auto',
            marker=dict(color=color_relleno,line=dict(color=color_borde, width=1.5))
        ))

    fig3.update_layout(
        barmode='group', 
        title="Gráfico género según tipo",
        title_font= dict(weight="bold"),
        title_x=0.5,
        yaxis=dict(title="Porcentaje", ticksuffix="%", range=[0, 100], gridcolor='lightgray',
                   zerolinecolor='lightgray'),
        xaxis_title="Género",
        plot_bgcolor='white', # fondo del grafico
        bargap=0.2, 
        bargroupgap=0.1,  
        autosize= True
    )

### **Gráfico 4: Distribución género segun tipo2

    conteo_ens = df.groupby(['RURAL_RBD','ENS']).size().reset_index(name='Cantidad')
    conteo_ens.columns = ['Género','Enseñanza', 'Cantidad']

# Calcular porcentaje total
    totales_por_ens = conteo_ens.groupby('Género')['Cantidad'].transform('sum')
    conteo_ens['Porcentaje'] = (conteo_ens['Cantidad'] / totales_por_ens) * 100

    fig4 = go.Figure()

    for ens in conteo_ens['Enseñanza'].unique():
        df_filtrado = conteo_ens[conteo_ens['Enseñanza'] == ens]
        fig4.add_trace(go.Bar(
            x =df_filtrado['Género'],
            y = df_filtrado['Porcentaje'],
            name= ens, 
            text=df_filtrado['Porcentaje'].apply(lambda x: f"{x:.2f}%"),
            textposition= 'auto'
            ))

    fig4.update_layout(
        barmode='group',
        title="Gráfico género según tipo",
        title_font= dict(weight="bold"),
        title_x=0.5,
        yaxis=dict(title="Porcentaje", range=[0, 100]),
        xaxis_title="Género",
        bargap=0.1,
        bargroupgap=0.1,
        autosize= True,
    )

    grafico_genero_zona_html = fig.to_html()
    grafico_genero_dependencia_html = fig2.to_html()
    grafico_genero_tipo_html = fig3.to_html()
    grafico_genero_ens_html = fig4.to_html()


    return render(request, 'educacion/graficos_basica_2023.html', {'grafico_html': grafico_genero_zona_html,
                                                      'grafico_dependencia_html': grafico_genero_dependencia_html,
                                                      'grafico_tipo_html': grafico_genero_tipo_html,
                                                      'grafico_enseñanza_html': grafico_genero_ens_html,
                                                      'region': region_seleccionada})

def grafico_matricula_basica_2022 (request):

    categorias_genero = {
        1: "Masculino",
        2: "Femenino",
    }

    categorias_rural = {
        0:"Urbano",
        1:"Rural",
    }

    categorias_dependencia = {
        1:"Municipal",
        2:"Particular Subvencionado",
        3:"Particular Pagado",
        4:"Corporación de Administración Delegada",
        5:"Servicio Local de Educación",
    }

    tipo_enseñanza = {
        2: "Niñas/os",
        3: "Adultas/os"
    }

    tipo2_enseñanza = {
        3: "Enseñanza Básica Regular",
        4: "Enseñanza Básica Especial",
        9: "Educación Básica Adultos"
    }

    # Obtener la región seleccionada desde la URL 
    region_seleccionada = request.GET.get('NOM_REG_RBD_A', "RM")

    datos = matricula_basica.objects.filter(AGNO=2022, GEN_ALU__in= [1, 2])
    # Obtener datos del modelo, filtrando por región si se especifica
  
    if region_seleccionada:
        datos = datos.filter(NOM_REG_RBD_A=region_seleccionada)

    datos= datos.values('GEN_ALU','RURAL_RBD','COD_DEPE2','COD_ENSE2','ENS')
    df = pd.DataFrame(datos)

    df['GEN_ALU'] = df['GEN_ALU'].map(categorias_genero)
    df['RURAL_RBD'] = df['RURAL_RBD'].map(categorias_rural)
    df['COD_DEPE2'] = df['COD_DEPE2'].map(categorias_dependencia)
    df['COD_ENSE2'] = df['COD_ENSE2'].map(tipo_enseñanza)
    df['ENS'] = df['ENS'].map(tipo2_enseñanza)


     # Contar cuántos hay de cada género
    conteo = df.groupby(['GEN_ALU','RURAL_RBD']).size().reset_index(name='Cantidad')
    conteo.columns = ['Género','Zona','Cantidad']
    

    # Convertir "Género" a tipo string (para que no sea numérico)
    conteo['Género'] = conteo['Género'].astype(str)
    conteo['Zona'] = conteo['Zona'].astype(str)
    conteo = conteo.dropna(subset=['Zona'])

    # Calcular el total por zona para obtener porcentajes
    totales_por_zona = conteo.groupby('Género')['Cantidad'].transform('sum')
    conteo['Porcentaje'] = (conteo['Cantidad'] / totales_por_zona) * 100


# Crear la figura manualmente
    fig = go.Figure()

    for zona in conteo['Zona'].unique():
        df_filtrado = conteo[conteo['Zona'] == zona]
        if zona == 'Urbano':
            color_relleno = 'skyblue'
            color_borde = 'deepskyblue'  # Más oscuro que skyblue
        else: 
            color_relleno = 'salmon'
            color_borde = 'indianred' 
        fig.add_trace(go.Bar(
            x=df_filtrado['Género'],
            y=df_filtrado['Porcentaje'],
            name=zona,  # Esto agrupará las barras por zona
            text=df_filtrado['Porcentaje'].apply(lambda x: f"{x:.2f}%"),  # Muestra los valores en las barras
            textposition='auto',
            marker=dict(color=color_relleno,line=dict(color=color_borde, width=1.5))
        ))

    fig.update_layout(
        barmode='group', 
        title="Gráfico género según zona",
        title_font= dict(weight="bold"),
        title_x=0.5,
        yaxis=dict(title="Porcentaje", ticksuffix="%", range=[0, 100], gridcolor='lightgray',
                   zerolinecolor='lightgray'),
        xaxis_title="Género",
        plot_bgcolor='white', # fondo del grafico
        bargap=0.2, 
        bargroupgap=0.1,  
        autosize= True
    )

### **Gráfico 2: Distribución género segun dependencia**

    conteo_dependencia = df.groupby(['GEN_ALU','COD_DEPE2']).size().reset_index(name='Cantidad')
    conteo_dependencia.columns = ['Género','Dependencia', 'Cantidad']

# Calcular porcentaje total
    totales_por_dependencia = conteo_dependencia.groupby('Género')['Cantidad'].transform('sum')
    conteo_dependencia['Porcentaje'] = (conteo_dependencia['Cantidad'] / totales_por_dependencia) * 100

    fig2 = make_subplots(
        rows=2, cols=1, 
        specs=[[{'type': 'domain'}], [{'type': 'domain'}]],
        subplot_titles=[
            'Distribución por dependencia - Mujeres', 
            'Distribución por dependencia - Hombres'
        ]
    )

# Filtrar por género
    generos = conteo_dependencia['Género'].unique()

    for i, genero in enumerate(generos):
        df_genero = conteo_dependencia[conteo_dependencia['Género'] == genero]
        
        fig2.add_trace(
            go.Pie(
                labels=df_genero['Dependencia'],
                values=df_genero['Cantidad'],
                name=genero,
                textinfo='percent',
                hoverinfo='percent+value'
            ),
            row=i+1, col=1
        )

    fig2.update_layout(
        title_text="Distribución por dependencia administrativa según género",
        title_font=dict(weight="bold"),
        title_x=0.5,
        showlegend=True,
        autosize=True,
        height=650,
        legend=dict(orientation="h", yanchor="bottom", y=-0.4, xanchor="center", x=0.5) 
    )

### **Gráfico 3: Distribución género segun tipo**

    conteo_tipo = df.groupby(['GEN_ALU','COD_ENSE2']).size().reset_index(name='Cantidad')
    conteo_tipo.columns = ['Género','Tipo', 'Cantidad']

# Calcular porcentaje total
    totales_por_tipo = conteo_tipo.groupby('Género')['Cantidad'].transform('sum')
    conteo_tipo['Porcentaje'] = (conteo_tipo['Cantidad'] / totales_por_tipo) * 100

    fig3 = go.Figure()

    for tipo in conteo_tipo['Tipo'].unique():
        df_filtrado = conteo_tipo[conteo_tipo['Tipo'] == tipo]
        if tipo == 'Niñas/os':
            color_relleno = 'skyblue'
            color_borde = 'deepskyblue'
        else:
            color_relleno = 'salmon'
            color_borde = 'indianred' 
        fig3.add_trace(go.Bar(
            x =df_filtrado['Género'],
            y = df_filtrado['Porcentaje'],
            name= tipo, 
            text=df_filtrado['Porcentaje'].apply(lambda x: f"{x:.2f}%"),
            textposition= 'auto',
            marker=dict(color=color_relleno,line=dict(color=color_borde, width=1.5))
            ))

    fig3.update_layout(
        barmode='group',
        title="Gráfico género según tipo",
        title_font= dict(weight="bold"),
        title_x=0.5,
        yaxis=dict(title="Porcentaje", range=[0, 100], gridcolor='lightgray',
                   zerolinecolor='lightgray', ticksuffix='%'),
        xaxis_title="Género",
        plot_bgcolor = 'white',
        bargap=0.1,
        bargroupgap=0.1,
        autosize= True,
    )

    grafico_genero_zona_html = fig.to_html()
    grafico_genero_dependencia_html = fig2.to_html()
    grafico_genero_tipo_html = fig3.to_html()

    return render(request, 'educacion/graficos_basica_2022.html', {'grafico_html': grafico_genero_zona_html,
                                                      'grafico_dependencia_html': grafico_genero_dependencia_html,
                                                      'grafico_tipo_html': grafico_genero_tipo_html,
                                                      'region': region_seleccionada})

def grafico_matricula_basica_2021 (request):

    categorias_genero = {
        1: "Masculino",
        2: "Femenino",
    }

    categorias_rural = {
        0:"Urbano",
        1:"Rural",
    }

    categorias_dependencia = {
        1:"Municipal",
        2:"Particular Subvencionado",
        3:"Particular Pagado",
        4:"Corporación de Administración Delegada",
        5:"Servicio Local de Educación",
    }

    tipo_enseñanza = {
        2: "Niñas/os",
        3: "Adultas/os"
    }

    tipo2_enseñanza = {
        3: "Enseñanza Básica Regular",
        4: "Enseñanza Básica Especial",
        9: "Educación Básica Adultos"
    }

    # Obtener la región seleccionada desde la URL 
    region_seleccionada = request.GET.get('NOM_REG_RBD_A', "RM")

    datos = matricula_basica.objects.filter(AGNO=2021, GEN_ALU__in= [1, 2])
    
    # Obtener datos del modelo, filtrando por región si se especifica
    if region_seleccionada:
        datos = datos.filter(NOM_REG_RBD_A=region_seleccionada)

    datos= datos.values('GEN_ALU','RURAL_RBD','COD_DEPE2','COD_ENSE2','ENS')
    df = pd.DataFrame(datos)

    df['GEN_ALU'] = df['GEN_ALU'].map(categorias_genero)
    df['RURAL_RBD'] = df['RURAL_RBD'].map(categorias_rural)
    df['COD_DEPE2'] = df['COD_DEPE2'].map(categorias_dependencia)
    df['COD_ENSE2'] = df['COD_ENSE2'].map(tipo_enseñanza)
    df['ENS'] = df['ENS'].map(tipo2_enseñanza)

     # Contar cuántos hay de cada género
    conteo = df.groupby(['GEN_ALU','RURAL_RBD']).size().reset_index(name='Cantidad')
    conteo.columns = ['Género','Zona','Cantidad']
    
    # Convertir "Género" a tipo string (para que no sea numérico)
    conteo['Género'] = conteo['Género'].astype(str)
    conteo['Zona'] = conteo['Zona'].astype(str)
    conteo = conteo.dropna(subset=['Zona'])

    # Calcular el total por zona para obtener porcentajes
    totales_por_zona = conteo.groupby('Género')['Cantidad'].transform('sum')
    conteo['Porcentaje'] = (conteo['Cantidad'] / totales_por_zona) * 100


# Crear la figura manualmente
    fig = go.Figure()

    for zona in conteo['Zona'].unique():
        df_filtrado = conteo[conteo['Zona'] == zona]
        if zona == 'Urbano':
            color_relleno = 'skyblue'
            color_borde = 'deepskyblue'  # Más oscuro que skyblue
        else: 
            color_relleno = 'salmon'
            color_borde = 'indianred' 
        fig.add_trace(go.Bar(
            x=df_filtrado['Género'],
            y=df_filtrado['Porcentaje'],
            name=zona,  # Esto agrupará las barras por zona
            text=df_filtrado['Porcentaje'].apply(lambda x: f"{x:.2f}%"),  # Muestra los valores en las barras
            textposition='auto',
            marker=dict(color=color_relleno,line=dict(color=color_borde, width=1.5))
        ))

    fig.update_layout(
        barmode='group', 
        title="Gráfico género según zona",
        title_font= dict(weight="bold"),
        title_x=0.5,
        yaxis=dict(title="Porcentaje", ticksuffix="%", range=[0, 100], gridcolor='lightgray',
                   zerolinecolor='lightgray'),
        xaxis_title="Género",
        plot_bgcolor='white', # fondo del grafico
        bargap=0.2, 
        bargroupgap=0.1,  
        autosize= True
    )

### **Gráfico 2: Distribución género segun dependencia**

    conteo_dependencia = df.groupby(['GEN_ALU','COD_DEPE2']).size().reset_index(name='Cantidad')
    conteo_dependencia.columns = ['Género','Dependencia', 'Cantidad']

# Calcular porcentaje total
    totales_por_dependencia = conteo_dependencia.groupby('Género')['Cantidad'].transform('sum')
    conteo_dependencia['Porcentaje'] = (conteo_dependencia['Cantidad'] / totales_por_dependencia) * 100

    fig2 = make_subplots(
        rows=2, cols=1, 
        specs=[[{'type': 'domain'}], [{'type': 'domain'}]],
        subplot_titles=[
            'Distribución por dependencia - Mujeres', 
            'Distribución por dependencia - Hombres'
        ]
    )

# Filtrar por género
    generos = conteo_dependencia['Género'].unique()

    for i, genero in enumerate(generos):
        df_genero = conteo_dependencia[conteo_dependencia['Género'] == genero]
        
        fig2.add_trace(
            go.Pie(
                labels=df_genero['Dependencia'],
                values=df_genero['Cantidad'],
                name=genero,
                textinfo='percent',
                hoverinfo='percent+value'
            ),
            row=i+1, col=1
        )

    fig2.update_layout(
        title_text="Distribución por dependencia administrativa según género",
        title_font=dict(weight="bold"),
        title_x=0.5,
        showlegend=True,
        autosize=True,
        height=650,
        legend=dict(orientation="h", yanchor="bottom", y=-0.4, xanchor="center", x=0.5) 
    )

### **Gráfico 3: Distribución género segun tipo**

    conteo_tipo = df.groupby(['GEN_ALU','COD_ENSE2']).size().reset_index(name='Cantidad')
    conteo_tipo.columns = ['Género','Tipo', 'Cantidad']

# Calcular porcentaje total
    totales_por_tipo = conteo_tipo.groupby('Género')['Cantidad'].transform('sum')
    conteo_tipo['Porcentaje'] = (conteo_tipo['Cantidad'] / totales_por_tipo) * 100

    fig3 = go.Figure()

    for tipo in conteo_tipo['Tipo'].unique():
        df_filtrado = conteo_tipo[conteo_tipo['Tipo'] == tipo]
        if tipo == 'Niñas/os':
            color_relleno = 'skyblue'
            color_borde = 'deepskyblue'
        else:
            color_relleno = 'salmon'
            color_borde = 'indianred' 
        fig3.add_trace(go.Bar(
            x =df_filtrado['Género'],
            y = df_filtrado['Porcentaje'],
            name= tipo, 
            text=df_filtrado['Porcentaje'].apply(lambda x: f"{x:.2f}%"),
            textposition= 'auto',
            marker=dict(color=color_relleno,line=dict(color=color_borde, width=1.5))
            ))

    fig3.update_layout(
        barmode='group',
        title="Gráfico género según tipo",
        title_font= dict(weight="bold"),
        title_x=0.5,
        yaxis=dict(title="Porcentaje", range=[0, 100], gridcolor='lightgray',
                   zerolinecolor='lightgray', ticksuffix='%'),
        xaxis_title="Género",
        plot_bgcolor = 'white',
        bargap=0.1,
        bargroupgap=0.1,
        autosize= True,
    )

    grafico_genero_zona_html = fig.to_html()
    grafico_genero_dependencia_html = fig2.to_html()
    grafico_genero_tipo_html = fig3.to_html()

    return render(request, 'educacion/graficos_basica_2021.html', {'grafico_html': grafico_genero_zona_html,
                                                      'grafico_dependencia_html': grafico_genero_dependencia_html,
                                                      'grafico_tipo_html': grafico_genero_tipo_html,
                                                      'region': region_seleccionada})

def grafico_matricula_basica_2020 (request):

    categorias_genero = {
        1: "Masculino",
        2: "Femenino",
    }

    categorias_rural = {
        0:"Urbano",
        1:"Rural",
    }

    categorias_dependencia = {
        1:"Municipal",
        2:"Particular Subvencionado",
        3:"Particular Pagado",
        4:"Corporación de Administración Delegada",
        5:"Servicio Local de Educación",
    }

    tipo_enseñanza = {
        2: "Niñas/os",
        3: "Adultas/os"
    }

    tipo2_enseñanza = {
        3: "Enseñanza Básica Regular",
        4: "Enseñanza Básica Especial",
        9: "Educación Básica Adultos"
    }

    # Obtener la región seleccionada desde la URL (por defecto muestra todos)
    region_seleccionada = request.GET.get('NOM_REG_RBD_A', "RM")

    datos = matricula_basica.objects.filter(AGNO=2020, GEN_ALU__in= [1, 2])
    
    # Obtener datos del modelo, filtrando por región si se especifica
    if region_seleccionada:
        datos = datos.filter(NOM_REG_RBD_A=region_seleccionada)

    datos= datos.values('GEN_ALU','RURAL_RBD','COD_DEPE2','COD_ENSE2','ENS')
    df = pd.DataFrame(datos)

    df['GEN_ALU'] = df['GEN_ALU'].map(categorias_genero)
    df['RURAL_RBD'] = df['RURAL_RBD'].map(categorias_rural)
    df['COD_DEPE2'] = df['COD_DEPE2'].map(categorias_dependencia)
    df['COD_ENSE2'] = df['COD_ENSE2'].map(tipo_enseñanza)
    df['ENS'] = df['ENS'].map(tipo2_enseñanza)

     # Contar cuántos hay de cada género
    conteo = df.groupby(['GEN_ALU','RURAL_RBD']).size().reset_index(name='Cantidad')
    conteo.columns = ['Género','Zona','Cantidad']
    

    # Convertir "Género" a tipo string (para que no sea numérico)
    conteo['Género'] = conteo['Género'].astype(str)
    conteo['Zona'] = conteo['Zona'].astype(str)
    conteo = conteo.dropna(subset=['Zona'])

    # Calcular el total por zona para obtener porcentajes
    totales_por_zona = conteo.groupby('Género')['Cantidad'].transform('sum')
    conteo['Porcentaje'] = (conteo['Cantidad'] / totales_por_zona) * 100


# Crear la figura manualmente
    fig = go.Figure()

    for zona in conteo['Zona'].unique():
        df_filtrado = conteo[conteo['Zona'] == zona]
        if zona == 'Urbano':
            color_relleno = 'skyblue'
            color_borde = 'deepskyblue'  # Más oscuro que skyblue
        else: 
            color_relleno = 'salmon'
            color_borde = 'indianred' 
        fig.add_trace(go.Bar(
            x=df_filtrado['Género'],
            y=df_filtrado['Porcentaje'],
            name=zona,  # Esto agrupará las barras por zona
            text=df_filtrado['Porcentaje'].apply(lambda x: f"{x:.2f}%"),  # Muestra los valores en las barras
            textposition='auto',
            marker=dict(color=color_relleno,line=dict(color=color_borde, width=1.5))
        ))

    fig.update_layout(
        barmode='group', 
        title="Gráfico género según zona",
        title_font= dict(weight="bold"),
        title_x=0.5,
        yaxis=dict(title="Porcentaje", ticksuffix="%", range=[0, 100], gridcolor='lightgray',
                   zerolinecolor='lightgray'),
        xaxis_title="Género",
        plot_bgcolor='white', # fondo del grafico
        bargap=0.2, 
        bargroupgap=0.1,  
        autosize= True
    )

### **Gráfico 2: Distribución género segun dependencia**

    conteo_dependencia = df.groupby(['GEN_ALU','COD_DEPE2']).size().reset_index(name='Cantidad')
    conteo_dependencia.columns = ['Género','Dependencia', 'Cantidad']

# Calcular porcentaje total
    totales_por_dependencia = conteo_dependencia.groupby('Género')['Cantidad'].transform('sum')
    conteo_dependencia['Porcentaje'] = (conteo_dependencia['Cantidad'] / totales_por_dependencia) * 100

    fig2 = make_subplots(
        rows=2, cols=1, 
        specs=[[{'type': 'domain'}], [{'type': 'domain'}]],
        subplot_titles=[
            'Distribución por dependencia - Mujeres', 
            'Distribución por dependencia - Hombres'
        ]
    )

# Filtrar por género
    generos = conteo_dependencia['Género'].unique()

    for i, genero in enumerate(generos):
        df_genero = conteo_dependencia[conteo_dependencia['Género'] == genero]
        
        fig2.add_trace(
            go.Pie(
                labels=df_genero['Dependencia'],
                values=df_genero['Cantidad'],
                name=genero,
                textinfo='percent',
                hoverinfo='percent+value'
            ),
            row=i+1, col=1
        )

    fig2.update_layout(
        title_text="Distribución por dependencia administrativa según género",
        title_font=dict(weight="bold"),
        title_x=0.5,
        showlegend=True,
        autosize=True,
        height=650,
        legend=dict(orientation="h", yanchor="bottom", y=-0.4, xanchor="center", x=0.5) 
    )

### **Gráfico 3: Distribución género segun tipo**

    conteo_tipo = df.groupby(['GEN_ALU','COD_ENSE2']).size().reset_index(name='Cantidad')
    conteo_tipo.columns = ['Género','Tipo', 'Cantidad']

# Calcular porcentaje total
    totales_por_tipo = conteo_tipo.groupby('Género')['Cantidad'].transform('sum')
    conteo_tipo['Porcentaje'] = (conteo_tipo['Cantidad'] / totales_por_tipo) * 100

    fig3 = go.Figure()

    for tipo in conteo_tipo['Tipo'].unique():
        df_filtrado = conteo_tipo[conteo_tipo['Tipo'] == tipo]
        if tipo == 'Niñas/os':
            color_relleno = 'skyblue'
            color_borde = 'deepskyblue'
        else:
            color_relleno = 'salmon'
            color_borde = 'indianred' 
        fig3.add_trace(go.Bar(
            x =df_filtrado['Género'],
            y = df_filtrado['Porcentaje'],
            name= tipo, 
            text=df_filtrado['Porcentaje'].apply(lambda x: f"{x:.2f}%"),
            textposition= 'auto',
            marker=dict(color=color_relleno,line=dict(color=color_borde, width=1.5))
            ))

    fig3.update_layout(
        barmode='group',
        title="Gráfico género según tipo",
        title_font= dict(weight="bold"),
        title_x=0.5,
        yaxis=dict(title="Porcentaje", range=[0, 100], gridcolor='lightgray',
                   zerolinecolor='lightgray', ticksuffix='%'),
        xaxis_title="Género",
        plot_bgcolor = 'white',
        bargap=0.1,
        bargroupgap=0.1,
        autosize= True,
    )

    grafico_genero_zona_html = fig.to_html()
    grafico_genero_dependencia_html = fig2.to_html()
    grafico_genero_tipo_html = fig3.to_html()

    return render(request, 'educacion/graficos_basica_2020.html', {'grafico_html': grafico_genero_zona_html,
                                                      'grafico_dependencia_html': grafico_genero_dependencia_html,
                                                      'grafico_tipo_html': grafico_genero_tipo_html,
                                                      'region': region_seleccionada})


#########################    GRAFICOS MATRICULA MEDIA  ########################################### 

def grafico_matricula_media_2023 (request):

    categorias_genero = {
        1: "Masculino",
        2: "Femenino",
    }

    categorias_rural = {
        0:"Urbano",
        1:"Rural",
    }

    categorias_dependencia = {
        1:"Municipal",
        2:"Particular Subvencionado",
        3:"Particular Pagado",
        4:"Corporación de Administración Delegada",
        5:"Servicio Local de Educación",
    }

    tipo_enseñanza = {
        5: "Jóvenes Científico-Humanísta",
        6: "Adultos Científico-Humanísta",
        7: "Jóvenes Técnico-Profesional",
        8: "Adultos Técnico-Profesional",
    }

    # Obtener la región seleccionada desde la URL 
    region_seleccionada = request.GET.get('NOM_REG_RBD_A', "RM")

    datos = matricula_media.objects.filter(AGNO=2023, GEN_ALU__in= [1, 2])
    
    # Obtener datos del modelo, filtrando por región si se especifica
    if region_seleccionada:
        datos = datos.filter(NOM_REG_RBD_A=region_seleccionada)

    datos= datos.values('GEN_ALU','RURAL_RBD','COD_DEPE2','COD_ENSE2')
    df = pd.DataFrame(datos)

    df['GEN_ALU'] = df['GEN_ALU'].map(categorias_genero)
    df['RURAL_RBD'] = df['RURAL_RBD'].map(categorias_rural)
    df['COD_DEPE2'] = df['COD_DEPE2'].map(categorias_dependencia)
    df['COD_ENSE2'] = df['COD_ENSE2'].map(tipo_enseñanza)


     # Contar cuántos hay de cada género
    conteo = df.groupby(['GEN_ALU','RURAL_RBD']).size().reset_index(name='Cantidad')
    conteo.columns = ['Género','Zona','Cantidad']
    

    # Convertir "Género" a tipo string (para que no sea numérico)
    conteo['Género'] = conteo['Género'].astype(str)
    conteo['Zona'] = conteo['Zona'].astype(str)
    conteo = conteo.dropna(subset=['Zona'])

    # Calcular el total por zona para obtener porcentajes
    totales_por_zona = conteo.groupby('Género')['Cantidad'].transform('sum')
    conteo['Porcentaje'] = (conteo['Cantidad'] / totales_por_zona) * 100


# Crear la figura manualmente
    fig = go.Figure()

    for zona in conteo['Zona'].unique():
        df_filtrado = conteo[conteo['Zona'] == zona]
        if zona == 'Urbano':
            color_relleno = 'skyblue'
            color_borde = 'deepskyblue'  # Más oscuro que skyblue
        else: 
            color_relleno = 'salmon'
            color_borde = 'indianred' 
        fig.add_trace(go.Bar(
            x=df_filtrado['Género'],
            y=df_filtrado['Porcentaje'],
            name=zona,  # Esto agrupará las barras por zona
            text=df_filtrado['Porcentaje'].apply(lambda x: f"{x:.2f}%"),  # Muestra los valores en las barras
            textposition='auto',
            marker=dict(color=color_relleno,line=dict(color=color_borde, width=1.5))
        ))

    fig.update_layout(
        barmode='group', 
        title="Gráfico género según zona",
        title_font= dict(weight="bold"),
        title_x=0.5,
        yaxis=dict(title="Porcentaje", ticksuffix="%", range=[0, 100], gridcolor='lightgray',
                   zerolinecolor='lightgray'),
        xaxis_title="Género",
        plot_bgcolor='white', # fondo del grafico
        bargap=0.2, 
        bargroupgap=0.1,  
        autosize= True
    )

### Gráfico 2: Distribución género segun dependencia

    conteo_dependencia = df.groupby(['GEN_ALU','COD_DEPE2']).size().reset_index(name='Cantidad')
    conteo_dependencia.columns = ['Género','Dependencia', 'Cantidad']

# Calcular porcentaje total
    totales_por_dependencia = conteo_dependencia.groupby('Género')['Cantidad'].transform('sum')
    conteo_dependencia['Porcentaje'] = (conteo_dependencia['Cantidad'] / totales_por_dependencia) * 100

    fig2 = make_subplots(
        rows=2, cols=1, 
        specs=[[{'type': 'domain'}], [{'type': 'domain'}]],
        subplot_titles=[
            'Distribución por dependencia - Mujeres', 
            'Distribución por dependencia - Hombres'
        ]
    )

# Filtrar por género
    generos = conteo_dependencia['Género'].unique()

    for i, genero in enumerate(generos):
        df_genero = conteo_dependencia[conteo_dependencia['Género'] == genero]
        
        fig2.add_trace(
            go.Pie(
                labels=df_genero['Dependencia'],
                values=df_genero['Cantidad'],
                name=genero,
                textinfo='percent',
                hoverinfo='percent+value'
            ),
            row=i+1, col=1
        )

    fig2.update_layout(
        title_text="Distribución por dependencia administrativa según género",
        title_font=dict(weight="bold"),
        title_x=0.5,
        showlegend=True,
        autosize=True,
        height=650,
        legend=dict(orientation="h", yanchor="bottom", y=-0.4, xanchor="center", x=0.5) 
    )

### Gráfico 3: Distribución género segun tipo de enseñanza

    conteo_tipo = df.groupby(['RURAL_RBD','COD_ENSE2']).size().reset_index(name='Cantidad')
    conteo_tipo.columns = ['Zona','Tipo', 'Cantidad']

# Calcular porcentaje total
    totales_por_tipo = conteo_tipo.groupby('Zona')['Cantidad'].transform('sum')
    conteo_tipo['Porcentaje'] = (conteo_tipo['Cantidad'] / totales_por_tipo) * 100

# Ordenar según valor ortiginal de la categoría
    conteo_tipo = conteo_tipo.sort_values(by='Tipo', key=lambda x: x.map({v: k for k, v in tipo_enseñanza.items()}))

    fig3 = make_subplots(
        rows=2, cols=1, 
        specs=[[{'type': 'domain'}], [{'type': 'domain'}]],
        subplot_titles=[
            'Distribución por tipo - Urbano', 
            'Distribución por tipo - Rural'
        ]
    )

# Filtrar por género
    zonas = conteo_tipo['Zona'].unique()

    for i, zona in enumerate(zonas):
        df_tipo = conteo_tipo[conteo_tipo['Zona'] == zona]
        
        fig3.add_trace(
            go.Pie(
                labels=df_tipo['Tipo'],
                values=df_tipo['Cantidad'],
                name=zona,
                textinfo='percent',
                hoverinfo='percent+value'
            ),
            row=i+1, col=1
        )

    fig3.update_layout(
        title_text="Distribución por tipo según zona",
        title_font=dict(weight="bold"),
        title_x=0.5,
        showlegend=True,
        autosize=True,
        height=650,
        legend=dict(orientation="h", yanchor="bottom", y=-0.4, xanchor="center", x=0.5) 
    )

    grafico_genero_zona_html = fig.to_html()
    grafico_genero_dependencia_html = fig2.to_html()
    grafico_zona_tipo_html = fig3.to_html()

    # Prueba de chi-cuadrado 
    tabla_tipo = pd.crosstab(df['RURAL_RBD'], df['COD_ENSE2'])
    chi2_tipo, p_tipo, _, _ = chi2_contingency(tabla_tipo)

    # Prueba V de Cramer
    def v_cramer (tabla_tipo):
        n = tabla_tipo.sum().sum()
        chi2_tipo, _, _, _ = chi2_contingency(tabla_tipo)
        phi2= chi2_tipo/n
        r, k = tabla_tipo.shape
        # Corregir phi2 (phi2corr) para evitar valores negativos
        phi2corr = max(0, phi2 - ((k - 1) * (r - 1)) / (n - 1))
        k_corr = k - (k - 1) * (k - 2) / (n - 1)
        r_corr = r - (r - 1) * (r - 2) / (n - 1)
        v = np.sqrt(phi2corr / min(k_corr - 1, r_corr - 1))
        
        return v
    va_cramer = v_cramer(tabla_tipo)


    return render(request, 'educacion/graficos_media_2023.html', {'grafico_html': grafico_genero_zona_html,
                                                      'grafico_dependencia_html': grafico_genero_dependencia_html,
                                                      'grafico_tipo_html': grafico_zona_tipo_html,
                                                      'chi2_tipo':round(chi2_tipo,2),
                                                      'p_tipo': round(p_tipo,2),
                                                      'va_cramer': round(va_cramer,2),
                                                      'region': region_seleccionada})

def grafico_matricula_media_2022 (request):

    categorias_genero = {
        1: "Masculino",
        2: "Femenino",
    }

    categorias_rural = {
        0:"Urbano",
        1:"Rural",
    }

    categorias_dependencia = {
        1:"Municipal",
        2:"Particular Subvencionado",
        3:"Particular Pagado",
        4:"Corporación de Administración Delegada",
        5:"Servicio Local de Educación",
    }

    tipo_enseñanza = {
        5: "Jóvenes Científico-Humanísta",
        6: "Adultos Científico-Humanísta",
        7: "Jóvenes Técnico-Profesional",
        8: "Adultos Técnico-Profesional",
    }

    # Obtener la región seleccionada desde la URL
    region_seleccionada = request.GET.get('NOM_REG_RBD_A', "RM")

    datos = matricula_media.objects.filter(AGNO=2022, GEN_ALU__in= [1, 2])
    
    # Obtener datos del modelo, filtrando por región si se especifica
    if region_seleccionada:
        datos = datos.filter(NOM_REG_RBD_A=region_seleccionada)

    datos= datos.values('GEN_ALU','RURAL_RBD','COD_DEPE2','COD_ENSE2')
    df = pd.DataFrame(datos)

    df['GEN_ALU'] = df['GEN_ALU'].map(categorias_genero)
    df['RURAL_RBD'] = df['RURAL_RBD'].map(categorias_rural)
    df['COD_DEPE2'] = df['COD_DEPE2'].map(categorias_dependencia)
    df['COD_ENSE2'] = df['COD_ENSE2'].map(tipo_enseñanza)


     # Contar cuántos hay de cada género
    conteo = df.groupby(['GEN_ALU','RURAL_RBD']).size().reset_index(name='Cantidad')
    conteo.columns = ['Género','Zona','Cantidad']
    

    # Convertir "Género" a tipo string (para que no sea numérico)
    conteo['Género'] = conteo['Género'].astype(str)
    conteo['Zona'] = conteo['Zona'].astype(str)
    conteo = conteo.dropna(subset=['Zona'])

    # Calcular el total por zona para obtener porcentajes
    totales_por_zona = conteo.groupby('Género')['Cantidad'].transform('sum')
    conteo['Porcentaje'] = (conteo['Cantidad'] / totales_por_zona) * 100


# Crear la figura manualmente
    fig = go.Figure()

    for zona in conteo['Zona'].unique():
        df_filtrado = conteo[conteo['Zona'] == zona]
        if zona == 'Urbano':
            color_relleno = 'skyblue'
            color_borde = 'deepskyblue'  # Más oscuro que skyblue
        else: 
            color_relleno = 'salmon'
            color_borde = 'indianred' 
        fig.add_trace(go.Bar(
            x=df_filtrado['Género'],
            y=df_filtrado['Porcentaje'],
            name=zona,  # Esto agrupará las barras por zona
            text=df_filtrado['Porcentaje'].apply(lambda x: f"{x:.2f}%"),  # Muestra los valores en las barras
            textposition='auto',
            marker=dict(color=color_relleno,line=dict(color=color_borde, width=1.5))
        ))

    fig.update_layout(
        barmode='group', 
        title="Gráfico género según zona",
        title_font= dict(weight="bold"),
        title_x=0.5,
        yaxis=dict(title="Porcentaje", ticksuffix="%", range=[0, 100], gridcolor='lightgray',
                   zerolinecolor='lightgray'),
        xaxis_title="Género",
        plot_bgcolor='white', # fondo del grafico
        bargap=0.2, 
        bargroupgap=0.1,  
        autosize= True
    )

### Gráfico 2: Distribución género segun dependencia

    conteo_dependencia = df.groupby(['GEN_ALU','COD_DEPE2']).size().reset_index(name='Cantidad')
    conteo_dependencia.columns = ['Género','Dependencia', 'Cantidad']

# Calcular porcentaje total
    totales_por_dependencia = conteo_dependencia.groupby('Género')['Cantidad'].transform('sum')
    conteo_dependencia['Porcentaje'] = (conteo_dependencia['Cantidad'] / totales_por_dependencia) * 100

    fig2 = make_subplots(
        rows=2, cols=1, 
        specs=[[{'type': 'domain'}], [{'type': 'domain'}]],
        subplot_titles=[
            'Distribución por dependencia - Mujeres', 
            'Distribución por dependencia - Hombres'
        ]
    )

# Filtrar por género
    generos = conteo_dependencia['Género'].unique()

    for i, genero in enumerate(generos):
        df_genero = conteo_dependencia[conteo_dependencia['Género'] == genero]
        
        fig2.add_trace(
            go.Pie(
                labels=df_genero['Dependencia'],
                values=df_genero['Cantidad'],
                name=genero,
                textinfo='percent',
                hoverinfo='percent+value'
            ),
            row=i+1, col=1
        )

    fig2.update_layout(
        title_text="Distribución por dependencia administrativa según género",
        title_font=dict(weight="bold"),
        title_x=0.5,
        showlegend=True,
        autosize=True,
        height=650,
        legend=dict(orientation="h", yanchor="bottom", y=-0.4, xanchor="center", x=0.5) 
    )

### Gráfico 3: Distribución género segun tipo de enseñanza

    conteo_tipo = df.groupby(['RURAL_RBD','COD_ENSE2']).size().reset_index(name='Cantidad')
    conteo_tipo.columns = ['Zona','Tipo', 'Cantidad']

# Calcular porcentaje total
    totales_por_tipo = conteo_tipo.groupby('Zona')['Cantidad'].transform('sum')
    conteo_tipo['Porcentaje'] = (conteo_tipo['Cantidad'] / totales_por_tipo) * 100
# Ordenar según valor ortiginal de la categoría
    conteo_tipo = conteo_tipo.sort_values(by='Tipo', key=lambda x: x.map({v: k for k, v in tipo_enseñanza.items()}))

    fig3 = make_subplots(
        rows=2, cols=1, 
        specs=[[{'type': 'domain'}], [{'type': 'domain'}]],
        subplot_titles=[
            'Distribución por tipo - Urbano', 
            'Distribución por tipo - Rural'
        ]
    )

# Filtrar por género
    zonas = conteo_tipo['Zona'].unique()

    for i, zona in enumerate(zonas):
        df_tipo = conteo_tipo[conteo_tipo['Zona'] == zona]
        
        fig3.add_trace(
            go.Pie(
                labels=df_tipo['Tipo'],
                values=df_tipo['Cantidad'],
                name=zona,
                textinfo='percent',
                hoverinfo='percent+value'
            ),
            row=i+1, col=1
        )

    fig3.update_layout(
        title_text="Distribución por tipo según zona",
        title_font=dict(weight="bold"),
        title_x=0.5,
        showlegend=True,
        autosize=True,
        height=650,
        legend=dict(orientation="h", yanchor="bottom", y=-0.4, xanchor="center", x=0.5) 
    )

    grafico_genero_zona_html = fig.to_html()
    grafico_genero_dependencia_html = fig2.to_html()
    grafico_zona_tipo_html = fig3.to_html()

    # Prueba de chi-cuadrado 
    tabla_tipo = pd.crosstab(df['RURAL_RBD'], df['COD_ENSE2'])
    chi2_tipo, p_tipo, _, _ = chi2_contingency(tabla_tipo)

    # Prueba V de Cramer
    def v_cramer (tabla_tipo):
        n = tabla_tipo.sum().sum()
        chi2_tipo, _, _, _ = chi2_contingency(tabla_tipo)
        phi2= chi2_tipo/n
        r, k = tabla_tipo.shape
        # Corregir phi2 (phi2corr) para evitar valores negativos
        phi2corr = max(0, phi2 - ((k - 1) * (r - 1)) / (n - 1))
        k_corr = k - (k - 1) * (k - 2) / (n - 1)
        r_corr = r - (r - 1) * (r - 2) / (n - 1)
        v = np.sqrt(phi2corr / min(k_corr - 1, r_corr - 1))
        
        return v
    va_cramer = v_cramer(tabla_tipo)

    return render(request, 'educacion/graficos_media_2022.html', {'grafico_html': grafico_genero_zona_html,
                                                      'grafico_dependencia_html': grafico_genero_dependencia_html,
                                                      'grafico_tipo_html': grafico_zona_tipo_html,
                                                      'chi2_tipo':round(chi2_tipo,2),
                                                      'p_tipo': round(p_tipo,2),
                                                      'va_cramer':round(va_cramer,2),
                                                      'region': region_seleccionada})

def grafico_matricula_media_2021 (request):

    categorias_genero = {
        1: "Masculino",
        2: "Femenino",
    }

    categorias_rural = {
        0:"Urbano",
        1:"Rural",
    }

    categorias_dependencia = {
        1:"Municipal",
        2:"Particular Subvencionado",
        3:"Particular Pagado",
        4:"Corporación de Administración Delegada",
        5:"Servicio Local de Educación",
    }

    tipo_enseñanza = {
        5: "Jóvenes Científico-Humanísta",
        6: "Adultos Científico-Humanísta",
        7: "Jóvenes Técnico-Profesional",
        8: "Adultos Técnico-Profesional",
    }

    # Obtener la región seleccionada desde la URL 
    region_seleccionada = request.GET.get('NOM_REG_RBD_A', "RM")

    datos = matricula_media.objects.filter(AGNO=2021, GEN_ALU__in= [1, 2])
    
    if region_seleccionada:
        datos = datos.filter(NOM_REG_RBD_A=region_seleccionada)

    datos= datos.values('GEN_ALU','RURAL_RBD','COD_DEPE2','COD_ENSE2')
    df = pd.DataFrame(datos)

    # Reemplazar los números con los nombres de género
    df['GEN_ALU'] = df['GEN_ALU'].map(categorias_genero)
    df['RURAL_RBD'] = df['RURAL_RBD'].map(categorias_rural)
    df['COD_DEPE2'] = df['COD_DEPE2'].map(categorias_dependencia)
    df['COD_ENSE2'] = df['COD_ENSE2'].map(tipo_enseñanza)


     # Contar cuántos hay de cada género
    conteo = df.groupby(['GEN_ALU','RURAL_RBD']).size().reset_index(name='Cantidad')
    conteo.columns = ['Género','Zona','Cantidad']
    

    # Convertir "Género" a tipo string (para que no sea numérico)
    conteo['Género'] = conteo['Género'].astype(str)
    conteo['Zona'] = conteo['Zona'].astype(str)
    conteo = conteo.dropna(subset=['Zona'])

    # Calcular el total por zona para obtener porcentajes
    totales_por_zona = conteo.groupby('Género')['Cantidad'].transform('sum')
    conteo['Porcentaje'] = (conteo['Cantidad'] / totales_por_zona) * 100

    fig = go.Figure()

    for zona in conteo['Zona'].unique():
        df_filtrado = conteo[conteo['Zona'] == zona]
        if zona == 'Urbano':
            color_relleno = 'skyblue'
            color_borde = 'deepskyblue'  # Más oscuro que skyblue
        else: 
            color_relleno = 'salmon'
            color_borde = 'indianred' 
        fig.add_trace(go.Bar(
            x=df_filtrado['Género'],
            y=df_filtrado['Porcentaje'],
            name=zona,  # Esto agrupará las barras por zona
            text=df_filtrado['Porcentaje'].apply(lambda x: f"{x:.2f}%"),  # Muestra los valores en las barras
            textposition='auto',
            marker=dict(color=color_relleno,line=dict(color=color_borde, width=1.5))
        ))

    fig.update_layout(
        barmode='group', 
        title="Gráfico género según zona",
        title_font= dict(weight="bold"),
        title_x=0.5,
        yaxis=dict(title="Porcentaje", ticksuffix="%", range=[0, 100], gridcolor='lightgray',
                   zerolinecolor='lightgray'),
        xaxis_title="Género",
        plot_bgcolor='white', # fondo del grafico
        bargap=0.2, 
        bargroupgap=0.1,  
        autosize= True
    )

### **Gráfico 2: Distribución género segun dependencia

    conteo_dependencia = df.groupby(['GEN_ALU','COD_DEPE2']).size().reset_index(name='Cantidad')
    conteo_dependencia.columns = ['Género','Dependencia', 'Cantidad']

# Calcular porcentaje total
    totales_por_dependencia = conteo_dependencia.groupby('Género')['Cantidad'].transform('sum')
    conteo_dependencia['Porcentaje'] = (conteo_dependencia['Cantidad'] / totales_por_dependencia) * 100

    fig2 = make_subplots(
        rows=2, cols=1, 
        specs=[[{'type': 'domain'}], [{'type': 'domain'}]],
        subplot_titles=[
            'Distribución por dependencia - Mujeres', 
            'Distribución por dependencia - Hombres'
        ]
    )

# Filtrar por género
    generos = conteo_dependencia['Género'].unique()

    for i, genero in enumerate(generos):
        df_genero = conteo_dependencia[conteo_dependencia['Género'] == genero]
        
        fig2.add_trace(
            go.Pie(
                labels=df_genero['Dependencia'],
                values=df_genero['Cantidad'],
                name=genero,
                textinfo='percent',
                hoverinfo='percent+value'
            ),
            row=i+1, col=1
        )

    fig2.update_layout(
        title_text="Distribución por dependencia administrativa según género",
        title_font=dict(weight="bold"),
        title_x=0.5,
        showlegend=True,
        autosize=True,
        height=650,
        legend=dict(orientation="h", yanchor="bottom", y=-0.4, xanchor="center", x=0.5) 
    )

### **Gráfico 3: Distribución género segun tipo de enseñanza

    conteo_tipo = df.groupby(['RURAL_RBD','COD_ENSE2']).size().reset_index(name='Cantidad')
    conteo_tipo.columns = ['Zona','Tipo', 'Cantidad']

# Calcular porcentaje total
    totales_por_tipo = conteo_tipo.groupby('Zona')['Cantidad'].transform('sum')
    conteo_tipo['Porcentaje'] = (conteo_tipo['Cantidad'] / totales_por_tipo) * 100
# Ordenar según valor ortiginal de la categoría
    conteo_tipo = conteo_tipo.sort_values(by='Tipo', key=lambda x: x.map({v: k for k, v in tipo_enseñanza.items()}))

    fig3 = make_subplots(
        rows=2, cols=1, 
        specs=[[{'type': 'domain'}], [{'type': 'domain'}]],
        subplot_titles=[
            'Distribución por tipo - Urbano', 
            'Distribución por tipo - Rural'
        ]
    )

# Filtrar por género
    zonas = conteo_tipo['Zona'].unique()

    for i, zona in enumerate(zonas):
        df_tipo = conteo_tipo[conteo_tipo['Zona'] == zona]
        
        fig3.add_trace(
            go.Pie(
                labels=df_tipo['Tipo'],
                values=df_tipo['Cantidad'],
                name=zona,
                textinfo='percent',
                hoverinfo='percent+value'
            ),
            row=i+1, col=1
        )

    fig3.update_layout(
        title_text="Distribución por tipo según zona",
        title_font=dict(weight="bold"),
        title_x=0.5,
        showlegend=True,
        autosize=True,
        height=650,
        legend=dict(orientation="h", yanchor="bottom", y=-0.4, xanchor="center", x=0.5) 
    )

    grafico_genero_zona_html = fig.to_html()
    grafico_genero_dependencia_html = fig2.to_html()
    grafico_zona_tipo_html = fig3.to_html()

    # Prueba de chi-cuadrado 
    tabla_tipo = pd.crosstab(df['RURAL_RBD'], df['COD_ENSE2'])
    chi2_tipo, p_tipo, _, _ = chi2_contingency(tabla_tipo)

    # Prueba V de Cramer
    def v_cramer (tabla_tipo):
        n = tabla_tipo.sum().sum()
        chi2_tipo, _, _, _ = chi2_contingency(tabla_tipo)
        phi2= chi2_tipo/n
        r, k = tabla_tipo.shape
        # Corregir phi2 (phi2corr) para evitar valores negativos
        phi2corr = max(0, phi2 - ((k - 1) * (r - 1)) / (n - 1))
        k_corr = k - (k - 1) * (k - 2) / (n - 1)
        r_corr = r - (r - 1) * (r - 2) / (n - 1)
        v = np.sqrt(phi2corr / min(k_corr - 1, r_corr - 1))
        
        return v
    va_cramer = v_cramer(tabla_tipo)

    return render(request, 'educacion/graficos_media_2021.html', {'grafico_html': grafico_genero_zona_html,
                                                      'grafico_dependencia_html': grafico_genero_dependencia_html,
                                                      'grafico_tipo_html': grafico_zona_tipo_html,
                                                      'chi2_tipo':round(chi2_tipo,2),
                                                      'p_tipo':round(p_tipo,2),
                                                      'va_cramer': round(va_cramer,2),
                                                      'region': region_seleccionada})

def grafico_matricula_media_2020 (request):


    categorias_genero = {
        1: "Masculino",
        2: "Femenino",
    }

    categorias_rural = {
        0:"Urbano",
        1:"Rural",
    }

    categorias_dependencia = {
        1:"Municipal",
        2:"Particular Subvencionado",
        3:"Particular Pagado",
        4:"Corporación de Administración Delegada",
        5:"Servicio Local de Educación",
    }

    tipo_enseñanza = {
        5: "Jóvenes Científico-Humanísta",
        6: "Adultos Científico-Humanísta",
        7: "Jóvenes Técnico-Profesional",
        8: "Adultos Técnico-Profesional",
    }

    # Obtener la región seleccionada desde la URL 
    region_seleccionada = request.GET.get('NOM_REG_RBD_A', "RM")

    datos = matricula_media.objects.filter(AGNO=2020, GEN_ALU__in= [1, 2])
    
    # Obtener datos del modelo, filtrando por región si se especifica
    if region_seleccionada:
        datos = datos.filter(NOM_REG_RBD_A=region_seleccionada)

    datos= datos.values('GEN_ALU','RURAL_RBD','COD_DEPE2','COD_ENSE2')
    df = pd.DataFrame(datos)

    # Reemplazar los números con los nombres de género
    df['GEN_ALU'] = df['GEN_ALU'].map(categorias_genero)
    df['RURAL_RBD'] = df['RURAL_RBD'].map(categorias_rural)
    df['COD_DEPE2'] = df['COD_DEPE2'].map(categorias_dependencia)
    df['COD_ENSE2'] = df['COD_ENSE2'].map(tipo_enseñanza)


     # Contar cuántos hay de cada género
    conteo = df.groupby(['GEN_ALU','RURAL_RBD']).size().reset_index(name='Cantidad')
    conteo.columns = ['Género','Zona','Cantidad']
    

    # Convertir "Género" a tipo string (para que no sea numérico)
    conteo['Género'] = conteo['Género'].astype(str)
    conteo['Zona'] = conteo['Zona'].astype(str)
    conteo = conteo.dropna(subset=['Zona'])

    # Calcular el total por zona para obtener porcentajes
    totales_por_zona = conteo.groupby('Género')['Cantidad'].transform('sum')
    conteo['Porcentaje'] = (conteo['Cantidad'] / totales_por_zona) * 100


    fig = go.Figure()

    for zona in conteo['Zona'].unique():
        df_filtrado = conteo[conteo['Zona'] == zona]
        if zona == 'Urbano':
            color_relleno = 'skyblue'
            color_borde = 'deepskyblue'  # Más oscuro que skyblue
        else: 
            color_relleno = 'salmon'
            color_borde = 'indianred' 
        fig.add_trace(go.Bar(
            x=df_filtrado['Género'],
            y=df_filtrado['Porcentaje'],
            name=zona,  # Esto agrupará las barras por zona
            text=df_filtrado['Porcentaje'].apply(lambda x: f"{x:.2f}%"),  # Muestra los valores en las barras
            textposition='auto',
            marker=dict(color=color_relleno,line=dict(color=color_borde, width=1.5))
        ))

    fig.update_layout(
        barmode='group', 
        title="Gráfico género según zona",
        title_font= dict(weight="bold"),
        title_x=0.5,
        yaxis=dict(title="Porcentaje", ticksuffix="%", range=[0, 100], gridcolor='lightgray',
                   zerolinecolor='lightgray'),
        xaxis_title="Género",
        plot_bgcolor='white', # fondo del grafico
        bargap=0.2, 
        bargroupgap=0.1,  
        autosize= True
    )

### **Gráfico 2: Distribución género segun dependencia

    conteo_dependencia = df.groupby(['GEN_ALU','COD_DEPE2']).size().reset_index(name='Cantidad')
    conteo_dependencia.columns = ['Género','Dependencia', 'Cantidad']

# Calcular porcentaje total
    totales_por_dependencia = conteo_dependencia.groupby('Género')['Cantidad'].transform('sum')
    conteo_dependencia['Porcentaje'] = (conteo_dependencia['Cantidad'] / totales_por_dependencia) * 100

    fig2 = make_subplots(
        rows=2, cols=1, 
        specs=[[{'type': 'domain'}], [{'type': 'domain'}]],
        subplot_titles=[
            'Distribución por dependencia - Mujeres', 
            'Distribución por dependencia - Hombres'
        ]
    )

# Filtrar por género
    generos = conteo_dependencia['Género'].unique()

    for i, genero in enumerate(generos):
        df_genero = conteo_dependencia[conteo_dependencia['Género'] == genero]
        
        fig2.add_trace(
            go.Pie(
                labels=df_genero['Dependencia'],
                values=df_genero['Cantidad'],
                name=genero,
                textinfo='percent',
                hoverinfo='percent+value'
            ),
            row=i+1, col=1
        )

    fig2.update_layout(
        title_text="Distribución por dependencia administrativa según género",
        title_font=dict(weight="bold"),
        title_x=0.5,
        showlegend=True,
        autosize=True,
        height=650,
        legend=dict(orientation="h", yanchor="bottom", y=-0.4, xanchor="center", x=0.5) 
    )

### **Gráfico 3: Distribución zona segun tipo de enseñanza

    conteo_tipo = df.groupby(['RURAL_RBD','COD_ENSE2']).size().reset_index(name='Cantidad')
    conteo_tipo.columns = ['Zona','Tipo', 'Cantidad']

# Calcular porcentaje total
    totales_por_tipo = conteo_tipo.groupby('Zona')['Cantidad'].transform('sum')
    conteo_tipo['Porcentaje'] = (conteo_tipo['Cantidad'] / totales_por_tipo) * 100

    fig3 = make_subplots(
        rows=2, cols=1, 
        specs=[[{'type': 'domain'}], [{'type': 'domain'}]],
        subplot_titles=[
            'Distribución por tipo - Urbano', 
            'Distribución por tipo - Rural'
        ]
    )

# Filtrar por género
    zonas = conteo_tipo['Zona'].unique()

    for i, zona in enumerate(zonas):
        df_tipo = conteo_tipo[conteo_tipo['Zona'] == zona]
        
        fig3.add_trace(
            go.Pie(
                labels=df_tipo['Tipo'],
                values=df_tipo['Cantidad'],
                name=zona,
                textinfo='percent',
                hoverinfo='percent+value'
            ),
            row=i+1, col=1
        )

    fig3.update_layout(
        title_text="Distribución por tipo según zona",
        title_font=dict(weight="bold"),
        title_x=0.5,
        showlegend=True,
        autosize=True,
        height=650,
        legend=dict(orientation="h", yanchor="bottom", y=-0.4, xanchor="center", x=0.5) 
    )

    grafico_genero_zona_html = fig.to_html()
    grafico_genero_dependencia_html = fig2.to_html()
    grafico_zona_tipo_html = fig3.to_html()

    # Prueba de chi-cuadrado 
    tabla_tipo = pd.crosstab(df['RURAL_RBD'], df['COD_ENSE2'])
    chi2_tipo, p_tipo, _, _ = chi2_contingency(tabla_tipo)

        # Prueba V de Cramer
    def v_cramer (tabla_tipo):
        n = tabla_tipo.sum().sum()
        chi2_tipo, _, _, _ = chi2_contingency(tabla_tipo)
        phi2= chi2_tipo/n
        r, k = tabla_tipo.shape
        # Corregir phi2 (phi2corr) para evitar valores negativos
        phi2corr = max(0, phi2 - ((k - 1) * (r - 1)) / (n - 1))
        k_corr = k - (k - 1) * (k - 2) / (n - 1)
        r_corr = r - (r - 1) * (r - 2) / (n - 1)
        v = np.sqrt(phi2corr / min(k_corr - 1, r_corr - 1))
        
        return v
    va_cramer = v_cramer(tabla_tipo)

    return render(request, 'educacion/graficos_media_2020.html', {'grafico_html': grafico_genero_zona_html,
                                                      'grafico_dependencia_html': grafico_genero_dependencia_html,
                                                      'grafico_tipo_html': grafico_zona_tipo_html,
                                                      'chi2_tipo': round(chi2_tipo,2),
                                                      'p_tipo': round(p_tipo,2),
                                                      'va_cramer': round(va_cramer,2),
                                                      'region': region_seleccionada})

#########################    GRAFICOS MATRICULA SUPERIOR  ########################################### 

def grafico_matricula_superior_2024 (request):

    categorias_genero = {
        1 : "Masculino",
        2 : "Femenino"
    }

    # Obtener la región seleccionada desde la URL 
    region_seleccionada = request.GET.get('region_sede', "Metropolitana")

    datos = matricula_superior.objects.filter(cat_periodo=2024).exclude(rango_edad='Sin Información')
    
    # Obtener datos del modelo, filtrando por región si se especifica
    if region_seleccionada:
        datos = datos.filter(region_sede=region_seleccionada)

    datos= datos.values('cat_periodo','region_sede','gen_alu','rango_edad','tipo_inst_1','tipo_inst_2',
                        'nomb_inst','modalidad','jornada','nivel_global','area_conocimiento','dur_estudio_carr',
                        'nivel_carrera_2','acreditada_carr')
    df = pd.DataFrame(datos)

    df['gen_alu']= df['gen_alu'].map(categorias_genero)

     # Contar cuántos hay de cada género
    conteo = df.groupby(['gen_alu','rango_edad']).size().reset_index(name='Cantidad')
    conteo.columns = ['Género','Edad','Cantidad']
    
    # Calcular el total por zona para obtener porcentajes
    totales_por_edad = conteo.groupby('Género')['Cantidad'].transform('sum')
    conteo['Porcentaje'] = (conteo['Cantidad'] / totales_por_edad) * 100


# Crear la figura manualmente
    fig = make_subplots(
        rows=2, cols=1, 
        specs=[[{'type': 'domain'}], [{'type': 'domain'}]],
        subplot_titles=[
            'Distribución por dependencia - Mujeres', 
            'Distribución por dependencia - Hombres'
        ]
    )

# Filtrar por género
    generos = conteo['Género'].unique()

    for i, genero in enumerate(generos):
        df_genero = conteo[conteo['Género'] == genero]
        
        fig.add_trace(
            go.Pie(
                labels=df_genero['Edad'],
                values=df_genero['Cantidad'],
                name=genero,
                textinfo='percent',
                hoverinfo='percent+value'
            ),
            row=i+1, col=1
        )

    fig.update_layout(
        title_text="Distribución por edades según género",
        title_font=dict(weight="bold"),
        title_x=0.5,
        showlegend=True,
        autosize=True,
        height=650,
        legend=dict(orientation="h", yanchor="bottom", y=-0.4, xanchor="center", x=0.5) 
    )

### Gráfico 2: Distribución género segun dependencia

    conteo_tipo = df.groupby(['gen_alu','tipo_inst_1']).size().reset_index(name='Cantidad')
    conteo_tipo.columns = ['Género','Tipo Institucion', 'Cantidad']

# Calcular porcentaje total
    totales_por_tipo = conteo_tipo.groupby('Género')['Cantidad'].transform('sum')
    conteo_tipo['Porcentaje'] = (conteo_tipo['Cantidad'] / totales_por_tipo) * 100

    fig2 = go.Figure()

    for tipo in conteo_tipo['Tipo Institucion'].unique():
        df_filtrado = conteo_tipo[conteo_tipo['Tipo Institucion'] == tipo]
        fig2.add_trace(go.Bar(
            x =df_filtrado['Género'],
            y = df_filtrado['Porcentaje'],
            name= tipo, 
            text=df_filtrado['Porcentaje'].apply(lambda x: f"{x:.2f}%"),
            textposition= 'auto'
            ))

    fig2.update_layout(
        barmode='group',
        title="Gráfico género según Tipo de Institución",
        title_font= dict(weight="bold"),
        title_x=0.5,
        yaxis=dict(title="Porcentaje",  range=[0, 100]),
        xaxis_title="Género",
        bargap=0.1,
        bargroupgap=0.1,
        autosize= True,
    )

### Gráfico 3: Distribución género segun tipo de enseñanza

    conteo_area = df.groupby(['gen_alu','area_conocimiento']).size().reset_index(name='Cantidad')
    conteo_area.columns = ['Genero','Area Conocimiento', 'Cantidad']

# Calcular porcentaje total
    totales_por_area = conteo_area.groupby('Genero')['Cantidad'].transform('sum')
    conteo_area['Porcentaje'] = (conteo_area['Cantidad'] / totales_por_area) * 100

    fig3 = go.Figure()

    for area in conteo_area['Area Conocimiento'].unique():
        df_filtrado = conteo_area[conteo_area['Area Conocimiento'] == area]
        fig3.add_trace(go.Bar(
            x =df_filtrado['Genero'],
            y = df_filtrado['Porcentaje'],
            name= area, 
            text=df_filtrado['Porcentaje'].apply(lambda x: f"{x:.2f}%"),
            textposition= 'auto'
            ))

    fig3.update_layout(
        barmode='group',
        title="Gráfico género según tipo",
        title_font= dict(weight="bold"),
        title_x=0.5,
        yaxis=dict(title="Porcentaje", range=[0, 60]),
        xaxis_title="Género",
        bargap=0.1,
        bargroupgap=0.1,
        autosize= True,
    )

    grafico_genero_edad_html = fig.to_html()
    grafico_genero_tipo_html = fig2.to_html()
    grafico_genero_area_html = fig3.to_html()

    return render(request, 'educacion/graficos_superior_2024.html', {'grafico_html': grafico_genero_edad_html,
                                                      'grafico_tipo_html': grafico_genero_tipo_html,
                                                      'grafico_area_html': grafico_genero_area_html,
                                                      'region': region_seleccionada})

def grafico_matricula_superior_2023 (request):

    categorias_genero = {
        1 : "Masculino",
        2 : "Femenino"
    }


        # Obtener la región seleccionada desde la URL 
    region_seleccionada = request.GET.get('region_sede', "Metropolitana")

    datos = matricula_superior.objects.filter(cat_periodo=2023).exclude(rango_edad='Sin Información')
    
    # Obtener datos del modelo, filtrando por región si se especifica
    if region_seleccionada:
        datos = datos.filter(region_sede=region_seleccionada)

    datos= datos.values('cat_periodo','region_sede','gen_alu','rango_edad','tipo_inst_1','tipo_inst_2',
                        'nomb_inst','modalidad','jornada','nivel_global','area_conocimiento','dur_estudio_carr',
                        'nivel_carrera_2','acreditada_carr')
    df = pd.DataFrame(datos)

    df['gen_alu']= df['gen_alu'].map(categorias_genero)

     # Contar cuántos hay de cada género
    conteo = df.groupby(['gen_alu','rango_edad']).size().reset_index(name='Cantidad')
    conteo.columns = ['Género','Edad','Cantidad']
    
    # Calcular el total por zona para obtener porcentajes
    totales_por_edad = conteo.groupby('Género')['Cantidad'].transform('sum')
    conteo['Porcentaje'] = (conteo['Cantidad'] / totales_por_edad) * 100


# Crear la figura manualmente
    fig = go.Figure()

    for edad in conteo['Edad'].unique():
        df_filtrado = conteo[conteo['Edad'] == edad]
        fig.add_trace(go.Bar(
            x=df_filtrado['Género'],
            y=df_filtrado['Porcentaje'],
            name=edad,  # Esto agrupará las barras por zona
            text=df_filtrado['Porcentaje'].apply(lambda x: f"{x:.2f}%"),  # Muestra los valores en las barras
            textposition='auto'
        ))

    fig.update_layout(
        barmode='group',  
        title="Gráfico género según edad",
        title_font= dict(weight="bold"),
        title_x=0.5,
        yaxis=dict(title="Porcentaje", range=[0, 100]),
        xaxis_title="Género",
        bargap=0.2,  
        bargroupgap=0.1,  
        autosize= True
    )

### Gráfico 2: Distribución género segun dependencia

    conteo_tipo = df.groupby(['gen_alu','tipo_inst_1']).size().reset_index(name='Cantidad')
    conteo_tipo.columns = ['Género','Tipo Institucion', 'Cantidad']

# Calcular porcentaje total
    totales_por_tipo = conteo_tipo.groupby('Género')['Cantidad'].transform('sum')
    conteo_tipo['Porcentaje'] = (conteo_tipo['Cantidad'] / totales_por_tipo) * 100

    fig2 = go.Figure()

    for tipo in conteo_tipo['Tipo Institucion'].unique():
        df_filtrado = conteo_tipo[conteo_tipo['Tipo Institucion'] == tipo]
        fig2.add_trace(go.Bar(
            x =df_filtrado['Género'],
            y = df_filtrado['Porcentaje'],
            name= tipo, 
            text=df_filtrado['Porcentaje'].apply(lambda x: f"{x:.2f}%"),
            textposition= 'auto'
            ))

    fig2.update_layout(
        barmode='group',
        title="Gráfico género según Tipo de Institución",
        title_font= dict(weight="bold"),
        title_x=0.5,
        yaxis=dict(title="Porcentaje", range=[0, 100]),
        xaxis_title="Género",
        bargap=0.1,
        bargroupgap=0.1,
        autosize= True,
    )

### Gráfico 3: Distribución género segun tipo de enseñanza

    conteo_area = df.groupby(['gen_alu','area_conocimiento']).size().reset_index(name='Cantidad')
    conteo_area.columns = ['Genero','Area Conocimiento', 'Cantidad']

# Calcular porcentaje total
    totales_por_area = conteo_area.groupby('Genero')['Cantidad'].transform('sum')
    conteo_area['Porcentaje'] = (conteo_area['Cantidad'] / totales_por_area) * 100

    fig3 = go.Figure()

    for area in conteo_area['Area Conocimiento'].unique():
        df_filtrado = conteo_area[conteo_area['Area Conocimiento'] == area]
        fig3.add_trace(go.Bar(
            x =df_filtrado['Genero'],
            y = df_filtrado['Porcentaje'],
            name= area, 
            text=df_filtrado['Porcentaje'].apply(lambda x: f"{x:.2f}%"),
            textposition= 'auto'
            ))

    fig3.update_layout(
        barmode='group',
        title="Gráfico género según tipo",
        title_font= dict(weight="bold"),
        title_x=0.5,
        yaxis=dict(title="Porcentaje", range=[0, 100]),
        xaxis_title="Zona",
        bargap=0.1,
        bargroupgap=0.1,
        autosize= True,
    )

    grafico_genero_edad_html = fig.to_html()
    grafico_genero_tipo_html = fig2.to_html()
    grafico_genero_area_html = fig3.to_html()

    return render(request, 'educacion/graficos_superior_2023.html', {'grafico_html': grafico_genero_edad_html,
                                                      'grafico_tipo_html': grafico_genero_tipo_html,
                                                      'grafico_area_html': grafico_genero_area_html,
                                                      'region': region_seleccionada})

def grafico_matricula_superior_2022 (request):

    categorias_genero = {
        1 : "Masculino",
        2 : "Femenino"
    }

        # Obtener la región seleccionada desde la URL 
    region_seleccionada = request.GET.get('region_sede', "Metropolitana")

    datos = matricula_superior.objects.filter(cat_periodo=2022).exclude(rango_edad='Sin Información')
    
    # Obtener datos del modelo, filtrando por región si se especifica
    if region_seleccionada:
        datos = datos.filter(region_sede=region_seleccionada)

    datos= datos.values('cat_periodo','region_sede','gen_alu','rango_edad','tipo_inst_1','tipo_inst_2',
                        'nomb_inst','modalidad','jornada','nivel_global','area_conocimiento','dur_estudio_carr',
                        'nivel_carrera_2','acreditada_carr')
    df = pd.DataFrame(datos)

    df['gen_alu'] = df['gen_alu'].map(categorias_genero)

     # Contar cuántos hay de cada género
    conteo = df.groupby(['gen_alu','rango_edad']).size().reset_index(name='Cantidad')
    conteo.columns = ['Género','Edad','Cantidad']
    
    # Calcular el total por zona para obtener porcentajes
    totales_por_edad = conteo.groupby('Género')['Cantidad'].transform('sum')
    conteo['Porcentaje'] = (conteo['Cantidad'] / totales_por_edad) * 100


# Crear la figura manualmente
    fig = go.Figure()

    for edad in conteo['Edad'].unique():
        df_filtrado = conteo[conteo['Edad'] == edad]
        fig.add_trace(go.Bar(
            x=df_filtrado['Género'],
            y=df_filtrado['Porcentaje'],
            name=edad,  # Esto agrupará las barras por zona
            text=df_filtrado['Porcentaje'].apply(lambda x: f"{x:.2f}%"),  # Muestra los valores en las barras
            textposition='auto'
        ))

    fig.update_layout(
        barmode='group',  
        title="Gráfico género según edad",
        title_font= dict(weight="bold"),
        title_x=0.5,
        yaxis=dict(title="Porcentaje", range=[0, 100]),
        xaxis_title="Género",
        bargap=0.2,  
        bargroupgap=0.1,  
        autosize= True
    )

### Gráfico 2: Distribución género segun dependencia

    conteo_tipo = df.groupby(['gen_alu','tipo_inst_1']).size().reset_index(name='Cantidad')
    conteo_tipo.columns = ['Género','Tipo Institucion', 'Cantidad']

# Calcular porcentaje total
    totales_por_tipo = conteo_tipo.groupby('Género')['Cantidad'].transform('sum')
    conteo_tipo['Porcentaje'] = (conteo_tipo['Cantidad'] / totales_por_tipo) * 100

    fig2 = go.Figure()

    for tipo in conteo_tipo['Tipo Institucion'].unique():
        df_filtrado = conteo_tipo[conteo_tipo['Tipo Institucion'] == tipo]
        fig2.add_trace(go.Bar(
            x =df_filtrado['Género'],
            y = df_filtrado['Porcentaje'],
            name= tipo, 
            text=df_filtrado['Porcentaje'].apply(lambda x: f"{x:.2f}%"),
            textposition= 'auto'
            ))

    fig2.update_layout(
        barmode='group',
        title="Gráfico género según Tipo de Institución",
        title_font= dict(weight="bold"),
        title_x=0.5,
        yaxis=dict(title="Porcentaje", range=[0, 100]),
        xaxis_title="Género",
        bargap=0.1,
        bargroupgap=0.1,
        autosize= True,
    )

### Gráfico 3: Distribución género segun tipo de enseñanza

    conteo_area = df.groupby(['gen_alu','area_conocimiento']).size().reset_index(name='Cantidad')
    conteo_area.columns = ['Genero','Area Conocimiento', 'Cantidad']

# Calcular porcentaje total
    totales_por_area = conteo_area.groupby('Genero')['Cantidad'].transform('sum')
    conteo_area['Porcentaje'] = (conteo_area['Cantidad'] / totales_por_area) * 100

    fig3 = go.Figure()

    for area in conteo_area['Area Conocimiento'].unique():
        df_filtrado = conteo_area[conteo_area['Area Conocimiento'] == area]
        fig3.add_trace(go.Bar(
            x =df_filtrado['Genero'],
            y = df_filtrado['Porcentaje'],
            name= area, 
            text=df_filtrado['Porcentaje'].apply(lambda x: f"{x:.2f}%"),
            textposition= 'auto'
            ))

    fig3.update_layout(
        barmode='group',
        title="Gráfico género según tipo",
        title_font= dict(weight="bold"),
        title_x=0.5,
        yaxis=dict(title="Porcentaje", range=[0, 100]),
        xaxis_title="Zona",
        bargap=0.1,
        bargroupgap=0.1,
        autosize= True,
    )

    grafico_genero_edad_html = fig.to_html()
    grafico_genero_tipo_html = fig2.to_html()
    grafico_genero_area_html = fig3.to_html()

    return render(request, 'educacion/graficos_superior_2022.html', {'grafico_html': grafico_genero_edad_html,
                                                      'grafico_tipo_html': grafico_genero_tipo_html,
                                                      'grafico_area_html': grafico_genero_area_html,
                                                      'region': region_seleccionada})

def grafico_matricula_superior_2021 (request):

    categorias_genero = {
        1 : "Masculino",
        2 : "Femenino"
    }

        # Obtener la región seleccionada desde la URL 
    region_seleccionada = request.GET.get('region_sede', "Metropolitana")

    datos = matricula_superior.objects.filter(cat_periodo=2021).exclude(rango_edad='Sin Información')
    
    # Obtener datos del modelo, filtrando por región si se especifica
    if region_seleccionada:
        datos = datos.filter(region_sede=region_seleccionada)

    datos= datos.values('cat_periodo','region_sede','gen_alu','rango_edad','tipo_inst_1','tipo_inst_2',
                        'nomb_inst','modalidad','jornada','nivel_global','area_conocimiento','dur_estudio_carr',
                        'nivel_carrera_2','acreditada_carr')
    df = pd.DataFrame(datos)

    df['gen_alu']= df['gen_alu'].map(categorias_genero)

     # Contar cuántos hay de cada género
    conteo = df.groupby(['gen_alu','rango_edad']).size().reset_index(name='Cantidad')
    conteo.columns = ['Género','Edad','Cantidad']
    
    # Calcular el total por zona para obtener porcentajes
    totales_por_edad = conteo.groupby('Género')['Cantidad'].transform('sum')
    conteo['Porcentaje'] = (conteo['Cantidad'] / totales_por_edad) * 100


# Crear la figura manualmente
    fig = go.Figure()

    for edad in conteo['Edad'].unique():
        df_filtrado = conteo[conteo['Edad'] == edad]
        fig.add_trace(go.Bar(
            x=df_filtrado['Género'],
            y=df_filtrado['Porcentaje'],
            name=edad,  # Esto agrupará las barras por zona
            text=df_filtrado['Porcentaje'].apply(lambda x: f"{x:.2f}%"),  # Muestra los valores en las barras
            textposition='auto'
        ))

    fig.update_layout(
        barmode='group',  
        title="Gráfico género según edad",
        title_font= dict(weight="bold"),
        title_x=0.5,
        yaxis=dict(title="Porcentaje", range=[0, 100]),
        xaxis_title="Género",
        bargap=0.2,  
        bargroupgap=0.1,  
        autosize= True
    )

### Gráfico 2: Distribución género segun dependencia

    conteo_tipo = df.groupby(['gen_alu','tipo_inst_1']).size().reset_index(name='Cantidad')
    conteo_tipo.columns = ['Género','Tipo Institucion', 'Cantidad']

# Calcular porcentaje total
    totales_por_tipo = conteo_tipo.groupby('Género')['Cantidad'].transform('sum')
    conteo_tipo['Porcentaje'] = (conteo_tipo['Cantidad'] / totales_por_tipo) * 100

    fig2 = go.Figure()

    for tipo in conteo_tipo['Tipo Institucion'].unique():
        df_filtrado = conteo_tipo[conteo_tipo['Tipo Institucion'] == tipo]
        fig2.add_trace(go.Bar(
            x =df_filtrado['Género'],
            y = df_filtrado['Porcentaje'],
            name= tipo, 
            text=df_filtrado['Porcentaje'].apply(lambda x: f"{x:.2f}%"),
            textposition= 'auto'
            ))

    fig2.update_layout(
        barmode='group',
        title="Gráfico género según Tipo de Institución",
        title_font= dict(weight="bold"),
        title_x=0.5,
        yaxis=dict(title="Porcentaje", range=[0, 100]),
        xaxis_title="Género",
        bargap=0.1,
        bargroupgap=0.1,
        autosize= True,
    )

### Gráfico 3: Distribución género segun tipo de enseñanza

    conteo_area = df.groupby(['gen_alu','area_conocimiento']).size().reset_index(name='Cantidad')
    conteo_area.columns = ['Genero','Area Conocimiento', 'Cantidad']

# Calcular porcentaje total
    totales_por_area = conteo_area.groupby('Genero')['Cantidad'].transform('sum')
    conteo_area['Porcentaje'] = (conteo_area['Cantidad'] / totales_por_area) * 100

    fig3 = go.Figure()

    for area in conteo_area['Area Conocimiento'].unique():
        df_filtrado = conteo_area[conteo_area['Area Conocimiento'] == area]
        fig3.add_trace(go.Bar(
            x =df_filtrado['Genero'],
            y = df_filtrado['Porcentaje'],
            name= area, 
            text=df_filtrado['Porcentaje'].apply(lambda x: f"{x:.2f}%"),
            textposition= 'auto'
            ))

    fig3.update_layout(
        barmode='group',
        title="Gráfico género según tipo",
        title_font= dict(weight="bold"),
        title_x=0.5,
        yaxis=dict(title="Porcentaje", range=[0, 100]),
        xaxis_title="Zona",
        bargap=0.1,
        bargroupgap=0.1,
        autosize= True,
    )

    grafico_genero_edad_html = fig.to_html()
    grafico_genero_tipo_html = fig2.to_html()
    grafico_genero_area_html = fig3.to_html()

    return render(request, 'educacion/graficos_superior_2021.html', {'grafico_html': grafico_genero_edad_html,
                                                      'grafico_tipo_html': grafico_genero_tipo_html,
                                                      'grafico_area_html': grafico_genero_area_html,
                                                      'region': region_seleccionada})

def grafico_matricula_superior_2020 (request):

    categorias_genero = {
        1 : "Masculino",
        2 : "Femenino"
    }

        # Obtener la región seleccionada desde la URL 
    region_seleccionada = request.GET.get('region_sede', "Metropolitana")

    datos = matricula_superior.objects.filter(cat_periodo=2020).exclude(rango_edad='Sin Información')
    
    # Obtener datos del modelo, filtrando por región si se especifica
    if region_seleccionada:
        datos = datos.filter(region_sede=region_seleccionada)

    datos= datos.values('cat_periodo','region_sede','gen_alu','rango_edad','tipo_inst_1','tipo_inst_2',
                        'nomb_inst','modalidad','jornada','nivel_global','area_conocimiento','dur_estudio_carr',
                        'nivel_carrera_2','acreditada_carr')
    df = pd.DataFrame(datos)

    df['gen_alu'] = df['gen_alu'].map(categorias_genero)

     # Contar cuántos hay de cada género
    conteo = df.groupby(['gen_alu','rango_edad']).size().reset_index(name='Cantidad')
    conteo.columns = ['Género','Edad','Cantidad']
    
    # Calcular el total por zona para obtener porcentajes
    totales_por_edad = conteo.groupby('Género')['Cantidad'].transform('sum')
    conteo['Porcentaje'] = (conteo['Cantidad'] / totales_por_edad) * 100


# Crear la figura manualmente
    fig = go.Figure()

    for edad in conteo['Edad'].unique():
        df_filtrado = conteo[conteo['Edad'] == edad]
        fig.add_trace(go.Bar(
            x=df_filtrado['Género'],
            y=df_filtrado['Porcentaje'],
            name=edad,  # Esto agrupará las barras por zona
            text=df_filtrado['Porcentaje'].apply(lambda x: f"{x:.2f}%"),  # Muestra los valores en las barras
            textposition='auto'
        ))

    fig.update_layout(
        barmode='group',  
        title="Gráfico género según edad",
        title_font= dict(weight="bold"),
        title_x=0.5,
        yaxis=dict(title="Porcentaje", range=[0, 100]),
        xaxis_title="Género",
        bargap=0.2,  
        bargroupgap=0.1,  
        autosize= True
    )

### Gráfico 2: Distribución género segun dependencia

    conteo_tipo = df.groupby(['gen_alu','tipo_inst_1']).size().reset_index(name='Cantidad')
    conteo_tipo.columns = ['Género','Tipo Institucion', 'Cantidad']

# Calcular porcentaje total
    totales_por_tipo = conteo_tipo.groupby('Género')['Cantidad'].transform('sum')
    conteo_tipo['Porcentaje'] = (conteo_tipo['Cantidad'] / totales_por_tipo) * 100

    fig2 = go.Figure()

    for tipo in conteo_tipo['Tipo Institucion'].unique():
        df_filtrado = conteo_tipo[conteo_tipo['Tipo Institucion'] == tipo]
        fig2.add_trace(go.Bar(
            x =df_filtrado['Género'],
            y = df_filtrado['Porcentaje'],
            name= tipo, 
            text=df_filtrado['Porcentaje'].apply(lambda x: f"{x:.2f}%"),
            textposition= 'auto'
            ))

    fig2.update_layout(
        barmode='group',
        title="Gráfico género según Tipo de Institución",
        title_font= dict(weight="bold"),
        title_x=0.5,
        yaxis=dict(title="Porcentaje", range=[0, 100]),
        xaxis_title="Género",
        bargap=0.1,
        bargroupgap=0.1,
        autosize= True,
    )

### Gráfico 3: Distribución género segun tipo de enseñanza

    conteo_area = df.groupby(['gen_alu','area_conocimiento']).size().reset_index(name='Cantidad')
    conteo_area.columns = ['Genero','Area Conocimiento', 'Cantidad']

# Calcular porcentaje total
    totales_por_area = conteo_area.groupby('Genero')['Cantidad'].transform('sum')
    conteo_area['Porcentaje'] = (conteo_area['Cantidad'] / totales_por_area) * 100

    fig3 = go.Figure()

    for area in conteo_area['Area Conocimiento'].unique():
        df_filtrado = conteo_area[conteo_area['Area Conocimiento'] == area]
        fig3.add_trace(go.Bar(
            x =df_filtrado['Genero'],
            y = df_filtrado['Porcentaje'],
            name= area, 
            text=df_filtrado['Porcentaje'].apply(lambda x: f"{x:.2f}%"),
            textposition= 'auto'
            ))

    fig3.update_layout(
        barmode='group',
        title="Gráfico género según tipo",
        title_font= dict(weight="bold"),
        title_x=0.5,
        yaxis=dict(title="Porcentaje", range=[0, 100]),
        xaxis_title="Zona",
        bargap=0.1,
        bargroupgap=0.1,
        autosize= True,
    )

    grafico_genero_edad_html = fig.to_html()
    grafico_genero_tipo_html = fig2.to_html()
    grafico_genero_area_html = fig3.to_html()

    return render(request, 'educacion/graficos_superior_2020.html', {'grafico_html': grafico_genero_edad_html,
                                                      'grafico_tipo_html': grafico_genero_tipo_html,
                                                      'grafico_area_html': grafico_genero_area_html,
                                                      'region': region_seleccionada})


############################  RESULTADOS SIMCE   #############################################
       
        # Determinar el mensaje basado en los valores de sigdif_lect_reg y sigdif_mate_reg

def obtener_mensaje(valor):
        if valor == 1:
            return " El cambio interanual es estadísticamente significativo y positivo."
        elif valor == -1:
            return " El cambio interanual es estadísticamente significativo y negativo."
        else:
            return "No hay cambios significativos."
        
def grafico_resultados_simce_4 (request):

    grado_dict = {
        "4b": "4° básico"
    }

    # Obtener la región seleccionada desde la URL
    region_seleccionada = request.GET.get('nom_reg', "Región metropolitana de santiago")

    datos = resultados_simce.objects.filter(grado='4b')
    
    # Obtener datos del modelo, filtrando por región si se especifica
    if region_seleccionada:
        datos = datos.filter(nom_reg=region_seleccionada)

    datos= datos.values('agno','prom_lect_reg','prom_mate_reg', 'grado', 'nom_reg', 'sigdif_lect_reg', 
                        'sigdif_mate_reg')
    df = pd.DataFrame(datos)

    # Reemplazar los números con los nombres de género
    df['grado'] = df['grado'].map(grado_dict)

    # Filtrar los datos para los años 2022 y 2023
    df_2022 = df[df["agno"] == 2022]
    df_2023 = df[df["agno"] == 2023]

    # Si ambos años tienen datos, comparamos
    if not df_2022.empty and not df_2023.empty:
        # Obtener los valores de 2023
        sigdif_lectura_2023 = df_2023["sigdif_lect_reg"].values[0]
        sigdif_matematicas_2023 = df_2023["sigdif_mate_reg"].values[0]

        # Obtener el mensaje de los cambios para 2023
        mensaje_lectura = obtener_mensaje(sigdif_lectura_2023)
        mensaje_matematicas = obtener_mensaje(sigdif_matematicas_2023)

        # Aquí podrías también comparar los puntajes entre los años para incluir la lógica de comparación
    else:
        # Si faltan datos para 2022 o 2023
        mensaje_lectura = "No se pueden comparar los datos"
        mensaje_matematicas = "No se pueden comparar los datos"

    fig = go.Figure()
     # Obtener los años únicos en el dataset
    años = sorted(df["agno"].unique())

    for año in años:
        df_año = df[df["agno"] == año]
        
        fig.add_trace(go.Bar(
            x=["Lenguaje", "Matemáticas"],  # Agrupar por asignatura
            y=[df_año["prom_lect_reg"].values[0], df_año["prom_mate_reg"].values[0]],  # Promedio para cada asignatura
            name=f"Año {año}",  # Etiqueta en la leyenda
            text=[df_año["prom_lect_reg"].values[0], df_año["prom_mate_reg"].values[0]],
            textposition="auto"
        ))

    fig.update_layout(
        barmode="group",  # Agrupar barras por asignatura
        title="Comparación de Puntajes por Asignatura y Año",
        xaxis_title="Asignaturas",
        yaxis=dict(title="Puntaje", tickformat=".2f"),
        xaxis={'categoryorder': 'category ascending'},
        bargap=0.2
    )
    grafico_genero_zona_html = fig.to_html()


    return render(request, 'educacion/graficos_simce_4.html', {'grafico_html': grafico_genero_zona_html,
                                                      'nom_reg': region_seleccionada,
                                                      'mensaje_lectura': mensaje_lectura,
                                                      'mensaje_matematicas': mensaje_matematicas})

def grafico_resultados_simce_2 (request):

    grado_dict = {
        "2m": "2° medio"
    }

    # Obtener la región seleccionada desde la URL 
    region_seleccionada = request.GET.get('nom_reg', "Región metropolitana de santiago")

    datos = resultados_simce.objects.filter(grado='2m')
    
    # Obtener datos del modelo, filtrando por región si se especifica
    if region_seleccionada:
        datos = datos.filter(nom_reg=region_seleccionada)

    datos= datos.values('agno','prom_lect_reg','prom_mate_reg', 'grado', 'nom_reg', 'sigdif_lect_reg', 
                        'sigdif_mate_reg')
    df = pd.DataFrame(datos)

    # Reemplazar los números con los nombres de género
    df['grado'] = df['grado'].map(grado_dict)

    
    # Filtrar los datos para los años 2022 y 2023
    df_2022 = df[df["agno"] == 2022]
    df_2023 = df[df["agno"] == 2023]

    # Si ambos años tienen datos, comparamos
    if not df_2022.empty and not df_2023.empty:
        # Obtener los valores de 2023
        sigdif_lectura_2023 = df_2023["sigdif_lect_reg"].values[0]
        sigdif_matematicas_2023 = df_2023["sigdif_mate_reg"].values[0]

        # Obtener el mensaje de los cambios para 2023
        mensaje_lectura = obtener_mensaje(sigdif_lectura_2023)
        mensaje_matematicas = obtener_mensaje(sigdif_matematicas_2023)

        # Aquí podrías también comparar los puntajes entre los años para incluir la lógica de comparación
    else:
        # Si faltan datos para 2022 o 2023
        mensaje_lectura = "No se pueden comparar los datos"
        mensaje_matematicas = "No se pueden comparar los datos"

    fig = go.Figure()
     # Obtener los años únicos en el dataset
    años = sorted(df["agno"].unique())

    for año in años:
        df_año = df[df["agno"] == año]
        
        fig.add_trace(go.Bar(
            x=["Lenguaje", "Matemáticas"],  # Agrupar por asignatura
            y=[df_año["prom_lect_reg"].values[0], df_año["prom_mate_reg"].values[0]],  # Promedio para cada asignatura
            name=f"Año {año}",  # Etiqueta en la leyenda
            text=[df_año["prom_lect_reg"].values[0], df_año["prom_mate_reg"].values[0]],
            textposition="auto"
        ))

    fig.update_layout(
        barmode="group",  # Agrupar barras por asignatura
        title="Comparación de Puntajes por Asignatura y Año",
        xaxis_title="Asignaturas",
        yaxis_title="Puntaje",
        xaxis={'categoryorder': 'category ascending'},
        bargap=0.2
    )
    grafico_genero_zona_html = fig.to_html()


    return render(request, 'educacion/graficos_simce_2.html', {'grafico_html': grafico_genero_zona_html,
                                                      'nom_reg': region_seleccionada,
                                                      'mensaje_lectura': mensaje_lectura,
                                                      'mensaje_matematicas': mensaje_matematicas})

############################  RESULTADOS SIMCE IDPS  #############################################

def grafico_resultados_idps22_4 (request):

    regiones = {
        "METROPOLITANA DE SANTIAGO": "Región Metropolitana",
        "DE TARAPACÁ": "Región de Tarapacá",
        "DE ANTOFAGASTA":"Región de Antofagasta",
        "DE ATACAMA":"Región de Atacama",
        "DE COQUIMBO":"Región de Coquimbo",
        "DE VALPARAÍSO":"Región de Valparaíso",
        "DEL LIBERTADOR BERNARDO O":"Región del Libertador Gral. Bernardo OHiggins",
        "DEL MAULE": "Región del Maule",
        "DEL BIOBÍO": "Región del Biobío",
        "DE LA ARAUCANÍA":"Región de la Araucanía",
        "DE LOS LAGOS": "Región de Los Lagos",
        "DE AYSÉN DEL GENERAL CARL": "Región de Aysén del Gral. Carlos Ibáñez del Campo",
        "DE MAGALLANES Y DE LA ANT":"Región de Magallanes y de la Antártica Chilena",
        "DE LOS RÍOS": "Región de Los Ríos",
        "DE ARICA Y PARINACOTA": "Región de Arica y Parinacota",
        "DE ÑUBLE": "Región de Ñuble"
    }

    dependencia_cat = {
        1:"Municipal",
        2:"Particular subvencionado",
        3:"Particular pagado",
        4:"SLEP"
    }

    zona ={
        1: "Urbano",
        2: "Rural"
    }

    ind_cat = {
        "AM":"Autoestima Académica y Motivación Escolar",
        "CC":"Clima de Convivencia Escolar",
        "HV":"Hábitos de Vida Saludable",
        "PF":"Participación y Formación Ciudadana"
    }


    colores_indicadores = {
    "AM": "#EF553B",  # Rojo
    "CC": "#636EFA",  # Azul
    "HV": "#D4A017",  # Dorado
    "PF": "#228B22"   # Verde
}
    

    # Obtener la región seleccionada 
    region_seleccionada = request.GET.get('nom_reg_rbd', "METROPOLITANA DE SANTIAGO")

    datos = resultados_simce_idps.objects.filter(grado='4', agno=2022)
    # Obtener datos del modelo, filtrando por región si se especifica
  
    if region_seleccionada:
        datos = datos.filter(nom_reg_rbd=region_seleccionada)

    datos= datos.values('agno', 'grado', 'nom_reg_rbd','cod_depe2','cod_rural_rbd','dim','ind','prom',
                        'nom_pro_rbd')
    df = pd.DataFrame(datos)

    df['nom_reg_rbd']=df['nom_reg_rbd'].map(regiones)
    df['ind'] = df['ind'].map(ind_cat)

    # Agrupar por región y tipo de indicador (ind), calculando el promedio de 'prom'
    df_promedios = df.groupby(['nom_reg_rbd', 'ind'])['prom'].mean().reset_index()


    fig = go.Figure()
    
     # Agregar barras para cada tipo de indicador (AM, CC, HV, PF)
    for indicador in df_promedios['ind'].unique():
        df_filtrado = df_promedios[df_promedios['ind'] == indicador]
        fig.add_trace(go.Bar(
            x=df_filtrado['nom_reg_rbd'],
            y=df_filtrado['prom'],
            name=indicador,
            text=df_filtrado['prom'].apply(lambda x: f"{x:.2f}"),  # Formato con 2 decimales
            textposition='inside'
        ))

    fig.update_layout(
        title="Promedio por Región según Tipo de Indicador",
        xaxis_title="Región",
        yaxis_title="Promedio",
        title_font= dict(weight="bold"),
        title_x=0.5,
        barmode='group',
        template="plotly_white",
    )

    # Gráfico 2 comparacion de resultados segun zona 

    df_zona = df.groupby(['nom_reg_rbd', 'ind', 'cod_rural_rbd'])['prom'].mean().reset_index()

    fig2 = go.Figure()

    for ruralidad in df_zona['cod_rural_rbd'].unique():
        df_filtrado = df_zona[df_zona['cod_rural_rbd'] == ruralidad]

        fig2.add_trace(go.Bar(
            x=df_filtrado['ind'], 
            y=df_filtrado['prom'],
            name=zona[ruralidad],  # La etiqueta solo será "Rural" o "Urbano"
            text=df_filtrado['prom'].apply(lambda x: f"{x:.2f}"),
            textposition='inside',
            marker_color='#EF553B' if ruralidad == 1 else '#636EFA'
        ))

    fig2.update_layout(
        title="Comparación de Indicadores por Zona",
        xaxis_title="Indicador",
        yaxis_title="Promedio",
        title_font= dict(weight="bold"),
        title_x=0.5,
        barmode='group',  
        template="plotly_white"
    )
        
     # Gráfico 3 comparando resultados según dependencia
    df_depe = df.groupby(['nom_reg_rbd', 'ind', 'cod_depe2'])['prom'].mean().reset_index()

    fig3= go.Figure()

    for dependencia in df_depe['cod_depe2'].unique():
        df_filtrado = df_depe[df_depe['cod_depe2'] == dependencia]

        fig3.add_trace(go.Bar(
            x=df_filtrado['ind'],  
            y=df_filtrado['prom'],
            name=dependencia_cat[dependencia],  
            text=df_filtrado['prom'].apply(lambda x: f"{x:.2f}"),
            textposition='inside'
        ))

    fig3.update_layout(
        title="Comparación de Indicadores por Dependencia",
        xaxis_title="Indicador",
        yaxis_title="Promedio",
        title_font= dict(weight="bold"),
        title_x=0.5,
        barmode='group',  
        template="plotly_white"
    )
    
        # Gráfico 4 comparando resultados según provincia 
    df_pro = df.groupby(['nom_reg_rbd', 'ind', 'nom_pro_rbd'])['prom'].mean().reset_index()

    fig4= go.Figure()

    for provincia in df_pro['nom_pro_rbd'].unique():
        df_filtrado = df_pro[df_pro['nom_pro_rbd'] == provincia]

        fig4.add_trace(go.Bar(
            x=df_filtrado['ind'],  
            y=df_filtrado['prom'],
            name=provincia,  
            text=df_filtrado['prom'].apply(lambda x: f"{x:.2f}"),
            textposition='inside'
        ))

    fig4.update_layout(
        title="Comparación de Indicadores por Provincia",
        xaxis_title="Indicador",
        yaxis_title="Promedio",
        title_font= dict(weight="bold"),
        title_x=0.5,
        barmode='group',  
        template="plotly_white"
    )

    grafico_html =fig.to_html(full_html=False, include_plotlyjs='cdn', config={'responsive': True})
    grafico_zona =fig2.to_html()
    grafico_dependencia =fig3.to_html()
    grafico_provincia =fig4.to_html()

    # Pruebas de chi-cuadrado 
    tabla_zona = df.pivot_table(index='ind', columns='cod_rural_rbd', values='prom', aggfunc='mean').fillna(0)
    chi2_zona, p_zona, _, _ = chi2_contingency(tabla_zona)

    tabla_depe = df.pivot_table(index='ind', columns='cod_depe2', values='prom', aggfunc='mean').fillna(0)
    chi2_depe, p_depe, _, _ = chi2_contingency(tabla_depe)

    tabla_pro = df.pivot_table(index='ind', columns='nom_pro_rbd', values='prom', aggfunc='mean').fillna(0)
    chi2_pro, p_pro, _, _ = chi2_contingency(tabla_pro)

    # Prueba V de Cramer
    def v_cramer (tabla_tipo):
        n = tabla_tipo.sum().sum()
        chi2_tipo, _, _, _ = chi2_contingency(tabla_tipo)
        phi2= chi2_tipo/n
        r, k = tabla_tipo.shape
        # Corregir phi2 (phi2corr) para evitar valores negativos
        phi2corr = max(0, phi2 - ((k - 1) * (r - 1)) / (n - 1))
        k_corr = k - (k - 1) * (k - 2) / (n - 1)
        r_corr = r - (r - 1) * (r - 2) / (n - 1)
        v = np.sqrt(phi2corr / min(k_corr - 1, r_corr - 1))
        
        return v
    v_cramer_zona= v_cramer(tabla_zona)
    v_cramer_depe= v_cramer(tabla_depe)
    v_cramer_pro= v_cramer(tabla_pro)

    return render(request, 'educacion/graficos_idps22_4.html', {'grafico_html': grafico_html,
                                                    'grafico_zona': grafico_zona,
                                                    'grafico_dependencia':grafico_dependencia,
                                                    'grafico_provincia':grafico_provincia,
                                                    'nom_reg_rbd': region_seleccionada,
                                                    'chi2_zona': round(chi2_zona,2),
                                                    'chi2_depe':round(chi2_depe,2),
                                                    'chi2_pro':round(chi2_pro,2),
                                                    'p_zona':round(p_zona,2),
                                                    'p_depe':round(p_depe,2),
                                                    'p_pro':round(p_pro,2),
                                                    'v_cramer_pro':round(v_cramer_pro,2),
                                                    'v_cramer_depe':round(v_cramer_depe,2),
                                                    'v_cramer_zona':round(v_cramer_zona,2)})
                
def grafico_resultados_idps22_2(request):

    regiones = {
        "METROPOLITANA DE SANTIAGO": "Región Metropolitana",
        "DE TARAPACÁ": "Región de Tarapacá",
        "DE ANTOFAGASTA": "Región de Antofagasta",
        "DE ATACAMA": "Región de Atacama",
        "DE COQUIMBO": "Región de Coquimbo",
        "DE VALPARAÍSO": "Región de Valparaíso",
        "DEL LIBERTADOR BERNARDO O": "Región del Libertador Gral. Bernardo OHiggins",
        "DEL MAULE": "Región del Maule",
        "DEL BIOBÍO": "Región del Biobío",
        "DE LA ARAUCANÍA": "Región de la Araucanía",
        "DE LOS LAGOS": "Región de Los Lagos",
        "DE AYSÉN DEL GENERAL CARL": "Región de Aysén del Gral. Carlos Ibáñez del Campo",
        "DE MAGALLANES Y DE LA ANT": "Región de Magallanes y de la Antártica Chilena",
        "DE LOS RÍOS": "Región de Los Ríos",
        "DE ARICA Y PARINACOTA": "Región de Arica y Parinacota",
        "DE ÑUBLE": "Región de Ñuble"
    }

    zona = {
        1: "Urbano",
        2: "Rural"
    }

    dependencia_cat = {
        1:"Municipal",
        2:"Particular subvencionado",
        3:"Particular pagado",
        4:"SLEP"
    }

    ind_cat = {
        "AM":"Autoestima Académica y Motivación Escolar",
        "CC":"Clima de Convivencia Escolar",
        "HV":"Hábitos de Vida Saludable",
        "PF":"Participación y Formación Ciudadana"
    }

    colores_indicadores = {
    "AM": "#EF553B",  # Rojo
    "CC": "#636EFA",  # Azul
    "HV": "#D4A017",  # Dorado
    "PF": "#228B22"   # Verde
}

    # Obtener la región seleccionada desde la URL 
    region_seleccionada = request.GET.get('nom_reg_rbd', "METROPOLITANA DE SANTIAGO")

    # Filtrar los datos 
    datos = resultados_simce_idps.objects.filter(grado='2', agno=2022)
    
    # Filtrar por región
    if region_seleccionada:
        datos = datos.filter(nom_reg_rbd=region_seleccionada)

    # Convertir los datos a DataFrame
    datos = datos.values('agno', 'grado', 'nom_reg_rbd', 'cod_depe2', 'cod_rural_rbd', 'dim', 'ind', 'prom',
                         'nom_pro_rbd')
    df = pd.DataFrame(datos)

    # Mapear las regiones
    df['nom_reg_rbd'] = df['nom_reg_rbd'].map(regiones)
    df['ind'] = df['ind'].map(ind_cat)

    # Agrupar por región y tipo de indicador (ind), calculando el promedio de 'prom'
    df_promedios = df.groupby(['nom_reg_rbd', 'ind'])['prom'].mean().reset_index()

    # Cambiar colores de las barras
    #colores = px.colors.sequential.Plasma
    #colores_indicadores = {ind: colores[i % len(colores)] for i, ind in enumerate(df_promedios['ind'].unique())}

    fig = go.Figure()

    for indicador in df_promedios['ind'].unique():
        df_filtrado = df_promedios[df_promedios['ind'] == indicador]
        fig.add_trace(go.Bar(
            x=df_filtrado['nom_reg_rbd'],
            y=df_filtrado['prom'],
            name=indicador,
            text=df_filtrado['prom'].apply(lambda x: f"{x:.2f}"),
            textposition='inside',
            #marker_color= colores_indicadores[indicador] #colores_indicadores.get(indicador, 'grey')
        ))

    fig.update_layout(
        title="Promedio por Región según Tipo de Indicador",
        xaxis_title="Región",
        yaxis_title="Promedio",
        title_font= dict(weight="bold"),
        title_x=0.5,
        barmode='group',
        template="plotly_white"
    )

    # Gráfico 2 comparando resultados según zona 
    df_zona = df.groupby(['nom_reg_rbd', 'ind', 'cod_rural_rbd'])['prom'].mean().reset_index()

    fig2 = go.Figure()

    for ruralidad in df_zona['cod_rural_rbd'].unique():
        df_filtrado = df_zona[df_zona['cod_rural_rbd'] == ruralidad]

        fig2.add_trace(go.Bar(
            x=df_filtrado['ind'],  
            y=df_filtrado['prom'],
            name=zona[ruralidad],  # La etiqueta solo será "Rural" o "Urbano"
            text=df_filtrado['prom'].apply(lambda x: f"{x:.2f}"),
            textposition='inside',
            marker_color='#EF553B' if ruralidad == 1 else '#636EFA'
        ))

    fig2.update_layout(
        title="Comparación de Indicadores por Zona",
        xaxis_title="Indicador",
        yaxis_title="Promedio",
        title_font= dict(weight="bold"),
        title_x=0.5,
        barmode='group',  
        template="plotly_white"
    )
        
     # Gráfico 3 comparando resultados según dependencia 
    df_depe = df.groupby(['nom_reg_rbd', 'ind', 'cod_depe2'])['prom'].mean().reset_index()

    fig3= go.Figure()

    for dependencia in df_depe['cod_depe2'].unique():
        df_filtrado = df_depe[df_depe['cod_depe2'] == dependencia]

        fig3.add_trace(go.Bar(
            x=df_filtrado['ind'],  
            y=df_filtrado['prom'],
            name=dependencia_cat[dependencia], 
            text=df_filtrado['prom'].apply(lambda x: f"{x:.2f}"),
            textposition='inside'
        ))

    fig3.update_layout(
        title="Comparación de Indicadores por Dependencia",
        xaxis_title="Indicador",
        yaxis_title="Promedio",
        title_font= dict(weight="bold"),
        title_x=0.5,
        barmode='group',  
        template="plotly_white"
    )
        
        
    # Gráfico 4 comparando resultados según provincia 
    df_pro = df.groupby(['nom_reg_rbd', 'ind', 'nom_pro_rbd'])['prom'].mean().reset_index()

    fig4= go.Figure()

    for provincia in df_pro['nom_pro_rbd'].unique():
        df_filtrado = df_pro[df_pro['nom_pro_rbd'] == provincia]

        fig4.add_trace(go.Bar(
            x=df_filtrado['ind'], 
            y=df_filtrado['prom'],
            name=provincia,  
            text=df_filtrado['prom'].apply(lambda x: f"{x:.2f}"),
            textposition='inside'
        ))

    fig4.update_layout(
        title="Comparación de Indicadores por Provincia",
        xaxis_title="Indicador",
        yaxis_title="Promedio",
        title_font= dict(weight="bold"),
        title_x=0.5,
        barmode='group',  
        template="plotly_white"
    )
        

    grafico_html = fig.to_html()
    grafico_zona = fig2.to_html()
    grafico_dependencia = fig3.to_html()
    grafico_provincia = fig4.to_html()

    # Pruebas de chi-cuadrado 
    tabla_zona = df.pivot_table(index='ind', columns='cod_rural_rbd', values='prom', aggfunc='mean').fillna(0)
    chi2_zona, p_zona, _, _ = chi2_contingency(tabla_zona)

    tabla_depe = df.pivot_table(index='ind', columns='cod_depe2', values='prom', aggfunc='mean').fillna(0)
    chi2_depe, p_depe, _, _ = chi2_contingency(tabla_depe)

    tabla_pro = df.pivot_table(index='ind', columns='nom_pro_rbd', values='prom', aggfunc='mean').fillna(0)
    chi2_pro, p_pro, _, _ = chi2_contingency(tabla_pro)

    return render(request, 'educacion/graficos_idps22_2.html', {
        'grafico_html': grafico_html,
        'grafico_zona': grafico_zona,
        'grafico_dependencia':grafico_dependencia,
        'grafico_provincia':grafico_provincia,
        'nom_reg_rbd': region_seleccionada,
        'chi2_zona': round(chi2_zona, 2),
        'p_zona': round(p_zona, 2),
        'chi2_depe': round(chi2_depe, 2),
        'p_depe': round(p_depe, 2),
        'chi2_pro':round(chi2_pro,2),
        'p_pro':round(p_pro,2),
    })

def grafico_resultados_idps23_4 (request):

    regiones = {
        "METROPOLITANA DE SANTIAGO": "Región Metropolitana",
        "DE TARAPACÁ": "Región de Tarapacá",
        "DE ANTOFAGASTA":"Región de Antofagasta",
        "DE ATACAMA":"Región de Atacama",
        "DE COQUIMBO":"Región de Coquimbo",
        "DE VALPARAÍSO":"Región de Valparaíso",
        "DEL LIBERTADOR BERNARDO O":"Región del Libertador Gral. Bernardo OHiggins",
        "DEL MAULE": "Región del Maule",
        "DEL BIOBÍO": "Región del Biobío",
        "DE LA ARAUCANÍA":"Región de la Araucanía",
        "DE LOS LAGOS": "Región de Los Lagos",
        "DE AYSÉN DEL GENERAL CARL": "Región de Aysén del Gral. Carlos Ibáñez del Campo",
        "DE MAGALLANES Y DE LA ANT":"Región de Magallanes y de la Antártica Chilena",
        "DE LOS RÍOS": "Región de Los Ríos",
        "DE ARICA Y PARINACOTA": "Región de Arica y Parinacota",
        "DE ÑUBLE": "Región de Ñuble"
    }

    dependencia_cat = {
        1:"Municipal",
        2:"Particular subvencionado",
        3:"Particular pagado",
        4:"SLEP"
    }

    zona ={
        1: "Urbano",
        2: "Rural"
    }

    ind_cat = {
        "AM":"Autoestima Académica y Motivación Escolar",
        "CC":"Clima de Convivencia Escolar",
        "HV":"Hábitos de Vida Saludable",
        "PF":"Participación y Formación Ciudadana"
    }


    colores_indicadores = {
    "AM": "#EF553B",  # Rojo
    "CC": "#636EFA",  # Azul
    "HV": "#D4A017",  # Dorado
    "PF": "#228B22"   # Verde
}
    

    # Obtener la región seleccionada desde la URL (por defecto muestra todos)
    region_seleccionada = request.GET.get('nom_reg_rbd', "METROPOLITANA DE SANTIAGO")

    datos = resultados_simce_idps.objects.filter(grado='4', agno=2023)
    # Obtener datos del modelo, filtrando por región si se especifica
  
    if region_seleccionada:
        datos = datos.filter(nom_reg_rbd=region_seleccionada)

    datos= datos.values('agno', 'grado', 'nom_reg_rbd','cod_depe2','cod_rural_rbd','dim','ind','prom',
                        'nom_pro_rbd')
    df = pd.DataFrame(datos)

    df['nom_reg_rbd']=df['nom_reg_rbd'].map(regiones)
    df['ind'] = df['ind'].map(ind_cat)

    # Agrupar por región y tipo de indicador (ind), calculando el promedio de 'prom'
    df_promedios = df.groupby(['nom_reg_rbd', 'ind'])['prom'].mean().reset_index()


    fig = go.Figure()
    
     # Agregar barras para cada tipo de indicador (AM, CC, HV, PF)
    for indicador in df_promedios['ind'].unique():
        df_filtrado = df_promedios[df_promedios['ind'] == indicador]
        fig.add_trace(go.Bar(
            x=df_filtrado['nom_reg_rbd'],
            y=df_filtrado['prom'],
            name=indicador,
            text=df_filtrado['prom'].apply(lambda x: f"{x:.2f}"),  # Formato con 2 decimales
            textposition='inside'
        ))

    # Configurar el diseño del gráfico
    fig.update_layout(
        title="Promedio por Región según Tipo de Indicador",
        xaxis_title="Región",
        yaxis_title="Promedio",
        title_font= dict(weight="bold"),
        title_x=0.5,
        barmode='group',
        template="plotly_white"
    )

    # Gráfico 2 comparacion de resultados segun zona 

    df_zona = df.groupby(['nom_reg_rbd', 'ind', 'cod_rural_rbd'])['prom'].mean().reset_index()

    fig2 = go.Figure()

    for ruralidad in df_zona['cod_rural_rbd'].unique():
        df_filtrado = df_zona[df_zona['cod_rural_rbd'] == ruralidad]

        fig2.add_trace(go.Bar(
            x=df_filtrado['ind'],  
            y=df_filtrado['prom'],
            name=zona[ruralidad],  # La etiqueta solo será "Rural" o "Urbano"
            text=df_filtrado['prom'].apply(lambda x: f"{x:.2f}"),
            textposition='inside',
            marker_color='#EF553B' if ruralidad == 1 else '#636EFA'
        ))

    fig2.update_layout(
        title="Comparación de Indicadores por Zona",
        xaxis_title="Indicador",
        yaxis_title="Promedio",
        title_font= dict(weight="bold"),
        title_x=0.5,
        barmode='group', 
        template="plotly_white"
    )
        
     # Gráfico 3 comparando resultados según dependencia
    df_depe = df.groupby(['nom_reg_rbd', 'ind', 'cod_depe2'])['prom'].mean().reset_index()

    fig3= go.Figure()

    for dependencia in df_depe['cod_depe2'].unique():
        df_filtrado = df_depe[df_depe['cod_depe2'] == dependencia]

        fig3.add_trace(go.Bar(
            x=df_filtrado['ind'],  
            y=df_filtrado['prom'],
            name=dependencia_cat[dependencia],  
            text=df_filtrado['prom'].apply(lambda x: f"{x:.2f}"),
            textposition='inside'
        ))

    fig3.update_layout(
        title="Comparación de Indicadores por Dependencia",
        xaxis_title="Indicador",
        yaxis_title="Promedio",
        title_font= dict(weight="bold"),
        title_x=0.5,
        barmode='group',  
        template="plotly_white"
    )
    
        # Gráfico 4 comparando resultados según provincia 
    df_pro = df.groupby(['nom_reg_rbd', 'ind', 'nom_pro_rbd'])['prom'].mean().reset_index()

    fig4= go.Figure()

    for provincia in df_pro['nom_pro_rbd'].unique():
        df_filtrado = df_pro[df_pro['nom_pro_rbd'] == provincia]

        fig4.add_trace(go.Bar(
            x=df_filtrado['ind'],  
            y=df_filtrado['prom'],
            name=provincia,  
            text=df_filtrado['prom'].apply(lambda x: f"{x:.2f}"),
            textposition='inside'
        ))

    fig4.update_layout(
        title="Comparación de Indicadores por Provincia",
        xaxis_title="Indicador",
        yaxis_title="Promedio",
        title_font= dict(weight="bold"),
        title_x=0.5,
        barmode='group',  
        template="plotly_white"
    )

    grafico_html =fig.to_html()
    grafico_zona =fig2.to_html()
    grafico_dependencia =fig3.to_html()
    grafico_provincia =fig4.to_html()

    # Pruebas de chi-cuadrado 
    tabla_zona = df.pivot_table(index='ind', columns='cod_rural_rbd', values='prom', aggfunc='mean').fillna(0)
    chi2_zona, p_zona, _, _ = chi2_contingency(tabla_zona)

    tabla_depe = df.pivot_table(index='ind', columns='cod_depe2', values='prom', aggfunc='mean').fillna(0)
    chi2_depe, p_depe, _, _ = chi2_contingency(tabla_depe)

    tabla_pro = df.pivot_table(index='ind', columns='nom_pro_rbd', values='prom', aggfunc='mean').fillna(0)
    chi2_pro, p_pro, _, _ = chi2_contingency(tabla_pro)

    # Prueba V de Cramer
    def v_cramer (tabla_tipo):
        n = tabla_tipo.sum().sum()
        chi2_tipo, _, _, _ = chi2_contingency(tabla_tipo)
        phi2= chi2_tipo/n
        r, k = tabla_tipo.shape
        # Corregir phi2 (phi2corr) para evitar valores negativos
        phi2corr = max(0, phi2 - ((k - 1) * (r - 1)) / (n - 1))
        k_corr = k - (k - 1) * (k - 2) / (n - 1)
        r_corr = r - (r - 1) * (r - 2) / (n - 1)
        v = np.sqrt(phi2corr / min(k_corr - 1, r_corr - 1))
        
        return v

    v_cramer_zona= v_cramer(tabla_zona)
    v_cramer_depe= v_cramer(tabla_depe)
    v_cramer_pro= v_cramer(tabla_pro)

    return render(request, 'educacion/graficos_idps23_4.html', {'grafico_html': grafico_html,
                                                                'grafico_zona': grafico_zona,
                                                                'grafico_dependencia':grafico_dependencia,
                                                                'grafico_provincia':grafico_provincia,
                                                                'nom_reg_rbd': region_seleccionada,
                                                                'chi2_zona': round(chi2_zona,2),
                                                                'chi2_depe':round(chi2_depe,2),
                                                                'chi2_pro':round(chi2_pro,2),
                                                                'p_zona':round(p_zona,2),
                                                                'p_depe':round(p_depe,2),
                                                                'p_pro':round(p_pro,2),
                                                                'v_cramer_pro':round(v_cramer_pro,2),
                                                                'v_cramer_depe':round(v_cramer_depe,2),
                                                                'v_cramer_zona':round(v_cramer_zona,2)})

def grafico_resultados_idps23_2(request):

    regiones = {
        "METROPOLITANA DE SANTIAGO": "Región Metropolitana",
        "DE TARAPACÁ": "Región de Tarapacá",
        "DE ANTOFAGASTA": "Región de Antofagasta",
        "DE ATACAMA": "Región de Atacama",
        "DE COQUIMBO": "Región de Coquimbo",
        "DE VALPARAÍSO": "Región de Valparaíso",
        "DEL LIBERTADOR BERNARDO O": "Región del Libertador Gral. Bernardo OHiggins",
        "DEL MAULE": "Región del Maule",
        "DEL BIOBÍO": "Región del Biobío",
        "DE LA ARAUCANÍA": "Región de la Araucanía",
        "DE LOS LAGOS": "Región de Los Lagos",
        "DE AYSÉN DEL GENERAL CARL": "Región de Aysén del Gral. Carlos Ibáñez del Campo",
        "DE MAGALLANES Y DE LA ANT": "Región de Magallanes y de la Antártica Chilena",
        "DE LOS RÍOS": "Región de Los Ríos",
        "DE ARICA Y PARINACOTA": "Región de Arica y Parinacota",
        "DE ÑUBLE": "Región de Ñuble"
    }

    zona = {
        1: "Urbano",
        2: "Rural"
    }

    dependencia_cat = {
        1:"Municipal",
        2:"Particular subvencionado",
        3:"Particular pagado",
        4:"SLEP"
    }

    ind_cat = {
        "AM":"Autoestima Académica y Motivación Escolar",
        "CC":"Clima de Convivencia Escolar",
        "HV":"Hábitos de Vida Saludable",
        "PF":"Participación y Formación Ciudadana"
    }

    colores_indicadores = {
    "AM": "#EF553B",  # Rojo
    "CC": "#636EFA",  # Azul
    "HV": "#D4A017",  # Dorado
    "PF": "#228B22"   # Verde
}

    # Obtener la región seleccionada 
    region_seleccionada = request.GET.get('nom_reg_rbd', "METROPOLITANA DE SANTIAGO")

    # Filtrar los datos
    datos = resultados_simce_idps.objects.filter(grado='2', agno=2023)
    
    # Filtrar por región 
    if region_seleccionada:
        datos = datos.filter(nom_reg_rbd=region_seleccionada)

    datos = datos.values('agno', 'grado', 'nom_reg_rbd', 'cod_depe2', 'cod_rural_rbd', 'dim', 'ind', 'prom',
                         'nom_pro_rbd')
    df = pd.DataFrame(datos)

    # Mapear las regiones
    df['nom_reg_rbd'] = df['nom_reg_rbd'].map(regiones)
    df['ind'] = df['ind'].map(ind_cat)

    # Agrupar por región y tipo de indicador (ind), calculando el promedio de 'prom'
    df_promedios = df.groupby(['nom_reg_rbd', 'ind'])['prom'].mean().reset_index()

    # Cambiar colores de las barras
    #colores = px.colors.sequential.Plasma
    #colores_indicadores = {ind: colores[i % len(colores)] for i, ind in enumerate(df_promedios['ind'].unique())}

    # Crear la figura para el gráfico de comparación por región
    fig = go.Figure()

    # Agregar barras para cada tipo de indicador
    for indicador in df_promedios['ind'].unique():
        df_filtrado = df_promedios[df_promedios['ind'] == indicador]
        fig.add_trace(go.Bar(
            x=df_filtrado['nom_reg_rbd'],
            y=df_filtrado['prom'],
            name=indicador,
            text=df_filtrado['prom'].apply(lambda x: f"{x:.2f}"),
            textposition='inside',
            #marker_color= colores_indicadores[indicador] #colores_indicadores.get(indicador, 'grey')
        ))

    fig.update_layout(
        title="Promedio por Región según Tipo de Indicador",
        xaxis_title="Región",
        yaxis_title="Promedio",
        title_font= dict(weight="bold"),
        title_x=0.5,
        barmode='group',
        template="plotly_white"
    )

    # Gráfico 2 comparando resultados según zona 
    df_zona = df.groupby(['nom_reg_rbd', 'ind', 'cod_rural_rbd'])['prom'].mean().reset_index()

    fig2 = go.Figure()

    for ruralidad in df_zona['cod_rural_rbd'].unique():
        df_filtrado = df_zona[df_zona['cod_rural_rbd'] == ruralidad]

        fig2.add_trace(go.Bar(
            x=df_filtrado['ind'],  
            y=df_filtrado['prom'],
            name=zona[ruralidad],  # La etiqueta solo será "Rural" o "Urbano"
            text=df_filtrado['prom'].apply(lambda x: f"{x:.2f}"),
            textposition='inside',
            marker_color='#EF553B' if ruralidad == 1 else '#636EFA'
        ))

    fig2.update_layout(
        title="Comparación de Indicadores por Zona",
        xaxis_title="Indicador",
        yaxis_title="Promedio",
        title_font= dict(weight="bold"),
        title_x=0.5,
        barmode='group', 
        template="plotly_white"
    )
        
     # Gráfico 3 comparando resultados según dependencia 
    df_depe = df.groupby(['nom_reg_rbd', 'ind', 'cod_depe2'])['prom'].mean().reset_index()

    fig3= go.Figure()

    for dependencia in df_depe['cod_depe2'].unique():
        df_filtrado = df_depe[df_depe['cod_depe2'] == dependencia]

        fig3.add_trace(go.Bar(
            x=df_filtrado['ind'],  
            y=df_filtrado['prom'],
            name=dependencia_cat[dependencia], 
            text=df_filtrado['prom'].apply(lambda x: f"{x:.2f}"),
            textposition='inside'
        ))

    fig3.update_layout(
        title="Comparación de Indicadores por Dependencia",
        xaxis_title="Indicador",
        yaxis_title="Promedio",
        title_font= dict(weight="bold"),
        title_x=0.5,
        barmode='group',  
        template="plotly_white"
    )
        
    # Gráfico 4 comparando resultados según provincia 
    df_pro = df.groupby(['nom_reg_rbd', 'ind', 'nom_pro_rbd'])['prom'].mean().reset_index()

    fig4= go.Figure()

    for provincia in df_pro['nom_pro_rbd'].unique():
        df_filtrado = df_pro[df_pro['nom_pro_rbd'] == provincia]

        fig4.add_trace(go.Bar(
            x=df_filtrado['ind'],  
            y=df_filtrado['prom'],
            name=provincia,  
            text=df_filtrado['prom'].apply(lambda x: f"{x:.2f}"),
            textposition='inside'
        ))

    fig4.update_layout(
        title="Comparación de Indicadores por Provincia",
        xaxis_title="Indicador",
        yaxis_title="Promedio",
        title_font= dict(weight="bold"),
        title_x=0.5,
        barmode='group',  
        template="plotly_white"
    )
        

    # Convertir gráficos a HTML
    grafico_html = fig.to_html()
    grafico_zona = fig2.to_html()
    grafico_dependencia = fig3.to_html()
    grafico_provincia = fig4.to_html()

    # Pruebas de chi-cuadrado 
    tabla_zona = df.pivot_table(index='ind', columns='cod_rural_rbd', values='prom', aggfunc='mean').fillna(0)
    chi2_zona, p_zona, _, _ = chi2_contingency(tabla_zona)

    tabla_depe = df.pivot_table(index='ind', columns='cod_depe2', values='prom', aggfunc='mean').fillna(0)
    chi2_depe, p_depe, _, _ = chi2_contingency(tabla_depe)

    tabla_pro = df.pivot_table(index='ind', columns='nom_pro_rbd', values='prom', aggfunc='mean').fillna(0)
    chi2_pro, p_pro, _, _ = chi2_contingency(tabla_pro)

    return render(request, 'educacion/graficos_idps23_2.html', {
        'grafico_html': grafico_html,
        'grafico_zona': grafico_zona,
        'grafico_dependencia':grafico_dependencia,
        'grafico_provincia':grafico_provincia,
        'nom_reg_rbd': region_seleccionada,
        'chi2_zona': round(chi2_zona, 2),
        'p_zona': round(p_zona, 2),
        'chi2_depe': round(chi2_depe, 2),
        'p_depe': round(p_depe, 2),
        'chi2_pro':round(chi2_pro,2),
        'p_pro':round(p_pro,2),
    })


############################  DOTACION DOCENTE  #############################################

def dotacion_docente_20 (request):

    # Obtener la región seleccionada 
    region_seleccionada = request.GET.get('NOM_REG_RBD_A', "METROPOLITANA DE SANTIAGO")

    # Filtrar los datos
    datos = dotacion_docente.objects.filter(AGNO=2020).values('AGNO','NOM_REG_RBD_A', 'COD_DEPE2', 'RURAL_RBD', 'DC_A', 'HH_A', 'DC_TOT',
                         'HH_TOT')

    
    # Filtrar por región 
    if region_seleccionada:
        datos = datos.filter(NOM_REG_RBD_A=region_seleccionada)

    df = pd.DataFrame(datos)

# Grafico dependencia y horas por docente
  
    df = df[df["DC_A"] > 0]  # Filtrar donde haya docentes para evitar división por cero
    df['Prom_Horas_Por_Docente'] = df['HH_A'] / df['DC_A']

    # Agrupar por COD_DEPE2 y calcular el promedio
    df_grouped = df.groupby('COD_DEPE2')['Prom_Horas_Por_Docente'].mean().reset_index()
    df_grouped.columns = ['Dependencia','Promedio horas']

    fig = go.Figure()

    for dependencia in df_grouped['Dependencia'].unique():
        df_filtrado = df_grouped[df_grouped['Dependencia']== dependencia]
        fig.add_trace(go.Bar(
            x=df_filtrado['Dependencia'],
            y=df_filtrado['Promedio horas'],
            text= df_filtrado['Promedio horas'].apply(lambda x: f"{x: .2f}"),
            textposition= 'auto',
            name= dependencia
        ))

    fig.update_layout(
        title="Promedio de Horas por Docente según Dependencia",
        xaxis_title="Código Dependencia",
        title_font= dict(),
        title_x= 0.5,
        template="plotly_white"
    )

    grafico_depe = fig.to_html()

    return render (request, 'educacion/grafico_docente_20',{'grafico_depe':grafico_depe})

def dotacion_docente_21 (request):
 
     # Obtener la región seleccionada 
    region_seleccionada = request.GET.get('NOM_REG_RBD_A', "METROPOLITANA DE SANTIAGO")

    # Filtrar los datos
    datos = dotacion_docente.objects.filter(AGNO=2021)
    
    # Filtrar por región 
    if region_seleccionada:
        datos = datos.filter(NOM_REG_RBD_A=region_seleccionada)

    datos = datos.values('AGNO','NOM_REG_RBD_A', 'COD_DEPE2', 'RURAL_RBD', 'DC_A', 'HH_A', 'DC_TOT',
                         'HH_TOT')
    df = pd.DataFrame(datos)

    # Grafico dependencia y horas por docente

    df = df['DC_A'] > 0  # Filtrar donde haya docentes para evitar división por cero
    df['Prom_Horas_Por_Docente'] = df['HH_A'] / df['DC_A']

    # Agrupar por COD_DEPE2 y calcular el promedio
    df_grouped = df.groupby('COD_DEPE2')['Prom_Horas_Por_Docente'].mean()

    fig = go.Figure()

    fig.add_bar(
        x=df_grouped['COD_DEPE2'],
        y=df_grouped['Prom_Horas_Por_Docente'],
        marker_color='blue',
        name='Horas promedio'
    )

    fig.update_layout(
        title="Promedio de Horas por Docente según Dependencia",
        xaxis_title="Código Dependencia",
        yaxis_title="Promedio de Horas",
        template="plotly_white"
    )

    grafico_depe = fig.to_html()

    return render (request, 'educacion/grafico_docente_21',{'grafico_depe':grafico_depe})

def dotacion_docente_22 (request):

    # Obtener la región seleccionada 
    region_seleccionada = request.GET.get('NOM_REG_RBD_A', "METROPOLITANA DE SANTIAGO")

    # Filtrar los datos
    datos = dotacion_docente.objects.filter(AGNO=2022)
    
    # Filtrar por región 
    if region_seleccionada:
        datos = datos.filter(NOM_REG_RBD_A=region_seleccionada)

    datos = datos.values('AGNO','NOM_REG_RBD_A', 'COD_DEPE2', 'RURAL_RBD', 'DC_A', 'HH_A', 'DC_TOT',
                         'HH_TOT')
    df = pd.DataFrame(datos)

    # Grafico dependencia y horas por docente

    df = df[df['DC_A'] > 0]  # Filtrar donde haya docentes para evitar división por cero
    df['Prom_Horas_Por_Docente'] = df['HH_A'] / df['DC_A']

    # Agrupar por COD_DEPE2 y calcular el promedio
    df_grouped = df.groupby('COD_DEPE2')['Prom_Horas_Por_Docente'].mean()

    fig = go.Figure()

    fig.add_bar(
        x=df_grouped['COD_DEPE2'],
        y=df_grouped['Prom_Horas_Por_Docente'],
        marker_color='blue',
        name='Horas promedio'
    )

    fig.update_layout(
        title="Promedio de Horas por Docente según Dependencia",
        xaxis_title="Código Dependencia",
        yaxis_title="Promedio de Horas",
        template="plotly_white"
    )

    grafico_depe = fig.to_html()

    return render (request, 'educacion/grafico_docente_22',{'grafico_depe':grafico_depe})

def dotacion_docente_23 (request):

    # Obtener la región seleccionada 
    region_seleccionada = request.GET.get('NOM_REG_RBD_A', "METROPOLITANA DE SANTIAGO")

    # Filtrar los datos
    datos = dotacion_docente.objects.filter(AGNO=2023)
    
    # Filtrar por región 
    if region_seleccionada:
        datos = datos.filter(NOM_REG_RBD_A=region_seleccionada)

    datos = datos.values('AGNO','NOM_REG_RBD_A', 'COD_DEPE2', 'RURAL_RBD', 'DC_A', 'HH_A', 'DC_TOT',
                         'HH_TOT')
    df = pd.DataFrame(datos)

    # Grafico dependencia y horas por docente

    df = df[df['DC_A'] > 0]  # Filtrar donde haya docentes para evitar división por cero
    df['Prom_Horas_Por_Docente'] = df['HH_A'] / df['DC_A']

    # Agrupar por COD_DEPE2 y calcular el promedio
    df_grouped = df.groupby('COD_DEPE2')['Prom_Horas_Por_Docente'].mean()

    fig = go.Figure()

    fig.add_bar(
        x=df_grouped['COD_DEPE2'],
        y=df_grouped['Prom_Horas_Por_Docente'],
        marker_color='blue',
        name='Horas promedio'
    )

    fig.update_layout(
        title="Promedio de Horas por Docente según Dependencia",
        xaxis_title="Código Dependencia",
        yaxis_title="Promedio de Horas",
        template="plotly_white"
    )

    grafico_depe = fig.to_html()

    return render (request, 'educacion/grafico_docente_23',{'grafico_depe':grafico_depe})

def dotacion_docente_24 (request):

        # Obtener la región seleccionada 
    region_seleccionada = request.GET.get('NOM_REG_RBD_A', "METROPOLITANA DE SANTIAGO")

    # Filtrar los datos
    datos = dotacion_docente.objects.filter(AGNO=2024)
    
    # Filtrar por región 
    if region_seleccionada:
        datos = datos.filter(NOM_REG_RBD_A=region_seleccionada)

    datos = datos.values('AGNO','NOM_REG_RBD_A', 'COD_DEPE2', 'RURAL_RBD', 'DC_A', 'HH_A', 'DC_TOT',
                         'HH_TOT')
    df = pd.DataFrame(datos)

    # Grafico dependencia y horas por docente

    df = df[df['DC_A'] > 0]  # Filtrar donde haya docentes para evitar división por cero
    df['Prom_Horas_Por_Docente'] = df['HH_A'] / df['DC_A']

    # Agrupar por COD_DEPE2 y calcular el promedio
    df_grouped = df.groupby('COD_DEPE2')['Prom_Horas_Por_Docente'].mean()

    fig = go.Figure()

    fig.add_bar(
        x=df_grouped['COD_DEPE2'],
        y=df_grouped['Prom_Horas_Por_Docente'],
        marker_color='blue',
        name='Horas promedio'
    )

    fig.update_layout(
        title="Promedio de Horas por Docente según Dependencia",
        xaxis_title="Código Dependencia",
        yaxis_title="Promedio de Horas",
        template="plotly_white"
    )

    grafico_depe = fig.to_html()

    return render (request, 'educacion/grafico_docente_24',{'grafico_depe':grafico_depe})


############################  RENDIMIENTO ACADEMICO  #############################################


def grafico_rendimiento_20 (request):

    region_seleccionada = request.GET.get("COD_REG_RBD", "13")

    datos = rendimiento_academico.objects.filter(AGNO = 2020)

    if region_seleccionada:
        datos = datos.filter(COD_REG_RBD=region_seleccionada)

    datos = datos.values("COD_DEPE", "RURAL_RBD","GEN_ALU","COD_JOR", "PROM_GRAL", 
                         "ASISTENCIA", "SIT_FIN_R", "EDAD_ALU", "COD_REG_RBD")

    df = pd.DataFrame(datos)


## Grafico promedio por genero
    
    prom_por_genero = df.groupby("GEN_ALU")["PROM_GRAL"].mean().reset_index()

    fig = go.Figure()


## Grafico asistencia por genero

    asis_por_genero = df.groupby("GEN_ALU")["ASISTENCIA"].mean().reset_index()
    asis_por_genero.columns = ["Género", "Asistencia"]

    fig2 = go.Figure()

## Grafico promedio por rural

    prom_por_zona = df.groupby("RURAL_RBD")["PROM_GRAL"].mean().reset_index()
    prom_por_zona.columns = ["Zona", "Promedio"]

    fig3 = go.Figure()

## Grafico asistencia por rural

    asis_por_zona = df.groupby("RURAL_RBD")["ASISTENCIA"].mean().reset_index()
    asis_por_zona.columns = ["Zona", "Asistencia"]

    fig4 = go.Figure()

def grafico_rendimiento_21 (request):

    categorias_genero = {
        1 : "Masculino",
        2 : "Femenino"
    }
    categorias_zona = {
        0 : "Urbano",
        1 : "Rural"
    }

    region_seleccionada = request.GET.get("COD_REG_RBD", "13")

    datos = rendimiento_academico.objects.filter(AGNO = 2021)

    if region_seleccionada:
        datos = datos.filter(COD_REG_RBD=region_seleccionada)

    datos = datos.values("COD_DEPE", "RURAL_RBD","GEN_ALU","COD_JOR", "PROM_GRAL", 
                         "ASISTENCIA", "SIT_FIN_R", "EDAD_ALU", "COD_REG_RBD")

    df = pd.DataFrame(datos)

    df['GEN_ALU']= df['GEN_ALU'].map(categorias_genero)
    df['RURAL_RBD']= df['RURAL_RBD'].map(categorias_zona)

## Grafico promedio por genero
    
    prom_por_genero = df.groupby("GEN_ALU")["PROM_GRAL"].mean().reset_index()
    prom_por_genero.columns = ['Género', 'Promedio']
    
    fig = go.Figure()

    for genero in prom_por_genero['Género'].unique():
        df_filtrado = prom_por_genero[prom_por_genero['Género']==genero]
        fig.add_trace(go.Bar(
            x=df_filtrado['Género'],
            y=df_filtrado['Promedio'],
            text= df_filtrado['Promedio'].apply(lambda x: f"{x: .2f}"),
            textposition= 'outside',
            name= genero
        ))

    fig.update_layout(
        title= 'Promedio Académico por Género',
        xaxis_title= 'Género',
        title_font= dict(weight="bold"),
        title_x=0.5,
        yaxis= dict(title='Promedio', range=[0,7]),
        bargap= 0.2,
        bargroupgap= 0.1,
        autosize= True,
        height= 400,
        template= 'simple_white'
    )
## Grafico asistencia por genero

    asis_por_genero = df.groupby("GEN_ALU")["ASISTENCIA"].mean().reset_index()
    asis_por_genero.columns = ["Género", "Asistencia"]

    fig2 = go.Figure()

    for genero in asis_por_genero['Género'].unique():
        df_filtrado = asis_por_genero[asis_por_genero['Género']==genero]
        fig2.add_trace(go.Bar(
            x= df_filtrado['Género'],
            y= df_filtrado['Asistencia'],
            text= df_filtrado['Asistencia'].apply(lambda x: f"{x: .2f}"),
            textposition= 'outside',
            name= genero
        ))

    fig2.update_layout(
        title= 'Asistencia por Género',
        xaxis_title= 'Género',
        title_font= dict(weight="bold"),
        title_x=0.5,
        yaxis= dict(title= "Promedio Asistencia", range=[0,100]),
        bargap= 0.2,
        bargroupgap= 0.1,
        autosize= True,
        height= 400,
        template= 'simple_white'
    )

## Grafico promedio por rural

    prom_por_zona = df.groupby("RURAL_RBD")["PROM_GRAL"].mean().reset_index()
    prom_por_zona.columns = ["Zona", "Promedio"]

    fig3 = go.Figure()

    for zona in prom_por_zona['Zona'].unique():
        df_filtrado= prom_por_zona[prom_por_zona['Zona']== zona]
        fig3.add_trace(go.Bar(
            x= df_filtrado['Zona'],
            y= df_filtrado['Promedio'],
            text= df_filtrado['Promedio'].apply(lambda x: f"{x: .2f}"),
            textposition= 'outside',
            name= zona
        ))

    fig3.update_layout(
        title= 'Promedio por Zona',
        xaxis_title= 'Zona',
        title_font= dict(weight="bold"),
        title_x=0.5,
        yaxis= dict(title='Promedio', range=[0,7]),
        bargap= 0.2,
        bargroupgap= 0.1,
        autosize= True,
        height= 400,
        template= 'simple_white'
    )

## Grafico asistencia por rural

    asis_por_zona = df.groupby("RURAL_RBD")["ASISTENCIA"].mean().reset_index()
    asis_por_zona.columns = ["Zona", "Asistencia"]

    fig4 = go.Figure()

    for zona in asis_por_zona['Zona'].unique():
        df_filtrado = asis_por_zona[asis_por_zona['Zona']== zona]
        fig4.add_trace(go.Bar(
            x= df_filtrado['Zona'],
            y= df_filtrado['Asistencia'],
            text= df_filtrado['Asistencia'].apply(lambda x: f"{x: .2f}"),
            textposition= 'outside',
            name= zona
        ))

    fig4.update_layout(
        title='Promedio Asistencia por Zona',
        xaxis_title= 'Zona',
        title_font= dict(weight="bold"),
        title_x=0.5,
        yaxis= dict(title= 'Promedio Asistencia', tickformat='.2f', range=[0,100]),
        bargap= 0.2,
        bargroupgap= 0.1,
        autosize= True,
        height= 400,
        template= 'simple_white'
    )

    grafico_prom_gen = fig.to_html()
    grafico_asis_gen = fig2.to_html()
    grafico_prom_ru = fig3.to_html()
    grafico_asis_ru = fig4.to_html()

    return render (request, 'educacion/grafico_rendimiento_21.html', {'region': region_seleccionada,
                                                                    'grafico_prom_gen': grafico_prom_gen,
                                                                    'grafico_asis_gen': grafico_asis_gen,
                                                                    'grafico_prom_ru': grafico_prom_ru,
                                                                    'grafico_asis_ru': grafico_asis_ru})

def grafico_rendimiento_22 (request):

    categorias_genero = {
        1 : "Masculino",
        2 : "Femenino"
    }
    categorias_zona = {
        0 : "Urbano",
        1 : "Rural"
    }

    region_seleccionada = request.GET.get("COD_REG_RBD", "13")

    datos = rendimiento_academico.objects.filter(AGNO=2022)

    if region_seleccionada:
        datos = datos.filter(COD_REG_RBD = region_seleccionada)

    datos = datos.values("COD_DEPE", "RURAL_RBD","GEN_ALU","COD_JOR", "PROM_GRAL", 
                         "ASISTENCIA", "SIT_FIN_R", "EDAD_ALU", "COD_REG_RBD")

    df = pd.DataFrame(datos)

    df['GEN_ALU'] = df['GEN_ALU'].map(categorias_genero)
    df['RURAL_RBD'] = df['RURAL_RBD'].map(categorias_zona)

## Grafico promedio por genero

    prom_por_genero = df.groupby("GEN_ALU")["PROM_GRAL"].mean().reset_index()
    prom_por_genero.columns = ["Género", "Promedio"]

    fig = go.Figure()

    for genero in prom_por_genero["Género"].unique():
        df_filtrado = prom_por_genero[prom_por_genero['Género']== genero]
        fig.add_trace(go.Bar(
            x= df_filtrado["Género"],
            y= df_filtrado["Promedio"],
            text= df_filtrado["Promedio"].apply(lambda x: f"{x: .2f}"),
            textposition= "outside",
            name= genero
        ))
    
    fig.update_layout(
        title="Promedio Académico por Género", 
        xaxis_title="Género",
        title_font= dict(weight="bold"),
        title_x=0.5, 
        yaxis=dict(title="Promedio", range=[0, 7]),
        bargap=0.2,
        bargroupgap=0.1,
        template="simple_white",
        autosize=True,
        height=400
    )

## Grafico asistencia por genero

    asis_por_genero = df.groupby("GEN_ALU")["ASISTENCIA"].mean().reset_index()
    asis_por_genero.columns = ["Género", "Asistencia"]

    fig2 = go.Figure()

    for genero in asis_por_genero["Género"].unique():
        df_filtrado = asis_por_genero[asis_por_genero["Género"]== genero]
        fig2.add_trace(go.Bar(
            x= df_filtrado["Género"],
            y= df_filtrado["Asistencia"],
            text = df_filtrado["Asistencia"].apply(lambda x: f"{x: .2f}"),
            textposition= "outside",
            name = genero
        ))

    fig2.update_layout(
            title="Asistencia por Género",
            xaxis_title="Zona",
            title_font= dict(weight="bold"),
            title_x=0.5,
            yaxis=dict(title="Promedio Asistencia", range=[0, 100]),
            bargap=0.2,
            bargroupgap=0.1,
            template="simple_white",
            autosize=True,
            height=400
        )

## Grafico promedio por rural

    prom_por_zona = df.groupby("RURAL_RBD")["PROM_GRAL"].mean().reset_index()
    prom_por_zona.columns = ["Zona", "Promedio"]

    fig3 = go.Figure()

    for zona in prom_por_zona["Zona"].unique():
        df_filtrado = prom_por_zona[prom_por_zona["Zona"]== zona]
        fig3.add_trace(go.Bar(
            x= df_filtrado["Zona"],
            y= df_filtrado["Promedio"],
            text= df_filtrado["Promedio"].apply(lambda x: f"{x: .2f}"), 
            textposition= "outside",
            name = zona
        ))

        fig3.update_layout(
            title="Promedio Académico por Zona",
            xaxis_title="Zona",
            title_font= dict(weight="bold"),
            title_x=0.5,
            yaxis=dict(title="Promedio", range=[0, 7]),
            bargap=0.2,
            bargroupgap=0.1,
            template="simple_white",
            autosize=True,
            height=400
        )

## Grafico asistencia por rural

    asis_por_zona = df.groupby("RURAL_RBD")["ASISTENCIA"].mean().reset_index()
    asis_por_zona.columns = ["Zona", "Asistencia"]

    fig4 = go.Figure()

    for zona in asis_por_zona['Zona'].unique():
        df_filtrado = asis_por_zona[asis_por_zona['Zona']==zona]
        fig4.add_trace(go.Bar(
            x= df_filtrado['Zona'],
            y= df_filtrado['Asistencia'],
            text= df_filtrado['Asistencia'].apply(lambda x: f"{x: .2f}"),
            textposition= 'outside',
            name= zona 
        ))
    
    fig4.update_layout(
            title="Asistencia por Zona",
            xaxis_title="Zona",
            title_font= dict(weight="bold"),
            title_x=0.5,
            yaxis=dict(title="Promedio Asistencia", range=[0, 100]),
            bargap=0.2,
            bargroupgap=0.1,
            template="simple_white",
            autosize=True,
            height=400
        )
    
    grafico_prom_gen = fig.to_html()
    grafico_asis_gen = fig2.to_html()
    grafico_prom_ru = fig3.to_html()
    grafico_asis_ru = fig4.to_html()

    return render(request, "educacion/grafico_rendimiento_22.html",{'region': region_seleccionada,
                                                                    'grafico_prom_gen': grafico_prom_gen,
                                                                    'grafico_asis_gen': grafico_asis_gen,
                                                                    'grafico_prom_ru': grafico_prom_ru,
                                                                    'grafico_asis_ru': grafico_asis_ru})

def grafico_rendimiento_23 (request):

    categorias_genero = {
        1 : "Masculino",
        2 : "Femenino"
    }
    categorias_zona = {
        0 : "Urbano",
        1 : "Rural"
    }

    region_seleccionada = request.GET.get("COD_REG_RBD", "13")

    datos = rendimiento_academico.objects.filter(AGNO=2023)

    if region_seleccionada:
        datos = datos.filter(COD_REG_RBD = region_seleccionada)

    datos = datos.values("COD_DEPE", "RURAL_RBD","GEN_ALU","COD_JOR", "PROM_GRAL", 
                         "ASISTENCIA", "SIT_FIN_R", "EDAD_ALU", "COD_REG_RBD")

    df = pd.DataFrame(datos)

    df["GEN_ALU"] = df["GEN_ALU"].map(categorias_genero)
    df['RURAL_RBD'] = df['RURAL_RBD'].map(categorias_zona)


## Grafico promedio por genero

    prom_por_genero = df.groupby("GEN_ALU")["PROM_GRAL"].mean().reset_index()
    prom_por_genero.columns = ["Género", "Promedio"]

    fig = go.Figure()
    for genero in prom_por_genero["Género"].unique():
        df_filtrado = prom_por_genero[prom_por_genero["Género"] == genero]
        fig.add_trace(go.Bar(
            x= df_filtrado["Género"], 
            y=df_filtrado["Promedio"],
            text=df_filtrado["Promedio"].apply(lambda x: f"{x:.2f}"),
            textposition='outside', 
            name= genero
        )) 
        
    fig.update_layout(
        title="Promedio Académico por Género", 
        xaxis_title="Género",
        title_font= dict(weight="bold"),
        title_x=0.5, 
        yaxis=dict(title="Promedio", tickformat=".2f", range=[0, 7]),
        bargap=0.2,
        bargroupgap=0.1,
        template="simple_white",
        autosize=True,
        height=400
        )

## Grafico asistencia por genero

    asis_por_genero = df.groupby("GEN_ALU")["ASISTENCIA"].mean().reset_index()
    asis_por_genero.columns = ['Género', 'Asistencia']

    fig2 = go.Figure()

    for genero in asis_por_genero['Género'].unique():
        df_filtrado = asis_por_genero[asis_por_genero['Género']== genero]
        fig2.add_trace(go.Bar(
                    x=df_filtrado["Género"], 
                    y=df_filtrado["Asistencia"], 
                    text= df_filtrado["Asistencia"].apply(lambda x: f"{x:.2f}"),
                    textposition= 'outside',
                    name=genero,
        ))
        
    fig2.update_layout(
        title="Asistencia Promedio por Género",
        xaxis_title="Género",
        title_font= dict(weight="bold"),
        title_x=0.5,
        yaxis=dict(title="Promedio", tickformat=".2f", range=[0, 100]),
        bargap=0.2,
        bargroupgap=0.1,
        template="simple_white",
        autosize=True,
        height=400
        )

## Grafico promedio por rural

    prom_por_zona = df.groupby("RURAL_RBD")["PROM_GRAL"].mean().reset_index()
    prom_por_zona.columns = ["Zona", "Promedio"]

    fig3 = go.Figure()

    for zona in prom_por_zona["Zona"].unique():
        df_filtrado = prom_por_zona[prom_por_zona['Zona'] == zona]
        fig3.add_trace(go.Bar(
            x=df_filtrado["Zona"],  # Solo esa zona
            y=df_filtrado["Promedio"],
            text=df_filtrado["Promedio"].apply(lambda x: f"{x:.2f}"),
            textposition='outside',
            name=zona
        ))

    fig3.update_layout(
        title="Promedio Académico por Zona",
        xaxis_title="Zona",
        title_font= dict(weight="bold"),
        title_x=0.5,
        yaxis=dict(title="Promedio", tickformat=".2f", range=[0, 7]),
        bargap=0.2,
        bargroupgap=0.1,
        template="simple_white",
        autosize=True,
        height=400
    )

## Grafico asistencia por rural

    asis_por_zona = df.groupby("RURAL_RBD")["ASISTENCIA"].mean().reset_index()
    asis_por_zona.columns = ["Zona", "Asistencia"]

    fig4 = go.Figure()

    for zona in asis_por_zona["Zona"].unique():
        df_filtrado = asis_por_zona[asis_por_zona['Zona']== zona]
        fig4.add_trace(go.Bar(
            x=df_filtrado["Zona"], 
            y=df_filtrado["Asistencia"],
            text= df_filtrado["Asistencia"].apply(lambda x: f"{x: .2f}"),
            textposition= "outside", 
            name= zona 
        ))
    
    fig4.update_layout(
        title="Promedio Asistencia por Zona",
        xaxis_title="Zona",
        title_font= dict(weight="bold"),
        title_x=0.5,
        yaxis=dict(title="Promedio", tickformat=".2f", range=[0, 100]),
        bargap=0.2,
        bargroupgap=0.1,
        template="simple_white",
        autosize=True,
        height=400
        )
    
    grafico_prom_gen = fig.to_html()
    grafico_asis_gen = fig2.to_html()
    grafico_prom_ru = fig3.to_html()
    grafico_asis_ru = fig4.to_html()

    return render (request, 'educacion/grafico_rendimiento_23.html', {"grafico_prom_gen": grafico_prom_gen,
                                                                      "grafico_asis_gen": grafico_asis_gen,
                                                                      "grafico_prom_ru": grafico_prom_ru,
                                                                      "grafico_asis_ru": grafico_asis_ru,
                                                                      "region": region_seleccionada})
