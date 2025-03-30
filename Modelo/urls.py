from django.urls import path
from .views import list_trained_models

urlpatterns = [
    path('modelo/listar', list_trained_models, name='list-trained-models'),
]