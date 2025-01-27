from django.shortcuts import render

def rentabilidad_view (request):
    return render (request, 'pensiones/rentabilidad.html')
