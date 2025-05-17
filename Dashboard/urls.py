from django.urls import path
from .views import (
    media_mensagens_por_agente,
    topico_mais_comum_por_agente,
    # most_common_keywords_by_agent
)

urlpatterns = [
    path("dashboard/media_mensagens_por_agente/", media_mensagens_por_agente, name="media_mensagens_por_agente"),
    path("dashboard/topico_mais_comum_por_agente/", topico_mais_comum_por_agente, name="topico_mais_comum_por_agente")
]
