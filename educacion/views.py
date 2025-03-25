from django.shortcuts import render
from .models import matricula_parvulo, matricula_basica, matricula_media, resultados_simce, resultados_simce_idps
from django.http import HttpResponse
from django.core.paginator import Paginator
from .forms import Estudiantes_filtro
from .admin import MatriculaParvuloResource
from django.db.models import Q
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from scipy.stats import chi2_contingency


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

    # Renombrar catagorias 
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
        fig.add_trace(go.Bar(
            x=df_filtrado['Género'],
            y=df_filtrado['Porcentaje'],
            name=zona,  # Esto agrupará las barras por zona
            text=df_filtrado['Porcentaje'].apply(lambda x: f"{x:.2f}%"),  # Muestra los valores en las barras
            textposition='auto'
        ))

    # Configurar el diseño del gráfico
    fig.update_layout(
        barmode='group',  # Agrupar barras
        title="Gráfico género según zona",
        title_font= dict(weight="bold"),
        title_x=0.5,
        yaxis=dict(title="Porcentaje", tickformat=".2f", range=[0, 100]),
        xaxis_title="Género",
        bargap=0.2,  # Espaciado entre barras de diferentes grupos
        bargroupgap=0.1,  # Espaciado dentro de un grupo
        autosize= True
    )


### **Gráfico 2: Distribución género segun dependencia**

    conteo_dependencia = df.groupby(['gen_alu','dependencia']).size().reset_index(name='Cantidad')
    conteo_dependencia.columns = ['Género','Dependencia', 'Cantidad']

# Calcular porcentaje total
    totales_por_dependencia = conteo_dependencia.groupby('Género')['Cantidad'].transform('sum')
    conteo_dependencia['Porcentaje'] = (conteo_dependencia['Cantidad'] / totales_por_dependencia) * 100

    fig2 = go.Figure()


    for dependencia in conteo_dependencia['Dependencia'].unique():
        df_filtrado = conteo_dependencia[conteo_dependencia['Dependencia'] == dependencia]
        fig2.add_trace(go.Bar(
            x =df_filtrado['Género'],
            y = df_filtrado['Porcentaje'],
            name= dependencia, 
            text=df_filtrado['Porcentaje'].apply(lambda x: f"{x:.2f}%"),
            textposition= 'auto'
            ))

    fig2.update_layout(
        barmode='group',
        title="Gráfico género según dependencia administrativa",
        title_font= dict(weight="bold"),
        title_x=0.5,
        yaxis=dict(title="Porcentaje", tickformat=".2f", range=[0, 100]),
        xaxis_title="Género",
        bargap=0.1,
        bargroupgap=0.1,
        autosize= True,
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
        fig3.add_trace(go.Bar(
            x =df_filtrado['Género'],
            y = df_filtrado['Porcentaje'],
            name= tipo, 
            text=df_filtrado['Porcentaje'].apply(lambda x: f"{x:.2f}%"),
            textposition= 'auto'
            ))

    fig3.update_layout(
        barmode='group',
        title="Gráfico género según tipo",
        title_font= dict(weight="bold"),
        title_x=0.5,
        yaxis=dict(title="Porcentaje", tickformat=".2f", range=[0, 100]),
        xaxis_title="Género",
        bargap=0.1,
        bargroupgap=0.1,
        autosize= True,
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


    for nivel in conteo_nivel['Nivel'].unique():
        df_filtrado = conteo_nivel[conteo_nivel['Nivel'] == nivel]
        fig4.add_trace(go.Bar(
            x =df_filtrado['Zona'],
            y = df_filtrado['Porcentaje'],
            name= nivel, 
            text=df_filtrado['Porcentaje'].apply(lambda x: f"{x:.2f}%"),
            textposition= 'auto'
            ))

    fig4.update_layout(
        barmode='group',
        title="Gráfico género según nivel",
        title_font= dict(weight="bold"),
        title_x=0.5,
        yaxis=dict(title="Porcentaje", tickformat=".2f", range=[0, 100]),
        xaxis_title="Zona",
        bargap=0.1,
        bargroupgap=0.1,
        autosize= True,
    )

    grafico_genero_zona_html = fig.to_html()
    grafico_genero_dependencia_html = fig2.to_html()
    grafico_genero_tipo_html = fig3.to_html()
    grafico_genero_nivel_html = fig4.to_html()


    # Prueba de chi-cuadrado para tipo de enseñanza (Ed. Parvularia vs. Ed. Especial)
    tabla_tipo = pd.crosstab(df['gen_alu'], df['cod_ense2_m'])
    chi2_tipo, p_tipo, _, _ = chi2_contingency(tabla_tipo)

    # Prueba de chi-cuadrado para nivel educativo (Sala cuna menor, mayor, etc.)
    tabla_nivel = pd.crosstab(df['rural_estab'], df['nivel1'])
    chi2_nivel, p_nivel, _, _ = chi2_contingency(tabla_nivel)

    return render(request, 'educacion/graficos_parvulo_2021.html', {'grafico_html': grafico_genero_zona_html,
                                                    'grafico_dependencia_html': grafico_genero_dependencia_html,
                                                    'grafico_tipo_html': grafico_genero_tipo_html,
                                                    'grafico_nivel_html':grafico_genero_nivel_html,
                                                    'chi2_tipo': round(chi2_tipo, 2),
                                                    'p_tipo': round(p_tipo, 4),
                                                    'chi2_nivel': round(chi2_nivel, 2),
                                                    'p_nivel': round(p_nivel, 4),
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
        fig.add_trace(go.Bar(
            x=df_filtrado['Género'],
            y=df_filtrado['Porcentaje'],
            name=zona,  # Esto agrupará las barras por zona
            text=df_filtrado['Porcentaje'].apply(lambda x: f"{x:.2f}%"),  # Muestra los valores en las barras
            textposition='auto'
        ))

    # Configurar el diseño del gráfico
    fig.update_layout(
        barmode='group',  # Agrupar barras
        title="Gráfico género según zona",
        title_font= dict(weight="bold"),
        title_x=0.5,
        yaxis=dict(title="Porcentaje", tickformat=".2f", range=[0, 100]),
        xaxis_title="Género",
        bargap=0.2,  # Espaciado entre barras de diferentes grupos
        bargroupgap=0.1,  # Espaciado dentro de un grupo
        autosize= True
    )


### **Gráfico 2: Distribución género segun dependencia**

    conteo_dependencia = df.groupby(['gen_alu','dependencia']).size().reset_index(name='Cantidad')
    conteo_dependencia.columns = ['Género','Dependencia', 'Cantidad']

# Calcular porcentaje total
    totales_por_dependencia = conteo_dependencia.groupby('Género')['Cantidad'].transform('sum')
    conteo_dependencia['Porcentaje'] = (conteo_dependencia['Cantidad'] / totales_por_dependencia) * 100

    fig2 = go.Figure()


    for dependencia in conteo_dependencia['Dependencia'].unique():
        df_filtrado = conteo_dependencia[conteo_dependencia['Dependencia'] == dependencia]
        fig2.add_trace(go.Bar(
            x =df_filtrado['Género'],
            y = df_filtrado['Porcentaje'],
            name= dependencia, 
            text=df_filtrado['Porcentaje'].apply(lambda x: f"{x:.2f}%"),
            textposition= 'auto'
            ))

    fig2.update_layout(
        barmode='group',
        title="Gráfico género según dependencia administrativa",
        title_font= dict(weight="bold"),
        title_x=0.5,
        yaxis=dict(title="Porcentaje", tickformat=".2f", range=[0, 100]),
        xaxis_title="Género",
        bargap=0.1,
        bargroupgap=0.1,
        autosize= True,
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
        fig3.add_trace(go.Bar(
            x =df_filtrado['Género'],
            y = df_filtrado['Porcentaje'],
            name= tipo, 
            text=df_filtrado['Porcentaje'].apply(lambda x: f"{x:.2f}%"),
            textposition= 'auto'
            ))

    fig3.update_layout(
        barmode='group',
        title="Gráfico género según tipo",
        title_font= dict(weight="bold"),
        title_x=0.5,
        yaxis=dict(title="Porcentaje", tickformat=".2f", range=[0, 100]),
        xaxis_title="Género",
        bargap=0.1,
        bargroupgap=0.1,
        autosize= True,
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


    for nivel in conteo_nivel['Nivel'].unique():
        df_filtrado = conteo_nivel[conteo_nivel['Nivel'] == nivel]
        fig4.add_trace(go.Bar(
            x =df_filtrado['Zona'],
            y = df_filtrado['Porcentaje'],
            name= nivel, 
            text=df_filtrado['Porcentaje'].apply(lambda x: f"{x:.2f}%"),
            textposition= 'auto'
            ))

    fig4.update_layout(
        barmode='group',
        title="Gráfico género según nivel",
        title_font= dict(weight="bold"),
        title_x=0.5,
        yaxis=dict(title="Porcentaje", tickformat=".2f", range=[0, 100]),
        xaxis_title="Zona",
        bargap=0.1,
        bargroupgap=0.1,
        autosize= True,
    )

    grafico_genero_zona_html = fig.to_html()
    grafico_genero_dependencia_html = fig2.to_html()
    grafico_genero_tipo_html = fig3.to_html()
    grafico_genero_nivel_html = fig4.to_html()

    # Prueba de chi-cuadrado para tipo de enseñanza (Ed. Parvularia vs. Ed. Especial)
    tabla_tipo = pd.crosstab(df['gen_alu'], df['cod_ense2_m'])
    chi2_tipo, p_tipo, _, _ = chi2_contingency(tabla_tipo)

    # Prueba de chi-cuadrado para nivel educativo (Sala cuna menor, mayor, etc.)
    tabla_nivel = pd.crosstab(df['rural_estab'], df['nivel1'])
    chi2_nivel, p_nivel, _, _ = chi2_contingency(tabla_nivel)

    return render(request, 'educacion/graficos_parvulo_2022.html', {'grafico_html': grafico_genero_zona_html,
                                                    'grafico_dependencia_html': grafico_genero_dependencia_html,
                                                    'grafico_tipo_html': grafico_genero_tipo_html,
                                                    'grafico_nivel_html':grafico_genero_nivel_html,
                                                    'chi2_tipo': round(chi2_tipo, 2),
                                                    'p_tipo': round(p_tipo, 4),
                                                    'chi2_nivel': round(chi2_nivel, 2),
                                                    'p_nivel': round(p_nivel, 4),
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
        fig.add_trace(go.Bar(
            x=df_filtrado['Género'],
            y=df_filtrado['Porcentaje'],
            name=zona,  # Esto agrupará las barras por zona
            text=df_filtrado['Porcentaje'].apply(lambda x: f"{x:.2f}%"),  # Muestra los valores en las barras
            textposition='auto'
        ))

    # Configurar el diseño del gráfico
    fig.update_layout(
        barmode='group',  # Agrupar barras
        title="Gráfico género según zona",
        title_font= dict(weight="bold"),
        title_x=0.5,
        yaxis=dict(title="Porcentaje", tickformat=".2f", range=[0, 100]),
        xaxis_title="Género",
        bargap=0.2,  # Espaciado entre barras de diferentes grupos
        bargroupgap=0.1,  # Espaciado dentro de un grupo
        autosize= True
    )


### **Gráfico 2: Distribución género segun dependencia**

    conteo_dependencia = df.groupby(['gen_alu','dependencia']).size().reset_index(name='Cantidad')
    conteo_dependencia.columns = ['Género','Dependencia', 'Cantidad']

# Calcular porcentaje total
    totales_por_dependencia = conteo_dependencia.groupby('Género')['Cantidad'].transform('sum')
    conteo_dependencia['Porcentaje'] = (conteo_dependencia['Cantidad'] / totales_por_dependencia) * 100

    fig2 = go.Figure()


    for dependencia in conteo_dependencia['Dependencia'].unique():
        df_filtrado = conteo_dependencia[conteo_dependencia['Dependencia'] == dependencia]
        fig2.add_trace(go.Bar(
            x =df_filtrado['Género'],
            y = df_filtrado['Porcentaje'],
            name= dependencia, 
            text=df_filtrado['Porcentaje'].apply(lambda x: f"{x:.2f}%"),
            textposition= 'auto'
            ))

    fig2.update_layout(
        barmode='group',
        title="Gráfico género según dependencia administrativa",
        title_font= dict(weight="bold"),
        title_x=0.5,
        yaxis=dict(title="Porcentaje", tickformat=".2f", range=[0, 100]),
        xaxis_title="Género",
        bargap=0.1,
        bargroupgap=0.1,
        autosize= True,
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
        fig3.add_trace(go.Bar(
            x =df_filtrado['Género'],
            y = df_filtrado['Porcentaje'],
            name= tipo, 
            text=df_filtrado['Porcentaje'].apply(lambda x: f"{x:.2f}%"),
            textposition= 'auto'
            ))

    fig3.update_layout(
        barmode='group',
        title="Gráfico género según tipo",
        title_font= dict(weight="bold"),
        title_x=0.5,
        yaxis=dict(title="Porcentaje", tickformat=".2f", range=[0, 100]),
        xaxis_title="Género",
        bargap=0.1,
        bargroupgap=0.1,
        autosize= True,
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


    for nivel in conteo_nivel['Nivel'].unique():
        df_filtrado = conteo_nivel[conteo_nivel['Nivel'] == nivel]
        fig4.add_trace(go.Bar(
            x =df_filtrado['Zona'],
            y = df_filtrado['Porcentaje'],
            name= nivel, 
            text=df_filtrado['Porcentaje'].apply(lambda x: f"{x:.2f}%"),
            textposition= 'auto'
            ))

    fig4.update_layout(
        barmode='group',
        title="Gráfico género según nivel",
        title_font= dict(weight="bold"),
        title_x=0.5,
        yaxis=dict(title="Porcentaje", tickformat=".2f", range=[0, 100]),
        xaxis_title="Zona",
        bargap=0.1,
        bargroupgap=0.1,
        autosize= True,
    )

    grafico_genero_zona_html = fig.to_html()
    grafico_genero_dependencia_html = fig2.to_html()
    grafico_genero_tipo_html = fig3.to_html()
    grafico_genero_nivel_html = fig4.to_html()

    # Prueba de chi-cuadrado para tipo de enseñanza (Ed. Parvularia vs. Ed. Especial)
    tabla_tipo = pd.crosstab(df['gen_alu'], df['cod_ense2_m'])
    chi2_tipo, p_tipo, _, _ = chi2_contingency(tabla_tipo)

    # Prueba de chi-cuadrado para nivel educativo (Sala cuna menor, mayor, etc.)
    tabla_nivel = pd.crosstab(df['rural_estab'], df['nivel1'])
    chi2_nivel, p_nivel, _, _ = chi2_contingency(tabla_nivel)

    return render(request, 'educacion/graficos_parvulo_2023.html', {'grafico_html': grafico_genero_zona_html,
                                                    'grafico_dependencia_html': grafico_genero_dependencia_html,
                                                    'grafico_tipo_html': grafico_genero_tipo_html,
                                                    'grafico_nivel_html':grafico_genero_nivel_html,
                                                    'chi2_tipo': round(chi2_tipo, 2),
                                                    'p_tipo': round(p_tipo, 4),
                                                    'chi2_nivel': round(chi2_nivel, 2),
                                                    'p_nivel': round(p_nivel, 4),
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
        fig.add_trace(go.Bar(
            x=df_filtrado['Género'],
            y=df_filtrado['Porcentaje'],
            name=zona,  # Esto agrupará las barras por zona
            text=df_filtrado['Porcentaje'].apply(lambda x: f"{x:.2f}%"),  # Muestra los valores en las barras
            textposition='auto'
        ))

    # Configurar el diseño del gráfico
    fig.update_layout(
        barmode='group',  # Agrupar barras
        title="Gráfico género según zona",
        title_font= dict(weight="bold"),
        title_x=0.5,
        yaxis=dict(title="Porcentaje", tickformat=".2f", range=[0, 100]),
        xaxis_title="Género",
        bargap=0.2,  # Espaciado entre barras de diferentes grupos
        bargroupgap=0.1,  # Espaciado dentro de un grupo
        autosize= True
    )


### **Gráfico 2: Distribución género segun dependencia**

    conteo_dependencia = df.groupby(['gen_alu','dependencia']).size().reset_index(name='Cantidad')
    conteo_dependencia.columns = ['Género','Dependencia', 'Cantidad']

# Calcular porcentaje total
    totales_por_dependencia = conteo_dependencia.groupby('Género')['Cantidad'].transform('sum')
    conteo_dependencia['Porcentaje'] = (conteo_dependencia['Cantidad'] / totales_por_dependencia) * 100

    fig2 = go.Figure()


    for dependencia in conteo_dependencia['Dependencia'].unique():
        df_filtrado = conteo_dependencia[conteo_dependencia['Dependencia'] == dependencia]
        fig2.add_trace(go.Bar(
            x =df_filtrado['Género'],
            y = df_filtrado['Porcentaje'],
            name= dependencia, 
            text=df_filtrado['Porcentaje'].apply(lambda x: f"{x:.2f}%"),
            textposition= 'auto'
            ))

    fig2.update_layout(
        barmode='group',
        title="Gráfico género según dependencia administrativa",
        title_font= dict(weight="bold"),
        title_x=0.5,
        yaxis=dict(title="Porcentaje", tickformat=".2f", range=[0, 100]),
        xaxis_title="Género",
        bargap=0.1,
        bargroupgap=0.1,
        autosize= True,
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
        fig3.add_trace(go.Bar(
            x =df_filtrado['Género'],
            y = df_filtrado['Porcentaje'],
            name= tipo, 
            text=df_filtrado['Porcentaje'].apply(lambda x: f"{x:.2f}%"),
            textposition= 'auto'
            ))

    fig3.update_layout(
        barmode='group',
        title="Gráfico género según tipo",
        title_font= dict(weight="bold"),
        title_x=0.5,
        yaxis=dict(title="Porcentaje", tickformat=".2f", range=[0, 100]),
        xaxis_title="Género",
        bargap=0.1,
        bargroupgap=0.1,
        autosize= True,
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


    for nivel in conteo_nivel['Nivel'].unique():
        df_filtrado = conteo_nivel[conteo_nivel['Nivel'] == nivel]
        fig4.add_trace(go.Bar(
            x =df_filtrado['Zona'],
            y = df_filtrado['Porcentaje'],
            name= nivel, 
            text=df_filtrado['Porcentaje'].apply(lambda x: f"{x:.2f}%"),
            textposition= 'auto'
            ))

    fig4.update_layout(
        barmode='group',
        title="Gráfico género según nivel",
        title_font= dict(weight="bold"),
        title_x=0.5,
        yaxis=dict(title="Porcentaje", tickformat=".2f", range=[0, 100]),
        xaxis_title="Zona",
        bargap=0.1,
        bargroupgap=0.1,
        autosize= True,
    )

    grafico_genero_zona_html = fig.to_html()
    grafico_genero_dependencia_html = fig2.to_html()
    grafico_genero_tipo_html = fig3.to_html()
    grafico_genero_nivel_html = fig4.to_html()

    # Prueba de chi-cuadrado para tipo de enseñanza (Ed. Parvularia vs. Ed. Especial)
    tabla_tipo = pd.crosstab(df['gen_alu'], df['cod_ense2_m'])
    chi2_tipo, p_tipo, _, _ = chi2_contingency(tabla_tipo)

    # Prueba de chi-cuadrado para nivel educativo (Sala cuna menor, mayor, etc.)
    tabla_nivel = pd.crosstab(df['rural_estab'], df['nivel1'])
    chi2_nivel, p_nivel, _, _ = chi2_contingency(tabla_nivel)

    return render(request, 'educacion/graficos_parvulo_2024.html', {'grafico_html': grafico_genero_zona_html,
                                                        'grafico_dependencia_html': grafico_genero_dependencia_html,
                                                        'grafico_tipo_html': grafico_genero_tipo_html,
                                                        'grafico_nivel_html':grafico_genero_nivel_html,
                                                        'chi2_tipo': round(chi2_tipo, 2),
                                                        'p_tipo': round(p_tipo, 4),
                                                        'chi2_nivel': round(chi2_nivel, 2),
                                                        'p_nivel': round(p_nivel, 4),
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

    # Obtener la región seleccionada desde la URL (por defecto muestra todos)
    region_seleccionada = request.GET.get('nom_reg_a_estab', "RM")

    datos = matricula_parvulo.objects.filter(agno=2020, gen_alu__in= [1, 2])
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
        fig.add_trace(go.Bar(
            x=df_filtrado['Género'],
            y=df_filtrado['Porcentaje'],
            name=zona,  # Esto agrupará las barras por zona
            text=df_filtrado['Porcentaje'].apply(lambda x: f"{x:.2f}%"),  # Muestra los valores en las barras
            textposition='auto'
        ))

    # Configurar el diseño del gráfico
    fig.update_layout(
        barmode='group',  # Agrupar barras
        title="Gráfico género según zona",
        title_font= dict(weight="bold"),
        title_x=0.5,
        yaxis=dict(title="Porcentaje", tickformat=".2f", range=[0, 100]),
        xaxis_title="Género",
        bargap=0.2,  # Espaciado entre barras de diferentes grupos
        bargroupgap=0.1,  # Espaciado dentro de un grupo
        autosize= True
    )


### **Gráfico 2: Distribución género segun dependencia**

    conteo_dependencia = df.groupby(['gen_alu','dependencia']).size().reset_index(name='Cantidad')
    conteo_dependencia.columns = ['Género','Dependencia', 'Cantidad']

# Calcular porcentaje total
    totales_por_dependencia = conteo_dependencia.groupby('Género')['Cantidad'].transform('sum')
    conteo_dependencia['Porcentaje'] = (conteo_dependencia['Cantidad'] / totales_por_dependencia) * 100

    fig2 = go.Figure()


    for dependencia in conteo_dependencia['Dependencia'].unique():
        df_filtrado = conteo_dependencia[conteo_dependencia['Dependencia'] == dependencia]
        fig2.add_trace(go.Bar(
            x =df_filtrado['Género'],
            y = df_filtrado['Porcentaje'],
            name= dependencia, 
            text=df_filtrado['Porcentaje'].apply(lambda x: f"{x:.2f}%"),
            textposition= 'auto'
            ))

    fig2.update_layout(
        barmode='group',
        title="Gráfico género según dependencia administrativa",
        title_font= dict(weight="bold"),
        title_x=0.5,
        yaxis=dict(title="Porcentaje", tickformat=".2f", range=[0, 100]),
        xaxis_title="Género",
        bargap=0.1,
        bargroupgap=0.1,
        autosize= True,
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
        fig3.add_trace(go.Bar(
            x =df_filtrado['Género'],
            y = df_filtrado['Porcentaje'],
            name= tipo, 
            text=df_filtrado['Porcentaje'].apply(lambda x: f"{x:.2f}%"),
            textposition= 'auto'
            ))

    fig3.update_layout(
        barmode='group',
        title="Gráfico género según tipo",
        title_font= dict(weight="bold"),
        title_x=0.5,
        yaxis=dict(title="Porcentaje", tickformat=".2f", range=[0, 100]),
        xaxis_title="Género",
        bargap=0.1,
        bargroupgap=0.1,
        autosize= True,
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


    for nivel in conteo_nivel['Nivel'].unique():
        df_filtrado = conteo_nivel[conteo_nivel['Nivel'] == nivel]
        fig4.add_trace(go.Bar(
            x =df_filtrado['Zona'],
            y = df_filtrado['Porcentaje'],
            name= nivel, 
            text=df_filtrado['Porcentaje'].apply(lambda x: f"{x:.2f}%"),
            textposition= 'auto'
            ))

    fig4.update_layout(
        barmode='group',
        title="Gráfico género según nivel",
        title_font= dict(weight="bold"),
        title_x=0.5,
        yaxis=dict(title="Porcentaje", tickformat=".2f", range=[0, 100]),
        xaxis_title="Zona",
        bargap=0.1,
        bargroupgap=0.1,
        autosize= True,
    )

    grafico_genero_zona_html = fig.to_html()
    grafico_genero_dependencia_html = fig2.to_html()
    grafico_genero_tipo_html = fig3.to_html()
    grafico_genero_nivel_html = fig4.to_html()

    # Prueba de chi-cuadrado para tipo de enseñanza (Ed. Parvularia vs. Ed. Especial)
    tabla_tipo = pd.crosstab(df['gen_alu'], df['cod_ense2_m'])
    chi2_tipo, p_tipo, _, _ = chi2_contingency(tabla_tipo)

    # Prueba de chi-cuadrado para nivel educativo (Sala cuna menor, mayor, etc.)
    tabla_nivel = pd.crosstab(df['rural_estab'], df['nivel1'])
    chi2_nivel, p_nivel, _, _ = chi2_contingency(tabla_nivel)

    return render(request, 'educacion/graficos_parvulo_2020.html', {'grafico_html': grafico_genero_zona_html,
                                                        'grafico_dependencia_html': grafico_genero_dependencia_html,
                                                        'grafico_tipo_html': grafico_genero_tipo_html,
                                                        'grafico_nivel_html':grafico_genero_nivel_html,
                                                        'chi2_tipo': round(chi2_tipo, 2),
                                                        'p_tipo': round(p_tipo, 4),
                                                        'chi2_nivel': round(chi2_nivel, 2),
                                                        'p_nivel': round(p_nivel, 4),
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
        3: "Adultas/os"
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

    # Reemplazar los números con los nombres de género
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
        fig.add_trace(go.Bar(
            x=df_filtrado['Género'],
            y=df_filtrado['Porcentaje'],
            name=zona,  # Esto agrupará las barras por zona
            text=df_filtrado['Porcentaje'].apply(lambda x: f"{x:.2f}%"),  # Muestra los valores en las barras
            textposition='auto'
        ))

    # Configurar el diseño del gráfico
    fig.update_layout(
        barmode='group',  # Agrupar barras
        title="Gráfico género según zona",
        title_font= dict(weight="bold"),
        title_x=0.5,
        yaxis=dict(title="Porcentaje", tickformat=".2f", range=[0, 100]),
        xaxis_title="Género",
        bargap=0.2,  # Espaciado entre barras de diferentes grupos
        bargroupgap=0.1,  # Espaciado dentro de un grupo
        autosize= True
    )

### **Gráfico 2: Distribución género segun dependencia**

    conteo_dependencia = df.groupby(['GEN_ALU','COD_DEPE2']).size().reset_index(name='Cantidad')
    conteo_dependencia.columns = ['Género','Dependencia', 'Cantidad']

# Calcular porcentaje total
    totales_por_dependencia = conteo_dependencia.groupby('Género')['Cantidad'].transform('sum')
    conteo_dependencia['Porcentaje'] = (conteo_dependencia['Cantidad'] / totales_por_dependencia) * 100

    fig2 = go.Figure()


    for dependencia in conteo_dependencia['Dependencia'].unique():
        df_filtrado = conteo_dependencia[conteo_dependencia['Dependencia'] == dependencia]
        fig2.add_trace(go.Bar(
            x =df_filtrado['Género'],
            y = df_filtrado['Porcentaje'],
            name= dependencia, 
            text=df_filtrado['Porcentaje'].apply(lambda x: f"{x:.2f}%"),
            textposition= 'auto'
            ))

    fig2.update_layout(
        barmode='group',
        title="Gráfico género según dependencia administrativa",
        title_font= dict(weight="bold"),
        title_x=0.5,
        yaxis=dict(title="Porcentaje", tickformat=".2f", range=[0, 100]),
        xaxis_title="Género",
        bargap=0.1,
        bargroupgap=0.1,
        autosize= True,
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
        fig3.add_trace(go.Bar(
            x =df_filtrado['Género'],
            y = df_filtrado['Porcentaje'],
            name= tipo, 
            text=df_filtrado['Porcentaje'].apply(lambda x: f"{x:.2f}%"),
            textposition= 'auto'
            ))

    fig3.update_layout(
        barmode='group',
        title="Gráfico género según tipo",
        title_font= dict(weight="bold"),
        title_x=0.5,
        yaxis=dict(title="Porcentaje", tickformat=".2f", range=[0, 100]),
        xaxis_title="Género",
        bargap=0.1,
        bargroupgap=0.1,
        autosize= True,
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
        yaxis=dict(title="Porcentaje", tickformat=".2f", range=[0, 100]),
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

    # Obtener la región seleccionada desde la URL (por defecto muestra todos)
    region_seleccionada = request.GET.get('NOM_REG_RBD_A', "RM")

    datos = matricula_basica.objects.filter(AGNO=2022, GEN_ALU__in= [1, 2])
    # Obtener datos del modelo, filtrando por región si se especifica
  
    if region_seleccionada:
        datos = datos.filter(NOM_REG_RBD_A=region_seleccionada)

    datos= datos.values('GEN_ALU','RURAL_RBD','COD_DEPE2','COD_ENSE2','ENS')
    df = pd.DataFrame(datos)

    # Reemplazar los números con los nombres de género
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
        fig.add_trace(go.Bar(
            x=df_filtrado['Género'],
            y=df_filtrado['Porcentaje'],
            name=zona,  # Esto agrupará las barras por zona
            text=df_filtrado['Porcentaje'].apply(lambda x: f"{x:.2f}%"),  # Muestra los valores en las barras
            textposition='auto'
        ))

    # Configurar el diseño del gráfico
    fig.update_layout(
        barmode='group',  # Agrupar barras
        title="Gráfico género según zona",
        title_font= dict(weight="bold"),
        title_x=0.5,
        yaxis=dict(title="Porcentaje", tickformat=".2f", range=[0, 100]),
        xaxis_title="Género",
        bargap=0.2,  # Espaciado entre barras de diferentes grupos
        bargroupgap=0.1,  # Espaciado dentro de un grupo
        autosize= True
    )

### **Gráfico 2: Distribución género segun dependencia**

    conteo_dependencia = df.groupby(['GEN_ALU','COD_DEPE2']).size().reset_index(name='Cantidad')
    conteo_dependencia.columns = ['Género','Dependencia', 'Cantidad']

# Calcular porcentaje total
    totales_por_dependencia = conteo_dependencia.groupby('Género')['Cantidad'].transform('sum')
    conteo_dependencia['Porcentaje'] = (conteo_dependencia['Cantidad'] / totales_por_dependencia) * 100

    fig2 = go.Figure()


    for dependencia in conteo_dependencia['Dependencia'].unique():
        df_filtrado = conteo_dependencia[conteo_dependencia['Dependencia'] == dependencia]
        fig2.add_trace(go.Bar(
            x =df_filtrado['Género'],
            y = df_filtrado['Porcentaje'],
            name= dependencia, 
            text=df_filtrado['Porcentaje'].apply(lambda x: f"{x:.2f}%"),
            textposition= 'auto'
            ))

    fig2.update_layout(
        barmode='group',
        title="Gráfico género según dependencia administrativa",
        title_font= dict(weight="bold"),
        title_x=0.5,
        yaxis=dict(title="Porcentaje", tickformat=".2f", range=[0, 100]),
        xaxis_title="Género",
        bargap=0.1,
        bargroupgap=0.1,
        autosize= True,
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
        fig3.add_trace(go.Bar(
            x =df_filtrado['Género'],
            y = df_filtrado['Porcentaje'],
            name= tipo, 
            text=df_filtrado['Porcentaje'].apply(lambda x: f"{x:.2f}%"),
            textposition= 'auto'
            ))

    fig3.update_layout(
        barmode='group',
        title="Gráfico género según tipo",
        title_font= dict(weight="bold"),
        title_x=0.5,
        yaxis=dict(title="Porcentaje", tickformat=".2f", range=[0, 100]),
        xaxis_title="Género",
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

    # Obtener la región seleccionada desde la URL (por defecto muestra todos)
    region_seleccionada = request.GET.get('NOM_REG_RBD_A', "RM")

    datos = matricula_basica.objects.filter(AGNO=2021, GEN_ALU__in= [1, 2])
    # Obtener datos del modelo, filtrando por región si se especifica
  
    if region_seleccionada:
        datos = datos.filter(NOM_REG_RBD_A=region_seleccionada)

    datos= datos.values('GEN_ALU','RURAL_RBD','COD_DEPE2','COD_ENSE2','ENS')
    df = pd.DataFrame(datos)

    # Reemplazar los números con los nombres de género
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
        fig.add_trace(go.Bar(
            x=df_filtrado['Género'],
            y=df_filtrado['Porcentaje'],
            name=zona,  # Esto agrupará las barras por zona
            text=df_filtrado['Porcentaje'].apply(lambda x: f"{x:.2f}%"),  # Muestra los valores en las barras
            textposition='auto'
        ))

    # Configurar el diseño del gráfico
    fig.update_layout(
        barmode='group',  # Agrupar barras
        title="Gráfico género según zona",
        title_font= dict(weight="bold"),
        title_x=0.5,
        yaxis=dict(title="Porcentaje", tickformat=".2f", range=[0, 100]),
        xaxis_title="Género",
        bargap=0.2,  # Espaciado entre barras de diferentes grupos
        bargroupgap=0.1,  # Espaciado dentro de un grupo
        autosize= True
    )

### **Gráfico 2: Distribución género segun dependencia**

    conteo_dependencia = df.groupby(['GEN_ALU','COD_DEPE2']).size().reset_index(name='Cantidad')
    conteo_dependencia.columns = ['Género','Dependencia', 'Cantidad']

# Calcular porcentaje total
    totales_por_dependencia = conteo_dependencia.groupby('Género')['Cantidad'].transform('sum')
    conteo_dependencia['Porcentaje'] = (conteo_dependencia['Cantidad'] / totales_por_dependencia) * 100

    fig2 = go.Figure()


    for dependencia in conteo_dependencia['Dependencia'].unique():
        df_filtrado = conteo_dependencia[conteo_dependencia['Dependencia'] == dependencia]
        fig2.add_trace(go.Bar(
            x =df_filtrado['Género'],
            y = df_filtrado['Porcentaje'],
            name= dependencia, 
            text=df_filtrado['Porcentaje'].apply(lambda x: f"{x:.2f}%"),
            textposition= 'auto'
            ))

    fig2.update_layout(
        barmode='group',
        title="Gráfico género según dependencia administrativa",
        title_font= dict(weight="bold"),
        title_x=0.5,
        yaxis=dict(title="Porcentaje", tickformat=".2f", range=[0, 100]),
        xaxis_title="Género",
        bargap=0.1,
        bargroupgap=0.1,
        autosize= True,
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
        fig3.add_trace(go.Bar(
            x =df_filtrado['Género'],
            y = df_filtrado['Porcentaje'],
            name= tipo, 
            text=df_filtrado['Porcentaje'].apply(lambda x: f"{x:.2f}%"),
            textposition= 'auto'
            ))

    fig3.update_layout(
        barmode='group',
        title="Gráfico género según tipo",
        title_font= dict(weight="bold"),
        title_x=0.5,
        yaxis=dict(title="Porcentaje", tickformat=".2f", range=[0, 100]),
        xaxis_title="Género",
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

    # Reemplazar los números con los nombres de género
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
        fig.add_trace(go.Bar(
            x=df_filtrado['Género'],
            y=df_filtrado['Porcentaje'],
            name=zona,  # Esto agrupará las barras por zona
            text=df_filtrado['Porcentaje'].apply(lambda x: f"{x:.2f}%"),  # Muestra los valores en las barras
            textposition='auto',
        ))

    # Configurar el diseño del gráfico
    fig.update_layout(
        barmode='group',  # Agrupar barras
        title="Gráfico género según zona",
        title_font= dict(weight="bold"),
        title_x=0.5,
        yaxis=dict(title="Porcentaje", tickformat=".2f", range=[0, 100]),
        xaxis_title="Género",
        bargap=0.2,  # Espaciado entre barras de diferentes grupos
        bargroupgap=0.1,  # Espaciado dentro de un grupo
        autosize= True
    )

### **Gráfico 2: Distribución género segun dependencia**

    conteo_dependencia = df.groupby(['GEN_ALU','COD_DEPE2']).size().reset_index(name='Cantidad')
    conteo_dependencia.columns = ['Género','Dependencia', 'Cantidad']

# Calcular porcentaje total
    totales_por_dependencia = conteo_dependencia.groupby('Género')['Cantidad'].transform('sum')
    conteo_dependencia['Porcentaje'] = (conteo_dependencia['Cantidad'] / totales_por_dependencia) * 100

    fig2 = go.Figure()


    for dependencia in conteo_dependencia['Dependencia'].unique():
        df_filtrado = conteo_dependencia[conteo_dependencia['Dependencia'] == dependencia]
        fig2.add_trace(go.Bar(
            x =df_filtrado['Género'],
            y = df_filtrado['Porcentaje'],
            name= dependencia, 
            text=df_filtrado['Porcentaje'].apply(lambda x: f"{x:.2f}%"),
            textposition= 'auto'
            ))

    fig2.update_layout(
        barmode='group',
        title="Gráfico género según dependencia administrativa",
        title_font= dict(weight="bold"),
        title_x=0.5,
        yaxis=dict(title="Porcentaje", tickformat=".2f", range=[0, 100]),
        xaxis_title="Género",
        bargap=0.1,
        bargroupgap=0.1,
        autosize= True,
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
        fig3.add_trace(go.Bar(
            x =df_filtrado['Género'],
            y = df_filtrado['Porcentaje'],
            name= tipo, 
            text=df_filtrado['Porcentaje'].apply(lambda x: f"{x:.2f}%"),
            textposition= 'auto'
            ))

    fig3.update_layout(
        barmode='group',
        title="Gráfico género según tipo",
        title_font= dict(weight="bold"),
        title_x=0.5,
        yaxis=dict(title="Porcentaje", tickformat=".2f", range=[0, 100]),
        xaxis_title="Género",
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

    # Obtener la región seleccionada desde la URL (por defecto muestra todos)
    region_seleccionada = request.GET.get('NOM_REG_RBD_A', "RM")

    datos = matricula_media.objects.filter(AGNO=2023, GEN_ALU__in= [1, 2])
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


# Crear la figura manualmente
    fig = go.Figure()

    for zona in conteo['Zona'].unique():
        df_filtrado = conteo[conteo['Zona'] == zona]
        fig.add_trace(go.Bar(
            x=df_filtrado['Género'],
            y=df_filtrado['Porcentaje'],
            name=zona,  # Esto agrupará las barras por zona
            text=df_filtrado['Porcentaje'].apply(lambda x: f"{x:.2f}%"),  # Muestra los valores en las barras
            textposition='auto'
        ))

    # Configurar el diseño del gráfico
    fig.update_layout(
        barmode='group',  # Agrupar barras
        title="Gráfico género según zona",
        title_font= dict(weight="bold"),
        title_x=0.5,
        yaxis=dict(title="Porcentaje", tickformat=".2f", range=[0, 100]),
        xaxis_title="Género",
        bargap=0.2,  # Espaciado entre barras de diferentes grupos
        bargroupgap=0.1,  # Espaciado dentro de un grupo
        autosize= True
    )

### Gráfico 2: Distribución género segun dependencia

    conteo_dependencia = df.groupby(['GEN_ALU','COD_DEPE2']).size().reset_index(name='Cantidad')
    conteo_dependencia.columns = ['Género','Dependencia', 'Cantidad']

# Calcular porcentaje total
    totales_por_dependencia = conteo_dependencia.groupby('Género')['Cantidad'].transform('sum')
    conteo_dependencia['Porcentaje'] = (conteo_dependencia['Cantidad'] / totales_por_dependencia) * 100

    fig2 = go.Figure()


    for dependencia in conteo_dependencia['Dependencia'].unique():
        df_filtrado = conteo_dependencia[conteo_dependencia['Dependencia'] == dependencia]
        fig2.add_trace(go.Bar(
            x =df_filtrado['Género'],
            y = df_filtrado['Porcentaje'],
            name= dependencia, 
            text=df_filtrado['Porcentaje'].apply(lambda x: f"{x:.2f}%"),
            textposition= 'auto'
            ))

    fig2.update_layout(
        barmode='group',
        title="Gráfico género según dependencia administrativa",
        title_font= dict(weight="bold"),
        title_x=0.5,
        yaxis=dict(title="Porcentaje", tickformat=".2f", range=[0, 100]),
        xaxis_title="Género",
        bargap=0.1,
        bargroupgap=0.1,
        autosize= True,
    )

### Gráfico 3: Distribución género segun tipo de enseñanza

    conteo_tipo = df.groupby(['RURAL_RBD','COD_ENSE2']).size().reset_index(name='Cantidad')
    conteo_tipo.columns = ['Zona','Tipo', 'Cantidad']

# Calcular porcentaje total
    totales_por_tipo = conteo_tipo.groupby('Zona')['Cantidad'].transform('sum')
    conteo_tipo['Porcentaje'] = (conteo_tipo['Cantidad'] / totales_por_tipo) * 100

# Ordenar según valor ortiginal de la categoría
    conteo_tipo = conteo_tipo.sort_values(by='Tipo', key=lambda x: x.map({v: k for k, v in tipo_enseñanza.items()}))


    fig3 = go.Figure()


    for tipo in conteo_tipo['Tipo'].unique():
        df_filtrado = conteo_tipo[conteo_tipo['Tipo'] == tipo]
        fig3.add_trace(go.Bar(
            x =df_filtrado['Zona'],
            y = df_filtrado['Porcentaje'],
            name= tipo, 
            text=df_filtrado['Porcentaje'].apply(lambda x: f"{x:.2f}%"),
            textposition= 'auto'
            ))

    fig3.update_layout(
        barmode='group',
        title="Gráfico género según tipo",
        title_font= dict(weight="bold"),
        title_x=0.5,
        yaxis=dict(title="Porcentaje", tickformat=".2f", range=[0, 100]),
        xaxis_title="Zona",
        bargap=0.1,
        bargroupgap=0.1,
        autosize= True,
    )

    grafico_genero_zona_html = fig.to_html()
    grafico_genero_dependencia_html = fig2.to_html()
    grafico_zona_tipo_html = fig3.to_html()

    # Prueba de chi-cuadrado para tipo de enseñanza (Ed. Parvularia vs. Ed. Especial)
    tabla_tipo = pd.crosstab(df['RURAL_RBD'], df['COD_ENSE2'])
    chi2_tipo, p_tipo, _, _ = chi2_contingency(tabla_tipo)

    return render(request, 'educacion/graficos_media_2023.html', {'grafico_html': grafico_genero_zona_html,
                                                      'grafico_dependencia_html': grafico_genero_dependencia_html,
                                                      'grafico_tipo_html': grafico_zona_tipo_html,
                                                      'chi2_tipo':round(chi2_tipo,2),
                                                      'p_tipo': round(p_tipo,4),
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

    # Obtener la región seleccionada desde la URL (por defecto muestra todos)
    region_seleccionada = request.GET.get('NOM_REG_RBD_A', "RM")

    datos = matricula_media.objects.filter(AGNO=2022, GEN_ALU__in= [1, 2])
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


# Crear la figura manualmente
    fig = go.Figure()

    for zona in conteo['Zona'].unique():
        df_filtrado = conteo[conteo['Zona'] == zona]
        fig.add_trace(go.Bar(
            x=df_filtrado['Género'],
            y=df_filtrado['Porcentaje'],
            name=zona,  # Esto agrupará las barras por zona
            text=df_filtrado['Porcentaje'].apply(lambda x: f"{x:.2f}%"),  # Muestra los valores en las barras
            textposition='auto'
        ))

    # Configurar el diseño del gráfico
    fig.update_layout(
        barmode='group',  # Agrupar barras
        title="Gráfico género según zona",
        title_font= dict(weight="bold"),
        title_x=0.5,
        yaxis=dict(title="Porcentaje", tickformat=".2f", range=[0, 100]),
        xaxis_title="Género",
        bargap=0.2,  # Espaciado entre barras de diferentes grupos
        bargroupgap=0.1,  # Espaciado dentro de un grupo
        autosize= True
    )

### Gráfico 2: Distribución género segun dependencia

    conteo_dependencia = df.groupby(['GEN_ALU','COD_DEPE2']).size().reset_index(name='Cantidad')
    conteo_dependencia.columns = ['Género','Dependencia', 'Cantidad']

# Calcular porcentaje total
    totales_por_dependencia = conteo_dependencia.groupby('Género')['Cantidad'].transform('sum')
    conteo_dependencia['Porcentaje'] = (conteo_dependencia['Cantidad'] / totales_por_dependencia) * 100

    fig2 = go.Figure()


    for dependencia in conteo_dependencia['Dependencia'].unique():
        df_filtrado = conteo_dependencia[conteo_dependencia['Dependencia'] == dependencia]
        fig2.add_trace(go.Bar(
            x =df_filtrado['Género'],
            y = df_filtrado['Porcentaje'],
            name= dependencia, 
            text=df_filtrado['Porcentaje'].apply(lambda x: f"{x:.2f}%"),
            textposition= 'auto'
            ))

    fig2.update_layout(
        barmode='group',
        title="Gráfico género según dependencia administrativa",
        title_font= dict(weight="bold"),
        title_x=0.5,
        yaxis=dict(title="Porcentaje", tickformat=".2f", range=[0, 100]),
        xaxis_title="Género",
        bargap=0.1,
        bargroupgap=0.1,
        autosize= True,
    )

### Gráfico 3: Distribución género segun tipo de enseñanza

    conteo_tipo = df.groupby(['RURAL_RBD','COD_ENSE2']).size().reset_index(name='Cantidad')
    conteo_tipo.columns = ['Zona','Tipo', 'Cantidad']

# Calcular porcentaje total
    totales_por_tipo = conteo_tipo.groupby('Zona')['Cantidad'].transform('sum')
    conteo_tipo['Porcentaje'] = (conteo_tipo['Cantidad'] / totales_por_tipo) * 100
# Ordenar según valor ortiginal de la categoría
    conteo_tipo = conteo_tipo.sort_values(by='Tipo', key=lambda x: x.map({v: k for k, v in tipo_enseñanza.items()}))

    fig3 = go.Figure()


    for tipo in conteo_tipo['Tipo'].unique():
        df_filtrado = conteo_tipo[conteo_tipo['Tipo'] == tipo]
        fig3.add_trace(go.Bar(
            x =df_filtrado['Zona'],
            y = df_filtrado['Porcentaje'],
            name= tipo, 
            text=df_filtrado['Porcentaje'].apply(lambda x: f"{x:.2f}%"),
            textposition= 'auto'
            ))

    fig3.update_layout(
        barmode='group',
        title="Gráfico género según tipo",
        title_font= dict(weight="bold"),
        title_x=0.5,
        yaxis=dict(title="Porcentaje", tickformat=".2f", range=[0, 100]),
        xaxis_title="Zona",
        bargap=0.1,
        bargroupgap=0.1,
        autosize= True,
    )

    grafico_genero_zona_html = fig.to_html()
    grafico_genero_dependencia_html = fig2.to_html()
    grafico_zona_tipo_html = fig3.to_html()

    # Prueba de chi-cuadrado para tipo de enseñanza (Ed. Parvularia vs. Ed. Especial)
    tabla_tipo = pd.crosstab(df['RURAL_RBD'], df['COD_ENSE2'])
    chi2_tipo, p_tipo, _, _ = chi2_contingency(tabla_tipo)

    return render(request, 'educacion/graficos_media_2022.html', {'grafico_html': grafico_genero_zona_html,
                                                      'grafico_dependencia_html': grafico_genero_dependencia_html,
                                                      'grafico_tipo_html': grafico_zona_tipo_html,
                                                      'chi2_tipo':round(chi2_tipo,4),
                                                      'p_tipo': round(p_tipo,4),
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

    # Obtener la región seleccionada desde la URL (por defecto muestra todos)
    region_seleccionada = request.GET.get('NOM_REG_RBD_A', "RM")

    datos = matricula_media.objects.filter(AGNO=2021, GEN_ALU__in= [1, 2])
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


# Crear la figura manualmente
    fig = go.Figure()

    for zona in conteo['Zona'].unique():
        df_filtrado = conteo[conteo['Zona'] == zona]
        fig.add_trace(go.Bar(
            x=df_filtrado['Género'],
            y=df_filtrado['Porcentaje'],
            name=zona,  # Esto agrupará las barras por zona
            text=df_filtrado['Porcentaje'].apply(lambda x: f"{x:.2f}%"),  # Muestra los valores en las barras
            textposition='auto'
        ))

    # Configurar el diseño del gráfico
    fig.update_layout(
        barmode='group',  # Agrupar barras
        title="Gráfico género según zona",
        title_font= dict(weight="bold"),
        title_x=0.5,
        yaxis=dict(title="Porcentaje", tickformat=".2f", range=[0, 100]),
        xaxis_title="Género",
        bargap=0.2,  # Espaciado entre barras de diferentes grupos
        bargroupgap=0.1,  # Espaciado dentro de un grupo
        autosize= True
    )

### **Gráfico 2: Distribución género segun dependencia

    conteo_dependencia = df.groupby(['GEN_ALU','COD_DEPE2']).size().reset_index(name='Cantidad')
    conteo_dependencia.columns = ['Género','Dependencia', 'Cantidad']

# Calcular porcentaje total
    totales_por_dependencia = conteo_dependencia.groupby('Género')['Cantidad'].transform('sum')
    conteo_dependencia['Porcentaje'] = (conteo_dependencia['Cantidad'] / totales_por_dependencia) * 100

    fig2 = go.Figure()


    for dependencia in conteo_dependencia['Dependencia'].unique():
        df_filtrado = conteo_dependencia[conteo_dependencia['Dependencia'] == dependencia]
        fig2.add_trace(go.Bar(
            x =df_filtrado['Género'],
            y = df_filtrado['Porcentaje'],
            name= dependencia, 
            text=df_filtrado['Porcentaje'].apply(lambda x: f"{x:.2f}%"),
            textposition= 'auto'
            ))

    fig2.update_layout(
        barmode='group',
        title="Gráfico género según dependencia administrativa",
        title_font= dict(weight="bold"),
        title_x=0.5,
        yaxis=dict(title="Porcentaje", tickformat=".2f", range=[0, 100]),
        xaxis_title="Género",
        bargap=0.1,
        bargroupgap=0.1,
        autosize= True,
    )

### **Gráfico 3: Distribución género segun tipo de enseñanza

    conteo_tipo = df.groupby(['RURAL_RBD','COD_ENSE2']).size().reset_index(name='Cantidad')
    conteo_tipo.columns = ['Zona','Tipo', 'Cantidad']

# Calcular porcentaje total
    totales_por_tipo = conteo_tipo.groupby('Zona')['Cantidad'].transform('sum')
    conteo_tipo['Porcentaje'] = (conteo_tipo['Cantidad'] / totales_por_tipo) * 100
# Ordenar según valor ortiginal de la categoría
    conteo_tipo = conteo_tipo.sort_values(by='Tipo', key=lambda x: x.map({v: k for k, v in tipo_enseñanza.items()}))

    fig3 = go.Figure()


    for tipo in conteo_tipo['Tipo'].unique():
        df_filtrado = conteo_tipo[conteo_tipo['Tipo'] == tipo]
        fig3.add_trace(go.Bar(
            x =df_filtrado['Zona'],
            y = df_filtrado['Porcentaje'],
            name= tipo, 
            text=df_filtrado['Porcentaje'].apply(lambda x: f"{x:.2f}%"),
            textposition= 'auto'
            ))

    fig3.update_layout(
        barmode='group',
        title="Gráfico zona según tipo",
        title_font= dict(weight="bold"),
        title_x=0.5,
        yaxis=dict(title="Porcentaje", tickformat=".2f", range=[0, 100]),
        xaxis_title="Zona",
        bargap=0.1,
        bargroupgap=0.1,
        autosize= True,
    )

    grafico_genero_zona_html = fig.to_html()
    grafico_genero_dependencia_html = fig2.to_html()
    grafico_zona_tipo_html = fig3.to_html()

    # Prueba de chi-cuadrado para tipo de enseñanza (Ed. Parvularia vs. Ed. Especial)
    tabla_tipo = pd.crosstab(df['RURAL_RBD'], df['COD_ENSE2'])
    chi2_tipo, p_tipo, _, _ = chi2_contingency(tabla_tipo)

    return render(request, 'educacion/graficos_media_2021.html', {'grafico_html': grafico_genero_zona_html,
                                                      'grafico_dependencia_html': grafico_genero_dependencia_html,
                                                      'grafico_tipo_html': grafico_zona_tipo_html,
                                                      'chi2_tipo':round(chi2_tipo,2),
                                                      'p_tipo':round(p_tipo,4),
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

    # Obtener la región seleccionada desde la URL (por defecto muestra todos)
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


# Crear la figura manualmente
    fig = go.Figure()

    for zona in conteo['Zona'].unique():
        df_filtrado = conteo[conteo['Zona'] == zona]
        fig.add_trace(go.Bar(
            x=df_filtrado['Género'],
            y=df_filtrado['Porcentaje'],
            name=zona,  # Esto agrupará las barras por zona
            text=df_filtrado['Porcentaje'].apply(lambda x: f"{x:.2f}%"),  # Muestra los valores en las barras
            textposition='auto'
        ))

    # Configurar el diseño del gráfico
    fig.update_layout(
        barmode='group',  # Agrupar barras
        title="Gráfico género según zona",
        title_font= dict(weight="bold"),
        title_x=0.5,
        yaxis=dict(title="Porcentaje", tickformat=".2f", range=[0, 100]),
        xaxis_title="Género",
        bargap=0.2,  # Espaciado entre barras de diferentes grupos
        bargroupgap=0.1,  # Espaciado dentro de un grupo
        autosize= True
    )

### **Gráfico 2: Distribución género segun dependencia

    conteo_dependencia = df.groupby(['GEN_ALU','COD_DEPE2']).size().reset_index(name='Cantidad')
    conteo_dependencia.columns = ['Género','Dependencia', 'Cantidad']

# Calcular porcentaje total
    totales_por_dependencia = conteo_dependencia.groupby('Género')['Cantidad'].transform('sum')
    conteo_dependencia['Porcentaje'] = (conteo_dependencia['Cantidad'] / totales_por_dependencia) * 100

    fig2 = go.Figure()


    for dependencia in conteo_dependencia['Dependencia'].unique():
        df_filtrado = conteo_dependencia[conteo_dependencia['Dependencia'] == dependencia]
        fig2.add_trace(go.Bar(
            x =df_filtrado['Género'],
            y = df_filtrado['Porcentaje'],
            name= dependencia, 
            text=df_filtrado['Porcentaje'].apply(lambda x: f"{x:.2f}%"),
            textposition= 'auto'
            ))

    fig2.update_layout(
        barmode='group',
        title="Gráfico género según dependencia administrativa",
        title_font= dict(weight="bold"),
        title_x=0.5,
        yaxis=dict(title="Porcentaje", tickformat=".2f", range=[0, 100]),
        xaxis_title="Género",
        bargap=0.1,
        bargroupgap=0.1,
        autosize= True,
    )

### **Gráfico 3: Distribución zona segun tipo de enseñanza

    conteo_tipo = df.groupby(['RURAL_RBD','COD_ENSE2']).size().reset_index(name='Cantidad')
    conteo_tipo.columns = ['Zona','Tipo', 'Cantidad']

# Calcular porcentaje total
    totales_por_tipo = conteo_tipo.groupby('Zona')['Cantidad'].transform('sum')
    conteo_tipo['Porcentaje'] = (conteo_tipo['Cantidad'] / totales_por_tipo) * 100
# Ordenar según valor ortiginal de la categoría
    conteo_tipo = conteo_tipo.sort_values(by='Tipo', key=lambda x: x.map({v: k for k, v in tipo_enseñanza.items()}))

    fig3 = go.Figure()


    for tipo in conteo_tipo['Tipo'].unique():
        df_filtrado = conteo_tipo[conteo_tipo['Tipo'] == tipo]
        fig3.add_trace(go.Bar(
            x =df_filtrado['Zona'],
            y = df_filtrado['Porcentaje'],
            name= tipo, 
            text=df_filtrado['Porcentaje'].apply(lambda x: f"{x:.2f}%"),
            textposition= 'auto'
            ))

    fig3.update_layout(
        barmode='group',
        title="Gráfico género según tipo",
        title_font= dict(weight="bold"),
        title_x=0.5,
        yaxis=dict(title="Porcentaje", tickformat=".2f", range=[0, 100]),
        xaxis_title="Zona",
        bargap=0.1,
        bargroupgap=0.1,
        autosize= True,
    )

    grafico_genero_zona_html = fig.to_html()
    grafico_genero_dependencia_html = fig2.to_html()
    grafico_zona_tipo_html = fig3.to_html()

    # Prueba de chi-cuadrado para tipo de enseñanza (Ed. Parvularia vs. Ed. Especial)
    tabla_tipo = pd.crosstab(df['RURAL_RBD'], df['COD_ENSE2'])
    chi2_tipo, p_tipo, _, _ = chi2_contingency(tabla_tipo)

    return render(request, 'educacion/graficos_media_2020.html', {'grafico_html': grafico_genero_zona_html,
                                                      'grafico_dependencia_html': grafico_genero_dependencia_html,
                                                      'grafico_tipo_html': grafico_zona_tipo_html,
                                                      'chi2_tipo': round(chi2_tipo,2),
                                                      'p_tipo': round(p_tipo,4),
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

    # Obtener la región seleccionada desde la URL (por defecto muestra todos)
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

    # Configurar el layout
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

    # Obtener la región seleccionada desde la URL (por defecto muestra todos)
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

    # Configurar el layout
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
    

    # Obtener la región seleccionada desde la URL (por defecto muestra todos)
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

    # Configurar el diseño del gráfico
    fig.update_layout(
        title="Promedio por Región según Tipo de Indicador",
        xaxis_title="Región",
        yaxis_title="Promedio",
        barmode='group',
        template="plotly_white"
    )

    # Gráfico 2 comparacion de resultados segun zona 

    df_zona = df.groupby(['nom_reg_rbd', 'ind', 'cod_rural_rbd'])['prom'].mean().reset_index()

    # Crear la figura con Plotly
    fig2 = go.Figure()

    # Iterar por cada zona (Rural y Urbano) primero
    for ruralidad in df_zona['cod_rural_rbd'].unique():
        df_filtrado = df_zona[df_zona['cod_rural_rbd'] == ruralidad]

        fig2.add_trace(go.Bar(
            x=df_filtrado['ind'],  # Agrupar por Indicador
            y=df_filtrado['prom'],
            name=zona[ruralidad],  # La etiqueta solo será "Rural" o "Urbano"
            text=df_filtrado['prom'].apply(lambda x: f"{x:.2f}"),
            textposition='inside',
            marker_color='#EF553B' if ruralidad == 1 else '#636EFA'
        ))

    # Configurar el diseño del gráfico
        fig2.update_layout(
        title="Comparación de Indicadores por Zona",
        xaxis_title="Indicador",
        yaxis_title="Promedio",
        barmode='group',  # Agrupar por Indicador
        template="plotly_white"
    )
        
     # Gráfico 3 comparando resultados según dependencia
    df_depe = df.groupby(['nom_reg_rbd', 'ind', 'cod_depe2'])['prom'].mean().reset_index()

    # Crear la figura para el gráfico de comparación por zona
    fig3= go.Figure()

    # Iterar por cada dependencia
    for dependencia in df_depe['cod_depe2'].unique():
        df_filtrado = df_depe[df_depe['cod_depe2'] == dependencia]

        fig3.add_trace(go.Bar(
            x=df_filtrado['ind'],  # Agrupar por Indicador
            y=df_filtrado['prom'],
            name=dependencia_cat[dependencia],  
            text=df_filtrado['prom'].apply(lambda x: f"{x:.2f}"),
            textposition='inside'
        ))

    # Configurar el diseño del gráfico
        fig3.update_layout(
        title="Comparación de Indicadores por Dependencia",
        xaxis_title="Indicador",
        yaxis_title="Promedio",
        barmode='group',  # Agrupar por Indicador
        template="plotly_white"
    )
    
        # Gráfico 4 comparando resultados según provincia 
    df_pro = df.groupby(['nom_reg_rbd', 'ind', 'nom_pro_rbd'])['prom'].mean().reset_index()

    # Crear la figura para el gráfico de comparación por provincia
    fig4= go.Figure()

    # Iterar por cada provincia
    for provincia in df_pro['nom_pro_rbd'].unique():
        df_filtrado = df_pro[df_pro['nom_pro_rbd'] == provincia]

        fig4.add_trace(go.Bar(
            x=df_filtrado['ind'],  # Agrupar por Indicador
            y=df_filtrado['prom'],
            name=provincia,  
            text=df_filtrado['prom'].apply(lambda x: f"{x:.2f}"),
            textposition='inside'
        ))

    # Configurar el diseño del gráfico
        fig4.update_layout(
        title="Comparación de Indicadores por Provincia",
        xaxis_title="Indicador",
        yaxis_title="Promedio",
        barmode='group',  # Agrupar por Indicador
        template="plotly_white"
    )

    grafico_html =fig.to_html()
    grafico_zona =fig2.to_html()
    grafico_dependencia =fig3.to_html()
    grafico_provincia =fig4.to_html()

    # Prueba de chi-cuadrado para zona (Rural/Urbano)
    tabla_zona = df.pivot_table(index='ind', columns='cod_rural_rbd', values='prom', aggfunc='mean').fillna(0)
    chi2_zona, p_zona, _, _ = chi2_contingency(tabla_zona)

    # Prueba de chi-cuadrado para dependencia
    tabla_depe = df.pivot_table(index='ind', columns='cod_depe2', values='prom', aggfunc='mean').fillna(0)
    chi2_depe, p_depe, _, _ = chi2_contingency(tabla_depe)

    # Prueba de chi-cuadrado para provincia
    tabla_pro = df.pivot_table(index='ind', columns='nom_pro_rbd', values='prom', aggfunc='mean').fillna(0)
    chi2_pro, p_pro, _, _ = chi2_contingency(tabla_pro)

    return render(request, 'educacion/graficos_idps22_4.html', {'grafico_html': grafico_html,
                                                                'grafico_zona': grafico_zona,
                                                                'grafico_dependencia':grafico_dependencia,
                                                                'grafico_provincia':grafico_provincia,
                                                                'nom_reg_rbd': region_seleccionada,
                                                                'chi2_zona': round(chi2_zona,2),
                                                                'chi2_depe':round(chi2_depe,2),
                                                                'chi2_pro':round(chi2_pro,2),
                                                                'p_zona':round(p_zona,4),
                                                                'p_depe':round(p_depe,4),
                                                                'p_pro':round(p_pro,4)})
                
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

    # Obtener la región seleccionada desde la URL (por defecto muestra todos)
    region_seleccionada = request.GET.get('nom_reg_rbd', "METROPOLITANA DE SANTIAGO")

    # Filtrar los datos por grado y año
    datos = resultados_simce_idps.objects.filter(grado='2', agno=2022)
    
    # Filtrar por región si es necesario
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

    # Configurar el diseño del gráfico por región
    fig.update_layout(
        title="Promedio por Región según Tipo de Indicador",
        xaxis_title="Región",
        yaxis_title="Promedio",
        barmode='group',
        template="plotly_white"
    )

    # Gráfico 2 comparando resultados según zona 
    df_zona = df.groupby(['nom_reg_rbd', 'ind', 'cod_rural_rbd'])['prom'].mean().reset_index()

    # Crear la figura para el gráfico de comparación por zona
    fig2 = go.Figure()

    # Iterar por cada zona (Rural y Urbano) primero
    for ruralidad in df_zona['cod_rural_rbd'].unique():
        df_filtrado = df_zona[df_zona['cod_rural_rbd'] == ruralidad]

        fig2.add_trace(go.Bar(
            x=df_filtrado['ind'],  # Agrupar por Indicador
            y=df_filtrado['prom'],
            name=zona[ruralidad],  # La etiqueta solo será "Rural" o "Urbano"
            text=df_filtrado['prom'].apply(lambda x: f"{x:.2f}"),
            textposition='inside',
            marker_color='#EF553B' if ruralidad == 1 else '#636EFA'
        ))

    # Configurar el diseño del gráfico
        fig2.update_layout(
        title="Comparación de Indicadores por Zona",
        xaxis_title="Indicador",
        yaxis_title="Promedio",
        barmode='group',  # Agrupar por Indicador
        template="plotly_white"
    )
        
     # Gráfico 3 comparando resultados según dependencia 
    df_depe = df.groupby(['nom_reg_rbd', 'ind', 'cod_depe2'])['prom'].mean().reset_index()

    # Crear la figura para el gráfico de comparación por dependencia
    fig3= go.Figure()

    # Iterar por cada dependencia
    for dependencia in df_depe['cod_depe2'].unique():
        df_filtrado = df_depe[df_depe['cod_depe2'] == dependencia]

        fig3.add_trace(go.Bar(
            x=df_filtrado['ind'],  # Agrupar por Indicador
            y=df_filtrado['prom'],
            name=dependencia_cat[dependencia], 
            text=df_filtrado['prom'].apply(lambda x: f"{x:.2f}"),
            textposition='inside'
        ))

    # Configurar el diseño del gráfico
        fig3.update_layout(
        title="Comparación de Indicadores por Dependencia",
        xaxis_title="Indicador",
        yaxis_title="Promedio",
        barmode='group',  # Agrupar por Indicador
        template="plotly_white"
    )
        
        
    # Gráfico 4 comparando resultados según provincia 
    df_pro = df.groupby(['nom_reg_rbd', 'ind', 'nom_pro_rbd'])['prom'].mean().reset_index()

    # Crear la figura para el gráfico de comparación por provincia
    fig4= go.Figure()

    # Iterar por cada provincia
    for provincia in df_pro['nom_pro_rbd'].unique():
        df_filtrado = df_pro[df_pro['nom_pro_rbd'] == provincia]

        fig4.add_trace(go.Bar(
            x=df_filtrado['ind'],  # Agrupar por Indicador
            y=df_filtrado['prom'],
            name=provincia,  
            text=df_filtrado['prom'].apply(lambda x: f"{x:.2f}"),
            textposition='inside'
        ))

    # Configurar el diseño del gráfico
        fig4.update_layout(
        title="Comparación de Indicadores por Provincia",
        xaxis_title="Indicador",
        yaxis_title="Promedio",
        barmode='group',  # Agrupar por Indicador
        template="plotly_white"
    )
        

        
    # Convertir ambos gráficos a HTML
    grafico_html = fig.to_html()
    grafico_zona = fig2.to_html()
    grafico_dependencia = fig3.to_html()
    grafico_provincia = fig4.to_html()

    # Prueba de chi-cuadrado para zona (Rural/Urbano)
    tabla_zona = df.pivot_table(index='ind', columns='cod_rural_rbd', values='prom', aggfunc='mean').fillna(0)
    chi2_zona, p_zona, _, _ = chi2_contingency(tabla_zona)

    # Prueba de chi-cuadrado para dependencia
    tabla_depe = df.pivot_table(index='ind', columns='cod_depe2', values='prom', aggfunc='mean').fillna(0)
    chi2_depe, p_depe, _, _ = chi2_contingency(tabla_depe)

    return render(request, 'educacion/graficos_idps22_2.html', {
        'grafico_html': grafico_html,
        'grafico_zona': grafico_zona,
        'grafico_dependencia':grafico_dependencia,
        'grafico_provincia':grafico_provincia,
        'nom_reg_rbd': region_seleccionada,
        'chi2_zona': round(chi2_zona, 2),
        'p_zona': round(p_zona, 4),
        'chi2_depe': round(chi2_depe, 2),
        'p_depe': round(p_depe, 4),
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
        barmode='group',
        template="plotly_white"
    )

    # Gráfico 2 comparacion de resultados segun zona 

    df_zona = df.groupby(['nom_reg_rbd', 'ind', 'cod_rural_rbd'])['prom'].mean().reset_index()

    # Crear la figura con Plotly
    fig2 = go.Figure()

    # Iterar por cada zona (Rural y Urbano) primero
    for ruralidad in df_zona['cod_rural_rbd'].unique():
        df_filtrado = df_zona[df_zona['cod_rural_rbd'] == ruralidad]

        fig2.add_trace(go.Bar(
            x=df_filtrado['ind'],  # Agrupar por Indicador
            y=df_filtrado['prom'],
            name=zona[ruralidad],  # La etiqueta solo será "Rural" o "Urbano"
            text=df_filtrado['prom'].apply(lambda x: f"{x:.2f}"),
            textposition='inside',
            marker_color='#EF553B' if ruralidad == 1 else '#636EFA'
        ))

    # Configurar el diseño del gráfico
        fig2.update_layout(
        title="Comparación de Indicadores por Zona",
        xaxis_title="Indicador",
        yaxis_title="Promedio",
        barmode='group',  # Agrupar por Indicador
        template="plotly_white"
    )
        
     # Gráfico 3 comparando resultados según dependencia
    df_depe = df.groupby(['nom_reg_rbd', 'ind', 'cod_depe2'])['prom'].mean().reset_index()

    # Crear la figura para el gráfico de comparación por zona
    fig3= go.Figure()

    # Iterar por cada dependencia
    for dependencia in df_depe['cod_depe2'].unique():
        df_filtrado = df_depe[df_depe['cod_depe2'] == dependencia]

        fig3.add_trace(go.Bar(
            x=df_filtrado['ind'],  # Agrupar por Indicador
            y=df_filtrado['prom'],
            name=dependencia_cat[dependencia],  
            text=df_filtrado['prom'].apply(lambda x: f"{x:.2f}"),
            textposition='inside'
        ))

    # Configurar el diseño del gráfico
        fig3.update_layout(
        title="Comparación de Indicadores por Dependencia",
        xaxis_title="Indicador",
        yaxis_title="Promedio",
        barmode='group',  # Agrupar por Indicador
        template="plotly_white"
    )
    
        # Gráfico 4 comparando resultados según provincia 
    df_pro = df.groupby(['nom_reg_rbd', 'ind', 'nom_pro_rbd'])['prom'].mean().reset_index()

    # Crear la figura para el gráfico de comparación por provincia
    fig4= go.Figure()

    # Iterar por cada provincia
    for provincia in df_pro['nom_pro_rbd'].unique():
        df_filtrado = df_pro[df_pro['nom_pro_rbd'] == provincia]

        fig4.add_trace(go.Bar(
            x=df_filtrado['ind'],  # Agrupar por Indicador
            y=df_filtrado['prom'],
            name=provincia,  
            text=df_filtrado['prom'].apply(lambda x: f"{x:.2f}"),
            textposition='inside'
        ))

    # Configurar el diseño del gráfico
        fig4.update_layout(
        title="Comparación de Indicadores por Provincia",
        xaxis_title="Indicador",
        yaxis_title="Promedio",
        barmode='group',  # Agrupar por Indicador
        template="plotly_white"
    )

    grafico_html =fig.to_html()
    grafico_zona =fig2.to_html()
    grafico_dependencia =fig3.to_html()
    grafico_provincia =fig4.to_html()

    # Prueba de chi-cuadrado para zona (Rural/Urbano)
    tabla_zona = df.pivot_table(index='ind', columns='cod_rural_rbd', values='prom', aggfunc='mean').fillna(0)
    chi2_zona, p_zona, _, _ = chi2_contingency(tabla_zona)

    # Prueba de chi-cuadrado para dependencia
    tabla_depe = df.pivot_table(index='ind', columns='cod_depe2', values='prom', aggfunc='mean').fillna(0)
    chi2_depe, p_depe, _, _ = chi2_contingency(tabla_depe)

    # Prueba de chi-cuadrado para provincia
    tabla_pro = df.pivot_table(index='ind', columns='nom_pro_rbd', values='prom', aggfunc='mean').fillna(0)
    chi2_pro, p_pro, _, _ = chi2_contingency(tabla_pro)

    return render(request, 'educacion/graficos_idps23_4.html', {'grafico_html': grafico_html,
                                                                'grafico_zona': grafico_zona,
                                                                'grafico_dependencia':grafico_dependencia,
                                                                'grafico_provincia':grafico_provincia,
                                                                'nom_reg_rbd': region_seleccionada,
                                                                'chi2_zona': round(chi2_zona,2),
                                                                'chi2_depe':round(chi2_depe,2),
                                                                'chi2_pro':round(chi2_pro,2),
                                                                'p_zona':round(p_zona,4),
                                                                'p_depe':round(p_depe,4),
                                                                'p_pro':round(p_pro,4)})

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

    # Obtener la región seleccionada desde la URL (por defecto muestra todos)
    region_seleccionada = request.GET.get('nom_reg_rbd', "METROPOLITANA DE SANTIAGO")

    # Filtrar los datos por grado y año
    datos = resultados_simce_idps.objects.filter(grado='2', agno=2023)
    
    # Filtrar por región si es necesario
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

    # Configurar el diseño del gráfico por región
    fig.update_layout(
        title="Promedio por Región según Tipo de Indicador",
        xaxis_title="Región",
        yaxis_title="Promedio",
        barmode='group',
        template="plotly_white"
    )

    # Gráfico 2 comparando resultados según zona 
    df_zona = df.groupby(['nom_reg_rbd', 'ind', 'cod_rural_rbd'])['prom'].mean().reset_index()

    # Crear la figura para el gráfico de comparación por zona
    fig2 = go.Figure()

    # Iterar por cada zona (Rural y Urbano) primero
    for ruralidad in df_zona['cod_rural_rbd'].unique():
        df_filtrado = df_zona[df_zona['cod_rural_rbd'] == ruralidad]

        fig2.add_trace(go.Bar(
            x=df_filtrado['ind'],  # Agrupar por Indicador
            y=df_filtrado['prom'],
            name=zona[ruralidad],  # La etiqueta solo será "Rural" o "Urbano"
            text=df_filtrado['prom'].apply(lambda x: f"{x:.2f}"),
            textposition='inside',
            marker_color='#EF553B' if ruralidad == 1 else '#636EFA'
        ))

    # Configurar el diseño del gráfico
        fig2.update_layout(
        title="Comparación de Indicadores por Zona",
        xaxis_title="Indicador",
        yaxis_title="Promedio",
        barmode='group',  # Agrupar por Indicador
        template="plotly_white"
    )
        
     # Gráfico 3 comparando resultados según dependencia 
    df_depe = df.groupby(['nom_reg_rbd', 'ind', 'cod_depe2'])['prom'].mean().reset_index()

    # Crear la figura para el gráfico de comparación por dependencia
    fig3= go.Figure()

    # Iterar por cada dependencia
    for dependencia in df_depe['cod_depe2'].unique():
        df_filtrado = df_depe[df_depe['cod_depe2'] == dependencia]

        fig3.add_trace(go.Bar(
            x=df_filtrado['ind'],  # Agrupar por Indicador
            y=df_filtrado['prom'],
            name=dependencia_cat[dependencia], 
            text=df_filtrado['prom'].apply(lambda x: f"{x:.2f}"),
            textposition='inside'
        ))

    # Configurar el diseño del gráfico
        fig3.update_layout(
        title="Comparación de Indicadores por Dependencia",
        xaxis_title="Indicador",
        yaxis_title="Promedio",
        barmode='group',  # Agrupar por Indicador
        template="plotly_white"
    )
        
        
    # Gráfico 4 comparando resultados según provincia 
    df_pro = df.groupby(['nom_reg_rbd', 'ind', 'nom_pro_rbd'])['prom'].mean().reset_index()

    # Crear la figura para el gráfico de comparación por provincia
    fig4= go.Figure()

    # Iterar por cada provincia
    for provincia in df_pro['nom_pro_rbd'].unique():
        df_filtrado = df_pro[df_pro['nom_pro_rbd'] == provincia]

        fig4.add_trace(go.Bar(
            x=df_filtrado['ind'],  # Agrupar por Indicador
            y=df_filtrado['prom'],
            name=provincia,  
            text=df_filtrado['prom'].apply(lambda x: f"{x:.2f}"),
            textposition='inside'
        ))

    # Configurar el diseño del gráfico
        fig4.update_layout(
        title="Comparación de Indicadores por Provincia",
        xaxis_title="Indicador",
        yaxis_title="Promedio",
        barmode='group',  # Agrupar por Indicador
        template="plotly_white"
    )
        

        
    # Convertir ambos gráficos a HTML
    grafico_html = fig.to_html()
    grafico_zona = fig2.to_html()
    grafico_dependencia = fig3.to_html()
    grafico_provincia = fig4.to_html()

    # Prueba de chi-cuadrado para zona (Rural/Urbano)
    tabla_zona = df.pivot_table(index='ind', columns='cod_rural_rbd', values='prom', aggfunc='mean').fillna(0)
    chi2_zona, p_zona, _, _ = chi2_contingency(tabla_zona)

    # Prueba de chi-cuadrado para dependencia
    tabla_depe = df.pivot_table(index='ind', columns='cod_depe2', values='prom', aggfunc='mean').fillna(0)
    chi2_depe, p_depe, _, _ = chi2_contingency(tabla_depe)

    return render(request, 'educacion/graficos_idps23_2.html', {
        'grafico_html': grafico_html,
        'grafico_zona': grafico_zona,
        'grafico_dependencia':grafico_dependencia,
        'grafico_provincia':grafico_provincia,
        'nom_reg_rbd': region_seleccionada,
        'chi2_zona': round(chi2_zona, 2),
        'p_zona': round(p_zona, 4),
        'chi2_depe': round(chi2_depe, 2),
        'p_depe': round(p_depe, 4),
    })
