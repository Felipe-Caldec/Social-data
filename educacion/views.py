from django.shortcuts import render
from .models import matricula_parvulo, matricula_basica, matricula_media
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

    # Obtener la región seleccionada desde la URL (por defecto muestra todos)
    region_seleccionada = request.GET.get('nom_reg_a_estab', None)

    datos = matricula_parvulo.objects.filter(agno=2021, gen_alu__in= [1, 2])
    # Obtener datos del modelo, filtrando por región si se especifica
  
    if region_seleccionada:
        datos = datos.filter(nom_reg_a_estab=region_seleccionada)

    datos= datos.values('gen_alu','rural_estab','dependencia','cod_ense2_m')
    df = pd.DataFrame(datos)

    # Reemplazar los números con los nombres de género
    df['gen_alu'] = df['gen_alu'].map(categorias_genero)
    df['rural_estab'] = df['rural_estab'].map(categorias_rural)
    df['dependencia'] = df['dependencia'].map(categorias_dependencia)
    df['cod_ense2_m'] = df['cod_ense2_m'].map(categorias_tipo)


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
    totales_por_tipo = conteo_dependencia.groupby('Género')['Cantidad'].transform('sum')
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

    return render(request, 'educacion/graficos_parvulo_2021.html', {'grafico_html': grafico_genero_zona_html,
                                                      'grafico_dependencia_html': grafico_genero_dependencia_html,
                                                      'grafico_tipo_html': grafico_genero_tipo_html,
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

    # Obtener la región seleccionada desde la URL (por defecto muestra todos)
    region_seleccionada = request.GET.get('nom_reg_a_estab', None)

    datos = matricula_parvulo.objects.filter(agno=2022, gen_alu__in= [1, 2])
    # Obtener datos del modelo, filtrando por región si se especifica
  
    if region_seleccionada:
        datos = datos.filter(nom_reg_a_estab=region_seleccionada)

    datos= datos.values('gen_alu','rural_estab','dependencia','cod_ense2_m')
    df = pd.DataFrame(datos)

    # Reemplazar los números con los nombres de género
    df['gen_alu'] = df['gen_alu'].map(categorias_genero)
    df['rural_estab'] = df['rural_estab'].map(categorias_rural)
    df['dependencia'] = df['dependencia'].map(categorias_dependencia)
    df['cod_ense2_m'] = df['cod_ense2_m'].map(categorias_tipo)


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
    totales_por_tipo = conteo_dependencia.groupby('Género')['Cantidad'].transform('sum')
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

    return render(request, 'educacion/graficos_parvulo_2022.html', {'grafico_html': grafico_genero_zona_html,
                                                      'grafico_dependencia_html': grafico_genero_dependencia_html,
                                                      'grafico_tipo_html': grafico_genero_tipo_html,
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

    # Obtener la región seleccionada desde la URL (por defecto muestra todos)
    region_seleccionada = request.GET.get('nom_reg_a_estab', None)

    datos = matricula_parvulo.objects.filter(agno=2023, gen_alu__in= [1, 2])
    # Obtener datos del modelo, filtrando por región si se especifica
  
    if region_seleccionada:
        datos = datos.filter(nom_reg_a_estab=region_seleccionada)

    datos= datos.values('gen_alu','rural_estab','dependencia','cod_ense2_m')
    df = pd.DataFrame(datos)

    # Reemplazar los números con los nombres de género
    df['gen_alu'] = df['gen_alu'].map(categorias_genero)
    df['rural_estab'] = df['rural_estab'].map(categorias_rural)
    df['dependencia'] = df['dependencia'].map(categorias_dependencia)
    df['cod_ense2_m'] = df['cod_ense2_m'].map(categorias_tipo)


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
    totales_por_tipo = conteo_dependencia.groupby('Género')['Cantidad'].transform('sum')
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

    return render(request, 'educacion/graficos_parvulo_2023.html', {'grafico_html': grafico_genero_zona_html,
                                                      'grafico_dependencia_html': grafico_genero_dependencia_html,
                                                      'grafico_tipo_html': grafico_genero_tipo_html,
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

    # Obtener la región seleccionada desde la URL (por defecto muestra todos)
    region_seleccionada = request.GET.get('nom_reg_a_estab', None)

    datos = matricula_parvulo.objects.filter(agno=2024, gen_alu__in= [1, 2])
    # Obtener datos del modelo, filtrando por región si se especifica
  
    if region_seleccionada:
        datos = datos.filter(nom_reg_a_estab=region_seleccionada)

    datos= datos.values('gen_alu','rural_estab','dependencia','cod_ense2_m')
    df = pd.DataFrame(datos)

    # Reemplazar los números con los nombres de género
    df['gen_alu'] = df['gen_alu'].map(categorias_genero)
    df['rural_estab'] = df['rural_estab'].map(categorias_rural)
    df['dependencia'] = df['dependencia'].map(categorias_dependencia)
    df['cod_ense2_m'] = df['cod_ense2_m'].map(categorias_tipo)


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
    totales_por_tipo = conteo_dependencia.groupby('Género')['Cantidad'].transform('sum')
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

    return render(request, 'educacion/graficos_parvulo_2024.html', {'grafico_html': grafico_genero_zona_html,
                                                      'grafico_dependencia_html': grafico_genero_dependencia_html,
                                                      'grafico_tipo_html': grafico_genero_tipo_html,
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

    # Obtener la región seleccionada desde la URL (por defecto muestra todos)
    region_seleccionada = request.GET.get('nom_reg_a_estab', None)

    datos = matricula_parvulo.objects.filter(agno=2020, gen_alu__in= [1, 2])
    # Obtener datos del modelo, filtrando por región si se especifica
  
    if region_seleccionada:
        datos = datos.filter(nom_reg_a_estab=region_seleccionada)

    datos= datos.values('gen_alu','rural_estab','dependencia','cod_ense2_m')
    df = pd.DataFrame(datos)

    # Reemplazar los números con los nombres de género
    df['gen_alu'] = df['gen_alu'].map(categorias_genero)
    df['rural_estab'] = df['rural_estab'].map(categorias_rural)
    df['dependencia'] = df['dependencia'].map(categorias_dependencia)
    df['cod_ense2_m'] = df['cod_ense2_m'].map(categorias_tipo)


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
    totales_por_tipo = conteo_dependencia.groupby('Género')['Cantidad'].transform('sum')
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

    return render(request, 'educacion/graficos_parvulo_2020.html', {'grafico_html': grafico_genero_zona_html,
                                                      'grafico_dependencia_html': grafico_genero_dependencia_html,
                                                      'grafico_tipo_html': grafico_genero_tipo_html,
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

    # Obtener la región seleccionada desde la URL (por defecto muestra todos)
    region_seleccionada = request.GET.get('NOM_REG_RBD_A', None)

    datos = matricula_basica.objects.filter(AGNO=2023, GEN_ALU__in= [1, 2])
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
    totales_por_tipo = conteo_dependencia.groupby('Género')['Cantidad'].transform('sum')
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

    return render(request, 'educacion/graficos_basica_2023.html', {'grafico_html': grafico_genero_zona_html,
                                                      'grafico_dependencia_html': grafico_genero_dependencia_html,
                                                      'grafico_tipo_html': grafico_genero_tipo_html,
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

    # Obtener la región seleccionada desde la URL (por defecto muestra todos)
    region_seleccionada = request.GET.get('NOM_REG_RBD_A', None)

    datos = matricula_basica.objects.filter(AGNO=2022, GEN_ALU__in= [1, 2])
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
    totales_por_tipo = conteo_dependencia.groupby('Género')['Cantidad'].transform('sum')
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

    # Obtener la región seleccionada desde la URL (por defecto muestra todos)
    region_seleccionada = request.GET.get('NOM_REG_RBD_A', None)

    datos = matricula_basica.objects.filter(AGNO=2021, GEN_ALU__in= [1, 2])
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
    totales_por_tipo = conteo_dependencia.groupby('Género')['Cantidad'].transform('sum')
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

    # Obtener la región seleccionada desde la URL (por defecto muestra todos)
    region_seleccionada = request.GET.get('NOM_REG_RBD_A', None)

    datos = matricula_basica.objects.filter(AGNO=2020, GEN_ALU__in= [1, 2])
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
    totales_por_tipo = conteo_dependencia.groupby('Género')['Cantidad'].transform('sum')
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

    tipo_ensenanza = {
        5: "Jóvenes Científico-Humanísta",
        6: "Adultos Científico-Humanísta",
        7: "Jóvenes Técnico-Profesional",
        8: "Adultos Técnico-Profesional",
    }

    # Obtener la región seleccionada desde la URL (por defecto muestra todos)
    region_seleccionada = request.GET.get('NOM_REG_RBD_A', None)

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
    df['COD_ENSE2'] = df['COD_ENSE2'].map(tipo_ensenanza)


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
    totales_por_tipo = conteo_dependencia.groupby('Género')['Cantidad'].transform('sum')
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

    return render(request, 'educacion/graficos_media_2023.html', {'grafico_html': grafico_genero_zona_html,
                                                      'grafico_dependencia_html': grafico_genero_dependencia_html,
                                                      'grafico_tipo_html': grafico_genero_tipo_html,
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
    region_seleccionada = request.GET.get('NOM_REG_RBD_A', None)

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
    totales_por_tipo = conteo_dependencia.groupby('Género')['Cantidad'].transform('sum')
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

    return render(request, 'educacion/graficos_media_2022.html', {'grafico_html': grafico_genero_zona_html,
                                                      'grafico_dependencia_html': grafico_genero_dependencia_html,
                                                      'grafico_tipo_html': grafico_genero_tipo_html,
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
    region_seleccionada = request.GET.get('NOM_REG_RBD_A', None)

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
    totales_por_tipo = conteo_dependencia.groupby('Género')['Cantidad'].transform('sum')
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

    return render(request, 'educacion/graficos_media_2021.html', {'grafico_html': grafico_genero_zona_html,
                                                      'grafico_dependencia_html': grafico_genero_dependencia_html,
                                                      'grafico_tipo_html': grafico_genero_tipo_html,
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
    region_seleccionada = request.GET.get('NOM_REG_RBD_A', None)

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
    totales_por_tipo = conteo_dependencia.groupby('Género')['Cantidad'].transform('sum')
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

    return render(request, 'educacion/graficos_media_2020.html', {'grafico_html': grafico_genero_zona_html,
                                                      'grafico_dependencia_html': grafico_genero_dependencia_html,
                                                      'grafico_tipo_html': grafico_genero_tipo_html,
                                                      'region': region_seleccionada})