from rest_framework import serializers
from .models import Chat, Mensagem
from Usuario.models import Usuario
from Agente.models import Agente

class ChatSerializer(serializers.ModelSerializer):
    class Meta:
        model = Chat
        fields = ["Usuario_id", "Agente_id"]

    def create(self, validated_data):
        validated_data["Usuario_id"] = Usuario.objects.get(id=validated_data["Usuario_id"])
        validated_data["Agente_id"] = Agente.objects.get(id=validated_data["Agente_id"])
        chat = Chat.objects.create_chat(**validated_data)
        return chat

class MensagemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Mensagem
        fields = ["texto", "Chat_id", "usuario"]

    def create(self, validated_data):
        # Check if Chat_id is already a Chat object
        if not isinstance(validated_data["Chat_id"], Chat):
            chat = Chat.objects.get(id=validated_data["Chat_id"])
            validated_data["Chat_id"] = chat
        
        mensagem = Mensagem.objects.create_mensagem(**validated_data)
        return mensagem