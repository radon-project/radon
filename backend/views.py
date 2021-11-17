from django.shortcuts import render


def index(request):
    return render(request, 'backend/index.html')


def themes(request):
    return render(request, 'backend/themes/index.html')
