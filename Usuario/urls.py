from django.urls import path
from .views import (
    UsuarioCreateView,
    UsuarioUpdateView,
    AdminCreateView,
    login
)

urlpatterns = [
    path("usuario/cadastrar", UsuarioCreateView.as_view(), name="usuario-cadastrar"),
    path('admin/cadastrar', AdminCreateView.as_view(), name='admin-cadastrar'),
    path("usuario/atualizar/<int:pk>", UsuarioUpdateView.as_view(), name="usuario-atualizar"),
    path("usuario/login", login, name="usuario-login"),
]