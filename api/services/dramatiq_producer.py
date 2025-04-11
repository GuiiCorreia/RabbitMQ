"""
Produtor Dramatiq para envio de mensagens a partir da API
"""
import json
import uuid
import dramatiq
from dramatiq.brokers.rabbitmq import RabbitmqBroker
from typing import Dict, Any, Optional

from shared.config import (
    RABBITMQ_HOST, RABBITMQ_PORT, RABBITMQ_USER, RABBITMQ_PASS,
    QUEUE_NAME, VIRTUAL_HOSTS, TASK_TYPE_TO_VHOST
)
from shared.utils import setup_logger, generate_task_id, timestamp_now, json_serializer

# Configuração de logging
logger = setup_logger('dramatiq_producer')

# Criar brokers para cada vhost
brokers = {}

def get_broker(vhost):
    """
    Obtém um broker Dramatiq para um virtual host específico
    
    Args:
        vhost: Virtual host para conectar
        
    Returns:
        RabbitmqBroker: Broker configurado
    """
    if vhost not in brokers:
        # URL de conexão para o RabbitMQ
        url = f"amqp://{RABBITMQ_USER}:{RABBITMQ_PASS}@{RABBITMQ_HOST}:{RABBITMQ_PORT}/{vhost}"
        
        # Criar broker
        broker = RabbitmqBroker(url=url)
        brokers[vhost] = broker
    
    return brokers[vhost]

# Obter broker para cada vhost
fluxo_clinico_broker = get_broker("fluxo_clinico")
fluxo_exames_broker = get_broker("fluxo_exames")
fluxo_opme_broker = get_broker("fluxo_opme")
ingestao_dados_broker = get_broker("ingestao_dados")

# Registrar o broker padrão com o Dramatiq
dramatiq.set_broker(fluxo_clinico_broker)

# Definir os atores do Dramatiq
@dramatiq.actor(queue_name=QUEUE_NAME, broker=fluxo_clinico_broker)
def process_fluxo_clinico(task_data_json):
    """Ator para processamento do fluxo clínico"""
    pass  # Implementação real está no worker

@dramatiq.actor(queue_name=QUEUE_NAME, broker=fluxo_exames_broker)
def process_fluxo_exames(task_data_json):
    """Ator para processamento do fluxo de exames"""
    pass  # Implementação real está no worker

@dramatiq.actor(queue_name=QUEUE_NAME, broker=fluxo_opme_broker)
def process_fluxo_opme(task_data_json):
    """Ator para processamento do fluxo OPME"""
    pass  # Implementação real está no worker

@dramatiq.actor(queue_name=QUEUE_NAME, broker=ingestao_dados_broker)
def process_fluxo_ingestao(task_data_json):
    """Ator para processamento do fluxo de ingestão"""
    pass  # Implementação real está no worker

class DramatiqProducer:
    """Classe para gerenciar o envio de tarefas via Dramatiq"""
    
    def send_task(self, task_data: Dict[str, Any], vhost: Optional[str] = None) -> Optional[str]:
        """
        Envia uma tarefa para o Dramatiq
        
        Args:
            task_data: Dados da tarefa a ser enviada
            vhost: Virtual host específico (detectado automaticamente se None)
        
        Returns:
            Optional[str]: ID da mensagem se enviada com sucesso, None caso contrário
        """
        try:
            # Determinar vhost baseado no tipo da tarefa se não especificado
            if vhost is None:
                task_type = task_data.get('tipo', '')
                vhost = TASK_TYPE_TO_VHOST.get(task_type)
                
                if not vhost:
                    logger.error(f"Tipo de tarefa '{task_type}' não mapeado para nenhum vhost")
                    return None
            
            # Validar vhost
            if vhost not in VIRTUAL_HOSTS:
                logger.error(f"Virtual host '{vhost}' não está na lista de vhosts válidos")
                return None
            
            # Adicionar ID à tarefa se não existir
            if 'id' not in task_data:
                task_data['id'] = generate_task_id()
            
            # Adicionar timestamp se não existir
            if 'timestamp' not in task_data:
                task_data['timestamp'] = timestamp_now()
            
            # Gerar message_id
            message_id = str(uuid.uuid4())
            task_data['message_id'] = message_id
            
            # Converter para JSON
            task_data_json = json.dumps(task_data, default=json_serializer)
            
            # Selecionar o ator apropriado baseado no vhost
            if vhost == "fluxo_clinico":
                process_fluxo_clinico.send(task_data_json)
            elif vhost == "fluxo_exames":
                process_fluxo_exames.send(task_data_json)
            elif vhost == "fluxo_opme":
                process_fluxo_opme.send(task_data_json)
            elif vhost == "ingestao_dados":
                process_fluxo_ingestao.send(task_data_json)
            else:
                logger.error(f"Vhost '{vhost}' não suportado")
                return None
            
            logger.info(f"Tarefa enviada via Dramatiq para vhost '{vhost}'. "
                        f"ID da tarefa: {task_data['id']}, Message ID: {message_id}")
            
            return message_id
        
        except Exception as e:
            logger.error(f"Erro ao enviar tarefa via Dramatiq: {e}")
            return None

    # Métodos para compatibilidade com o produtor anterior
    def connect(self, vhost: str):
        """Método mantido para compatibilidade"""
        pass
    
    def close(self, vhost: Optional[str] = None):
        """Método mantido para compatibilidade"""
        pass

# Instância singleton para ser importada pelo FastAPI
producer = DramatiqProducer()