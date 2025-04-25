import google.generativeai as genai
from django.conf import settings
from Contexto.models import Contexto
from Agente.models import Agente

class GeminiService:
    def __init__(self):
        # Configurar a API do Gemini
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-pro')
        
    def prepare_context(self, agent_id):
        """Prepara o contexto do agente para o modelo"""
        try:
            # Obtém o agente
            agent = Agente.objects.get(id=agent_id)
            
            # Obtém todos os contextos deste agente
            contexts = Contexto.objects.filter(Agente_id=agent)
            
            # Prepara o contexto para o prompt do Gemini
            system_prompt = f"""
            Você é um assistente de IA chamado {agent.nome}. 
            Sua função é responder perguntas relacionadas ao contexto fornecido.
            
            Para qualquer pergunta fora do contexto, responda educadamente que não possui essa informação.
            """
            
            # Adiciona o contexto ao prompt
            context_data = []
            for ctx in contexts:
                context_data.append(f"Pergunta: {ctx.pergunta}\nResposta: {ctx.resposta}")
            
            full_context = "\n\n".join(context_data)
            
            return system_prompt, full_context
        except Exception as e:
            print(f"Erro ao preparar contexto: {str(e)}")
            return "", ""
    
    def answer_question(self, agent_id, question):
        """Responde uma pergunta usando o modelo Gemini com contexto do agente"""
        try:
            system_prompt, context = self.prepare_context(agent_id)
            
            if not system_prompt or not context:
                return {
                    'answer': "Desculpe, ocorreu um erro ao processar sua pergunta.",
                    'confidence': 0,
                    'in_scope': False
                }
            
            # Prepara o prompt completo
            prompt = f"""
            {system_prompt}
            
            CONTEXTO:
            {context}
            
            PERGUNTA DO USUÁRIO: {question}
            
            Responda de forma concisa e direta com base apenas no contexto acima.
            """
            
            # Gera a resposta do Gemini
            response = self.model.generate_content(prompt)
            
            if response and hasattr(response, 'text'):
                answer = response.text.strip()
                return {
                    'answer': answer,
                    'confidence': 0.95,
                    'in_scope': True
                }
            else:
                return {
                    'answer': "Não consegui processar sua pergunta. Por favor, tente novamente.",
                    'confidence': 0,
                    'in_scope': False
                }
                
        except Exception as e:
            print(f"Erro ao gerar resposta com Gemini: {str(e)}")
            return {
                'answer': "Ocorreu um erro ao processar sua pergunta.",
                'confidence': 0,
                'in_scope': False
            }