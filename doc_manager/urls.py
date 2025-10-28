from . import views
from django.urls import path

# The list of URL patterns for the users app
urlpatterns = [
    path("upload/", views.DocumentCreateView.as_view(), name='document_upload'),
]