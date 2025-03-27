from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.model_selection import GridSearchCV
from sklearn.pipeline import Pipeline
import pickle
import nltk
import os
import warnings
import re
import numpy as np

warnings.filterwarnings("ignore", message="The parameter 'token_pattern' will not be used")
warnings.filterwarnings("ignore", message="Your stop_words may be inconsistent with your preprocessing")

from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import RSLPStemmer

nltk.download('rslp', quiet=True)
nltk.download('punkt', quiet=True)
nltk.download('stopwords', quiet=True)

stemmer = RSLPStemmer()
stop_words_stemmed_pt = [stemmer.stem(word) for word in stopwords.words('portuguese')]

def tokenize_and_stem(text):
    # Converte para minúsculas e tokeniza
    # Modificando para preservar hífens em palavras
    tokens = []
    for word in word_tokenize(text.lower(), language='portuguese'):
        # Verifica se o token contém hífen e não é apenas um hífen isolado
        if "-" in word and word != "-":
            # Preserva o token com hífen
            tokens.append(word)
        elif word.isalpha():
            tokens.append(word)
    
    # Aplica stemming (com tratamento especial para palavras com hífen)
    stemmed_tokens = []
    for token in tokens:
        if "-" in token:
            # Para palavras com hífen, mantém o token original
            stemmed_tokens.append(token)
        else:
            # Para outras palavras, aplica stemming normal
            stemmed_tokens.append(stemmer.stem(token))
    
    return stemmed_tokens

def generate_question_variations(question):
    """Gera variações simples da pergunta original"""
    variations = []
    
    # Variação 1: Transformar "Como posso" para "Como faço para"
    if re.search(r'\bcomo\s+posso\b', question.lower()):
        variations.append(re.sub(r'\bcomo\s+posso\b', 'como faço para', question.lower()))
    
    # Variação 2: Transformar "Qual é" para "Qual"
    if re.search(r'\bqual\s+é\b', question.lower()):
        variations.append(re.sub(r'\bqual\s+é\b', 'qual', question.lower()))
    
    # Variação 3: Transformar "Onde encontro" para "Onde posso encontrar"
    if re.search(r'\bonde\s+encontro\b', question.lower()):
        variations.append(re.sub(r'\bonde\s+encontro\b', 'onde posso encontrar', question.lower()))
    
    # Variação 4: Adicionar "Por favor," no início
    if not question.lower().startswith("por favor"):
        variations.append(f"Por favor, {question.lower()}")
    
    # Variação 5: Transformar "Como solicitar" para "Como posso solicitar"
    if re.search(r'\bcomo\s+solicitar\b', question.lower()):
        variations.append(re.sub(r'\bcomo\s+solicitar\b', 'como posso solicitar', question.lower()))
    
    # Variação 6: Outra formulação
    if question.lower().startswith("como"):
        variations.append(re.sub(r'^como', 'de que forma', question.lower()))
    
    # Variação 7: Formulação mais direta
    if question.lower().startswith("qual é"):
        variations.append(re.sub(r'^qual é', 'informe', question.lower()))
        
    return variations

# Sample training data: (question, answer)
training_data_rh = [
    (
        "Qual é a política de férias da empresa?",
        "Os colaboradores têm direito a 30 dias de férias após 12 meses de trabalho. As férias podem ser divididas em até 3 períodos, sendo que um deles não pode ser inferior a 14 dias corridos e os demais não podem ser inferiores a 5 dias corridos."
    ),
    (
        "Como solicitar férias no sistema da empresa?",
        "Para solicitar férias, acesse o sistema de RH, clique em 'Solicitações', selecione 'Férias' e preencha o formulário com as datas desejadas. A solicitação será enviada ao seu gestor para aprovação. Recomendamos solicitar com pelo menos 30 dias de antecedência."
    ),
    (
        "Como posso conhecer o processo de integração de novos funcionários?",
        "O processo de admissão inclui: 1) Coleta de documentos pessoais e profissionais; 2) Exame médico admissional; 3) Assinatura do contrato de trabalho; 4) Cadastro nos sistemas internos; 5) Integração com RH; 6) Apresentação ao departamento e equipe."
    ),
    (
        "Onde encontro a lista de documentos necessários para contratação?",
        "Para contratação são necessários: RG, CPF, Carteira de Trabalho, PIS, Comprovante de Residência, Comprovante de Escolaridade, Certidão de Nascimento dos filhos menores de 14 anos (se houver), Dados bancários, Foto 3x4 e Atestado de Antecedentes Criminais."
    ),
    (
        "Qual é a cobertura do plano de saúde oferecido?",
        "O plano de saúde é oferecido para todos os funcionários após o período de experiência. Possui cobertura nacional, abrange consultas, exames e internações. Os dependentes podem ser incluídos com coparticipação. O plano atual é da operadora XYZ, com rede credenciada disponível no portal do funcionário."
    ),
    (
        "Qual é o horário de trabalho da empresa?",
        "O horário padrão de trabalho é de segunda a sexta-feira, das 8h às 17h, com 1 hora de almoço. Alguns departamentos possuem jornadas específicas. Temos flexibilidade de horário, permitindo entrada entre 7h e 9h e saída entre 16h e 18h, respeitando a carga horária contratual."
    ),
    (
        "Como posso justificar faltas no trabalho?",
        "As faltas justificadas são aquelas previstas em lei, como por motivo de casamento (3 dias), doação de sangue (1 dia), falecimento de parente próximo (2 dias), entre outras. Envie atestados médicos ou justificativas de faltas para o email rh@empresa.com em até 48 horas após o ocorrido."
    ),
    (
        "Qual é a política de home office (trabalho em casa) da empresa?",
        "Nossa política de home office permite trabalho remoto até 3 dias por semana, mediante acordo com o gestor e conforme a natureza da função. É necessário ter conexão adequada e equipamentos para realizáção das atividades. Reuniões presenciais podem ser convocadas independentemente do regime de trabalho."
    ),
    ( 
        "Onde encontro informações sobre o vale-refeição?",
        "O vale-refeição é disponibilizado no cartão até o 5º dia útil de cada mês. O valor diário é de R$ 35,00 por dia útil trabalhado. Não há desconto em folha de pagamento."  
    ),
    (
        "Como posso saber mais sobre as avaliações de desempenho?",
        "A avaliação de desempenho ocorre semestralmente, nos meses de junho e dezembro. O processo inclui autoavaliação, feedback do gestor imediato e definição de metas para o próximo período. O resultado impacta as oportunidades de promoção e desenvolvimento na empresa."
    ),
    (
        "Qual é o pacote de benefícios oferecido pela empresa?",
        "Além do salário, a empresa oferece: vale-refeição, vale-transporte, plano de saúde, plano odontológico, seguro de vida, previdência privada, auxílio-creche, programa de participação nos lucros e resultados, e descontos em estabelecimentos parceiros."
    ),
    (
        "Como solicitar licença maternidade ou paternidade?",
        "A licença maternidade é de 180 dias (6 meses), incluindo os 120 dias previstos em lei mais 60 dias de extensão opcional. A licença paternidade é de 20 dias. Ambas devem ser comunicadas ao RH com antecedência para planejamento da cobertura durante o período de ausência."
    ),
    (
        "Onde encontro o código de vestimenta da empresa (dress code)?",
        "A empresa adota o estilo casual business, permitindo roupas casuais mas profissionais no dia a dia. Em reuniões com clientes ou eventos externos, recomenda-se vestimenta mais formal. Não são permitidas roupas transparentes, decotes excessivos, shorts curtos ou camisetas com mensagens ofensivas."
    ),
    (
        "Como posso participar dos programas de treinamento?",
        "A empresa disponibiliza uma plataforma online de cursos com diversos temas técnicos e comportamentais. Cada colaborador possui uma verba anual para treinamentos externos. Para solicitá-los, é necessário preencher o formulário na intranet com pelo menos 15 dias de antecedência e obter aprovação do gestor."
    ),
    (
        "Qual é o procedimento de desligamento da empresa?",
        "O processo de desligamento inclui: comunicação formal ao colaborador, entrevista de desligamento com RH, devolução de equipamentos e crachá, cancelamento de acessos aos sistemas, e agendamento dos exames demissionais. A quitação das verbas rescisórias ocorre em até 10 dias após o último dia de trabalho."
    ),
    (
        "Como solicitar compensação de horas extras?",
        "As horas extras são registradas automaticamente no sistema de ponto eletrônico e compõem o banco de horas, que pode ser utilizado para folgas mediante acordo com o gestor. O saldo do banco de horas deve ser zerado a cada 6 meses. Horas negativas são limitadas a 8 horas por mês."
    ),
    (
        "Como posso me candidatar a vagas internas?",
        "Para solicitar transferência interna, o colaborador deve ter no mínimo 1 ano na posição atual, estar com bom desempenho e se candidatar às vagas divulgadas na intranet. O processo inclui entrevistas com o gestor da área desejada e aprovação do gestor atual."
    ),
    (
        "Onde encontro informações sobre diversidade e inclusão?",
        "A empresa valoriza a diversidade e promove um ambiente inclusivo, com políticas de contratação que visam a equidade, treinamentos sobre vieses inconscientes, grupos de afinidade e canais de denúncia para casos de discriminação. Temos metas específicas para aumentar a representatividade em todos os níveis hierárquicos."
    ),
    (
        "Qual é a política de viagens corporativas da empresa?",
        "As viagens corporativas devem ser solicitadas com antecedência mínima de 10 dias úteis através do sistema de viagens. Todas as reservas (hotel, transporte, etc.) devem ser feitas pela agência credenciada. Para reembolso de despesas, apresente os comprovantes originais em até 5 dias úteis após o retorno. Diárias nacionais são de R$ 150,00 e internacionais variam conforme o país de destino."
    ),
    (
        "Qual é a política de previdência privada da empresa?",
        "O plano de previdência privada é opcional e disponível após 3 meses de empresa. A contribuição mínima é de 2% do salário, e a empresa faz contrapartida de até 4%, dependendo do tempo de casa. O resgate parcial é permitido após 2 anos de contribuição, seguindo as regras da operadora do plano."
    ),
]

# Aplicar aumento de dados
print("Expandindo conjunto de dados com variações automáticas...")
augmented_training_data = []
for question, answer in training_data_rh:
    # Adiciona a pergunta original
    augmented_training_data.append((question, answer))    # In the same Django shell
    question = "Como funcionam as férias na empresa?"
    response = model_service.answer_question(agent_id, question)
    print(f"Response: {response['answer']}")
    print(f"Confidence: {response['confidence']}")
    
    # Adiciona variações automáticas
    variations = generate_question_variations(question)
    for variation in variations:
        augmented_training_data.append((variation, answer))

# Separate the training questions and answers
questions, answers = zip(*augmented_training_data)
print(f"Conjunto de dados expandido de {len(training_data_rh)} para {len(augmented_training_data)} exemplos")

# Criação e otimização do pipeline
print("\nRealizando validação cruzada para encontrar os melhores parâmetros...")
pipeline = Pipeline([
    ('vectorizer', TfidfVectorizer(
        tokenizer=tokenize_and_stem,
        stop_words=stop_words_stemmed_pt,
        token_pattern=r"(?u)\b[A-Za-z\-]+\b",  # Padrão modificado para incluir hífens
        lowercase=False)),
    ('classifier', MultinomialNB())
])

# Parâmetros para otimização
parameters = {
    'vectorizer__ngram_range': [(1, 1), (1, 2)],
    'classifier__alpha': [0.1, 0.5, 1.0, 2.0]
}

# Validação cruzada com 3 folds (ou menos se não houver exemplos suficientes)
n_folds = min(3, len(set(answers)))
grid_search = GridSearchCV(pipeline, parameters, cv=n_folds)
grid_search.fit(questions, answers)

# Informações sobre o melhor modelo encontrado
print(f"\nMelhores parâmetros encontrados:")
print(f"Alpha: {grid_search.best_params_['classifier__alpha']}")
print(f"N-grams: {grid_search.best_params_['vectorizer__ngram_range']}")
print(f"Pontuação da validação cruzada: {grid_search.best_score_:.2f}")

# Obter o modelo final otimizado
best_model = grid_search.best_estimator_

# Extrair o vetorizador e o classificador do pipeline
best_vectorizer = best_model.named_steps['vectorizer']
best_classifier = best_model.named_steps['classifier']

# Get the directory where the script is located
script_dir = os.path.dirname(os.path.abspath(__file__))

# Salvar o modelo e vetorizador otimizados
print("\nSalvando modelo e vetorizador otimizados...")
with open(os.path.join(script_dir, "model_rh.pkl"), "wb") as f:
    pickle.dump(best_classifier, f)
with open(os.path.join(script_dir, "vectorizer_rh.pkl"), "wb") as f:
    pickle.dump(best_vectorizer, f)

print("\nTreinamento concluído e arquivos salvos com sucesso!")

# Mostrar algumas das features utilizadas pelo modelo
print("\nAlgumas características (features) do modelo:")
feature_names = best_vectorizer.get_feature_names_out()
print(f"Total de features: {len(feature_names)}")
print(f"Amostra de features: {sorted(feature_names)[:20]}")