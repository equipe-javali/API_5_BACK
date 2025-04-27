from rest_framework import generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Agente
from django.contrib.auth import get_user_model
Usuario = get_user_model()
from .serializers import AgenteSerializer

class AgenteCreateView(generics.CreateAPIView):
    queryset = Agente.objects.all()
    serializer_class = AgenteSerializer

@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_agent(_, id):
    """
    Deleta um agente específico pelo ID (id).
    """
    try:
        agent = Agente.objects.get(id=id)
        agent.delete()
        return Response({"message": "Agente deletado com sucesso."}, status=200)
    except Agente.DoesNotExist:
        return Response({"error": "Agente não encontrado."}, status=404)

@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def update_agent(request, id):
    """
    Atualiza um agente específico pelo ID (id).
    """
    try:
        agent = Agente.objects.get(id=id)
    except Agente.DoesNotExist:
        return Response({"error": "Agente não encontrado."}, status=404)

    serializer = AgenteSerializer(agent, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=200)
    return Response(serializer.errors, status=400)

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def list_user_agents(request):
    """Lista apenas os agentes que o usuário tem permissão para acessar"""
    user = request.user
    
    user_permissions = []
    
    # Verificar como as permissões estão estruturadas no modelo
    if hasattr(user, 'permissoes') and isinstance(user.permissoes, list):
        # Se permissões são armazenadas diretamente como lista
        user_permissions = user.permissoes
    else:
        # Buscar do relacionamento (mais comum em Django)
        user_data = Usuario.objects.filter(id=user.id).values('permissoes').first()
        if user_data and 'permissoes' in user_data:
            user_permissions = user_data['permissoes']
    
    # Filtrar apenas os agentes com permissão
    agents = Agente.objects.filter(id__in=user_permissions)
    
    serializer = AgenteSerializer(agents, many=True)
    return Response(serializer.data)

# Add this missing function
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def list_all_agents(request):
    """Lista todos os agentes disponíveis"""
    agents = Agente.objects.all()
    serializer = AgenteSerializer(agents, many=True)
    return Response(serializer.data)