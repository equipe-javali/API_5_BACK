from rest_framework import generics
from .models import Agente
from .serializers import AgenteSerializer

class AgenteCreateView(generics.CreateAPIView):
    queryset = Agente.objects.all()
    serializer_class = AgenteSerializer
