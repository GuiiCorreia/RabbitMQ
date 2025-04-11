"""
Utilitários compartilhados para toda a aplicação
"""
import json
import uuid
import logging
from datetime import datetime
from typing import Dict, Any, Optional

# Configurar logging
def setup_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Configura e retorna um logger formatado
    
    Args:
        name: Nome do logger
        level: Nível de log (default: logging.INFO)
        
    Returns:
        logging.Logger: Logger configurado
    """
    logger = logging.getLogger(name)
    
    # Verificar se o logger já tem handlers para evitar duplicação
    if not logger.handlers:
        logger.setLevel(level)
        
        # Criar handler para console
        handler = logging.StreamHandler()
        handler.setLevel(level)
        
        # Definir formato
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        
        # Adicionar handler ao logger
        logger.addHandler(handler)
    
    return logger

def generate_task_id() -> str:
    """
    Gera um ID único para tarefas
    
    Returns:
        str: ID único
    """
    return str(uuid.uuid4())

def timestamp_now() -> str:
    """
    Retorna o timestamp atual em formato ISO
    
    Returns:
        str: Timestamp em formato ISO
    """
    return datetime.now().isoformat()

# Serializador personalizado para datetime e outros tipos complexos
def json_serializer(obj):
    """
    Serializador personalizado para objetos que o JSON padrão não suporta
    
    Args:
        obj: Objeto a ser serializado
        
    Returns:
        str ou dict: Representação serializável do objeto
    """
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")

def format_task_data(task_type: str, data: Dict[str, Any], 
                    priority: int = 0, task_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Formata os dados de uma tarefa para envio
    
    Args:
        task_type: Tipo da tarefa
        data: Dados da tarefa
        priority: Prioridade (default: 0)
        task_id: ID da tarefa (opcional, gerado se None)
        
    Returns:
        Dict[str, Any]: Dados formatados da tarefa
    """
    return {
        "id": task_id or generate_task_id(),
        "tipo": task_type,
        "dados": data,
        "prioridade": priority,
        "timestamp": timestamp_now()
    }

def safe_json_dumps(data: Any) -> str:
    """
    Converte dados para JSON de forma segura, lidando com tipos não serializáveis
    
    Args:
        data: Dados a serem convertidos
        
    Returns:
        str: String JSON
    """
    return json.dumps(data, default=json_serializer, ensure_ascii=False)