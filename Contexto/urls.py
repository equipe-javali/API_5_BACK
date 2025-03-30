from django.urls import path
from .views import (
    ContextoCreateView, 
    importar_contextos, 
    train_agent_model, 
    get_agent_response,
    list_agent_contexts
)

urlpatterns = [
    path("contexto/cadastrar-individual", ContextoCreateView.as_view(), name="contexto-cadastrar-individual"),
    path("contexto/cadastrar-em-massa", importar_contextos, name="contexto-cadastrar-em-massa"),
    path("contexto/treinar", train_agent_model, name="contexto-treinar"),
    path("contexto/responder", get_agent_response, name="contexto-responder"),
    path("contexto/listar/<int:agent_id>", list_agent_contexts, name="contexto-listar"),
]