from django.urls import path
from .views import UsuarioCreateView, login

urlpatterns = [
    path("usuario/cadastrar", UsuarioCreateView.as_view(), name="usuario-cadastrar"),
    path("usuario/login", login, name="usuario-login"),
]