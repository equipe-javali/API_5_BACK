from django.urls import path
from .views import AgenteCreateView

urlpatterns = [
    path("agente/cadastrar", AgenteCreateView.as_view(), name="agente-cadastrar"),
]