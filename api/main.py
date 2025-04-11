"""
Aplicação principal FastAPI
"""
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware

# Importar routers
from api.routers import clinico, exames, opme, ingestao
from api.services.rabbitmq_producer import producer
from shared.config import API_HOST, API_PORT
from shared.utils import setup_logger

# Configuração de logging
logger = setup_logger("api_main")

# Criar aplicação FastAPI
app = FastAPI(
    title="Banquete API",
    description="API para processamento de tarefas com CrewAI via RabbitMQ",
    version="1.0.0"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Substituir por origens específicas em produção
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers
app.include_router(clinico.router)
app.include_router(exames.router)
app.include_router(opme.router)
app.include_router(ingestao.router)

# Endpoint raiz
@app.get("/")
async def root():
    """Endpoint raiz da API"""
    return {
        "message": "Banquete API",
        "status": "online",
        "docs": "/docs"
    }

# Endpoints de saúde
@app.get("/health")
async def health():
    """Endpoint de verificação de saúde da API"""
    return {"status": "healthy"}

@app.get("/ready")
async def ready():
    """Endpoint de prontidão da API"""
    return {"status": "ready"}

# Eventos do ciclo de vida da aplicação
@app.on_event("startup")
async def startup_event():
    """Executado quando a aplicação FastAPI inicia"""
    # Conectar ao RabbitMQ quando a aplicação iniciar
    logger.info("Iniciando a API...")
    
    # Pré-conectar aos vhosts mais usados para melhor performance
    try:
        producer.connect("fluxo_clinico")
        producer.connect("fluxo_exames")
    except Exception as e:
        logger.error(f"Erro ao conectar ao RabbitMQ: {e}")
        logger.warning("A API continuará funcionando, mas pode ter problemas ao enviar mensagens")

@app.on_event("shutdown")
async def shutdown_event():
    """Executado quando a aplicação FastAPI é encerrada"""
    # Fechar conexão com RabbitMQ quando a aplicação encerrar
    logger.info("Encerrando a API...")
    producer.close()

if __name__ == "__main__":
    import uvicorn
    # Iniciar aplicação para testes
    logger.info(f"Iniciando servidor na porta {API_PORT}...")
    uvicorn.run("api.main:app", host=API_HOST, port=API_PORT, reload=True)