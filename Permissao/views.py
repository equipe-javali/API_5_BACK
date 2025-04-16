from rest_framework import generics
from .models import Permissao
from .serializers import PermissaoSerializer

class PermissaoCreateView(generics.CreateAPIView):
    queryset = Permissao.objects.all()
    serializer_class = PermissaoSerializer
