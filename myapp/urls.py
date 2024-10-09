from django.urls import path
from myapp.views import home, regenerate_readme
from .views import download_files


urlpatterns = [
    path('', home, name='home'),
    path('regenerate/<int:document_id>/', regenerate_readme, name='regenerate_readme'),
    path('download/<int:document_id>/', download_files, name='download_files'),

]