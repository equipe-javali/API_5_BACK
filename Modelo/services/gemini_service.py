import google.generativeai as genai
import traceback
import os
from django.conf import settings
from Contexto.models import Contexto
from Agente.models import Agente

class GeminiService:
    def __init__(self):
        try:
            # Melhor detecção de ambiente Render
            self.is_deploy_environment = os.environ.get('RENDER', '').lower() == 'true'
            print(f"Ambiente de deploy? {'Sim' if self.is_deploy_environment else 'Não'}")
            
            # Verificação de segurança para a chave API
            if not hasattr(settings, 'GEMINI_API_KEY') or not settings.GEMINI_API_KEY:
                print("ALERTA: GEMINI_API_KEY não encontrada em settings.py")
                self.api_configured = False
                return
                
            # Configuração da API
            genai.configure(api_key=settings.GEMINI_API_KEY)
            
            # Lista todos os modelos disponíveis (para debug)
            try:
                models = genai.list_models()
                print("Listando modelos disponíveis na API Gemini:")
                for model in models:
                    print(f"- Modelo: {model.name}")
            except Exception as e:
                print(f"Erro ao listar modelos: {e}")
            
            # IMPORTANTE: No deploy, SEMPRE usar o modelo mais leve
            if self.is_deploy_environment:
                self.model_name = "gemini-1.5-flash"  # Modelo mais leve em produção
            else:
                self.model_name = "gemini-1.5-flash"  # Temporariamente usar o mesmo modelo leve em dev também
            
            print(f"Usando modelo: {self.model_name}")
            self.model = genai.GenerativeModel(self.model_name)
            self.api_configured = True
            print("Serviço Gemini inicializado com sucesso")
            
        except Exception as e:
            print(f"Erro ao inicializar GeminiService: {e}")
            traceback.print_exc()
            self.api_configured = False

    def answer_question(self, agent_id, question):
        """Método principal com proteção adicional"""
        # Contadores de erro para telemetria
        error_count = getattr(self, '_error_count', 0)
        
        # Verifica se o API está configurada
        if not self.api_configured:
            return {
                'success': False,
                'error': 'API Gemini não configurada',
                'answer': "Desculpe, o serviço de IA não está disponível no momento."
            }           
            
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
            
            # Prepara o contexto para o prompt (limitando o tamanho para reduzir tokens)
            context_data = []
            for ctx in contexts:
                context_data.append(f"Pergunta: {ctx.pergunta}\nResposta: {ctx.resposta}")
            
            # Limitar o número de contextos para economizar tokens
            if len(context_data) > 3:
                context_data = context_data[:3]  # Usar apenas os 3 primeiros contextos
                
            context_text = "\n\n".join(context_data)
            
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
                # Resetar contador de erros
                self._error_count = 0
                return {
                    'success': True,
                    'answer': answer,
                    'confidence': 0.95,
                    'in_scope': True
                }
            else:
                print(f"Formato inesperado de resposta do Gemini: {completion}")
                return self._generate_fallback_response(agent_id, question, contexts)
            
        except Exception as e:
            # Incrementar contador de erros
            self._error_count = error_count + 1
            print(f"Erro ao gerar resposta com Gemini ({self._error_count}): {e}")
            traceback.print_exc()
            
            # Se for erro de quota, use respostas do contexto diretamente
            if "quota" in str(e).lower() or "429" in str(e):
                return self._generate_fallback_response(agent_id, question, contexts)
            
            return {
                'success': False,
                'error': str(e),
                'answer': 'Ocorreu um erro ao processar sua pergunta. Tente novamente mais tarde.'
            }
    
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
                
            # Busca por palavras-chave (mais de 3 letras)
            keywords = [w.lower() for w in question.split() if len(w) > 3]
            
            # Se não houver palavras-chave significativas, usar resposta genérica
            if not keywords:
                random_ctx = contexts.first()
                return {
                    'success': True,
                    'fallback': True,
                    'answer': f"Aqui está uma informação que pode ajudar: {random_ctx.resposta}"
                }
            
            # Buscar contexto mais relevante
            best_match = None
            best_score = 0
            
            for ctx in contexts:
                # Calcular pontuação de relevância
                score = 0
                for keyword in keywords:
                    if keyword in ctx.pergunta.lower():
                        score += 2  # Maior peso para match na pergunta
                    if keyword in ctx.resposta.lower():
                        score += 1
                
                if score > best_score:
                    best_score = score
                    best_match = ctx
            
            # Se encontrou alguma correspondência
            if best_match and best_score > 0:
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