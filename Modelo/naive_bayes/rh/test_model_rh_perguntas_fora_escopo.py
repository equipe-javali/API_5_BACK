import os
import pickle
import nltk
import numpy as np
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import RSLPStemmer
import pandas as pd
from tabulate import tabulate

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

def carregar_modelo():
    """Carrega o modelo treinado e o vetorizador"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    with open(os.path.join(script_dir, "model_rh.pkl"), "rb") as f:
        model = pickle.load(f)
    with open(os.path.join(script_dir, "vectorizer_rh.pkl"), "rb") as f:
        vectorizer = pickle.load(f)
    
    return model, vectorizer

def analisar_pergunta(pergunta, model, vectorizer, threshold_abs=0.20, threshold_diff=0.035):
    """Analisa a pergunta e verifica se está dentro do escopo usando limiares"""
    X_input = vectorizer.transform([pergunta])
    probas = model.predict_proba(X_input)[0]
    
    classes = model.classes_
    class_probas = [(classes[i], probas[i]) for i in range(len(classes))]
    sorted_probas = sorted(class_probas, key=lambda x: x[1], reverse=True)
    
    top_prob = sorted_probas[0][1]
    second_prob = sorted_probas[1][1] if len(sorted_probas) > 1 else 0
    prob_diff = top_prob - second_prob
    
    is_in_scope = top_prob >= threshold_abs and prob_diff >= threshold_diff
    
    return {
        'top_answer': sorted_probas[0][0],
        'top_prob': top_prob,
        'second_prob': second_prob,
        'prob_diff': prob_diff,
        'is_in_scope': is_in_scope,
        'top_3': sorted_probas[:3]
    }

def main():
    print("Carregando modelo de rh...")
    model, vectorizer = carregar_modelo()
    print("Modelo carregado com sucesso!\n")
    
    # Definir conjunto de perguntas fora do escopo
    perguntas_nao_relacionadas = [
        # Culinária
        "Qual é a receita de um bolo de chocolate?",
        "Como fazer pão caseiro?",
        "Qual a temperatura ideal para assar frango?",
        
        # Tecnologia não contábil
        "Como instalar o Windows 11?",
        "Qual é o melhor celular de 2024?",
        "Como resolver problemas de conexão Wi-Fi?",
        
        # Saúde
        "Quais são os sintomas da gripe?",
        "Como baixar a pressão arterial naturalmente?",
        "Qual seu esporte preferido?",
        
        # Entretenimento
        "Quais são os filmes indicados ao Oscar 2025?",
        "Onde posso assistir a série Game of Thrones?",
        "Quando começa a próxima Copa do Mundo?",
        
        # Perguntas parcialmente relacionadas (com termos similares)
        "Como pago as contas da minha casa?",
        "Qual escritório de contabilidade é melhor para minha pequena empresa?",
        "Como organizar minhas finanças pessoais?",
        
        # Perguntas absurdas
        "Os elefantes podem voar se tiverem asas?",
        "Quanto tempo levaria para andar até a lua?",
        "Meu cachorro pode tomar sorvete?",
    ]
    
    # Definir limiares para teste
    threshold_abs = 0.20
    threshold_diff = 0.035
    
    # Analisar cada pergunta
    resultados = []
    
    print(f"Testando {len(perguntas_nao_relacionadas)} perguntas não relacionadas...\n")
    
    for pergunta in perguntas_nao_relacionadas:
        resultado = analisar_pergunta(pergunta, model, vectorizer, threshold_abs, threshold_diff)
        resultados.append({
            'pergunta': pergunta,
            'top_prob': resultado['top_prob'],
            'prob_diff': resultado['prob_diff'],
            'is_in_scope': resultado['is_in_scope'],
            'top_answer': resultado['top_answer'][:50] + "..." if len(resultado['top_answer']) > 50 else resultado['top_answer']
        })
    
    # Criar tabela de resultados com pandas
    df = pd.DataFrame(resultados)
    
    # Exibir resultados em formato tabular
    print(tabulate(df, headers='keys', tablefmt='pretty', showindex=True))
    
    # Análise estatística dos resultados
    corretamente_identificados = df[df['is_in_scope'] == False].shape[0]
    falsos_positivos = df[df['is_in_scope'] == True].shape[0]
    
    print(f"\n===== RESUMO DOS RESULTADOS =====")
    print(f"Total de perguntas testadas: {len(perguntas_nao_relacionadas)}")
    print(f"Perguntas corretamente identificadas como fora do escopo: {corretamente_identificados} ({corretamente_identificados/len(perguntas_nao_relacionadas)*100:.1f}%)")
    print(f"Falsos positivos (perguntas incorretamente aceitas): {falsos_positivos} ({falsos_positivos/len(perguntas_nao_relacionadas)*100:.1f}%)")
    
    # Se houver falsos positivos, listar quais são
    if falsos_positivos > 0:
        print("\nPerguntas incorretamente aceitas como dentro do escopo:")
        for idx, row in df[df['is_in_scope'] == True].iterrows():
            print(f"- {row['pergunta']} (prob: {row['top_prob']:.4f}, diff: {row['prob_diff']:.4f})")
            print(f"  Resposta sugerida: {row['top_answer']}")
    
    print(f"\n===== LIMIARES UTILIZADOS =====")
    print(f"Limiar de probabilidade absoluta: {threshold_abs}")
    print(f"Limiar de diferença entre probabilidades: {threshold_diff}")
    
    # Sugestão de ajuste de limiares
    if falsos_positivos > 0:
        top_probs = df[df['is_in_scope'] == True]['top_prob'].tolist()
        prob_diffs = df[df['is_in_scope'] == True]['prob_diff'].tolist()
        
        new_threshold_abs = max(threshold_abs, max(top_probs) + 0.05)
        new_threshold_diff = max(threshold_diff, max(prob_diffs) + 0.05)
        
        print(f"\nSugestão de novos limiares para eliminar falsos positivos:")
        print(f"- Limiar de probabilidade absoluta: {new_threshold_abs:.2f}")
        print(f"- Limiar de diferença entre probabilidades: {new_threshold_diff:.2f}")

if __name__ == "__main__":
    main()