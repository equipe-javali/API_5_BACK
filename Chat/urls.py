from django.urls import path
from .views import (
    chat_view,
    chat_enviar_mensagem
)

urlpatterns = [
    path("chat/visualizar", chat_view, name="chat-visualizar"),
    path("chat/enviar-mensagem", chat_enviar_mensagem, name="chat-enviar-mensagem"),
]