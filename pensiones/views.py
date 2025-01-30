from django.shortcuts import render, redirect
from .forms import Cal_Rentabi_Forms

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

