from rest_framework import serializers
from .models import Contexto
from Agente.models import Agente

class ContextoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contexto
        fields = ["pergunta", "resposta", "Agente_id"]

    def create(self, validated_data):
        contexto = Contexto.objects.create_contexto(**validated_data)
        return contexto