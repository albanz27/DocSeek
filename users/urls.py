from . import views
from django.urls import path

urlpatterns = [
    path('register/', views.signup, name='register'),
    
    path('', views.home, name='home'),
]