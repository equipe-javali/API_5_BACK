import unittest
import os
import pickle
import random
import nltk
import numpy as np
from tabulate import tabulate
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import accuracy_score
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import RSLPStemmer

import warnings
warnings.filterwarnings("ignore", message="The parameter 'token_pattern' will not be used")
warnings.filterwarnings("ignore", message="Your stop_words may be inconsistent with your preprocessing")

# Define the same tokenize_and_stem function that was used in the training script
stemmer = RSLPStemmer()
stop_words_stemmed_pt = [stemmer.stem(word) for word in stopwords.words('portuguese')]

def tokenize_and_stem(text):
    # Modifique para preservar hífens em palavras
    tokens = []
    for word in word_tokenize(text.lower(), language='portuguese'):
        if "-" in word and word != "-":
            tokens.append(word)
        elif word.isalpha():
            tokens.append(word)
    
    stemmed_tokens = []
    for token in tokens:
        if "-" in token:
            stemmed_tokens.append(token)
        else:
            stemmed_tokens.append(stemmer.stem(token))
    
    return stemmed_tokens

class TestNaiveBayesModel(unittest.TestCase):
    
    def setUp(self):
        # Ensure NLTK resources are available
        try:
            nltk.data.find('tokenizers/punkt')
            nltk.data.find('corpora/stopwords')
            nltk.data.find('stemmers/rslp')
        except LookupError:
            nltk.download('punkt')
            nltk.download('stopwords')
            nltk.download('rslp')
        
        # Get the directory where the model files are stored
        script_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Load the model and vectorizer
        with open(os.path.join(script_dir, "model_rh.pkl"), "rb") as f:
            self.model = pickle.load(f)
        with open(os.path.join(script_dir, "vectorizer_rh.pkl"), "rb") as f:
            self.vectorizer = pickle.load(f)
            
        # Load original training data - rh (completo com 20 perguntas)
            self.training_data_rh = [
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
        "Qual é a política de home office da empresa?",
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
        
    def get_answer_with_proba(self, question):
        """Predict answer with probabilities for a given question using the loaded model"""
        X_input = self.vectorizer.transform([question])
        predictions = self.model.predict(X_input)
        probas = self.model.predict_proba(X_input)[0]
        
        # Obter as classes e suas probabilidades
        classes = self.model.classes_
        class_probas = [(classes[i], probas[i]) for i in range(len(classes))]
        # Ordenar por probabilidade (descendente)
        sorted_probas = sorted(class_probas, key=lambda x: x[1], reverse=True)
        
        return predictions[0], sorted_probas[:3]  # Retorna previsão e top 3 probabilidades

    def test_original_questions_accuracy(self):
        """Test the model accuracy on the original training questions"""
        correct = 0
        total = len(self.training_data_rh)
        
        print("\nTesting original questions:")
        for question, expected_answer in self.training_data_rh:
            predicted_answer, top_probas = self.get_answer_with_proba(question)
            is_correct = predicted_answer == expected_answer
            correct += int(is_correct)
                
        accuracy = correct / total
        print(f"Accuracy on original questions: {accuracy:.2%} ({correct}/{total})")
        self.assertGreater(accuracy, 0.95, "Model should correctly predict almost all training examples")
        
    def test_complete_variant_questions_accuracy(self):
        """Test the model on variations of all original questions"""
        complete_variant_questions = [
            # Variações para perguntas sobre férias, faltas, documentos, benefícios
            ("Como faço para tirar férias na empresa?", 
             "Os colaboradores têm direito a 30 dias de férias após 12 meses de trabalho. As férias podem ser divididas em até 3 períodos, sendo que um deles não pode ser inferior a 14 dias corridos e os demais não podem ser inferiores a 5 dias corridos."),
            
            ("Qual o procedimento para solicitar férias?", 
             "Para solicitar férias, acesse o sistema de RH, clique em 'Solicitações', selecione 'Férias' e preencha o formulário com as datas desejadas. A solicitação será enviada ao seu gestor para aprovação. Recomendamos solicitar com pelo menos 30 dias de antecedência."),
            
            ("Me explique como funciona a integração de novos colaboradores?", 
             "O processo de admissão inclui: 1) Coleta de documentos pessoais e profissionais; 2) Exame médico admissional; 3) Assinatura do contrato de trabalho; 4) Cadastro nos sistemas internos; 5) Integração com RH; 6) Apresentação ao departamento e equipe."),
            
            ("Quais são os documentos que preciso entregar para ser contratado?", 
             "Para contratação são necessários: RG, CPF, Carteira de Trabalho, PIS, Comprovante de Residência, Comprovante de Escolaridade, Certidão de Nascimento dos filhos menores de 14 anos (se houver), Dados bancários, Foto 3x4 e Atestado de Antecedentes Criminais."),
            
            ("O que cobre o plano de saúde da empresa?",
             "O plano de saúde é oferecido para todos os funcionários após o período de experiência. Possui cobertura nacional, abrange consultas, exames e internações. Os dependentes podem ser incluídos com coparticipação. O plano atual é da operadora XYZ, com rede credenciada disponível no portal do funcionário."),
            
            # Variações para perguntas sobre rotina, políticas e procedimentos
            ("Quais são os horários de expediente da empresa?", 
             "O horário padrão de trabalho é de segunda a sexta-feira, das 8h às 17h, com 1 hora de almoço. Alguns departamentos possuem jornadas específicas. Temos flexibilidade de horário, permitindo entrada entre 7h e 9h e saída entre 16h e 18h, respeitando a carga horária contratual."),
            
            ("Como devo proceder quando faltar ao trabalho?", 
             "As faltas justificadas são aquelas previstas em lei, como por motivo de casamento (3 dias), doação de sangue (1 dia), falecimento de parente próximo (2 dias), entre outras. Envie atestados médicos ou justificativas de faltas para o email rh@empresa.com em até 48 horas após o ocorrido."),
            
            ("Quantos dias posso trabalhar de casa semanalmente?", 
             "Nossa política de home office permite trabalho remoto até 3 dias por semana, mediante acordo com o gestor e conforme a natureza da função. É necessário ter conexão adequada e equipamentos para realizáção das atividades. Reuniões presenciais podem ser convocadas independentemente do regime de trabalho."),
            
            ("Qual é o valor do vale-refeição fornecido?", 
             "O vale-refeição é disponibilizado no cartão até o 5º dia útil de cada mês. O valor diário é de R$ 35,00 por dia útil trabalhado. Não há desconto em folha de pagamento."),
            
            ("Quando acontecem as avaliações de performance na empresa?", 
             "A avaliação de desempenho ocorre semestralmente, nos meses de junho e dezembro. O processo inclui autoavaliação, feedback do gestor imediato e definição de metas para o próximo período. O resultado impacta as oportunidades de promoção e desenvolvimento na empresa."),
            
            # Variações para demais tópicos
            ("Quais benefícios eu tenho direito como funcionário?", 
             "Além do salário, a empresa oferece: vale-refeição, vale-transporte, plano de saúde, plano odontológico, seguro de vida, previdência privada, auxílio-creche, programa de participação nos lucros e resultados, e descontos em estabelecimentos parceiros."),
            
            ("Como funciona a licença para recém-pais e mães?", 
             "A licença maternidade é de 180 dias (6 meses), incluindo os 120 dias previstos em lei mais 60 dias de extensão opcional. A licença paternidade é de 20 dias. Ambas devem ser comunicadas ao RH com antecedência para planejamento da cobertura durante o período de ausência."),
            
            ("Existe dress code na empresa?", 
             "A empresa adota o estilo casual business, permitindo roupas casuais mas profissionais no dia a dia. Em reuniões com clientes ou eventos externos, recomenda-se vestimenta mais formal. Não são permitidas roupas transparentes, decotes excessivos, shorts curtos ou camisetas com mensagens ofensivas."),
            
            ("Como faço para me inscrever nos treinamentos disponíveis?", 
             "A empresa disponibiliza uma plataforma online de cursos com diversos temas técnicos e comportamentais. Cada colaborador possui uma verba anual para treinamentos externos. Para solicitá-los, é necessário preencher o formulário na intranet com pelo menos 15 dias de antecedência e obter aprovação do gestor."),
            
            ("O que acontece quando um funcionário é desligado?", 
             "O processo de desligamento inclui: comunicação formal ao colaborador, entrevista de desligamento com RH, devolução de equipamentos e crachá, cancelamento de acessos aos sistemas, e agendamento dos exames demissionais. A quitação das verbas rescisórias ocorre em até 10 dias após o último dia de trabalho."),
            
            ("Como posso converter minhas horas extras em folgas?", 
             "As horas extras são registradas automaticamente no sistema de ponto eletrônico e compõem o banco de horas, que pode ser utilizado para folgas mediante acordo com o gestor. O saldo do banco de horas deve ser zerado a cada 6 meses. Horas negativas são limitadas a 8 horas por mês."),
            
            ("Quais requisitos devo cumprir para transferência entre departamentos?", 
             "Para solicitar transferência interna, o colaborador deve ter no mínimo 1 ano na posição atual, estar com bom desempenho e se candidatar às vagas divulgadas na intranet. O processo inclui entrevistas com o gestor da área desejada e aprovação do gestor atual."),
            
            ("Quais ações a empresa realiza para promover a inclusão?", 
             "A empresa valoriza a diversidade e promove um ambiente inclusivo, com políticas de contratação que visam a equidade, treinamentos sobre vieses inconscientes, grupos de afinidade e canais de denúncia para casos de discriminação. Temos metas específicas para aumentar a representatividade em todos os níveis hierárquicos."),
            
            ("Preciso fazer uma viagem a trabalho. Como devo fazer?",
             "As viagens corporativas devem ser solicitadas com antecedência mínima de 10 dias úteis através do sistema de viagens. Todas as reservas (hotel, transporte, etc.) devem ser feitas pela agência credenciada. Para reembolso de despesas, apresente os comprovantes originais em até 5 dias úteis após o retorno. Diárias nacionais são de R$ 150,00 e internacionais variam conforme o país de destino."),
            
            ("Como funciona a previdência complementar oferecida?", 
             "O plano de previdência privada é opcional e disponível após 3 meses de empresa. A contribuição mínima é de 2% do salário, e a empresa faz contrapartida de até 4%, dependendo do tempo de casa. O resgate parcial é permitido após 2 anos de contribuição, seguindo as regras da operadora do plano.")
        ]
        
        correct = 0
        total = len(complete_variant_questions)
        
        print("\nTesting variant questions:")
        for question, expected_answer in complete_variant_questions:
            predicted_answer, top_probas = self.get_answer_with_proba(question)
            is_correct = predicted_answer == expected_answer
            correct += int(is_correct)
            
            print(f"Q: {question}")
            print(f"Expected: {expected_answer}")
            print(f"Predicted: {predicted_answer}")
            print(f"Top probabilities:")
            for answer, prob in top_probas:
                print(f"- {prob:.4f}: {answer}")
            print(f"Correct: {is_correct}\n")
                
        accuracy = correct / total
        print(f"Accuracy on variant questions: {accuracy:.2%} ({correct}/{total})")
        self.assertGreater(accuracy, 0.75, "Model should generalize well to similar questions")
    

    def test_model_parameters(self):
        """Test to display the model parameters selected by GridSearchCV"""
        print("\nModel parameters:")
        if hasattr(self.model, "alpha"):
            print(f"Alpha: {self.model.alpha}")
        
        print("\nVectorizer parameters:")
        if hasattr(self.vectorizer, "ngram_range"):
            print(f"N-gram range: {self.vectorizer.ngram_range}")
        
        # Verificar algumas features (características) do modelo
        feature_names = self.vectorizer.get_feature_names_out()
        print(f"Total de features: {len(feature_names)}")
        print(f"Amostra de features: {sorted(feature_names)[:20]}")
        
        # Este teste não tem assertivas, é apenas informativo
        self.assertTrue(True)
        
    def test_model_files_exist(self):
        """Test that model and vectorizer files exist"""
        script_dir = os.path.dirname(os.path.abspath(__file__))
        self.assertTrue(os.path.exists(os.path.join(script_dir, "model_rh.pkl")))
        self.assertTrue(os.path.exists(os.path.join(script_dir, "vectorizer_rh.pkl")))

if __name__ == "__main__":
    unittest.main()