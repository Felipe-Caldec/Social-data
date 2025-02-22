from django.shortcuts import render
from .models import matricula_parvulo
from django.http import HttpResponse
from django.core.paginator import Paginator
from .forms import Estudiantes_filtro
from .admin import MatriculaParvuloResource
from django.db.models import Q
import plotly.express as px
import pandas as pd
import plotly.graph_objects as go
import plotly.figure_factory as ff

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

# GRAFICOS

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

    # Obtener la región seleccionada desde la URL (por defecto muestra todos)
    region_seleccionada = request.GET.get('nom_reg_a_estab', None)

    datos = matricula_parvulo.objects.filter(agno=2021, gen_alu__in= [1, 2])
    # Obtener datos del modelo, filtrando por región si se especifica
  
    if region_seleccionada:
        datos = datos.filter(nom_reg_a_estab=region_seleccionada)

    datos= datos.values('gen_alu','rural_estab','dependencia')
    df = pd.DataFrame(datos)

    # Reemplazar los números con los nombres de género
    df['gen_alu'] = df['gen_alu'].map(categorias_genero)
    df['rural_estab'] = df['rural_estab'].map(categorias_rural)
    df['dependencia'] = df['dependencia'].map(categorias_dependencia)


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
        title_x=0.5,
        yaxis=dict(title="Porcentaje", tickformat=".2f", range=[0, 100]),
        xaxis_title="Género",
        bargap=0.2,  # Espaciado entre barras de diferentes grupos
        bargroupgap=0.1  # Espaciado dentro de un grupo
    )


### **Gráfico 2: Distribución total de género**

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
        title_x=0.5,
        yaxis=dict(title="Porcentaje", tickformat=".2f", range=[0, 100]),
        xaxis_title="Género",
        bargap=0.1,
        bargroupgap=0.1,
    )


    grafico_genero_zona_html = fig.to_html()
    grafico_genero_dependencia_html = fig2.to_html()

    return render(request, 'educacion/grafico.html', {'grafico_html': grafico_genero_zona_html,
                                                      'grafico_dependencia_html': grafico_genero_dependencia_html,
                                                      'region': region_seleccionada})




####################################################################################



def grafico_matricula_parvulo_2022_genero_dep (request):

    categorias_genero = {
        1: "Masculino",
        2: "Femenino",
    }

    categorias_rural = {
        0: "Urbano",
        1:"Rural",
    }

    # Obtener la región seleccionada desde la URL (por defecto muestra todos)
    region_seleccionada = request.GET.get('nom_reg_a_estab', None)

    datos = matricula_parvulo.objects.filter(agno=2022, gen_alu__in= [1, 2])
    # Obtener datos del modelo, filtrando por región si se especifica
  
    if region_seleccionada:
        datos = datos.filter(nom_reg_a_estab=region_seleccionada)

    datos= datos.values('gen_alu','rural_estab')
    df = pd.DataFrame(datos)

    # Reemplazar los números con los nombres de género
    df['gen_alu'] = df['gen_alu'].map(categorias_genero)
    df['rural_estab'] = df['rural_estab'].map(categorias_rural)


     # Contar cuántos hay de cada género
    conteo = df.groupby(['gen_alu','rural_estab']).size().reset_index(name='Cantidad')
    conteo.columns = ['Género','Zona','Cantidad']
    

    # Convertir "Género" a tipo string (para que no sea numérico)
    conteo['Género'] = conteo['Género'].astype(str)
    conteo['Zona'] = conteo['Zona'].astype(str)
    conteo = conteo.dropna(subset=['Zona'])

    # Calcular el total por zona para obtener porcentajes
    totales_por_zona = conteo.groupby('Zona')['Cantidad'].transform('sum')
    conteo['Porcentaje'] = (conteo['Cantidad'] / totales_por_zona) * 100


# Crear la figura manualmente
    fig = go.Figure()

    for zona in conteo['Zona'].unique():
        df_filtrado = conteo[conteo['Zona'] == zona]
        fig.add_trace(go.Bar(
            x=df_filtrado['Género'],
            y=df_filtrado['Porcentaje'],
            name=zona,  # Esto agrupará las barras por zona
            text=df_filtrado['Porcentaje'].apply(lambda x: f"{x:.1f}%"),  # Muestra los valores en las barras
            textposition='auto'
        ))

    # Configurar el diseño del gráfico
    fig.update_layout(
        barmode='group',  # Agrupar barras
        title="Distribución porcentual de género según zona",
        title_x=0.5,
        yaxis=dict(title="Porcentaje", tickformat=".1f"), # Mostrar decimales en el eje Y),
        xaxis_title="Género",
        bargap=0.2,  # Espaciado entre barras de diferentes grupos
        bargroupgap=0.1  # Espaciado dentro de un grupo
    )


    grafico_genero_zona_html = fig.to_html()

    return render(request, 'educacion/grafico.html', {'grafico_html': grafico_genero_zona_html,
                                                      'region': region_seleccionada})