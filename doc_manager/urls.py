from . import views
from django.urls import path

# The list of URL patterns for the users app
urlpatterns = [
    path("upload/", views.DocumentCreateView.as_view(), name='document_upload'),
    path("", views.DocumentListView.as_view(), name='document_list'),
    path("process/<int:pk>/", views.DocumentProcessView.as_view(), name='document_process'),
    path("delete/<int:pk>/", views.DocumentDeleteView.as_view(), name='document_delete'),
    path("dashboard/", views.UploaderDashboardView.as_view(), name='uploader_dashboard'),
    path("view/<int:pk>/", views.DocumentViewerView.as_view(), name='document_viewer'),
    path("file/<int:pk>/", views.serve_document_file, name='serve_document'),
]