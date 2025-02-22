from django.shortcuts import render


def bienvenida_view(request):
    return render(request, 'bienvenida.html')

