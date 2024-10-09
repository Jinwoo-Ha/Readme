from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('regenerate/<int:document_id>/', views.regenerate_readme, name='regenerate_readme'),
    path('download/<int:document_id>/', views.download_files, name='download_files'),
    path('loading/', views.loading, name='loading'),
    path('result/', views.result, name='result'),
    path('check_readme_status/', views.check_readme_status, name='check_readme_status'),
]