from django.urls import path
from .views import AgenteCreateView, list_user_agents
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated

urlpatterns = [
    path("agente/cadastrar", AgenteCreateView.as_view(), name="agente-cadastrar"),
    path("agente/listar-usuario", list_user_agents, name="agente-listar-usuario"),
]