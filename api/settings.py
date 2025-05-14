import os
from pathlib import Path
import dj_database_url # Importar dj_database_url

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
# Leia a SECRET_KEY da variável de ambiente
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY')

# Leia a GEMINI_API_KEY da variável de ambiente
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
# Leia DEBUG da variável de ambiente, padrão 'False' se não definida
DEBUG = os.environ.get('DEBUG', 'False') == 'True'

ALLOWED_HOSTS = []
RENDER_EXTERNAL_HOSTNAME = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)

# Se DEBUG for True (desenvolvimento local), adicione hosts comuns
if DEBUG:
    ALLOWED_HOSTS.extend(['localhost', '127.0.0.1'])


# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework_swagger', 
    'rest_framework',
    'drf_yasg',
    'Usuario',
    'Permissao',
    'Agente',
    'Chat',
    'Contexto',
    'Modelo',
    'corsheaders',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware', # Para servir estáticos
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware', # Coloque antes de CommonMiddleware
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # Remova o 'django.middleware.common.CommonMiddleware' duplicado se houver
]

# Configuração do CORS
# Remova CORS_ALLOW_ALL_ORIGINS = True para produção
# CORS_ALLOW_ALL_ORIGINS = True # Mantenha comentado ou remova em produção
CORS_ALLOWED_ORIGINS = [
    # Adicione a URL do seu frontend no Render aqui. Ex: "https://seu-frontend.onrender.com"
    # Para desenvolvimento local, você pode ter:
    # "http://localhost:3000", (se seu frontend roda na porta 3000)
    # "http://localhost:5173", (se seu frontend Vue/React/Vite roda na porta 5173)
]
# Se você precisar que o frontend envie credenciais (cookies, tokens de autorização)
# CORS_ALLOW_CREDENTIALS = True


ROOT_URLCONF = 'api.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'api.wsgi.application'


# Database
# Use dj_database_url para ler a configuração do banco da variável de ambiente DATABASE_URL
DATABASES = {
    'default': dj_database_url.config(
        # Fallback para um SQLite local se DATABASE_URL não estiver definida (útil para dev inicial)
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        conn_max_age=600, # Opcional: tempo de vida da conexão
        conn_health_checks=True, # Opcional: verificações de saúde da conexão
        ssl_require=os.environ.get('DB_SSL_REQUIRE', 'False') == 'True' # Para Neon, SSL é geralmente True
    )
}
# Se a variável de ambiente DATABASE_URL for como a do Neon (com sslmode=require no final da string),
# dj_database_url geralmente lida com isso automaticamente.
# A opção ssl_require acima é uma forma explícita se a DATABASE_URL não incluir o parâmetro sslmode.


# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'pt-br' # Alterado para português do Brasil
TIME_ZONE = 'America/Sao_Paulo' # Alterado para fuso horário de São Paulo
USE_I18N = True
USE_TZ = True


# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles') # Para collectstatic
# Para servir estáticos com WhiteNoise em produção
# STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage' # Opcional para otimizações

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

REST_FRAMEWORK = {
   'DEFAULT_AUTHENTICATION_CLASSES': [
       'rest_framework_simplejwt.authentication.JWTAuthentication',
   ],
   'DEFAULT_PERMISSION_CLASSES': [
       'rest_framework.permissions.IsAuthenticated', # Ou outra permissão padrão desejada
   ],
}

AUTH_USER_MODEL = 'Usuario.Usuario'

# CSRF Protection (Render geralmente usa HTTPS)
# Se você tiver um domínio customizado e HTTPS, pode habilitá-los
# CSRF_COOKIE_SECURE = not DEBUG # True em produção
# SESSION_COOKIE_SECURE = not DEBUG # True em produção

CSRF_TRUSTED_ORIGINS = []
if RENDER_EXTERNAL_HOSTNAME:
    CSRF_TRUSTED_ORIGINS.append(f"https://{RENDER_EXTERNAL_HOSTNAME}")
# Adicione a URL do seu frontend aqui também se ele fizer requisições que precisam de CSRF
# Ex: CSRF_TRUSTED_ORIGINS.append('https://seu-frontend.onrender.com')

# Logging (opcional, mas recomendado para produção)
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO', # Em produção, pode ser 'INFO' ou 'WARNING'
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
            'propagate': False,
        },
    },
}