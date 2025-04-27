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
from Modelo.services.gemini_service import GeminiService

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
        # se já existir, não cria de novo
        chat, created = Chat.objects.get_or_create(
            Usuario_id=usuario,
            Agente_id=agente
        )

        # buscar todo o histórico desse chat
        mensagens = Mensagem.objects.filter(Chat_id=chat)
        serializer_msgs = MensagemSerializer(mensagens, many=True)

        return Response({
            "chat_id": chat.id,
            "messages": serializer_msgs.data,
            "created": created
        }, status=status.HTTP_200_OK)

    except Agente.DoesNotExist:
        return Response({"error": "Agente não encontrado."},
                        status=status.HTTP_404_NOT_FOUND)
    except Usuario.DoesNotExist:
        return Response({"error": "Usuário não encontrado."},
                        status=status.HTTP_404_NOT_FOUND)
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


class ModelService:
    def __init__(self):
        # Instanciar o serviço do Gemini
        self.gemini_service = GeminiService()
        
    def answer_question(self, agent_id, question):
        """Responde uma pergunta usando o modelo Gemini"""
        # Use o serviço Gemini para responder
        return self.gemini_service.answer_question(agent_id, question)
    
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def listar_chatbots(request):
    """
    Retorna os chatbots pertencentes ao usuário autenticado.
    """
    if request.user.is_staff:
        # Administradores podem acessar todos os chatbots
        chatbots = Chat.objects.all()
    else:
        # Usuários comuns acessam apenas seus próprios chatbots
        chatbots = Chat.objects.filter(Usuario_id=request.user.id)

    serializer = ChatSerializer(chatbots, many=True)
    return Response(serializer.data)

@api_view(["POST"])
@permission_classes([AllowAny])
def chat_enviar_mensagem(request):
    try:
        texto = request.data.get("texto")
        Chat_id = request.data.get("Chat_id")
        
        print(f"DEBUG: Received message request with texto: {texto}, Chat_id: {Chat_id}")

        # Salvar mensagem do usuário
        modified_data = request.data.copy()
        modified_data["usuario"] = True

        serializer = MensagemSerializer(data=modified_data)
        if serializer.is_valid():
            print("DEBUG: User message serializer is valid")
            mensagem_usuario = serializer.save(texto=texto, Chat_id=Chat_id)
            print(f"DEBUG: Saved user message: {mensagem_usuario.id}")

            try:
                # Obter o chat e o agente
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
                # Obter resposta da IA usando o ModelService (que agora integra Gemini)
                model_service = ModelService()
                print(f"DEBUG: Created ModelService instance")
                result = model_service.answer_question(agent_id, texto)
                print(f"DEBUG: Got result from answer_question: {result}")
            except Exception as model_error:
                print(f"ERROR in model service: {str(model_error)}")
                import traceback
                print(traceback.format_exc())
                return Response({
                    "error": "Model service error",
                    "details": str(model_error)
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            # Obter a resposta a partir do resultado
            ai_response = result.get('answer', '')
            if not ai_response or ai_response.strip() == "":
                ai_response = "Desculpe, não consegui processar sua pergunta."
            
            # Salvar resposta da IA
            ai_message = Mensagem.objects.create(
                texto=ai_response,
                Chat_id=chat,
                usuario=False
            )
            
            return Response({
                "success": True,
                "user_message": MensagemSerializer(mensagem_usuario).data,
                "ai_message": MensagemSerializer(ai_message).data
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

