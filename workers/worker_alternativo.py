"""
Worker simplificado para processamento de tarefas
Este script inicia workers para processar mensagens do RabbitMQ usando CrewAI
"""
import os
import sys
import time
import logging
import json
import pika
import multiprocessing
import signal
import traceback
from datetime import datetime

# Importar configurações
from shared.config import (
    RABBITMQ_HOST, RABBITMQ_PORT, RABBITMQ_USER, RABBITMQ_PASS,
    VIRTUAL_HOSTS, QUEUE_NAME
)
from shared.utils import setup_logger, json_serializer

# Importar handlers específicos
from workers.crewai_handlers.clinico_handler import process_clinico_task
from workers.crewai_handlers.exames_handler import process_exame_task
from workers.crewai_handlers.opme_handler import process_opme_task
from workers.crewai_handlers.ingestao_handler import process_ingestao_task

# Configuração de logging
logger = setup_logger("dramatiq_worker_simple")

# Mapeamento de handlers por virtual host
HANDLERS = {
    "fluxo_clinico": process_clinico_task,
    "fluxo_exames": process_exame_task,
    "fluxo_opme": process_opme_task,
    "ingestao_dados": process_ingestao_task
}

# Flag para controlar o encerramento
should_exit = False

def signal_handler(sig, frame):
    """Handler para sinais de interrupção"""
    global should_exit
    logger.info("Encerrando worker...")
    should_exit = True

def connect_to_rabbitmq(vhost):
    """
    Conecta ao RabbitMQ em um vhost específico
    
    Args:
        vhost: Virtual host para conectar
        
    Returns:
        pika.BlockingConnection: Conexão com o RabbitMQ
    """
    credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS)
    parameters = pika.ConnectionParameters(
        host=RABBITMQ_HOST,
        port=RABBITMQ_PORT,
        virtual_host=vhost,
        credentials=credentials,
        heartbeat=60,
        blocked_connection_timeout=300
    )
    
    connection = pika.BlockingConnection(parameters)
    return connection

def process_message(vhost, body, properties):
    """
    Processa uma mensagem usando o handler adequado
    
    Args:
        vhost: Virtual host da mensagem
        body: Corpo da mensagem
        properties: Propriedades da mensagem
        
    Returns:
        Dict: Resultado do processamento
    """
    try:
        # Converter mensagem para JSON
        message_str = body.decode('utf-8')
        task_data = json.loads(message_str)
        
        # Identificar handler baseado no vhost
        handler = HANDLERS.get(vhost)
        if not handler:
            logger.error(f"Nenhum handler definido para vhost {vhost}")
            return {
                "status": "error",
                "error": f"Nenhum handler definido para vhost {vhost}"
            }
        
        # Log de início do processamento
        task_id = task_data.get("id", "unknown")
        task_type = task_data.get("tipo", "unknown")
        logger.info(f"[{vhost}] Processando tarefa {task_id} (tipo: {task_type})")
        
        # Processar com CrewAI
        start_time = time.time()
        result = handler(task_data)
        elapsed_time = time.time() - start_time
        
        # Log do resultado
        logger.info(f"[{vhost}] Tarefa {task_id} processada em {elapsed_time:.2f} segundos")
        return result
        
    except Exception as e:
        logger.error(f"[{vhost}] Erro ao processar mensagem: {e}")
        logger.error(traceback.format_exc())
        return {
            "status": "error", 
            "error": str(e)
        }

def callback_factory(vhost, channel):
    """
    Cria uma função de callback para um vhost específico
    
    Args:
        vhost: Virtual host
        channel: Canal do RabbitMQ
        
    Returns:
        function: Função de callback
    """
    def callback(ch, method, properties, body):
        """Callback para processar mensagens"""
        try:
            # Processar a mensagem
            result = process_message(vhost, body, properties)
            
            # Confirmar processamento
            ch.basic_ack(delivery_tag=method.delivery_tag)
            logger.info(f"[{vhost}] Mensagem confirmada (ACK)")
            
            # Salvar resultado (poderia ser em um banco de dados)
            try:
                result_json = json.dumps(result, default=json_serializer)
                logger.info(f"[{vhost}] Resultado salvo (tamanho: {len(result_json)})")
            except Exception as e:
                logger.error(f"[{vhost}] Erro ao serializar resultado: {e}")
            
        except Exception as e:
            logger.error(f"[{vhost}] Erro no callback: {e}")
            # Rejeitar com possibilidade de retentativa
            requeue = True
            try:
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=requeue)
                logger.info(f"[{vhost}] Mensagem rejeitada (requeue={requeue})")
            except Exception as nack_e:
                logger.error(f"[{vhost}] Erro ao rejeitar mensagem: {nack_e}")
    
    return callback

def worker_process(vhost):
    """
    Processo worker para consumir mensagens de um vhost
    
    Args:
        vhost: Virtual host para consumir
    """
    # Configurar handler para sinais
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    logger.info(f"[{vhost}] Iniciando worker...")
    
    connection = None
    channel = None
    
    # Loop principal
    while not should_exit:
        try:
            # Se não há conexão ou a conexão foi fechada, conectar novamente
            if connection is None or not connection.is_open:
                connection = connect_to_rabbitmq(vhost)
                channel = connection.channel()
                
                # Configurar prefetch
                channel.basic_qos(prefetch_count=1)
                
                # Verificar se a fila existe
                try:
                    queue_declare_result = channel.queue_declare(
                        queue=QUEUE_NAME, 
                        passive=True
                    )
                    logger.info(f"[{vhost}] Fila '{QUEUE_NAME}' encontrada. "
                               f"Mensagens: {queue_declare_result.method.message_count}")
                except Exception as e:
                    logger.warning(f"[{vhost}] A fila '{QUEUE_NAME}' não existe ou não é acessível: {e}")
                    time.sleep(5)
                    continue
                
                # Configurar consumo
                channel.basic_consume(
                    queue=QUEUE_NAME,
                    on_message_callback=callback_factory(vhost, channel),
                    auto_ack=False
                )
                
                logger.info(f"[{vhost}] Worker iniciado e aguardando mensagens...")
            
            # Processar mensagens com timeout para verificar should_exit
            connection.process_data_events(time_limit=1.0)
            time.sleep(0.1)  # Pequena pausa para não sobrecarregar CPU
            
        except pika.exceptions.AMQPConnectionError as e:
            logger.error(f"[{vhost}] Erro de conexão AMQP: {e}")
            if connection and connection.is_open:
                try:
                    connection.close()
                except:
                    pass
            connection = None
            time.sleep(5)  # Aguardar antes de tentar reconectar
            
        except Exception as e:
            logger.error(f"[{vhost}] Erro inesperado: {e}")
            logger.error(traceback.format_exc())
            
            if connection and connection.is_open:
                try:
                    connection.close()
                except:
                    pass
            connection = None
            time.sleep(5)
    
    # Cleanup
    if connection and connection.is_open:
        try:
            connection.close()
        except:
            pass
    
    logger.info(f"[{vhost}] Worker encerrado")

def main():
    """Função principal para iniciar os workers"""
    global should_exit
    
    # Configurar handler para sinais
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    logger.info(f"Iniciando workers para {len(VIRTUAL_HOSTS)} virtual hosts...")
    
    # Iniciar um processo para cada vhost
    processes = []
    for vhost in VIRTUAL_HOSTS:
        process = multiprocessing.Process(
            target=worker_process,
            args=(vhost,),
            name=f"worker-{vhost}"
        )
        process.daemon = True
        processes.append((vhost, process))
        process.start()
        logger.info(f"Worker para vhost '{vhost}' iniciado (PID: {process.pid})")
    
    # Monitorar os processos
    try:
        while not should_exit:
            for i, (vhost, process) in enumerate(processes):
                if not process.is_alive():
                    logger.warning(f"Worker para vhost '{vhost}' morreu. Reiniciando...")
                    # Reiniciar processo
                    new_process = multiprocessing.Process(
                        target=worker_process,
                        args=(vhost,),
                        name=f"worker-{vhost}"
                    )
                    new_process.daemon = True
                    processes[i] = (vhost, new_process)
                    new_process.start()
                    logger.info(f"Worker para vhost '{vhost}' reiniciado (PID: {new_process.pid})")
            
            # Verificar a cada 30 segundos
            time.sleep(30)
            
    except KeyboardInterrupt:
        logger.info("Interrupção detectada. Encerrando workers...")
        should_exit = True
        
    # Aguardar todos os processos terminarem
    for vhost, process in processes:
        if process.is_alive():
            process.join(timeout=5)
            if process.is_alive():
                logger.warning(f"Worker para '{vhost}' não encerrou graciosamente. Terminando...")
                process.terminate()
    
    logger.info("Todos os workers foram encerrados")

if __name__ == "__main__":
    main()