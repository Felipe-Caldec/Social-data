from django.shortcuts import render

def establecimientos_view (request):
    return render (request, 'educacion/establecimientos.html')
