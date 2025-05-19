import nltk
import ssl
import os

try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context

# Definir o diretório NLTK para um local específico no projeto
nltk_data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'nltk_data')
os.makedirs(nltk_data_dir, exist_ok=True)
os.environ['NLTK_DATA'] = nltk_data_dir

# Baixar todos os pacotes necessários
print("Baixando pacotes NLTK...")
nltk.download('rslp', download_dir=nltk_data_dir)
nltk.download('punkt', download_dir=nltk_data_dir)
nltk.download('stopwords', download_dir=nltk_data_dir)
try:
    nltk.download('punkt_tab', download_dir=nltk_data_dir)
except:
    print("Aviso: Pacote punkt_tab não encontrado, ignorando...")

print(f"Download de pacotes NLTK concluído em {nltk_data_dir}!")