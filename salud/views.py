from django.shortcuts import render

def dependencia_view(request):
    return render (request, 'salud/dependencia.html')
