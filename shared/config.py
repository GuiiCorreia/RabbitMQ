"""
Configurações compartilhadas para toda a aplicação
"""
from typing import Dict, List
from shared.env import get_env

# Configurações para conexão com RabbitMQ
RABBITMQ_HOST = get_env("RABBITMQ_HOST", "localhost")
RABBITMQ_PORT = int(get_env("RABBITMQ_PORT", "5672"))
RABBITMQ_USER = get_env("RABBITMQ_USER", "guest")
RABBITMQ_PASS = get_env("RABBITMQ_PASS", "guest")

# Nome da fila em cada virtual host
QUEUE_NAME = "eventos"

# Lista de Virtual Hosts disponíveis
VIRTUAL_HOSTS: List[str] = [
    "fluxo_clinico",
    "fluxo_exames",
    "fluxo_opme",
    "ingestao_dados"
]

# Mapeamento de tipos de tarefas para virtual hosts
TASK_TYPE_TO_VHOST: Dict[str, str] = {
    # Fluxo Clínico
    "consulta": "fluxo_clinico",
    "internacao": "fluxo_clinico",
    "alta": "fluxo_clinico",
    
    # Fluxo Exames
    "hemograma": "fluxo_exames",
    "raio_x": "fluxo_exames",
    "tomografia": "fluxo_exames",
    
    # Fluxo OPME
    "protese": "fluxo_opme",
    "orgao": "fluxo_opme",
    "material": "fluxo_opme",
    
    # Fluxo Ingestão
    "carga_pacientes": "ingestao_dados",
    "carga_medicos": "ingestao_dados",
    "carga_exames": "ingestao_dados"
}

# Configurações da API
API_HOST = get_env("API_HOST", "0.0.0.0")
API_PORT = int(get_env("API_PORT", "8000"))
API_WORKERS = int(get_env("API_WORKERS", "1"))

# Configurações do Worker
WORKER_PREFETCH_COUNT = int(get_env("WORKER_PREFETCH_COUNT", "1"))
WORKER_RECONNECT_DELAY = int(get_env("WORKER_RECONNECT_DELAY", "5"))

# Configurações do CrewAI
OPENAI_API_KEY = get_env("OPENAI_API_KEY", "")