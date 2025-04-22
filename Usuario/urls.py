from django.urls import path
from .views import (
    UsuarioCreateView,
    UsuarioUpdateView,
    AdminCreateView,
    login,
    delete_user,
    listar_usuarios_todos
)

urlpatterns = [
    path("usuario/cadastrar", UsuarioCreateView.as_view(), name="usuario-cadastrar"),
    path('admin/cadastrar', AdminCreateView.as_view(), name='admin-cadastrar'),
    path("usuario/atualizar/<int:pk>", UsuarioUpdateView.as_view(), name="usuario-atualizar"),
    path("usuario/excluir/<int:pk>", delete_user, name="usuario-excluir"),
    path("usuario/login", login, name="usuario-login"),
    path("usuario/listagem-todos", listar_usuarios_todos, name="usuario-listagem-todos"),
]