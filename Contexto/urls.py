from django.urls import path
from .views import ContextoCreateView, train_agent_model, get_agent_response

urlpatterns = [
    path("contexto/cadastrar", ContextoCreateView.as_view(), name="contexto-cadastrar"),
    path("contexto/treinar", train_agent_model, name="contexto-treinar"),
    path("contexto/responder", get_agent_response, name="contexto-responder"),
]