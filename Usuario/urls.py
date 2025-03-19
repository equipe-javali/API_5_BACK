from django.urls import path
from .views import (
    UsuarioCreateView,
    UsuarioUpdateView,
    login
)

urlpatterns = [
    path("usuario/cadastrar", UsuarioCreateView.as_view(), name="usuario-cadastrar"),
    path("usuario/atualizar/<int:pk>", UsuarioUpdateView.as_view(), name="usuario-atualizar"),
    path("usuario/login", login, name="usuario-login"),
]