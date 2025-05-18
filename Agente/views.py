from rest_framework import generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Agente
from Contexto.models import Contexto
from django.contrib.auth import get_user_model
Usuario = get_user_model()
from .serializers import AgenteSerializer

from rest_framework import status
from Chat.models import Chat, Mensagem
from datetime import datetime, timedelta

class AgenteCreateView(generics.CreateAPIView):
    queryset = Agente.objects.all()
    serializer_class = AgenteSerializer

class AgenteDeleteView(generics.DestroyAPIView):
    """
    Classe para deletar um agente específico.
    """
    queryset = Agente.objects.all()
    serializer_class = AgenteSerializer
    permission_classes = [IsAuthenticated]

class AgenteUpdateView(generics.UpdateAPIView):
    """
    Classe para atualizar um agente específico.
    """
    queryset = Agente.objects.all()
    serializer_class = AgenteSerializer
    permission_classes = [IsAuthenticated]

@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_agent(request, id):
    """
    Deleta um agente específico pelo ID (id), incluindo seus contextos e chats.
    """
    try:
        agent = Agente.objects.get(id=id)
               
        from Chat.models import Chat, Mensagem                 
        chats = Chat.objects.filter(Agente_id=agent)
        chats_count = chats.count()
        
        # Para cada chat, exclua todas as mensagens associadas
        mensagens_count = 0
        for chat in chats:
            # Exclua as mensagens associadas ao chat
            
            try:                
                chat_mensagens = Mensagem.objects.filter(Chat_id=chat)
                mensagens_count += chat_mensagens.count()
                chat_mensagens.delete()
            except:
                try:
                    chat_mensagens = Mensagem.objects.filter(chat=chat)
                    mensagens_count += chat_mensagens.count()
                    chat_mensagens.delete()
                except Exception as msg_err:
                    print(f"Erro ao excluir mensagens: {str(msg_err)}")
        
        # Excluir os chats
        chats.delete()
        
        # Excluir os contextos associados
        contextos_count = Contexto.objects.filter(Agente_id=agent).count()
        Contexto.objects.filter(Agente_id=agent).delete()
        
        # Excluir o agente
        agent_name = agent.nome
        agent.delete()
        
        return Response({
            "message": f"Agente '{agent_name}' excluído com sucesso junto com {contextos_count} contextos, {chats_count} chats e {mensagens_count} mensagens."
        }, status=200)
    except Agente.DoesNotExist:
        return Response({"error": "Agente não encontrado."}, status=404)
    except Exception as e:
        return Response({"error": f"Erro ao excluir agente: {str(e)}"}, status=500)

@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def update_agent(request, id):
    """
    Atualiza um agente específico pelo ID (id).
    """
    try:
        agent = Agente.objects.get(id=id)
    except Agente.DoesNotExist:
        return Response({"error": "Agente não encontrado."}, status=404)

    serializer = AgenteSerializer(agent, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=200)
    return Response(serializer.errors, status=400)

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def list_user_agents(request):
    """Lista apenas os agentes que o usuário tem permissão para acessar"""
    user = request.user
    
    # Obter as permissões do usuário (IDs dos agentes permitidos)
    user_permissions = []
    
    # Verificar como as permissões estão estruturadas no modelo
    if hasattr(user, 'permissoes') and isinstance(user.permissoes, list):
        # Se permissões são armazenadas diretamente como lista
        user_permissions = user.permissoes
    else:
        # Buscar do relacionamento (mais comum em Django)
        user_data = Usuario.objects.filter(id=user.id).values('permissoes').first()
        if user_data and 'permissoes' in user_data:
            user_permissions = user_data['permissoes']
    
    # Filtrar apenas os agentes com permissão
    agents = Agente.objects.filter(id__in=user_permissions)
    
    serializer = AgenteSerializer(agents, many=True)
    return Response(serializer.data)

# Add this missing function
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def list_all_agents(request):
    """Lista todos os agentes disponíveis"""
    agents = Agente.objects.all()
    serializer = AgenteSerializer(agents, many=True)
    return Response(serializer.data)

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def tempo_resposta_metricas(request):
    """
    Calcula o tempo médio de resposta dos agentes.
    Filtros: agente_id, inicio, fim (datas)
    """
    agente_id = request.GET.get("agente_id")
    inicio = request.GET.get("inicio")
    fim = request.GET.get("fim")

    mensagens = Mensagem.objects.all().order_by("Chat_id", "dataCriacao")

    if agente_id:
        chats = Chat.objects.filter(Agente_id=agente_id)
        mensagens = mensagens.filter(Chat_id__in=chats)
    if inicio:
        mensagens = mensagens.filter(dataCriacao__gte=inicio)
    if fim:
        mensagens = mensagens.filter(dataCriacao__lte=fim)

    tempos_resposta = []
    mensagens = list(mensagens)

    for i, msg in enumerate(mensagens):
        if msg.usuario:  # mensagem do usuário
            # Procura a próxima mensagem do agente no mesmo chat
            for next_msg in mensagens[i+1:]:
                if next_msg.Chat_id_id == msg.Chat_id_id and not next_msg.usuario:
                    diff = (next_msg.dataCriacao - msg.dataCriacao).total_seconds()
                    if diff >= 0:
                        tempos_resposta.append(diff)
                    break

    tempo_medio = sum(tempos_resposta) / len(tempos_resposta) if tempos_resposta else 0

    return Response({
        "tempo_medio": round(tempo_medio, 2),
        "quantidade": len(tempos_resposta)
    })