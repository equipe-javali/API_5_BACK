from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from .models import Contexto
from .serializers import ContextoSerializer
from Agente.models import Agente
from Modelo.services.ml_service import ModelService
from Modelo.models import TrainedModel

class ContextoCreateView(generics.CreateAPIView):
    queryset = Contexto.objects.all()
    serializer_class = ContextoSerializer
    permission_classes = [AllowAny]

@api_view(["POST"])
@permission_classes([AllowAny])
def importar_contextos(request):
    """Importa múltiplos contextos para um agente"""
    agente_id = request.data.get("Agente_id")
    contextos = request.data.get("contextos", [])
    
    if not agente_id or not isinstance(contextos, list):
        return Response({"error": "Formato inválido. Forneça Agente_id e uma lista de contextos"}, 
                       status=status.HTTP_400_BAD_REQUEST)
    
    # Validate agent existence
    try:
        agente = Agente.objects.get(id=agente_id)
    except Agente.DoesNotExist:
        return Response({"error": "O agente não existe. Crie o agente antes de adicionar contextos."}, 
                       status=status.HTTP_404_NOT_FOUND)
    
    # Validate context format
    for c in contextos:
        if not ("pergunta" in c and "resposta" in c):
            return Response({"error": "Cada contexto deve ter os campos 'pergunta' e 'resposta'"},
                          status=status.HTTP_400_BAD_REQUEST)
    
    try:
        contextos_criados = []
        
        for c in contextos:
            contexto = Contexto.objects.create_contexto(
                pergunta=c["pergunta"],
                resposta=c["resposta"],
                Agente_id=agente
            )
            contextos_criados.append(contexto.id)
        
        return Response({
            "success": True,
            "message": f"Criados {len(contextos_criados)} contextos para o agente {agente.nome}",
            "contextos_ids": contextos_criados
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
@api_view(["POST"])
@permission_classes([AllowAny])
def train_agent_model(request):
    """
    Train a model for a specific agent using all its contexts
    """
    agent_id = request.data.get("Agente_id")
    
    if not agent_id:
        return Response({"error": "Agente_id is required"}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Get agent to verify it exists
        agent = Agente.objects.get(id=agent_id)
        
        # Get all contexts for this agent
        contexts = Contexto.objects.filter(Agente_id=agent_id)
        
        if not contexts.exists():
            return Response(
                {"error": f"Nenhum contexto encontrado para o agente '{agent.nome}'. Adicione contextos antes de treinar."},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Check minimum number of contexts for effective training
        if contexts.count() < 3:
            return Response(
                {"error": f"O agente '{agent.nome}' precisa de pelo menos 3 contextos para um treinamento eficaz."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Convert contexts to training data format (question, answer)
        training_data = [(ctx.pergunta, ctx.resposta) for ctx in contexts]
        
        # Train the model
        model_service = ModelService()
        result = model_service.train_model(agent_id, training_data)

        # After training, fetch the model record
        trained_model = TrainedModel.objects.filter(Agente_id=agent_id, is_active=True).first()
        
        return Response({
            "success": True,
            "message": f"Modelo para o agente '{agent.nome}' treinado com sucesso",
            "details": result,
            "model_info": {
                "id": trained_model.id,
                "created_at": trained_model.created_at,
                "examples_count": trained_model.examples_count,
                "performance": trained_model.performance_score
            }
        }, status=status.HTTP_200_OK)
        
    except Agente.DoesNotExist:
        return Response({"error": "Agente não encontrado"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(["POST"])
@permission_classes([AllowAny])  # Changed to AllowAny to let any user query the agent
def get_agent_response(request):
    """
    Get a response from a trained agent model
    """
    agent_id = request.data.get("Agente_id")
    question = request.data.get("pergunta")
    
    if not agent_id or not question:
        return Response(
            {"error": "Agente_id e pergunta são obrigatórios"}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        # Verify agent exists
        agent = Agente.objects.get(id=agent_id)
        
        # Check if agent has a trained model
        model_exists = TrainedModel.objects.filter(Agente_id=agent_id, is_active=True).exists()
        if not model_exists:
            return Response({
                "error": "Este agente ainda não foi treinado",
                "message": f"O agente '{agent.nome}' precisa ser treinado antes de responder perguntas"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get response from model
        model_service = ModelService()
        result = model_service.answer_question(agent_id, question)
        
        if not result.get('success', False):
            return Response({
                "error": result.get('error', "Erro desconhecido"),
                "message": f"O agente '{agent.nome}' não conseguiu processar sua pergunta"
            }, status=status.HTTP_404_NOT_FOUND)
        
        return Response({
            "success": True,
            "agent": agent.nome,
            "pergunta": question,
            "resposta": result['answer'],
            "confidence": result.get('confidence', 0),
            "in_scope": result.get('in_scope', False)
        }, status=status.HTTP_200_OK)
        
    except Agente.DoesNotExist:
        return Response({"error": "Agente não encontrado"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(["GET"])
@permission_classes([AllowAny])  # Allow anyone to see contexts for an agent
def list_agent_contexts(request, agent_id):
    """
    List all contexts for a specific agent
    """
    try:
        # Check if agent exists
        agent = Agente.objects.get(id=agent_id)
        
        # Get contexts for this agent
        contexts = Contexto.objects.filter(Agente_id=agent_id)
        
        serializer = ContextoSerializer(contexts, many=True)
        
        return Response({
            "success": True,
            "agent": agent.nome,
            "contexts_count": contexts.count(),
            "contexts": serializer.data
        }, status=status.HTTP_200_OK)
        
    except Agente.DoesNotExist:
        return Response({"error": "Agente não encontrado"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)