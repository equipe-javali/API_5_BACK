from rest_framework import serializers
from .models import TrainedModel

class TrainedModelSerializer(serializers.ModelSerializer): 
    Agente_nome = serializers.CharField(source="Agente_id.nome", read_only=True) 
    class Meta: 
        model = TrainedModel 
        fields = ["id", 
                "Agente_nome", 
                "created_at", 
                "examples_count", 
                "performance_score", 
                "is_active"] 