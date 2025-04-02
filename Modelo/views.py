import os
from rest_framework.response import Response 
from rest_framework.decorators import api_view, permission_classes 
from rest_framework.permissions import AllowAny 
from .models import TrainedModel
from .serializers import TrainedModelSerializer

@api_view(["GET"])
@permission_classes([AllowAny])
def list_trained_models(request): 
    models = TrainedModel.objects.filter(is_active=True) 
    serializer = TrainedModelSerializer(models, many=True) 
    return Response(serializer.data)  

@api_view(["GET"])
@permission_classes([AllowAny])
def listar_modelos_completo(request):
    """List all trained models with complete agent details"""
    modelos = TrainedModel.objects.select_related('Agente_id').all()
    data = []
    
    for modelo in modelos:
        if modelo.is_active:
            item = {
                'id': modelo.id,
                'Agente_id_id': modelo.Agente_id.id,  # This is the correct agent ID
                'Agente_nome': modelo.Agente_id.nome,
                'examples_count': modelo.examples_count,
                'performance_score': modelo.performance_score,
                'created_at': modelo.created_at,
                'is_active': modelo.is_active
            }
            data.append(item)
    
    return Response(data)