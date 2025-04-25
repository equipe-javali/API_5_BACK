import os
import pickle
import nltk
import numpy as np
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import RSLPStemmer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.model_selection import GridSearchCV
from sklearn.pipeline import Pipeline
import re
from Modelo.models import TrainedModel
from Agente.models import Agente
from .gemini_service import GeminiService

# Ensure NLTK resources are downloaded
nltk.download('rslp', quiet=True)
nltk.download('punkt', quiet=True)
nltk.download('stopwords', quiet=True)
nltk.download('punkt_tab', quiet=True)

# Set up stemmer
stemmer = RSLPStemmer()
stop_words_stemmed_pt = [stemmer.stem(word) for word in stopwords.words('portuguese')]

def tokenize_and_stem(text):
    # Process text preserving hyphens
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

class ModelService:
    def __init__(self):
        self.base_model_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'trained_models')
        os.makedirs(self.base_model_dir, exist_ok=True)
        
        # Inicializar o serviço Gemini para o modelo híbrido
        self.gemini_service = GeminiService()
        
        # Configurar modo híbrido (pode ser alterado em runtime)
        self.use_hybrid_approach = True
    
    def train_model(self, agent_id, training_data):
        """
        Train a model for a specific agent using provided training data
        
        Args:
            agent_id: The ID of the agent
            training_data: List of tuples (question, answer)
        
        Returns:
            Dictionary with training results
        """
        # Create agent directory if it doesn't exist
        agent_dir = os.path.join(self.base_model_dir, f'agent_{agent_id}')
        os.makedirs(agent_dir, exist_ok=True)
        
        print(f"Training model for agent {agent_id} with {len(training_data)} examples")
        
        # Apply data augmentation
        augmented_training_data = []
        for question, answer in training_data:
            # Add original question
            augmented_training_data.append((question, answer))
            
            # Add variations
            variations = generate_question_variations(question)
            for variation in variations:
                augmented_training_data.append((variation, answer))
        
        print(f"Expanded dataset from {len(training_data)} to {len(augmented_training_data)} examples")
        
        # Separate questions and answers
        questions, answers = zip(*augmented_training_data)
        
        # Create and optimize pipeline
        pipeline = Pipeline([
            ('vectorizer', TfidfVectorizer(
                tokenizer=tokenize_and_stem,
                stop_words=stop_words_stemmed_pt,
                token_pattern=r"(?u)\b[A-Za-z\-]+\b",
                lowercase=False)),
            ('classifier', MultinomialNB())
        ])
        
        # Parameters for optimization
        parameters = {
            'vectorizer__ngram_range': [(1, 1), (1, 2)],
            'classifier__alpha': [0.1, 0.5, 1.0, 2.0]
        }
        
        # Cross-validation
        n_folds = min(3, len(set(answers)))
        grid_search = GridSearchCV(pipeline, parameters, cv=n_folds)
        grid_search.fit(questions, answers)
        
        # Get the best model
        best_model = grid_search.best_estimator_
        best_vectorizer = best_model.named_steps['vectorizer']
        best_classifier = best_model.named_steps['classifier']
        
        # Save the model and vectorizer
        model_path = os.path.join(agent_dir, "model.pkl")
        vectorizer_path = os.path.join(agent_dir, "vectorizer.pkl")
        
        with open(model_path, "wb") as f:
            pickle.dump(best_classifier, f)
        with open(vectorizer_path, "wb") as f:
            pickle.dump(best_vectorizer, f)
        
        print(f"Model for agent {agent_id} trained and saved successfully")
        
        # After saving the model files, also save a record in the database        
        agent = Agente.objects.get(id=agent_id)
        
        # Deactivate all previous models for this agent
        TrainedModel.objects.filter(Agente_id=agent).update(is_active=False)
        
        # Create a new active model record
        TrainedModel.objects.create_trained_model(
            Agente_id=agent,
            model_path=model_path,
            vectorizer_path=vectorizer_path,
            examples_count=len(training_data),
            performance_score=grid_search.best_score_
        )
        
        return {
            'success': True,
            'model_path': model_path,
            'vectorizer_path': vectorizer_path,
            'best_params': grid_search.best_params_,
            'best_score': grid_search.best_score_,
            'examples_count': len(training_data),
            'augmented_count': len(augmented_training_data)
        }
    
    def answer_question(self, agent_id, question, threshold_abs=0.20, threshold_diff=0.035):
        """
        Answer a question using the trained model for a specific agent
        and enhance it with Gemini if needed (modelo híbrido)
        
        Args:
            agent_id: The ID of the agent
            question: The question to answer
            threshold_abs: Minimum probability threshold
            threshold_diff: Minimum difference between top probabilities
            
        Returns:
            Dictionary with answer and confidence metrics
        """
        try:
            # Obter o nome do agente para uso no Gemini
            try:
                agent = Agente.objects.get(id=agent_id)
                agent_name = agent.nome
            except Agente.DoesNotExist:
                agent_name = "Assistente"
                
            # Use relative path based on this file's location instead of DB paths
            agent_dir = os.path.join(self.base_model_dir, f'agent_{agent_id}')
            model_path = os.path.join(agent_dir, "model.pkl")
            vectorizer_path = os.path.join(agent_dir, "vectorizer.pkl")
            
            print(f"DEBUG: Using relative paths: {model_path}, {vectorizer_path}")
            
            # Check if the model files exist
            if not os.path.exists(model_path) or not os.path.exists(vectorizer_path):
                print(f"WARNING: Model files not found at paths: {model_path}, {vectorizer_path}")
                
                # Try alternative path without the "agent_" prefix
                alt_dir = os.path.join(self.base_model_dir, f'{agent_id}')
                alt_model = os.path.join(alt_dir, "model.pkl")
                alt_vectorizer = os.path.join(alt_dir, "vectorizer.pkl")
                
                if os.path.exists(alt_model) and os.path.exists(alt_vectorizer):
                    model_path = alt_model
                    vectorizer_path = alt_vectorizer
                    print(f"DEBUG: Found model at alternative path: {alt_model}")
                else:
                    # Final check if model exists
                    print("Model not found. Using Gemini as fallback.")
                    return self.gemini_service.answer_question(agent_id, question)
            
            # Load the model and vectorizer
            try:
                with open(model_path, "rb") as f:
                    model = pickle.load(f)
                with open(vectorizer_path, "rb") as f:
                    vectorizer = pickle.load(f)
            except Exception as e:
                print(f"Error loading model: {str(e)}. Using Gemini as fallback.")
                return self.gemini_service.answer_question(agent_id, question)
            
            # Transform the question
            X_input = vectorizer.transform([question])
            probas = model.predict_proba(X_input)[0]
            
            # Get classes and probabilities
            classes = model.classes_
            class_probas = [(classes[i], probas[i]) for i in range(len(classes))]
            
            # Sort by probability (descending)
            sorted_probas = sorted(class_probas, key=lambda x: x[1], reverse=True)
            
            top_class = sorted_probas[0][0]
            top_prob = sorted_probas[0][1]
            second_prob = sorted_probas[1][1] if len(sorted_probas) > 1 else 0
            
            # Check if answer is below confidence thresholds
            diff = top_prob - second_prob
            
            # MODELO HÍBRIDO: baixa confiança -> usa Gemini diretamente
            if top_prob < threshold_abs or diff < threshold_diff:
                print(f"Low confidence: {top_prob:.4f}. Using Gemini to generate response.")
                return self.gemini_service.answer_question(agent_id, question)
            else:
                # MODELO HÍBRIDO: alta confiança -> usa modelo local e aprimora com Gemini
                if self.use_hybrid_approach:
                    print(f"High confidence: {top_prob:.4f}. Enhancing model response with Gemini.")
                    
                    # Obter a resposta original do modelo
                    original_answer = top_class
                    
                    # Usar Gemini para aprimorar a resposta
                    enhanced_answer = self.enhance_response_with_gemini(
                        original_answer, question, agent_name
                    )
                    
                    return {
                        'success': True,
                        'answer': enhanced_answer,
                        'original_answer': original_answer,
                        'confidence': top_prob,
                        'diff': diff,
                        'in_scope': True,
                        'top_probas': sorted_probas[:3],
                        'enhanced': True
                    }
                else:
                    # Usar apenas o modelo local sem aprimoramento
                    return {
                        'success': True,
                        'answer': top_class,
                        'confidence': top_prob,
                        'diff': diff,
                        'in_scope': True,
                        'top_probas': sorted_probas[:3],
                        'enhanced': False
                    }
        except Exception as e:
            print(f"Unexpected error in answer_question: {str(e)}. Using Gemini as fallback.")
            # Em caso de qualquer erro, usar Gemini como fallback
            return self.gemini_service.answer_question(agent_id, question)
    
    def enhance_response_with_gemini(self, original_response, question, agent_name="Assistente"):
        """
        Aprimora a resposta do modelo local usando a API Gemini
        para torná-la mais conversacional e natural
        """
        try:
            return self.gemini_service.enhance_response(original_response, question, agent_name)
        except Exception as e:
            print(f"Error enhancing response with Gemini: {str(e)}")
            # Em caso de erro, retornar a resposta original
            return original_response