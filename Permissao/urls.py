from django.urls import path
from .views import PermissaoCreateView

urlpatterns = [
    path("permissao/cadastrar", PermissaoCreateView.as_view(), name="permissao-cadastrar"),
]