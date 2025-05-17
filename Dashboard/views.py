from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from Chat.models import Chat, Mensagem
from Agente.models import Agente
import nltk
nltk.download('stopwords')
from rake_nltk import Rake
from nltk.corpus import stopwords
import re


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def media_mensagens_por_agente(request):
    dados = {"agentes": dict()}

    agentes = Agente.objects.all()
    for agente in agentes:
        dados["agentes"][str(agente.id)] = {"media_de_mensagens_por_usuario": 0}
        mensagens_por_chat = list()

        chats = Chat.objects.filter(Agente_id=agente.id)
        for chat in chats:
            mensagens = Mensagem.objects.filter(Chat_id=chat.id).filter(usuario=False)
            mensagens_por_chat.append(len(mensagens))

        dados["agentes"][str(agente.id)]["media_de_mensagens_por_usuario"] = sum(mensagens_por_chat) // len(mensagens_por_chat)
    
    return Response(dados)

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def topico_mais_comum_por_agente(request):
    rake = Rake(language='portuguese', stopwords=stopwords.words("portuguese"))

    def limpar_frases(frases):
        frases_limpas = []
        padrao_irrelevante = re.compile(r"^(quero|saber|pode|olá|tudo bem|boa tarde|bom dia|ajudar|teste|(:)|x)$", re.IGNORECASE)
        for frase in frases:
            if not padrao_irrelevante.match(frase.strip()):
                frases_limpas.append(frase)
        return frases_limpas

    def extrair_palavras_chave(texto, min_score = 0.3):
        rake.extract_keywords_from_text(texto)
        termos = []
        for score, frase in rake.get_ranked_phrases_with_scores():
            try:
                if float(score) >= min_score:
                    termos.append(frase)
            except ValueError:
                continue
        return termos

    dados = {"agentes": dict()}
    for agente in Agente.objects.all():
        dados["agentes"][str(agente.id)] = {"usuarios": dict()}
        for chat in Chat.objects.filter(Agente_id=agente.id):
            mensagens = Mensagem.objects.filter(Chat_id=chat.id).filter(usuario=True)
            if len(mensagens) < 1:
                continue

            termos = [extrair_palavras_chave(msg.texto) for msg in mensagens]
            termos = sum([limpar_frases(termo) for termo in termos], [])
            termos.sort(key=lambda x: len(x), reverse=True)
            
            dados["agentes"][str(agente.id)]["usuarios"][str(chat.Usuario_id.id)] = termos[:10]

    return Response(dados)
