from rest_framework import generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from .models import Chat, Mensagem
from .serializers import ChatSerializer, MensagemSerializer
from Modelo.services.ml_service import ModelService
from Agente.models import Agente
from Usuario.models import Usuario
from .models import Chat

@api_view(["POST"])
@permission_classes([AllowAny])
def iniciar_conversa(request):
    agenteId = request.data.get("agenteId")
    usuarioId = request.data.get("usuarioId")
    if not agenteId or not usuarioId:
        return Response({"error": "Parâmetros faltando."}, status=status.HTTP_400_BAD_REQUEST)
    try:
        agente = Agente.objects.get(id=agenteId)
        usuario = Usuario.objects.get(id=usuarioId)
        chat = Chat.objects.create_chat(Usuario_id=usuario, Agente_id=agente)
        return Response({"chat_id": chat.id}, status=status.HTTP_201_CREATED)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

# Modified to allow any user
@api_view(["POST"])
@permission_classes([AllowAny])
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
        novo_chat = serializer.save() # Armazene o chat criado em uma variável
        
        response_data = serializer.data
        # Use novo_chat.id em vez de chat.id
        mensagens = Mensagem.objects.filter(Chat_id=novo_chat.id)
        response_data["mensagens"] = MensagemSerializer(mensagens, many=True).data
        return Response(response_data, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# Modified to allow any user
@api_view(["POST"])
@permission_classes([AllowAny])
def chat_enviar_mensagem(request):
    try:
        texto = request.data.get("texto")
        Chat_id = request.data.get("Chat_id")
        
        print(f"DEBUG: Received message request with texto: {texto}, Chat_id: {Chat_id}")

        # Save user message
        modified_data = request.data.copy()
        modified_data["usuario"] = True

        serializer = MensagemSerializer(data=modified_data)
        if serializer.is_valid():
            print("DEBUG: User message serializer is valid")
            mensagem_usuario = serializer.save(texto=texto, Chat_id=Chat_id)
            print(f"DEBUG: Saved user message: {mensagem_usuario.id}")

            try:
                # Get the chat and agent
                chat = Chat.objects.get(id=Chat_id)
                print(f"DEBUG: Found chat: {chat.id}")
                agent_id = chat.Agente_id.id
                print(f"DEBUG: Found agent_id: {agent_id} for chat_id: {Chat_id}")
            except Exception as chat_error:
                print(f"ERROR retrieving chat: {str(chat_error)}")
                return Response({
                    "error": "Chat not found",
                    "details": str(chat_error)
                }, status=status.HTTP_404_NOT_FOUND)

            try:
                # Get AI response
                model_service = ModelService()
                print(f"DEBUG: Created ModelService instance")
                result = model_service.answer_question(agent_id, texto)
                print(f"DEBUG: Got result from answer_question: {result}")
            except Exception as model_error:
                print(f"ERROR in model service: {str(model_error)}")
                print(traceback.format_exc())
                return Response({
                    "error": "Model service error",
                    "details": str(model_error)
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            ai_response = result.get('answer')
            if not ai_response or ai_response.strip() == "":
                ai_response = "Desculpe, não consegui processar sua pergunta."
            
            print(f"DEBUG: AI response: {ai_response}")

            # Save AI response
            ai_message_data = {
                "texto": ai_response,
                "Chat_id": Chat_id,
                "usuario": False
            }

            ai_serializer = MensagemSerializer(data=ai_message_data)
            if ai_serializer.is_valid():
                ai_message = ai_serializer.save()
                print(f"DEBUG: Saved AI message: {ai_message.id}")

                # Return both messages
                return Response({
                    "user_message": serializer.data,
                    "ai_message": ai_serializer.data,
                    "confidence": result.get('confidence', 0),
                    "in_scope": result.get('in_scope', False)
                }, status=status.HTTP_201_CREATED)
            else:
                print(f"DEBUG: AI message serializer errors: {ai_serializer.errors}")
                return Response({
                    "error": "AI message serializer errors",
                    "details": ai_serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
        else:
            print(f"DEBUG: User message serializer errors: {serializer.errors}")
            return Response({
                "error": "User message serializer errors",
                "details": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        import traceback
        print(f"ERROR in chat_enviar_mensagem: {str(e)}")
        print(traceback.format_exc())
        return Response({
            "error": "Internal Server Error",
            "details": str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)