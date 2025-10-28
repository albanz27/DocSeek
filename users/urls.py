from . import views
from django.urls import path

# The list of URL patterns for the users app
urlpatterns = [
    path('register/', views.signup, name='register'),
    # Registration view will go here later
    path('', views.home, name='home'),
]