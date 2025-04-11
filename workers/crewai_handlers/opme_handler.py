"""
Handler específico para processar tarefas do fluxo OPME com CrewAI
"""
from typing import Dict, Any, List
from datetime import datetime
import json

from crewai import Agent, Task, Crew
# Não importar Task de crewai.tasks

from shared.utils import setup_logger

# Configuração de logging
logger = setup_logger("opme_handler")

def process_protese(task_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Processa uma tarefa de prótese usando CrewAI
    
    Args:
        task_data: Dados da tarefa recebida
        
    Returns:
        Dict: Resultado do processamento
    """
    logger.info(f"Processando solicitação de prótese - ID: {task_data.get('id')}")
    
    try:
        # Extrair dados relevantes
        paciente = task_data.get("paciente", {})
        cirurgiao = task_data.get("cirurgiao", {})
        procedimento = task_data.get("procedimento", "")
        itens = task_data.get("itens", [])
        
        # Criar string de itens para processamento
        itens_str = ""
        for i, item in enumerate(itens, 1):
            itens_str += f"{i}. Código: {item.get('codigo', 'N/A')}, "
            itens_str += f"Descrição: {item.get('descricao', 'N/A')}, "
            itens_str += f"Quantidade: {item.get('quantidade', 1)}\n"
        
        # Criar agentes CrewAI
        orthopedic_specialist = Agent(
            role="Orthopedic Specialist",
            goal="Evaluate prosthetic requirements and provide clinical recommendations",
            backstory="You are a highly experienced orthopedic surgeon specializing in "
                    "joint replacements and prosthetic selection. You have performed "
                    "hundreds of implant surgeries and understand the critical factors "
                    "in prosthetic selection.",
            verbose=True
        )
        
        material_analyst = Agent(
            role="Medical Materials Analyst",
            goal="Analyze prosthetic materials and ensure optimal selection",
            backstory="You are a specialist in medical materials with expertise in "
                    "biocompatibility, durability, and functional characteristics of "
                    "various prosthetic options.",
            verbose=True
        )
        
        # Criar tarefa
        analysis_task = Task(
            description=f"""
            Analyze the following prosthetic request:
            
            Patient: {paciente.get('nome', 'Unknown')}, ID: {paciente.get('id', 'Unknown')}
            Age: {paciente.get('idade', 'Not specified')}
            
            Surgeon: {cirurgiao.get('nome', 'Unknown')}, Specialty: {cirurgiao.get('especialidade', 'Unknown')}
            
            Procedure: {procedimento}
            
            Requested items:
            {itens_str}
            
            Your task is to:
            1. Evaluate the appropriateness of the requested prosthetics for the procedure
            2. Discuss key considerations for this type of prosthetic
            3. Identify potential alternatives or complements if applicable
            4. Explain the expected outcomes and lifespan of the requested implants
            
            Be thorough and precise in your analysis.
            """,
            agent=orthopedic_specialist
        )
        
        materials_task = Task(
            description=f"""
            Based on the orthopedic specialist's analysis, provide a detailed materials assessment:
            
            1. Analyze the materials of the requested prosthetics
            2. Discuss their biomechanical properties and biocompatibility
            3. Evaluate durability and wear characteristics
            4. Consider patient-specific factors that might influence material selection
            5. Recommend optimal material choices based on the patient and procedure
            
            Focus on evidence-based recommendations and current best practices in materials science.
            """,
            agent=material_analyst
        )
        
        # Criar crew
        crew = Crew(
            agents=[orthopedic_specialist, material_analyst],
            tasks=[analysis_task, materials_task],
            verbose=True
        )
        
        # Executar análise
        result = crew.kickoff()
        
        # Retornar resultado
        return {
            "task_id": task_data.get("id"),
            "result": result,
            "analysis_summary": "Análise de prótese completa",
            "status": "completed",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Erro ao processar solicitação de prótese: {e}")
        return {
            "task_id": task_data.get("id"),
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

def process_material(task_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Processa uma tarefa de material especial usando CrewAI
    
    Args:
        task_data: Dados da tarefa recebida
        
    Returns:
        Dict: Resultado do processamento
    """
    logger.info(f"Processando solicitação de material especial - ID: {task_data.get('id')}")
    
    try:
        # Extrair dados relevantes
        dados = task_data.get("dados", {})
        
        # Criar agentes CrewAI
        material_specialist = Agent(
            role="Medical Supplies Specialist",
            goal="Evaluate special medical materials and ensure appropriate selection",
            backstory="You are a specialist in medical supplies and special materials "
                    "with extensive knowledge of surgical consumables, implantable "
                    "devices, and specialized medical equipment.",
            verbose=True
        )
        
        # Criar tarefa
        analysis_task = Task(
            description=f"""
            Analyze the following special material request:
            
            {json.dumps(dados, indent=2)}
            
            Your task is to:
            1. Evaluate the appropriateness of the requested materials
            2. Discuss specifications and quality considerations
            3. Identify potential alternatives if applicable
            4. Provide recommendations for handling and utilization
            
            Be thorough and precise in your analysis.
            """,
            agent=material_specialist
        )
        
        # Criar crew
        crew = Crew(
            agents=[material_specialist],
            tasks=[analysis_task],
            verbose=True
        )
        
        # Executar análise
        result = crew.kickoff()
        
        # Retornar resultado
        return {
            "task_id": task_data.get("id"),
            "result": result,
            "status": "completed",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Erro ao processar solicitação de material especial: {e}")
        return {
            "task_id": task_data.get("id"),
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

def process_opme_task(task_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Processa uma tarefa do fluxo OPME baseado no tipo
    
    Args:
        task_data: Dados da tarefa recebida
        
    Returns:
        Dict: Resultado do processamento
    """
    task_type = task_data.get("tipo", "").lower()
    
    # Direcionar para o handler específico baseado no tipo
    if task_type == "protese":
        return process_protese(task_data)
    elif task_type == "material":
        return process_material(task_data)
    elif task_type == "orgao":
        # Handler para órgãos (transplantes) seria implementado aqui
        logger.info(f"Processando solicitação de órgão - ID: {task_data.get('id')}")
        return {
            "task_id": task_data.get("id"),
            "status": "completed",
            "result": "Análise de solicitação de órgão para transplante",
            "timestamp": datetime.now().isoformat()
        }
    else:
        logger.warning(f"Tipo de OPME desconhecido: {task_type}")
        return {
            "task_id": task_data.get("id"),
            "status": "error",
            "error": f"Tipo de OPME desconhecido: {task_type}",
            "timestamp": datetime.now().isoformat()
        }