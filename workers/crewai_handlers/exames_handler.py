"""
Handler específico para processar tarefas do fluxo de exames com CrewAI
"""
from typing import Dict, Any
from datetime import datetime
import json

from crewai import Agent, Task, Crew
# Não importar Task de crewai.tasks

from shared.utils import setup_logger

# Configuração de logging
logger = setup_logger("exames_handler")

def process_hemograma(task_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Processa uma tarefa de hemograma usando CrewAI
    
    Args:
        task_data: Dados da tarefa recebida
        
    Returns:
        Dict: Resultado do processamento
    """
    logger.info(f"Processando hemograma - ID: {task_data.get('id')}")
    
    try:
        # Extrair dados relevantes
        paciente = task_data.get("paciente", {})
        solicitante = task_data.get("solicitante", {})
        observacoes = task_data.get("observacoes", "")
        
        # Criar agentes CrewAI
        lab_analyst = Agent(
            role="Laboratory Analyst",
            goal="Provide accurate and comprehensive blood test analysis",
            backstory="You are an experienced laboratory analyst with expertise in hematology. "
                    "You have analyzed thousands of blood samples and can identify patterns "
                    "and anomalies in blood test results.",
            verbose=True
        )
        
        hematologist = Agent(
            role="Hematologist",
            goal="Interpret blood test results and provide clinical insights",
            backstory="You are a specialized hematologist with years of experience in diagnosing "
                    "blood disorders and interpreting complex blood test results.",
            verbose=True
        )
        
        # Criar tarefa
        analysis_task = Task(
            description=f"""
            Analyze the following blood test request:
            
            Patient: {paciente.get('nome', 'Unknown')}, ID: {paciente.get('id', 'Unknown')}
            Age: {paciente.get('idade', 'Not specified')}
            
            Requester: {solicitante.get('nome', 'Unknown')}, Specialty: {solicitante.get('especialidade', 'Unknown')}
            
            Observations: {observacoes}
            
            Your task is to:
            1. Determine what blood parameters should be analyzed based on the available information
            2. Explain the significance of each parameter
            3. Describe what abnormal values might indicate
            4. Suggest any additional tests that might be needed based on the clinical scenario
            
            Be thorough and precise in your analysis.
            """,
            agent=lab_analyst
        )
        
        interpretation_task = Task(
            description=f"""
            Based on the laboratory analyst's recommendations:
            
            1. Provide a clinical interpretation of the suggested tests
            2. Explain how the results would guide clinical decision-making
            3. Discuss potential diagnoses that might be confirmed or ruled out by these tests
            4. Suggest appropriate follow-up based on potential results
            
            Focus on clinical relevance and actionable information for the requesting physician.
            """,
            agent=hematologist
        )
        
        # Criar crew
        crew = Crew(
            agents=[lab_analyst, hematologist],
            tasks=[analysis_task, interpretation_task],
            verbose=True
        )
        
        # Executar análise
        result = crew.kickoff()
        
        # Retornar resultado
        return {
            "task_id": task_data.get("id"),
            "result": result,
            "analysis_summary": "Análise de hemograma completa",
            "status": "completed",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Erro ao processar hemograma: {e}")
        return {
            "task_id": task_data.get("id"),
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

def process_imagem(task_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Processa uma tarefa de exame de imagem usando CrewAI
    
    Args:
        task_data: Dados da tarefa recebida
        
    Returns:
        Dict: Resultado do processamento
    """
    logger.info(f"Processando exame de imagem ({task_data.get('tipo')}) - ID: {task_data.get('id')}")
    
    try:
        # Extrair dados relevantes
        tipo_exame = task_data.get("tipo", "").lower()
        paciente = task_data.get("paciente", {})
        solicitante = task_data.get("solicitante", {})
        
        # Criar agentes CrewAI
        radiologist = Agent(
            role="Radiologist",
            goal="Provide accurate and detailed interpretation of imaging studies",
            backstory=f"You are an experienced radiologist specialized in {tipo_exame} interpretation. "
                    "You have analyzed thousands of imaging studies and can identify subtle "
                    "abnormalities and patterns.",
            verbose=True
        )
        
        # Criar tarefa
        analysis_task = Task(
            description=f"""
            Analyze the following imaging study request:
            
            Type of study: {tipo_exame}
            Patient: {paciente.get('nome', 'Unknown')}, ID: {paciente.get('id', 'Unknown')}
            Age: {paciente.get('idade', 'Not specified')}
            
            Requester: {solicitante.get('nome', 'Unknown')}, Specialty: {solicitante.get('especialidade', 'Unknown')}
            
            Your task is to:
            1. Describe the proper protocol for conducting this type of imaging study
            2. Explain what anatomical structures and pathologies can be visualized with this technique
            3. Discuss common findings and their clinical significance
            4. Outline the reporting structure for this type of study
            5. Recommend appropriate follow-up studies if abnormalities are detected
            
            Be thorough and precise in your analysis.
            """,
            agent=radiologist
        )
        
        # Criar crew
        crew = Crew(
            agents=[radiologist],
            tasks=[analysis_task],
            verbose=True
        )
        
        # Executar análise
        result = crew.kickoff()
        
        # Retornar resultado
        return {
            "task_id": task_data.get("id"),
            "result": result,
            "analysis_summary": f"Análise de {tipo_exame} completa",
            "status": "completed",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Erro ao processar exame de imagem: {e}")
        return {
            "task_id": task_data.get("id"),
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

def process_exame_task(task_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Processa uma tarefa do fluxo de exames baseado no tipo
    
    Args:
        task_data: Dados da tarefa recebida
        
    Returns:
        Dict: Resultado do processamento
    """
    task_type = task_data.get("tipo", "").lower()
    
    # Direcionar para o handler específico baseado no tipo
    if task_type == "hemograma":
        return process_hemograma(task_data)
    elif task_type in ["raio_x", "tomografia", "ultrassonografia", "ressonancia"]:
        return process_imagem(task_data)
    else:
        logger.warning(f"Tipo de exame desconhecido: {task_type}")
        return {
            "task_id": task_data.get("id"),
            "status": "error",
            "error": f"Tipo de exame desconhecido: {task_type}",
            "timestamp": datetime.now().isoformat()
        }