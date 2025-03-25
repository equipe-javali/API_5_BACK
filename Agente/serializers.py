from rest_framework import serializers
from .models import Agente

class AgenteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Agente
        fields = ["nome", "descricao", "Permissao_id"]

    def create(self, validated_data):
        agente = Agente.objects.create_agente(**validated_data)
        return agente