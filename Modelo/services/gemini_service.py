import google.generativeai as genai
import traceback
from django.conf import settings
from Contexto.models import Contexto
from Agente.models import Agente

class GeminiService:
    def __init__(self):
        try:
            # Verificação de segurança para a chave API
            if not hasattr(settings, 'GEMINI_API_KEY') or not settings.GEMINI_API_KEY:
                print("ALERTA: GEMINI_API_KEY não encontrada em settings.py")
                self.api_configured = False
                return
                
            # Configurar a API do Gemini
            genai.configure(api_key=settings.GEMINI_API_KEY)
            
            # Listar modelos disponíveis primeiro para diagnóstico
            try:
                print("Listando modelos disponíveis na API Gemini:")
                for model in genai.list_models():
                    print(f"- Modelo: {model.name}")
                    
                # Usar o modelo correto baseado nos disponíveis
                model_names = [m.name for m in genai.list_models()]
                
                if any("gemini-2.0-flash-lite" in name for name in model_names):
                    self.model_name = "gemini-2.0-flash-lite"
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
                        
                print(f"Usando modelo: {self.model_name}")
                self.model = genai.GenerativeModel(self.model_name)
                
            except Exception as model_error:
                print(f"Erro ao listar modelos: {model_error}")
                # Tentar usar o modelo padrão como fallback
                self.model_name = "gemini-1.5-pro"
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
            
        try:
            # Construir o prompt para o Gemini
            prompt = f"""
                Você é um assistente de IA chamado {agent_name or 'Assistente'}.
                
                A seguinte pergunta foi feita: "{question}"
                
                A resposta técnica é: "{original_response}"
                
                Por favor, reescreva esta resposta de uma maneira conversacional e natural, porém não adicione informações que não estejam na resposta técnica.
                
                INSTRUÇÕES IMPORTANTES:
                1. Responda de forma direta e clara, mantendo a essência da resposta original.
                2. Seja natural, amigável e prestativo.
                3. NUNCA use frases como "Com base nas informações que tenho", "De acordo com o contexto" ou similares.
                4. Não mencione limites do seu conhecimento ou fontes de informação.
                5. Se não souber a resposta, diga apenas "Não tenho essa informação, sugiro consultar o setor responsável".
                6. Responda como se já soubesse a informação, sem referir-se a contextos ou dados fornecidos.
                7. Evite jargões técnicos desnecessários para um usuário comum.
                8. Mantenha um tom conversacional natural como se estivesse em um diálogo em tempo real.
            """ 
            completion = self.model.generate_content(prompt)
            
            # Verificar e retornar a resposta
            if hasattr(completion, 'text'):
                return completion.text.strip()
            else:
                print(f"Formato de resposta inesperado: {type(completion)}")
                return original_response
                
        except Exception as e:
            print(f"Erro ao melhorar resposta com Gemini: {e}")
            traceback.print_exc()
            return original_response

    def answer_question(self, agent_id, question):
        """
        Este método é usado quando queremos usar o Gemini diretamente para responder
        """
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
            
            # Prepara o contexto para o prompt
            context_data = []
            for ctx in contexts:
                context_data.append(f"Pergunta: {ctx.pergunta}\nResposta: {ctx.resposta}")
            
            context_text = "\n\n".join(context_data)
            
            # Configuração para mais criatividade na formulação, sem alterar conteúdo
            generation_config = {
                "temperature": 0.7,  # Aumentado para mais naturalidade
                "top_p": 0.8,
                "top_k": 40
            }
            
            # Construir o prompt para o Gemini
            prompt = f"""
                Você é um assistente de IA chamado {agent_name} que responde de forma amigável e acolhedora.
                
                CONTEXTO (Esta é a única fonte de informação que você possui): 
                {context_text}
                
                Pergunta do usuário: {question}
                
                INSTRUÇÕES:
                1. Use SOMENTE as informações do CONTEXTO fornecido acima para responder.
                2. Responda como um atendente simpático faria.
                3. Use linguagem simples e acessível, com um tom conversacional.
                4. NUNCA comece com "Com base no contexto" ou "Segundo as informações".
                5. NÃO INVENTE informações que não estejam no contexto.
                6. Se a informação não estiver no contexto, responda de forma gentil: "Não tenho essa informação específica no momento, sugiro consultar o setor responsável."
                7. Humanize a resposta com pequenas transições ou cumprimentos quando apropriado.
                8. Mantenha-se 100% fiel ao conteúdo do contexto, apenas deixando mais conversacional.
                
                Sua resposta:
            """
            
            print(f"Enviando prompt para o modelo {self.model_name}")
            
            # Criar modelo temporário com a configuração específica
            temp_model = genai.GenerativeModel(
                self.model_name,
                generation_config=generation_config
            )
            
            # Gerar resposta com o Gemini
            completion = temp_model.generate_content(prompt)
            
            if hasattr(completion, 'text'):
                answer = completion.text.strip()
                print(f"Resposta do Gemini recebida com sucesso ({len(answer)} caracteres)")
                return {
                    'success': True,
                    'answer': answer,
                    'confidence': 0.95,
                    'in_scope': True
                }
            else:
                print(f"Formato inesperado de resposta do Gemini: {completion}")
                return {
                    'success': False,
                    'error': 'Formato de resposta inválido',
                    'answer': 'Desculpe, ocorreu um erro ao processar sua pergunta.'
                }
            
        except Exception as e:
            print(f"Erro ao gerar resposta com Gemini: {e}")
            traceback.print_exc()
            
            # Resposta de fallback baseada no contexto - CORRIGIDO o problema de escopo
            try:
                # Busca simples por palavras-chave no contexto (usando Contexto já importado)
                keywords = [w.lower() for w in question.split() if len(w) > 3]
                fallback_contexts = Contexto.objects.filter(Agente_id=agent_id)
                
                for ctx in fallback_contexts:
                    matches = 0
                    for keyword in keywords:
                        if keyword in ctx.pergunta.lower() or keyword in ctx.resposta.lower():
                            matches += 1
                    
                    if matches > 0 and len(keywords) > 0 and matches >= len(keywords) / 2:
                        return {
                            'success': True,
                            'answer': ctx.resposta,
                            'confidence': 0.7,
                            'in_scope': True,
                            'fallback': True
                        }
            except Exception as fallback_error:
                print(f"Erro no fallback: {fallback_error}")
                
            return {
                'success': False,
                'error': str(e),
                'answer': 'Ocorreu um erro ao processar sua pergunta. Tente novamente mais tarde.'
            }