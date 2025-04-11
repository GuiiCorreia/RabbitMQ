"""
Router para o fluxo de ingestão de dados na API
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from typing import Dict, Any, List

from api.models.schemas import IngestaoTask, FormatoIngestao, TaskResponse, StatusResponse
from api.services.rabbitmq_producer import producer
from shared.utils import setup_logger, generate_task_id

# Configuração de logging
logger = setup_logger("api_router_ingestao")

# Criar router
router = APIRouter(
    prefix="/api/ingestao",
    tags=["Fluxo de Ingestão"],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=TaskResponse, status_code=202)
async def criar_ingestao(
    ingestao: IngestaoTask, 
    background_tasks: BackgroundTasks
):
    """
    Cria uma nova tarefa de ingestão de dados
    """
    # Preparar dados da tarefa
    task_data = ingestao.dict()
    
    # Enviar tarefa para a fila (em background para não bloquear a resposta)
    def send_to_queue():
        message_id = producer.send_task(task_data, vhost="ingestao_dados")
        if not message_id:
            logger.error(f"Falha ao enviar tarefa {task_data['id']} para a fila")
    
    background_tasks.add_task(send_to_queue)
    
    return {
        "message": f"Ingestão de dados ({ingestao.tipo}) enviada para processamento",
        "task_id": task_data["id"],
        "status": "pending"
    }

@router.post("/pacientes/", response_model=TaskResponse, status_code=202)
async def criar_ingestao_pacientes(
    dados: Dict[str, Any],
    background_tasks: BackgroundTasks
):
    """
    Cria uma nova tarefa de ingestão de dados de pacientes
    """
    # Validar formato
    formato = dados.get("formato")
    if formato and formato not in [f.value for f in FormatoIngestao]:
        raise HTTPException(
            status_code=400, 
            detail=f"Formato inválido. Deve ser um dos seguintes: {[f.value for f in FormatoIngestao]}"
        )
    
    # Gerar ID único para a tarefa
    task_id = generate_task_id()
    
    # Preparar dados da tarefa
    task_data = {
        "id": task_id,
        "tipo": "carga_pacientes",
        "origem": dados.get("origem", "sistema_externo"),
        "formato": dados.get("formato", "csv"),
        "quantidade_registros": dados.get("quantidade_registros"),
        "metadados": dados.get("metadados")
    }
    
    # Enviar tarefa para a fila
    def send_to_queue():
        message_id = producer.send_task(task_data, vhost="ingestao_dados")
        if not message_id:
            logger.error(f"Falha ao enviar tarefa {task_id} para a fila")
    
    background_tasks.add_task(send_to_queue)
    
    return {
        "message": "Ingestão de dados de pacientes enviada para processamento",
        "task_id": task_id,
        "status": "pending"
    }

@router.post("/medicos/", response_model=TaskResponse, status_code=202)
async def criar_ingestao_medicos(
    dados: Dict[str, Any],
    background_tasks: BackgroundTasks
):
    """
    Cria uma nova tarefa de ingestão de dados de médicos
    """
    # Gerar ID único para a tarefa
    task_id = generate_task_id()
    
    # Preparar dados da tarefa
    task_data = {
        "id": task_id,
        "tipo": "carga_medicos",
        "origem": dados.get("origem", "sistema_externo"),
        "formato": dados.get("formato", "csv"),
        "quantidade_registros": dados.get("quantidade_registros"),
        "metadados": dados.get("metadados")
    }
    
    # Enviar tarefa para a fila
    def send_to_queue():
        message_id = producer.send_task(task_data, vhost="ingestao_dados")
        if not message_id:
            logger.error(f"Falha ao enviar tarefa {task_id} para a fila")
    
    background_tasks.add_task(send_to_queue)
    
    return {
        "message": "Ingestão de dados de médicos enviada para processamento",
        "task_id": task_id,
        "status": "pending"
    }

@router.get("/formatos/", response_model=List[str])
async def listar_formatos():
    """
    Lista todos os formatos de arquivo suportados para ingestão
    """
    return [formato.value for formato in FormatoIngestao]

@router.get("/status/{task_id}", response_model=StatusResponse)
async def verificar_status(task_id: str):
    """
    Verifica o status de uma tarefa no fluxo de ingestão
    
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