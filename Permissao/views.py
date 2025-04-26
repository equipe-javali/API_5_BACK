from rest_framework import generics
from .models import Permissao
from .serializers import PermissaoSerializer
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes

class PermissaoCreateView(generics.CreateAPIView):
    queryset = Permissao.objects.all()
    serializer_class = PermissaoSerializer

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def buscar_permissao(request):
    """
    Busca permissões pelo nome
    """
    nome = request.GET.get('nome')
    if not nome:
        return Response({"error": "Nome não fornecido"}, status=400)
    
    permissoes = Permissao.objects.filter(nome=nome)
    serializer = PermissaoSerializer(permissoes, many=True)
    return Response(serializer.data)
