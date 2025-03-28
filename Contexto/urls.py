from django.urls import path
from .views import ContextoCreateView, importar_contextos, train_agent_model, get_agent_response

urlpatterns = [
    path("contexto/cadastrar-individual", ContextoCreateView.as_view(), name="contexto-cadastrar-individual"),
    path("contexto/cadastrar-em-massa", importar_contextos, name="contexto-cadastrar-em-massa"),
    path("contexto/treinar", train_agent_model, name="contexto-treinar"),
    path("contexto/responder", get_agent_response, name="contexto-responder"),
]