"""
Modelos Pydantic para validação de dados na API
"""
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum
import uuid

# Classes base
class BaseTask(BaseModel):
    """Modelo base para todas as tarefas"""
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))
    prioridade: Optional[int] = 0
    timestamp: Optional[datetime] = Field(default_factory=datetime.now)

# Modelos para Fluxo Clínico
class Pessoa(BaseModel):
    """Modelo para representar uma pessoa (paciente, médico, etc)"""
    id: int
    nome: str
    
class Paciente(Pessoa):
    """Modelo específico para pacientes"""
    idade: Optional[int] = None
    genero: Optional[str] = None

class Medico(Pessoa):
    """Modelo específico para médicos"""
    especialidade: Optional[str] = None
    crm: Optional[str] = None

class TipoConsulta(str, Enum):
    """Tipos de consulta disponíveis"""
    INICIAL = "inicial"
    RETORNO = "retorno"
    EMERGENCIA = "emergencia"

class ConsultaTask(BaseTask):
    """Tarefa de consulta médica"""
    tipo: str = "consulta"
    paciente: Paciente
    medico: Medico
    data: datetime
    tipo_consulta: TipoConsulta
    observacoes: Optional[str] = None

# Modelos para Fluxo de Exames
class TipoExame(str, Enum):
    """Tipos de exame disponíveis"""
    HEMOGRAMA = "hemograma"
    RAIO_X = "raio_x"
    TOMOGRAFIA = "tomografia"
    ULTRASSONOGRAFIA = "ultrassonografia"
    RESSONANCIA = "ressonancia"

class ExameTask(BaseTask):
    """Tarefa de exame médico"""
    tipo: str = Field(default="hemograma")
    paciente: Paciente
    solicitante: Medico
    data_solicitacao: datetime = Field(default_factory=datetime.now)
    urgente: bool = False
    observacoes: Optional[str] = None

# Modelos para Fluxo OPME
class ItemOPME(BaseModel):
    """Item de OPME (órtese, prótese, materiais especiais)"""
    codigo: str
    descricao: str
    quantidade: int = 1

class OPMETask(BaseTask):
    """Tarefa de OPME"""
    tipo: str = "protese"
    paciente: Paciente
    cirurgiao: Medico
    procedimento: str
    data_cirurgia: datetime
    itens: List[ItemOPME]
    
# Modelos para Fluxo de Ingestão de Dados
class TipoIngestao(str, Enum):
    """Tipos de ingestão de dados"""
    PACIENTES = "pacientes"
    MEDICOS = "medicos"
    EXAMES = "exames"

class FormatoIngestao(str, Enum):
    """Formatos de arquivo para ingestão"""
    CSV = "csv"
    JSON = "json"
    XML = "xml"
    HL7 = "hl7"

class IngestaoTask(BaseTask):
    """Tarefa de ingestão de dados"""
    tipo: str = "carga_pacientes"
    origem: str
    formato: FormatoIngestao
    quantidade_registros: Optional[int] = None
    metadados: Optional[Dict[str, Any]] = None

# Modelo genérico para tarefas
class GenericTask(BaseTask):
    """Modelo genérico para qualquer tipo de tarefa"""
    tipo: str
    dados: Dict[str, Any]

# Modelos de resposta
class TaskResponse(BaseModel):
    """Resposta após criar uma tarefa"""
    message: str
    task_id: str
    status: str = "pending"

class StatusResponse(BaseModel):
    """Resposta ao verificar status de uma tarefa"""
    task_id: str
    status: str
    resultado: Optional[Any] = None
    erro: Optional[str] = None
    timestamp: datetime