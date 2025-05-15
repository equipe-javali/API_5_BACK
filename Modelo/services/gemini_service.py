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
import random
from datetime import datetime

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
            
            # Lista modelos disponíveis para diagnóstico
            try:
                if not self.is_deploy_environment:
                    print("Listando modelos disponíveis na API Gemini:")
                    for model in genai.list_models():
                        print(f"- Modelo: {model.name}")
                
                # Em produção, usar um modo econômico que limita chamadas
                if self.is_deploy_environment:
                   
                    self.api_usage_probability = 0.50  # Apenas 50% das solicitações usam a API
                    print(f"Modo econômico ativado: {int(self.api_usage_probability * 100)}% de uso da API")
                    self.model_name = "gemini-1.5-flash"  # Modelo mais econômico
                    
                    # Cache de longa duração em produção
                    self.cache_ttl = 60 * 60 * 24 * 7 * 14  # 7 dias
                    
                else:
                    # Em ambiente de desenvolvimento, usar a API normalmente
                    self.api_usage_probability = 1.0  # 100% das solicitações
                    
                    # Detectar modelo disponível
                    model_names = [m.name for m in genai.list_models()]
                    
                    # Prioridades de modelo
                    if any("gemini-1.5-pro" in name for name in model_names):
                        self.model_name = "gemini-1.5-pro"
                    elif any("gemini-1.0-pro" in name for name in model_names):
                        self.model_name = "gemini-1.0-pro"
                    elif any("gemini-pro" in name for name in model_names):
                        self.model_name = "gemini-pro"
                    else:
                        # Usar o primeiro modelo que suporta generateContent
                        for model in genai.list_models():
                            if hasattr(model, "supported_generation_methods") and "generateContent" in model.supported_generation_methods:
                                self.model_name = model.name
                                break
                        else:
                            raise ValueError("Nenhum modelo compatível encontrado")
                    
                    # Cache curto em desenvolvimento
                    self.cache_ttl = 60 * 30  # 30 minutos
                
                print(f"Usando modelo: {self.model_name}")
                self.model = genai.GenerativeModel(self.model_name)

                self.request_timeout = 10.0  # 5 segundos de timeout
                print(f"Timeout configurado: {self.request_timeout}s")
                
            except Exception as model_error:
                print(f"Erro ao listar modelos: {model_error}")
                # Tentar usar o modelo padrão como fallback
                self.model_name = "gemini-1.5-flash"
                print(f"Tentando usar modelo padrão: {self.model_name}")
                self.model = genai.GenerativeModel(self.model_name)
            
            self.api_configured = True
            print("Serviço Gemini inicializado com sucesso")
            
        except Exception as e:
            print(f"Erro ao inicializar GeminiService: {e}")
            traceback.print_exc()
            self.api_configured = False
    
    def enhance_response(self, original_response, question, agent_name=None):
        """
        Melhora a resposta original usando o Gemini para torná-la mais conversacional
        """
        if not self.api_configured:
            print("API do Gemini não configurada. Retornando resposta original.")
            return original_response
        
        # Em produção, usar cache e economizar API
        if self.is_deploy_environment:
            # Gerar um cache_key baseado na pergunta e resposta
            cache_key = f"enhance_{hash(question + original_response)}"
            cached_response = cache.get(cache_key)
            
            if cached_response:
                print("Usando resposta aprimorada do cache")
                return cached_response
            
            # Aplicar probabilidade de uso da API para economizar
            if random.random() > self.api_usage_probability:
                print("Modo econômico: pulando aprimoramento via API")
                return original_response
        
        try:
            # Construir o prompt para o Gemini            
            
            prompt = f"""
            Você é um assistente de IA chamado {agent_name or 'Assistente'}.
            
            A seguinte pergunta foi feita: "{question}"
            
            A resposta técnica é: "{original_response}"
            
            INSTRUÇÕES:
            1. Reescreva esta resposta em tom conversacional e natural, mantendo TODAS as informações técnicas originais.
            2. Adicione saudações amigáveis e elementos de diálogo natural.
            3. NÃO adicione informações que não estavam na resposta original.
            4. Use linguagem cordial e acessível, como se estivesse em uma conversa real.
            5. Responda em português do Brasil com fluidez e clareza.
            6. Se a resposta original menciona limitações de conhecimento, mantenha essa informação mas expresse de forma empática.
            """
            
            # Gerar resposta aprimorada com o Gemini
            completion = self.model.generate_content(
                prompt,
                generation_config={
                    "temperature": 0.2,
                    "max_output_tokens": 200,  # Limitar tamanho da resposta
                }
            )
            
            # Verificar e retornar a resposta
            if hasattr(completion, 'text'):
                enhanced_response = completion.text.strip()
                
                # Guardar no cache para uso futuro
                if self.is_deploy_environment:
                    cache.set(cache_key, enhanced_response, self.cache_ttl)
                
                return enhanced_response
            else:
                print(f"Formato de resposta inesperado: {type(completion)}")
                return original_response
                
        except Exception as e:
            print(f"Erro ao melhorar resposta com Gemini: {e}")
            traceback.print_exc()
            return original_response

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
        
        # Em produção, aplicar a probabilidade para economizar API
        if self.is_deploy_environment and random.random() > self.api_usage_probability:
            print("Modo econômico: usando fallback para economizar API")
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
            Você é {agent_name}, um assistente de IA amigável e eficiente.

            CONTEXTO AUTORIZADO (USE APENAS ESTAS INFORMAÇÕES):
            {context_text}
           

            Pergunta do usuário: {question}
           
             Se a resposta não estiver no contexto, responda educadamente que não possui essa informação e que a pessoa deverá contatar o setor responsável.
            Responda em português do Brasil de forma natural e conversacional.
            """
                
            print(f"Enviando prompt para o modelo {self.model_name}")
            
                        
            try:
                # Adicionar tratamento específico de timeout
                import asyncio
                from concurrent.futures import TimeoutError
                
                try:
                    start_time = datetime.now()
                    
                    # Configurar o modelo com timeout mais rigoroso
                    completion = self.model.generate_content(
                        prompt,
                        generation_config={
                            "temperature": 0.1,
                            "max_output_tokens": 150,
                            "top_p": 0.8,
                            "top_k": 20,
                        }
                    )
                    
                    elapsed = (datetime.now() - start_time).total_seconds()
                    if elapsed > self.request_timeout:
                        print(f"Tempo de resposta excedeu limite: {elapsed:.2f}s > {self.request_timeout:.2f}s")
                        return {
                            'success': True,
                            'fallback': True,
                            'timeout': True,
                            'answer': 'Este assunto deve ser direcionado ao setor responsável, pois não tenho informações suficientes a respeito.'
                        }
                        
                except (TimeoutError, asyncio.TimeoutError, Exception) as timeout_error:
                    print(f"Timeout ou erro ao gerar resposta: {timeout_error}")
                    return {
                        'success': True,
                        'fallback': True,
                        'timeout': True,
                        'answer': 'Este assunto deve ser direcionado ao setor responsável, pois não tenho informações suficientes a respeito.'
                    }
            except Exception as e:
                print(f"Erro ao configurar timeout: {e}")
                return self._generate_fallback_response(agent_id, question, contexts)
                    
            if hasattr(completion, 'text'):
                answer = completion.text.strip()
                print(f"Resposta do Gemini recebida com sucesso ({len(answer)} caracteres)")
                
                result = {
                    'success': True,
                    'answer': answer,
                    'confidence': 0.95,
                    'in_scope': True
                }
                
                # Armazenar em cache por mais tempo em produção
                cache.set(cache_key, result, self.cache_ttl)
                
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
    
    def _find_relevant_contexts(self, contexts, question, limit=2):  # Reduzir de 3 para 2
        """Encontra os contextos mais relevantes para uma pergunta"""
        context_cache_key = f"relevant_contexts_{hash(question)}"
        cached_contexts = cache.get(context_cache_key)
        if cached_contexts:
            print("Usando contextos relevantes do cache")
            return cached_contexts
        
        # Otimização: processamento mais eficiente de palavras-chave
        question_words = set(word.lower() for word in question.split() 
                            if len(word) > 3 and word.lower() not in 
                            {'como', 'qual', 'quem', 'onde', 'quando', 'para', 'sobre'})        
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
        result = [ctx for ctx, _ in sorted_contexts[:limit]]
        cache.set(context_cache_key, result, 60 * 60 * 24)  # 24 horas
        return result
    
    # Modifique o método _generate_fallback_response nas linhas 306-366:
    
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
                    'answer': 'Este assunto deve ser direcionado ao setor responsável, pois não tenho informações suficientes a respeito.'
                }
            
            # Utiliza a abordagem do código fornecido que corrige problemas de escopo
            keywords = [w.lower() for w in question.split() if len(w) > 3]
            
            # Se não tiver palavras-chave significativas, não tente responder
            if len(keywords) < 1:
                return {
                    'success': True,
                    'fallback': True,
                    'answer': 'Este assunto deve ser direcionado ao setor responsável, pois não tenho informações suficientes a respeito.'
                }
            
            best_matches = []
            for ctx in contexts:
                matches = 0
                for keyword in keywords:
                    if keyword in ctx.pergunta.lower():
                        matches += 2.0  # Dar maior peso a correspondências na pergunta
                    elif keyword in ctx.resposta.lower():
                        matches += 0.5
                
                if matches > 0:
                    best_matches.append((ctx, matches))
            
            # Se encontrou correspondências
            if best_matches:
                # Ordenar pelo número de correspondências (maior primeiro)
                best_matches.sort(key=lambda x: x[1], reverse=True)
                best_ctx = best_matches[0][0]
                
                # ALTERAÇÃO CRUCIAL: Verificação mais rigorosa de correspondência
                # Exigir no mínimo 70% de correspondência para responder
                if len(keywords) > 0 and best_matches[0][1] >= (len(keywords) * 0.7):
                    return {
                        'success': True,
                        'fallback': True,
                        'answer': best_ctx.resposta,
                        'confidence': 0.7,
                        'in_scope': True
                    }
                else:
                    # Se não tiver correspondência forte, NÃO responda
                    return {
                        'success': True,
                        'fallback': True,
                        'answer': 'Este assunto deve ser direcionado ao setor responsável, pois não tenho informações suficientes a respeito.',
                        'confidence': 0.5,
                        'in_scope': False
                    }
            
            # Fallback final - NÃO use contexto aleatório, recuse-se a responder
            return {
                'success': True,
                'fallback': True,
                'answer': 'Este assunto deve ser direcionado ao setor responsável, pois não tenho informações suficientes a respeito.',
                'confidence': 0.3,
                'in_scope': False
            }
            
        except Exception as fallback_error:
            print(f"Erro no fallback: {fallback_error}")
            return {
                'success': False,
                'error': str(fallback_error),
                'answer': 'Este assunto deve ser direcionado ao setor responsável. Nosso serviço está temporariamente indisponível.'
            }