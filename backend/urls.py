from django.urls import path
from backend import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('/themes', views.themes, name='themes'),
]