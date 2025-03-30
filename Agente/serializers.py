from rest_framework import serializers
from .models import Agente
from Permissao.models import Permissao
from rest_framework.exceptions import ValidationError

class AgenteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Agente
        fields = ["id", "nome", "descricao", "Permissao_id"]  # include id here

    def validate_Permissao_id(self, value):
        try:
            permission = Permissao.objects.get(id=value.id)
            return value
        except Permissao.DoesNotExist:
            raise ValidationError(f"A permissão com ID {value.id} não existe. Crie a permissão primeiro.")

    def create(self, validated_data):
        agente = Agente.objects.create_agente(**validated_data)
        return agente