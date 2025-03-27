from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Contexto
from .serializers import ContextoSerializer
from Agente.models import Agente
from Modelo.services.ml_service import ModelService
from Modelo.models import TrainedModel

class ContextoCreateView(generics.CreateAPIView):
    queryset = Contexto.objects.all()
    serializer_class = ContextoSerializer
    permission_classes = [IsAuthenticated]

@api_view(["POST"])
@permission_classes([IsAuthenticated])
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
                {"error": f"No contexts found for agent '{agent.nome}'. Add contexts before training."},
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
            "message": f"Model for agent '{agent.nome}' trained successfully",
            "details": result,
            "model_info": {
                "id": trained_model.id,
                "created_at": trained_model.created_at,
                "examples_count": trained_model.examples_count,
                "performance": trained_model.performance_score
            }
        }, status=status.HTTP_200_OK)
        
    except Agente.DoesNotExist:
        return Response({"error": "Agent not found"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def get_agent_response(request):
    """
    Get a response from a trained agent model
    """
    agent_id = request.data.get("Agente_id")
    question = request.data.get("pergunta")
    
    if not agent_id or not question:
        return Response(
            {"error": "Both Agente_id and pergunta are required"}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        # Verify agent exists
        agent = Agente.objects.get(id=agent_id)
        
        # Get response from model
        model_service = ModelService()
        result = model_service.answer_question(agent_id, question)
        
        if not result['success']:
            return Response({
                "error": result['error'],
                "message": f"Agent '{agent.nome}' could not process your question"
            }, status=status.HTTP_404_NOT_FOUND)
        
        return Response({
            "success": True,
            "agent": agent.nome,
            "pergunta": question,
            "resposta": result['answer'],
            "confidence": result['confidence'],
            "in_scope": result['in_scope']
        }, status=status.HTTP_200_OK)
        
    except Agente.DoesNotExist:
        return Response({"error": "Agent not found"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)