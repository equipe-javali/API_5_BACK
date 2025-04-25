from django.urls import path
from .views import (
    chat_view,
    chat_enviar_mensagem,
    iniciar_conversa, 
    listar_chatbots,       
)

urlpatterns = [
    path("chat/visualizar", chat_view, name="chat-visualizar"),
    path("chat/enviar-mensagem", chat_enviar_mensagem, name="chat-enviar-mensagem"),
    path("chat/iniciar-conversa", iniciar_conversa, name="chat-iniciar-conversa"),  # New route
    path("chat/listar", listar_chatbots, name="listar-chatbots"),
]