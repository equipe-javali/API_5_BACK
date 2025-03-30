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