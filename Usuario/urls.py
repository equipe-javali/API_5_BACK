from django.urls import path
from .views import UsuarioCreateView

urlpatterns = [
    path("usuario/cadastrar", UsuarioCreateView.as_view(), name="usuario-cadastrar"),
]