"""
Router para o fluxo clínico na API
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from typing import Dict, Any

from api.models.schemas import ConsultaTask, TaskResponse, StatusResponse
from api.services.rabbitmq_producer import producer
from shared.utils import setup_logger, generate_task_id

# Configuração de logging
logger = setup_logger("api_router_clinico")

# Criar router
router = APIRouter(
    prefix="/api/clinico",
    tags=["Fluxo Clínico"],
    responses={404: {"description": "Not found"}},
)

@router.post("/consulta/", response_model=TaskResponse, status_code=202)
async def criar_consulta(
    consulta: ConsultaTask, 
    background_tasks: BackgroundTasks
):
    """
    Cria uma nova tarefa de consulta médica no fluxo clínico
    """
    # Preparar dados da tarefa
    task_data = consulta.dict()
    
    # Enviar tarefa para a fila (em background para não bloquear a resposta)
    def send_to_queue():
        message_id = producer.send_task(task_data, vhost="fluxo_clinico")
        if not message_id:
            logger.error(f"Falha ao enviar tarefa {task_data['id']} para a fila")
    
    background_tasks.add_task(send_to_queue)
    
    return {
        "message": "Consulta enviada para processamento",
        "task_id": task_data["id"],
        "status": "pending"
    }

@router.post("/internacao/", response_model=TaskResponse, status_code=202)
async def criar_internacao(
    dados: Dict[str, Any],
    background_tasks: BackgroundTasks
):
    """
    Cria uma nova tarefa de internação no fluxo clínico
    """
    # Gerar ID único para a tarefa
    task_id = generate_task_id()
    
    # Preparar dados da tarefa
    task_data = {
        "id": task_id,
        "tipo": "internacao",
        "dados": dados,
        "prioridade": dados.get("urgente", False) and 1 or 0
    }
    
    # Enviar tarefa para a fila
    def send_to_queue():
        message_id = producer.send_task(task_data, vhost="fluxo_clinico")
        if not message_id:
            logger.error(f"Falha ao enviar tarefa {task_id} para a fila")
    
    background_tasks.add_task(send_to_queue)
    
    return {
        "message": "Internação enviada para processamento",
        "task_id": task_id,
        "status": "pending"
    }

@router.post("/alta/", response_model=TaskResponse, status_code=202)
async def criar_alta(
    dados: Dict[str, Any],
    background_tasks: BackgroundTasks
):
    """
    Cria uma nova tarefa de alta hospitalar no fluxo clínico
    """
    # Gerar ID único para a tarefa
    task_id = generate_task_id()
    
    # Preparar dados da tarefa
    task_data = {
        "id": task_id,
        "tipo": "alta",
        "dados": dados
    }
    
    # Enviar tarefa para a fila
    def send_to_queue():
        message_id = producer.send_task(task_data, vhost="fluxo_clinico")
        if not message_id:
            logger.error(f"Falha ao enviar tarefa {task_id} para a fila")
    
    background_tasks.add_task(send_to_queue)
    
    return {
        "message": "Alta enviada para processamento",
        "task_id": task_id,
        "status": "pending"
    }

@router.get("/status/{task_id}", response_model=StatusResponse)
async def verificar_status(task_id: str):
    """
    Verifica o status de uma tarefa no fluxo clínico
    
    (Nota: Esta é uma simulação - em produção, consultaria um banco de dados)
    """
    # Simulação - em produção, consultaria um banco de dados
    return {
        "task_id": task_id,
        "status": "processing",  # ou "completed", "failed", etc.
        "resultado": None,
        "erro": None,
        "timestamp": "2023-01-01T00:00:00"
    }