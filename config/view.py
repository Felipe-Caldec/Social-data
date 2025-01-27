from django.shortcuts import render


def bienvenida_view(request):
    return render(request, 'bienvenida.html')

def bienvenida2 (request):
    return render(request, 'bienvenida copy.html')