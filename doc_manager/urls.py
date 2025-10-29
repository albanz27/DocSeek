from . import views
from django.urls import path

# The list of URL patterns for the users app
urlpatterns = [
    path("upload/", views.DocumentCreateView.as_view(), name='document_upload'),
    path("", views.DocumentListView.as_view(), name='document_list'),
    path("process/<int:pk>/", views.DocumentProcessView.as_view(), name='document_process'),
    path("dashboard/", views.UploaderDashboardView.as_view(), name='uploader_dashboard'),
]