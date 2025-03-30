from django.urls import path
from .views import list_trained_models, listar_modelos_completo

urlpatterns = [
    path('modelo/listar', list_trained_models, name='list-trained-models'),
    path('modelo/listar-completo', listar_modelos_completo, name='listar_modelos_completo'),
]