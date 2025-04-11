"""
Worker final do Dramatiq configurado para apenas consumir filas existentes
"""
import os
import sys
import time
import json
import pika
import dramatiq
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
logger = setup_logger("dramatiq_final_worker")

# Flag para controlar o encerramento
should_exit = False

def signal_handler(sig, frame):
    """Handler para sinais de interrupção"""
    global should_exit
    logger.info("Encerrando worker...")
    should_exit = True

def connect_rabbitmq(vhost):
    """
    Conecta ao RabbitMQ em um determinado vhost
    
    Args:
        vhost: Virtual host para conectar
        
    Returns:
        pika.BlockingConnection: Conexão estabelecida
    """
    credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS)
    parameters = pika.ConnectionParameters(
        host=RABBITMQ_HOST,
        port=RABBITMQ_PORT,
        virtual_host=vhost,
        credentials=credentials,
        heartbeat=60
    )
    return pika.BlockingConnection(parameters)

def handler_for_vhost(vhost):
    """
    Retorna o handler adequado para um vhost
    
    Args:
        vhost: Virtual host
        
    Returns:
        function: Handler para o vhost
    """
    if vhost == "fluxo_clinico":
        return process_clinico_task
    elif vhost == "fluxo_exames":
        return process_exame_task
    elif vhost == "fluxo_opme":
        return process_opme_task
    elif vhost == "ingestao_dados":
        return process_ingestao_task
    else:
        raise ValueError(f"Vhost desconhecido: {vhost}")

def process_message(vhost, body):
    """
    Processa uma mensagem usando o handler adequado
    
    Args:
        vhost: Virtual host da mensagem
        body: Corpo da mensagem
        
    Returns:
        Dict: Resultado do processamento
    """
    try:
        # Converter mensagem para JSON
        message_str = body.decode('utf-8')
        task_data = json.loads(message_str)
        
        # Obter handler para o vhost
        handler = handler_for_vhost(vhost)
        
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
        
        # Aqui você poderia salvar o resultado (por exemplo, em um banco de dados)
        
        return result
        
    except Exception as e:
        logger.error(f"[{vhost}] Erro ao processar mensagem: {e}")
        logger.error(traceback.format_exc())
        raise

def callback_factory(vhost, channel):
    """
    Cria função de callback para processar mensagens de um vhost
    
    Args:
        vhost: Virtual host
        channel: Canal RabbitMQ
        
    Returns:
        function: Callback configurado
    """
    def callback(ch, method, properties, body):
        try:
            # Processar mensagem
            result = process_message(vhost, body)
            
            # Confirmar processamento
            ch.basic_ack(delivery_tag=method.delivery_tag)
            logger.info(f"[{vhost}] Mensagem processada e confirmada")
            
        except Exception as e:
            logger.error(f"[{vhost}] Erro no processamento: {e}")
            
            # Decidir se reenvia a mensagem para a fila baseado no tipo de erro
            requeue = True
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=requeue)
            logger.info(f"[{vhost}] Mensagem rejeitada (requeue={requeue})")
    
    return callback

def worker_process(vhost):
    """
    Worker para consumir mensagens de um vhost específico
    
    Args:
        vhost: Virtual host para consumir
    """
    # Configurar handler para sinais
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    logger.info(f"Iniciando worker para vhost '{vhost}'...")
    
    connection = None
    channel = None
    
    # Registrar o Dramatiq para métricas e monitoramento
    # (sem tentar configurar ou criar filas)
    try:
        dramatiq.set_broker(dramatiq.brokers.stub.StubBroker())
    except Exception as e:
        logger.warning(f"Não foi possível inicializar o Dramatiq: {e}")
    
    # Loop principal
    retry_interval = 5  # segundos
    
    while not should_exit:
        try:
            # Estabelecer conexão se necessário
            if connection is None or not connection.is_open:
                connection = connect_rabbitmq(vhost)
                channel = connection.channel()
                
                # Configurar prefetch
                channel.basic_qos(prefetch_count=1)
                
                # Verificar se a fila existe (não tentar modificar)
                try:
                    queue_info = channel.queue_declare(
                        queue=QUEUE_NAME, 
                        passive=True  # Apenas verificar, não tentar criar ou modificar
                    )
                    message_count = queue_info.method.message_count
                    logger.info(f"[{vhost}] Conectado à fila '{QUEUE_NAME}'. Mensagens pendentes: {message_count}")
                    
                    # Configurar consumo
                    channel.basic_consume(
                        queue=QUEUE_NAME,
                        on_message_callback=callback_factory(vhost, channel),
                        auto_ack=False  # Controle manual de ACK/NACK
                    )
                    
                    logger.info(f"[{vhost}] Worker iniciado e aguardando mensagens...")
                    
                except Exception as e:
                    logger.error(f"[{vhost}] Erro ao verificar/configurar fila: {e}")
                    if connection and connection.is_open:
                        connection.close()
                    connection = None
                    time.sleep(retry_interval)
                    continue
            
            # Processar eventos e verificar sinais
            connection.process_data_events(time_limit=1.0)
            time.sleep(0.1)  # Evitar uso intensivo de CPU
            
        except pika.exceptions.AMQPConnectionError as e:
            logger.error(f"[{vhost}] Erro de conexão AMQP: {e}")
            if connection and connection.is_open:
                try:
                    connection.close()
                except:
                    pass
            connection = None
            time.sleep(retry_interval)
            
        except Exception as e:
            logger.error(f"[{vhost}] Erro inesperado: {e}")
            logger.error(traceback.format_exc())
            
            if connection and connection.is_open:
                try:
                    connection.close()
                except:
                    pass
            connection = None
            time.sleep(retry_interval)
    
    # Cleanup ao sair
    if connection and connection.is_open:
        try:
            connection.close()
            logger.info(f"[{vhost}] Conexão encerrada")
        except:
            pass

def main():
    """Função principal para iniciar os workers"""
    global should_exit
    
    # Configurar handler para sinais
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    logger.info(f"Iniciando workers para {len(VIRTUAL_HOSTS)} virtual hosts...")
    
    # Iniciar processo para cada vhost
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
    
    # Monitorar processos
    try:
        while not should_exit:
            for i, (vhost, process) in enumerate(processes):
                if not process.is_alive():
                    logger.warning(f"Worker para vhost '{vhost}' morreu. Reiniciando...")
                    # Reiniciar
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
        
    # Aguardar processos terminarem
    for vhost, process in processes:
        if process.is_alive():
            process.join(timeout=5)
            if process.is_alive():
                logger.warning(f"Worker para '{vhost}' não encerrou graciosamente. Terminando...")
                process.terminate()
    
    logger.info("Todos os workers foram encerrados")

if __name__ == "__main__":
    main()