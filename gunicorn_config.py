# filepath: c:\Users\katia\OneDrive - Fatec Centro Paula Souza\API_5\API_5_BACK\gunicorn_config.py

# Timeout para workers (em segundos)
timeout = 120

# Número de workers (use uma fórmula ajustada à memória disponível)
workers = 2  # Valor baixo para economizar memória

# Ajuste de memória
worker_class = 'sync'
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 100

# Logging
loglevel = 'info'
accesslog = '-'
errorlog = '-'