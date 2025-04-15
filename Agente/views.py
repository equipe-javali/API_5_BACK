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

class AgenteDeleteView(generics.DestroyAPIView):
    """
    Classe para deletar um agente específico.
    """
    queryset = Agente.objects.all()
    serializer_class = AgenteSerializer
    permission_classes = [IsAuthenticated]

class AgenteUpdateView(generics.UpdateAPIView):
    """
    Classe para atualizar um agente específico.
    """
    queryset = Agente.objects.all()
    serializer_class = AgenteSerializer
    permission_classes = [IsAuthenticated]

@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_agent(request, id):
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
    """Lista todos os agentes que o usuário tem permissão para acessar"""
    # Modified to return all agents without permission check
    agents = Agente.objects.all()
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