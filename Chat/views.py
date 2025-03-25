from rest_framework import generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .models import Chat, Mensagem
from .serializers import ChatSerializer, MensagemSerializer

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def chat_view(request):
    Usuario_id = request.data.get("Usuario_id")
    Agente_id = request.data.get("Agente_id")

    chat = Chat.objects.filter(Usuario_id=Usuario_id, Agente_id=Agente_id).first()
    if chat:
        serializer = ChatSerializer(chat)

        response_data = serializer.data
        mensagens = Mensagem.objects.filter(Chat_id=chat.id)
        response_data["mensagens"] = MensagemSerializer(mensagens, many=True).data
        return Response(response_data)
    
    serializer = ChatSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(Usuario_id=Usuario_id, Agente_id=Agente_id)

        response_data = serializer.data
        mensagens = Mensagem.objects.filter(Chat_id=chat.id)
        response_data["mensagens"] = MensagemSerializer(mensagens, many=True).data
        return Response(response_data, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def chat_enviar_mensagem(request):
    texto = request.data.get("texto")
    Chat_id = request.data.get("Chat_id")

    modified_data = request.data.copy()
    modified_data["usuario"] = True

    serializer = MensagemSerializer(data=modified_data)
    if serializer.is_valid():
        serializer.save(texto=texto, Chat_id=Chat_id)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
