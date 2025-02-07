from django.shortcuts import render, redirect
from .forms import Cal_Rentabi_Forms, FechaForm


def rentabilidad_view (request):
    return render (request, 'pensiones/rentabilidad.html')

def Cal_Rentabi_View(request):

    form = Cal_Rentabi_Forms(request.POST or None)
    context = {}

    if request.method == "POST":
        if form.is_valid():
            form.save()
            return redirect ("rentabi-cal")
    context = {"form_rentabi": form}
    
    return render (request, "pensiones/calculo.html", context )

def rentabilidad_fondos_view(request):
    form = FechaForm()  # Formulario vacío por defecto
    import pandas as pd
    if request.method == "POST":
        form = FechaForm(request.POST)  # Procesar datos enviados por POST
        if form.is_valid():
            fecha_inicial = form.cleaned_data.get("fecha_inicial")  # Usar .get() en cleaned_data, no en request
            fecha_actual = form.cleaned_data.get("fecha_actual")
            
            lista_fecha=pd.date_range(pd.to_datetime(fecha_inicial),pd.to_datetime(fecha_actual))
            df_l=pd.DataFrame({'fecha':lista_fecha,'n':[x for x in range(len(lista_fecha))]})

            # Pasar las fechas al contexto
            return render(request, "pensiones/fondos.html", {"form": form, "fondos.html": df_l.to_html(classes="table table-striped", index=False)})

    # Si no es POST, renderiza solo el formulario vacío
