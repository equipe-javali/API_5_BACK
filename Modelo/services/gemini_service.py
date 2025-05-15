try:
    import google.generativeai as genai
except ImportError:
    print("AVISO: Biblioteca google.generativeai não encontrada. Usando modo fallback.")
    genai = None

import traceback
import os
from django.conf import settings
from Contexto.models import Contexto
from Agente.models import Agente
from django.core.cache import cache

class GeminiService:
    def __init__(self):
        try:
            # Melhor detecção de ambiente Render
            self.is_deploy_environment = os.environ.get('RENDER', '').lower() == 'true'
            print(f"Ambiente de deploy? {'Sim' if self.is_deploy_environment else 'Não'}")
            
            # Se genai não está disponível, desabilita o serviço
            if genai is None:
                print("Modo fallback ativado: API Gemini não disponível")
                self.api_configured = False
                return
                
            # Verificação de segurança para a chave API
            if not hasattr(settings, 'GEMINI_API_KEY') or not settings.GEMINI_API_KEY:
                print("ALERTA: GEMINI_API_KEY não encontrada em settings.py")
                self.api_configured = False
                return
                
            # Configuração da API
            genai.configure(api_key=settings.GEMINI_API_KEY)
            
            # IMPORTANTE: No deploy, SEMPRE usar o modelo mais leve
            if self.is_deploy_environment:
                self.model_name = "gemini-1.5-flash"  # Modelo mais leve em produção
            else:
                self.model_name = "gemini-1.5-flash"  # Mesmo modelo em dev
            
            print(f"Usando modelo: {self.model_name}")
            self.model = genai.GenerativeModel(self.model_name)
            self.api_configured = True
            print("Serviço Gemini inicializado com sucesso")
            
        except Exception as e:
            print(f"Erro ao inicializar GeminiService: {e}")
            traceback.print_exc()
            self.api_configured = False

    def answer_question(self, agent_id, question):
        """Método principal com cache e proteção adicional"""
        # Verificar se a resposta está em cache
        cache_key = f"gemini_response_{agent_id}_{hash(question)}"
        cached_response = cache.get(cache_key)
        
        if cached_response:
            print(f"Usando resposta em cache para agente {agent_id}")
            return cached_response
            
        # Verifica se o API está configurada
        if not self.api_configured:
            return self._generate_fallback_response(agent_id, question)
                       
        try:
            # Busca informações do agente
            try:
                agent = Agente.objects.get(id=agent_id)
                agent_name = agent.nome
            except Agente.DoesNotExist:
                print(f"Agente ID {agent_id} não encontrado")
                agent_name = "Assistente"
            
            # Busca todos os contextos deste agente
            contexts = Contexto.objects.filter(Agente_id=agent_id)
            print(f"Encontrados {contexts.count()} contextos para o agente {agent_id}")
            
            # Se não tivermos contextos, usar resposta padrão
            if contexts.count() == 0:
                return {
                    'success': True, 
                    'answer': 'Desculpe, não tenho informações suficientes para responder a essa pergunta.'
                }
            
            # Limitar o número de contextos para reduzir tokens
            relevant_contexts = self._find_relevant_contexts(contexts, question, limit=3)
            context_text = "\n\n".join([
                f"Pergunta: {ctx.pergunta}\nResposta: {ctx.resposta}" 
                for ctx in relevant_contexts
            ])
            
            # Construir o prompt para o Gemini (mais enxuto)
            prompt = f"""
            Você é {agent_name}.
            
            CONTEXTO:
            {context_text}
            
            Responda à pergunta abaixo usando apenas o contexto acima:
            Pergunta: {question}
            
            Se não souber, apenas diga que não tem essa informação.
            """
            
            print(f"Enviando prompt para o modelo {self.model_name}")
            
            # Tentar gerar resposta com parâmetros de geração mais econômicos
            completion = self.model.generate_content(
                prompt,
                generation_config={
                    "temperature": 0.2,
                    "max_output_tokens": 200,  # Limitar tamanho da resposta
                }
            )
            
            if hasattr(completion, 'text'):
                answer = completion.text.strip()
                print(f"Resposta do Gemini recebida com sucesso ({len(answer)} caracteres)")
                
                result = {
                    'success': True,
                    'answer': answer,
                    'confidence': 0.95,
                    'in_scope': True
                }
                
                # Armazenar em cache por 1 hora
                cache.set(cache_key, result, 60 * 60)
                
                return result
            else:
                print(f"Formato inesperado de resposta do Gemini: {completion}")
                return self._generate_fallback_response(agent_id, question, contexts)
            
        except Exception as e:
            print(f"Erro ao gerar resposta com Gemini: {e}")
            traceback.print_exc()
            
            # Se for erro de quota, use respostas do contexto diretamente
            if "quota" in str(e).lower() or "429" in str(e):
                return self._generate_fallback_response(agent_id, question, contexts)
            
            return {
                'success': False,
                'error': str(e),
                'answer': 'Ocorreu um erro ao processar sua pergunta. Tente novamente mais tarde.'
            }
    
    def _find_relevant_contexts(self, contexts, question, limit=3):
        """Encontra os contextos mais relevantes para uma pergunta"""
        question_words = set(word.lower() for word in question.split() if len(word) > 3)
        
        scored_contexts = []
        for ctx in contexts:
            score = 0
            ctx_words = set(word.lower() for word in ctx.pergunta.split() if len(word) > 3)
            # Calcular palavras em comum
            common_words = question_words.intersection(ctx_words)
            score = len(common_words)
            
            # Verificar palavras na resposta também
            for word in question_words:
                if word in ctx.resposta.lower():
                    score += 0.5
                    
            scored_contexts.append((ctx, score))
        
        # Ordenar por pontuação (maior primeiro) e pegar os primeiros 'limit'
        sorted_contexts = sorted(scored_contexts, key=lambda x: x[1], reverse=True)
        return [ctx for ctx, _ in sorted_contexts[:limit]]
    
    def _generate_fallback_response(self, agent_id, question, contexts=None):
        """Método para gerar respostas de fallback quando a API falha"""
        try:
            # Busca simples por palavras-chave no contexto
            if contexts is None:
                contexts = Contexto.objects.filter(Agente_id=agent_id)
                
            if contexts.count() == 0:
                return {
                    'success': True,
                    'fallback': True,
                    'answer': 'Não tenho informações suficientes para responder a essa pergunta.'
                }
            
            # Reuso do método para encontrar contextos relevantes
            relevant_contexts = self._find_relevant_contexts(contexts, question, limit=1)
            
            if relevant_contexts:
                best_match = relevant_contexts[0]
                return {
                    'success': True,
                    'fallback': True,
                    'answer': best_match.resposta,
                    'confidence': 0.7,
                    'in_scope': True
                }
            
            # Fallback final - retornar qualquer contexto
            random_ctx = contexts.first()
            return {
                'success': True,
                'fallback': True,
                'answer': f"Com base no que sei: {random_ctx.resposta}",
                'confidence': 0.5,
                'in_scope': False
            }
            
        except Exception as fallback_error:
            print(f"Erro no fallback: {fallback_error}")
            return {
                'success': False,
                'error': str(fallback_error),
                'answer': 'Nosso serviço está temporariamente indisponível. Por favor, tente novamente mais tarde.'
            }