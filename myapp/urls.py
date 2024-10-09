from django.urls import path
from myapp.views import home, regenerate_readme

urlpatterns = [
    path('', home, name='home'),
    path('regenerate/<int:document_id>/', regenerate_readme, name='regenerate_readme'),
]