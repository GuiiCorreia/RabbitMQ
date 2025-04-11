"""
Router para o fluxo de exames na API
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from typing import Dict, Any, List

from api.models.schemas import ExameTask, TaskResponse, StatusResponse, TipoExame
from api.services.rabbitmq_producer import producer
from shared.utils import setup_logger, generate_task_id

# Configuração de logging
logger = setup_logger("api_router_exames")

# Criar router
router = APIRouter(
    prefix="/api/exames",
    tags=["Fluxo de Exames"],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=TaskResponse, status_code=202)
async def criar_exame(
    exame: ExameTask, 
    background_tasks: BackgroundTasks
):
    """
    Cria uma nova tarefa de exame médico
    """
    # Preparar dados da tarefa
    task_data = exame.dict()
    
    # Enviar tarefa para a fila (em background para não bloquear a resposta)
    def send_to_queue():
        message_id = producer.send_task(task_data, vhost="fluxo_exames")
        if not message_id:
            logger.error(f"Falha ao enviar tarefa {task_data['id']} para a fila")
    
    background_tasks.add_task(send_to_queue)
    
    return {
        "message": f"Exame de {exame.tipo} enviado para processamento",
        "task_id": task_data["id"],
        "status": "pending"
    }

@router.post("/hemograma/", response_model=TaskResponse, status_code=202)
async def criar_hemograma(
    dados: Dict[str, Any],
    background_tasks: BackgroundTasks
):
    """
    Cria uma nova tarefa específica de hemograma
    """
    # Gerar ID único para a tarefa
    task_id = generate_task_id()
    
    # Preparar dados da tarefa
    task_data = {
        "id": task_id,
        "tipo": "hemograma",
        "dados": dados,
        "prioridade": dados.get("urgente", False) and 1 or 0
    }
    
    # Enviar tarefa para a fila
    def send_to_queue():
        message_id = producer.send_task(task_data, vhost="fluxo_exames")
        if not message_id:
            logger.error(f"Falha ao enviar tarefa {task_id} para a fila")
    
    background_tasks.add_task(send_to_queue)
    
    return {
        "message": "Hemograma enviado para processamento",
        "task_id": task_id,
        "status": "pending"
    }

@router.post("/imagem/{tipo_exame}", response_model=TaskResponse, status_code=202)
async def criar_exame_imagem(
    tipo_exame: TipoExame,
    dados: Dict[str, Any],
    background_tasks: BackgroundTasks
):
    """
    Cria uma nova tarefa de exame de imagem 
    (raio_x, tomografia, ultrassonografia, ressonancia)
    """
    # Validar tipo de exame (deve ser um exame de imagem)
    exames_imagem = [
        TipoExame.RAIO_X, 
        TipoExame.TOMOGRAFIA, 
        TipoExame.ULTRASSONOGRAFIA, 
        TipoExame.RESSONANCIA
    ]
    
    if tipo_exame not in exames_imagem:
        raise HTTPException(
            status_code=400, 
            detail=f"Tipo de exame inválido. Deve ser um dos seguintes: {[e.value for e in exames_imagem]}"
        )
    
    # Gerar ID único para a tarefa
    task_id = generate_task_id()
    
    # Preparar dados da tarefa
    task_data = {
        "id": task_id,
        "tipo": tipo_exame.value,
        "dados": dados,
        "prioridade": dados.get("urgente", False) and 1 or 0
    }
    
    # Enviar tarefa para a fila
    def send_to_queue():
        message_id = producer.send_task(task_data, vhost="fluxo_exames")
        if not message_id:
            logger.error(f"Falha ao enviar tarefa {task_id} para a fila")
    
    background_tasks.add_task(send_to_queue)
    
    return {
        "message": f"Exame de {tipo_exame.value} enviado para processamento",
        "task_id": task_id,
        "status": "pending"
    }

@router.get("/tipos/", response_model=List[str])
async def listar_tipos_exame():
    """
    Lista todos os tipos de exame disponíveis
    """
    return [tipo.value for tipo in TipoExame]

@router.get("/status/{task_id}", response_model=StatusResponse)
async def verificar_status(task_id: str):
    """
    Verifica o status de uma tarefa no fluxo de exames
    
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