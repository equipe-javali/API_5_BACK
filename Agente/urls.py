from django.urls import path
from .views import AgenteCreateView, list_user_agents, list_all_agents, delete_agent, update_agent, tempo_resposta_metricas
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

urlpatterns = [
    path("agente/cadastrar", AgenteCreateView.as_view(), name="agente-cadastrar"),
    path('agente/deletar/<int:id>', delete_agent, name='agente-deletar'),
    path('agente/atualizar/<int:id>', update_agent, name='agente-atualizar'),
    path("agente/listar-usuario", list_user_agents, name="agente-listar-usuario"),
    path("agente/listar-todos", list_all_agents, name="agente-listar-todos"),
    path("agente/tempo-resposta", tempo_resposta_metricas, name="agente-tempo-resposta"),
]