from rest_framework import generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from .models import Agente
from .serializers import AgenteSerializer
from Permissao.models import PermissaoUsuario

class AgenteCreateView(generics.CreateAPIView):
    queryset = Agente.objects.all()
    serializer_class = AgenteSerializer

@api_view(["GET"])
@permission_classes([AllowAny])
def list_user_agents(request):
    """Lista todos os agentes que o usuário tem permissão para acessar"""
    # Modified to return all agents without permission check
    agents = Agente.objects.all()
    serializer = AgenteSerializer(agents, many=True)
    return Response(serializer.data)

# Add this missing function
@api_view(["GET"])
@permission_classes([AllowAny])
def list_all_agents(request):
    """Lista todos os agentes disponíveis"""
    agents = Agente.objects.all()
    serializer = AgenteSerializer(agents, many=True)
    return Response(serializer.data)