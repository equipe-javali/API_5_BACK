from rest_framework import generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Agente
from .serializers import AgenteSerializer
from Permissao.models import PermissaoUsuario

class AgenteCreateView(generics.CreateAPIView):
    queryset = Agente.objects.all()
    serializer_class = AgenteSerializer

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def list_user_agents(request):
    """Lista todos os agentes que o usuário tem permissão para acessar"""
    user_id = request.user.id
    
    # Obter todas as permissões do usuário
    user_permissions = PermissaoUsuario.objects.filter(Usuario_id=user_id).values_list('Permissao_id', flat=True)
    
    # Obter todos os agentes associados a essas permissões
    agents = Agente.objects.filter(Permissao_id__in=user_permissions)
    
    serializer = AgenteSerializer(agents, many=True)
    return Response(serializer.data)