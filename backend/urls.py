from django.urls import path
from backend import views

urlpatterns = [
    path('', views.index, name='index'),
    path('/themes', views.themes, name='themes'),
]