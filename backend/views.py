from django.shortcuts import render
import glob

context ={}

def dashboard(request):
    return render(request, 'backend/index.html')


def themes(request):
    themes = glob.glob1(dirname='rn-themes', pattern='*')
    context['themes'] = themes

    return render(request, 'backend/themes/index.html', context)
