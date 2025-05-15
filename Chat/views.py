import os
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
import json
from django.core.cache import cache

# Configure a detecção de ambiente corretamente
IS_DEPLOY_ENVIRONMENT = os.getenv('RENDER', '').lower() == 'true'
print(f"Ambiente de deploy? {IS_DEPLOY_ENVIRONMENT}")

# Cache simples para histórico de chat
CACHE_TTL = 60 * 60  # 1 hora em segundos

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

        # Armazenar em cache para acesso rápido futuro
        cache_key = f"chat_history_{chat.id}"
        cache.set(cache_key, serializer_msgs.data, CACHE_TTL)

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

# Endpoint para obter histórico do chat
@api_view(["GET"])
@permission_classes([AllowAny])
def obter_historico_chat(request, chat_id):
    """
    Retorna o histórico de mensagens de um chat específico
    """
    try:
        # Verificar se temos em cache primeiro
        cache_key = f"chat_history_{chat_id}"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            print(f"Retornando histórico em cache para chat {chat_id}")
            return Response({
                "messages": cached_data,
                "from_cache": True
            })
            
        # Se não tiver em cache, buscar do banco
        chat = Chat.objects.get(id=chat_id)
        mensagens = Mensagem.objects.filter(Chat_id=chat)
        serializer = MensagemSerializer(mensagens, many=True)
        
        # Armazenar em cache
        cache.set(cache_key, serializer.data, CACHE_TTL)
        
        return Response({
            "messages": serializer.data,
            "from_cache": False
        })
    except Chat.DoesNotExist:
        return Response(
            {"error": f"Chat com ID {chat_id} não encontrado"}, 
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {"error": str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

# Classe para processamento de respostas via fallback local
class ModelService:
    def __init__(self):
        # Instanciar o serviço do Gemini com tratamento de falhas
        try:
            self.gemini_service = GeminiService()
            self.use_gemini = True
        except Exception as e:
            print(f"Erro ao inicializar GeminiService: {e}")
            self.use_gemini = False
        
    def answer_question(self, agent_id, question):
        """Responde uma pergunta usando o modelo Gemini ou fallback"""
        try:
            # Tenta usar o serviço Gemini se estiver disponível
            if self.use_gemini:
                return self.gemini_service.answer_question(agent_id, question)
            else:
                # Fallback para processamento local
                return self._fallback_answer(agent_id, question)
        except Exception as e:
            print(f"Erro ao processar pergunta: {e}")
            return {
                'success': False, 
                'error': str(e),
                'answer': 'Desculpe, estamos enfrentando problemas técnicos. Tente novamente mais tarde.'
            }
    
    def _fallback_answer(self, agent_id, question):
        """Método para gerar respostas quando o Gemini falha"""
        try:
            from Contexto.models import Contexto
            
            # Busca contextos do agente
            contextos = Contexto.objects.filter(Agente_id=agent_id)
            
            if not contextos.exists():
                return {'success': True, 'answer': 'Não tenho informações suficientes para responder.'}
            
            # Busca simples por palavras-chave
            keywords = [w.lower() for w in question.split() if len(w) > 3]
            best_match = None
            best_score = 0
            
            for ctx in contextos:
                score = 0
                for keyword in keywords:
                    if keyword in ctx.pergunta.lower():
                        score += 2
                    if keyword in ctx.resposta.lower():
                        score += 1
                
                if score > best_score:
                    best_score = score
                    best_match = ctx
            
            if best_match and best_score > 0:
                return {
                    'success': True,
                    'answer': best_match.resposta,
                    'confidence': 0.7
                }
            
            # Sem correspondência, retorna o primeiro contexto
            fallback = contextos.first()
            return {
                'success': True,
                'answer': f"Com base no que sei: {fallback.resposta}",
                'confidence': 0.5
            }
        except Exception as e:
            print(f"Erro no fallback: {e}")
            return {
                'success': False,
                'answer': 'Desculpe, não consegui processar sua pergunta.'
            }
    
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
    # Remova o código que causa o erro 503 em ambiente de produção
    # Vamos verificar se a API Gemini está disponível e usar fallback se necessário
    # em vez de retornar erro de manutenção

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
                # Obter resposta da IA usando o ModelService (que agora tem fallback robusto)
                model_service = ModelService()
                print(f"DEBUG: Created ModelService instance")
                result = model_service.answer_question(agent_id, texto)
                print(f"DEBUG: Got result from answer_question: {result}")
            except Exception as model_error:
                print(f"ERROR in model service: {str(model_error)}")
                import traceback
                print(traceback.format_exc())
                
                # Em caso de erro no serviço de IA, usar resposta padrão
                result = {
                    'answer': 'Desculpe, não consegui processar sua pergunta neste momento.'
                }

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
            
            # Invalidar o cache para este chat
            cache_key = f"chat_history_{Chat_id}"
            cache.delete(cache_key)
            
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