"""
Serviço para produção de mensagens no RabbitMQ a partir da API
"""
import pika
import json
import uuid
from datetime import datetime
from typing import Dict, Any, Optional

from shared.config import (
    RABBITMQ_HOST, RABBITMQ_PORT, RABBITMQ_USER, RABBITMQ_PASS,
    QUEUE_NAME, VIRTUAL_HOSTS, TASK_TYPE_TO_VHOST
)
from shared.utils import setup_logger, generate_task_id, timestamp_now

# Configuração de logging
logger = setup_logger('rabbitmq_producer')

# Serializador personalizado para datetime
def json_serializer(obj):
    """Serializador personalizado para objetos que o JSON padrão não suporta"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")

class RabbitMQProducer:
    """Classe para gerenciar a produção de mensagens para o RabbitMQ"""
    
    def __init__(self):
        self.connections = {}  # Conexões por vhost
        self.channels = {}     # Canais por vhost
    
    def connect(self, vhost: str):
        """
        Estabelece conexão com o RabbitMQ para um virtual host específico
        
        Args:
            vhost: Virtual host para conectar
        """
        # Verificar se já existe uma conexão aberta
        if vhost in self.connections and self.connections[vhost].is_open:
            return
            
        credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS)
        parameters = pika.ConnectionParameters(
            host=RABBITMQ_HOST,
            port=RABBITMQ_PORT,
            virtual_host=vhost,
            credentials=credentials,
            heartbeat=60
        )
        
        self.connections[vhost] = pika.BlockingConnection(parameters)
        self.channels[vhost] = self.connections[vhost].channel()
        
        # Verificar se a fila existe (não declarar, pois é uma quorum queue)
        try:
            self.channels[vhost].queue_declare(queue=QUEUE_NAME, passive=True)
            logger.info(f"Fila '{QUEUE_NAME}' encontrada no vhost '{vhost}'")
        except Exception as e:
            logger.warning(f"Erro ao verificar fila: {e}")
            logger.warning("As Quorum Queues devem ser declaradas com políticas específicas no RabbitMQ")
        
        logger.info(f"Conectado ao RabbitMQ ({RABBITMQ_HOST}:{RABBITMQ_PORT}, vhost={vhost})")
    
    def close(self, vhost: Optional[str] = None):
        """
        Fecha a conexão com o RabbitMQ
        
        Args:
            vhost: Virtual host específico para fechar (ou todos se None)
        """
        if vhost:
            # Fechar conexão específica
            if vhost in self.connections and self.connections[vhost].is_open:
                self.connections[vhost].close()
                logger.info(f"Conexão com RabbitMQ fechada para vhost '{vhost}'")
                del self.connections[vhost]
                if vhost in self.channels:
                    del self.channels[vhost]
        else:
            # Fechar todas as conexões
            for vh, conn in list(self.connections.items()):
                if conn.is_open:
                    conn.close()
                    logger.info(f"Conexão com RabbitMQ fechada para vhost '{vh}'")
            
            self.connections = {}
            self.channels = {}
    
    def send_task(self, task_data: Dict[str, Any], vhost: Optional[str] = None) -> Optional[str]:
        """
        Envia uma tarefa para a fila do RabbitMQ
        
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
            
            # Garantir que temos uma conexão
            self.connect(vhost)
            
            # Adicionar ID à tarefa se não existir
            if 'id' not in task_data:
                task_data['id'] = generate_task_id()
            
            # Adicionar timestamp se não existir
            if 'timestamp' not in task_data:
                task_data['timestamp'] = timestamp_now()
            
            # Converter os dados para JSON usando o serializador personalizado
            message_body = json.dumps(task_data, default=json_serializer)
            
            # Gerar message_id
            message_id = str(uuid.uuid4())
            
            # Publicar a mensagem
            self.channels[vhost].basic_publish(
                exchange='',  # Exchange padrão
                routing_key=QUEUE_NAME,  # Nome da fila
                body=message_body,
                properties=pika.BasicProperties(
                    delivery_mode=2,  # Mensagem persistente
                    content_type='application/json',
                    message_id=message_id
                )
            )
            
            logger.info(f"Tarefa enviada para a fila '{QUEUE_NAME}' no vhost '{vhost}'. "
                        f"ID da tarefa: {task_data['id']}, Message ID: {message_id}")
            return message_id
            
        except Exception as e:
            logger.error(f"Erro ao enviar tarefa para a fila: {e}")
            if vhost and vhost in self.connections:
                # Fechar conexão problemática para reconectar na próxima tentativa
                self.close(vhost)
            return None

# Instância singleton para ser importada pelo FastAPI
producer = RabbitMQProducer()