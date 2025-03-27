import os
import pickle
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import RSLPStemmer

# Certifique-se de que os recursos NLTK estão disponíveis
try:
    nltk.data.find('tokenizers/punkt')
    nltk.data.find('corpora/stopwords')
    nltk.data.find('stemmers/rslp')
except LookupError:
    nltk.download('punkt', quiet=True)
    nltk.download('stopwords', quiet=True)
    nltk.download('rslp', quiet=True)

# Define a função de tokenização e stemming usada no treinamento
stemmer = RSLPStemmer()
def tokenize_and_stem(text):
    tokens = word_tokenize(text.lower(), language='portuguese')
    return [stemmer.stem(token) for token in tokens if token.isalpha()]

class RHAssistant:
    def __init__(self, threshold_abs=0.20, threshold_diff=0.035):
        """Inicializa o assistente com os limiares para detecção de perguntas fora do escopo"""
        self.threshold_abs = threshold_abs
        self.threshold_diff = threshold_diff
        
        # Obtém o diretório onde o script está localizado
        script_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Carrega o modelo e o vetorizador
        print("Carregando modelo e vetorizador...")
        with open(os.path.join(script_dir, "model_rh.pkl"), "rb") as f:
            self.model = pickle.load(f)
        with open(os.path.join(script_dir, "vectorizer_rh.pkl"), "rb") as f:
            self.vectorizer = pickle.load(f)
        print("Modelo carregado com sucesso!")
    
    def answer_question(self, question):
        """Responde uma pergunta com verificação de confiança"""
        X_input = self.vectorizer.transform([question])
        probas = self.model.predict_proba(X_input)[0]
        
        # Obter as classes e suas probabilidades
        classes = self.model.classes_
        class_probas = [(classes[i], probas[i]) for i in range(len(classes))]
        
        # Ordenar por probabilidade (descendente)
        sorted_probas = sorted(class_probas, key=lambda x: x[1], reverse=True)
        
        top_answer = sorted_probas[0][0]
        top_prob = sorted_probas[0][1]
        second_prob = sorted_probas[1][1] if len(sorted_probas) > 1 else 0
        
        # Verifica se a resposta está abaixo dos limiares de confiança
        diff = top_prob - second_prob
        
        if top_prob < self.threshold_abs or diff < self.threshold_diff:
            return {
                'answer': "Desculpe, não encontrei uma resposta relevante para sua pergunta.",
                'confidence': top_prob,
                'diff': diff,
                'in_scope': False,
                'top_probas': sorted_probas[:3]
            }
        else:
            return {
                'answer': top_answer,
                'confidence': top_prob,
                'diff': diff,
                'in_scope': True,
                'top_probas': sorted_probas[:3]
            }

def main():
    assistant = RHAssistant()
    
    print("\n=== Assistente de RH ===")
    print("Digite suas perguntas ou 'sair' para encerrar.")
    print("=" * 40)
    
    while True:
        question = input("\nSua pergunta: ")
        if question.lower() in ['sair', 'exit', 'quit', 'q']:
            print("Encerrando o assistente. Até logo!")
            break
            
        if not question.strip():
            continue
            
        result = assistant.answer_question(question)
        
        print("\nResposta:", end=" ")
        if result['in_scope']:
            print(f"{result['answer']}")
        else:
            print(f"{result['answer']} (fora do escopo)")
        
        print(f"\nConfiança: {result['confidence']:.4f}")
        print(f"Diferença: {result['diff']:.4f}")
        
        print("\nTop 3 probabilidades:")
        for ans, prob in result['top_probas']:
            print(f"- {prob:.4f}: {ans[:80]}...")

if __name__ == "__main__":
    main()