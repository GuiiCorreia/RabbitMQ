"""
Router para o fluxo OPME (Órteses, Próteses e Materiais Especiais) na API
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from typing import Dict, Any, List

from api.models.schemas import OPMETask, TaskResponse, StatusResponse
from api.services.rabbitmq_producer import producer
from shared.utils import setup_logger, generate_task_id

# Configuração de logging
logger = setup_logger("api_router_opme")

# Criar router
router = APIRouter(
    prefix="/api/opme",
    tags=["Fluxo OPME"],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=TaskResponse, status_code=202)
async def criar_opme(
    opme: OPMETask, 
    background_tasks: BackgroundTasks
):
    """
    Cria uma nova tarefa de OPME
    """
    # Preparar dados da tarefa
    task_data = opme.dict()
    
    # Enviar tarefa para a fila (em background para não bloquear a resposta)
    def send_to_queue():
        message_id = producer.send_task(task_data, vhost="fluxo_opme")
        if not message_id:
            logger.error(f"Falha ao enviar tarefa {task_data['id']} para a fila")
    
    background_tasks.add_task(send_to_queue)
    
    return {
        "message": f"Solicitação de {opme.tipo} enviada para processamento",
        "task_id": task_data["id"],
        "status": "pending"
    }

@router.post("/protese/", response_model=TaskResponse, status_code=202)
async def criar_protese(
    dados: Dict[str, Any],
    background_tasks: BackgroundTasks
):
    """
    Cria uma nova tarefa específica de prótese
    """
    # Gerar ID único para a tarefa
    task_id = generate_task_id()
    
    # Preparar dados da tarefa
    task_data = {
        "id": task_id,
        "tipo": "protese",
        "dados": dados,
        "prioridade": dados.get("urgencia", False) and 1 or 0
    }
    
    # Enviar tarefa para a fila
    def send_to_queue():
        message_id = producer.send_task(task_data, vhost="fluxo_opme")
        if not message_id:
            logger.error(f"Falha ao enviar tarefa {task_id} para a fila")
    
    background_tasks.add_task(send_to_queue)
    
    return {
        "message": "Solicitação de prótese enviada para processamento",
        "task_id": task_id,
        "status": "pending"
    }

@router.post("/material/", response_model=TaskResponse, status_code=202)
async def criar_material(
    dados: Dict[str, Any],
    background_tasks: BackgroundTasks
):
    """
    Cria uma nova tarefa de material especial
    """
    # Gerar ID único para a tarefa
    task_id = generate_task_id()
    
    # Preparar dados da tarefa
    task_data = {
        "id": task_id,
        "tipo": "material",
        "dados": dados,
        "prioridade": dados.get("urgencia", False) and 1 or 0
    }
    
    # Enviar tarefa para a fila
    def send_to_queue():
        message_id = producer.send_task(task_data, vhost="fluxo_opme")
        if not message_id:
            logger.error(f"Falha ao enviar tarefa {task_id} para a fila")
    
    background_tasks.add_task(send_to_queue)
    
    return {
        "message": "Solicitação de material especial enviada para processamento",
        "task_id": task_id,
        "status": "pending"
    }

@router.get("/status/{task_id}", response_model=StatusResponse)
async def verificar_status(task_id: str):
    """
    Verifica o status de uma tarefa no fluxo OPME
    
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