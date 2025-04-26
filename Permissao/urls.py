from django.urls import path
from .views import PermissaoCreateView, buscar_permissao

urlpatterns = [
    path("permissao/cadastrar", PermissaoCreateView.as_view(), name="permissao-cadastrar"),
    path("permissao/buscar", buscar_permissao, name="permissao-buscar"),
]