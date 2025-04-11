# Sistema de Processamento com RabbitMQ e CrewAI

Este projeto implementa um sistema assíncrono para processamento de tarefas utilizando RabbitMQ para gerenciamento de filas e CrewAI para processamento inteligente de tarefas médicas e administrativas.

## Estrutura do Projeto

```
RabbitMQ/
│
├── api/                      # Aplicação FastAPI
│   ├── main.py              # Ponto de entrada da API
│   ├── routers/             # Rotas da API organizadas por domínio
│   │   ├── clinico.py
│   │   ├── exames.py
│   │   ├── opme.py
│   │   └── ingestao.py
│   ├── models/              # Modelos Pydantic 
│   │   └── schemas.py
│   └── services/
│       └── rabbitmq_producer.py   # Produtor RabbitMQ para FastAPI
│
├── workers/                  # Workers para processamento
│   ├── worker_alternativo.py  # Worker baseado em Pika
│   ├── dramatiq_worker.py   # Worker híbrido Pika/Dramatiq
│   ├── crewai_handlers/      # Handlers específicos para o CrewAI
│       ├── clinico_handler.py
│       ├── exames_handler.py
│       ├── opme_handler.py
│       └── ingestao_handler.py
│
├── shared/                   # Código compartilhado
│   ├── config.py            # Configurações compartilhadas
│   ├── env.py               # Carregamento de variáveis de ambiente
│   └── utils.py             # Utilitários comuns
│
├── Dockerfile.api           # Dockerfile para a API
├── Dockerfile.worker        # Dockerfile para os workers
├── docker-compose.yml       # Composição dos serviços
├── requirements.api.txt     # Dependências da API
├── requirements.worker.txt  # Dependências do worker
├── .env.example             # Exemplo de variáveis de ambiente
└── .gitignore               # Arquivos ignorados pelo Git
```

## Arquitetura

Este sistema utiliza uma arquitetura em camadas com as seguintes responsabilidades:

1. **API (FastAPI)**: Recebe requisições, valida dados, e envia tarefas para processamento
2. **RabbitMQ**: Sistema de mensageria que gerencia as filas de tarefas
3. **Workers**: Consumidores que processam as mensagens usando CrewAI
4. **CrewAI**: Framework de IA para execução de tarefas complexas com agentes inteligentes

### Fluxo de Processamento

```
Cliente → API → RabbitMQ → Workers → CrewAI → Resultado
```

## Configuração do RabbitMQ

O sistema usa múltiplos virtual hosts no RabbitMQ, cada um para um domínio específico do negócio:

| Virtual Host    | Fila      | Tipo    | Descrição                       |
|-----------------|-----------|---------|----------------------------------|
| fluxo_clinico   | eventos   | quorum  | Tarefas relacionadas a pacientes |
| fluxo_exames    | eventos   | quorum  | Tarefas relacionadas a exames    |
| fluxo_opme      | eventos   | quorum  | Tarefas de órteses e próteses    |
| ingestao_dados  | eventos   | quorum  | Tarefas de ingestão de dados     |

## Inicialização

### Configuração do Ambiente

1. Clone o repositório:
   ```bash
   git clone https://seu-repositorio.git
   cd seu-projeto
   ```

2. Crie um arquivo `.env` baseado no `.env.example`:
   ```bash
   cp .env.example .env
   ```

3. Edite o arquivo `.env` com suas configurações, especialmente a chave da API OpenAI:
   ```
   OPENAI_API_KEY=sua_chave_api_aqui
   ```

### Ambiente de Desenvolvimento

1. Instale as dependências:
   ```bash
   # Para a API
   pip install -r requirements.api.txt
   
   # Para o worker
   pip install -r requirements.worker.txt
   ```

2. Execute a API:
   ```bash
   python -m api.main
   ```

3. Execute o worker (escolha uma das opções):
   ```bash
   # Opção 1: Worker baseado em Pika
   python -m workers.worker_alternativo
   
   # Opção 2: Worker híbrido (Pika/Dramatiq)
   python -m workers.dramatiq_worker
   ```

### Usando Docker

Para iniciar todos os serviços usando Docker Compose:

```bash
docker-compose up -d
```

Para escalar os workers:

```bash
docker-compose up -d --scale worker=3
```

## Endpoints da API

A API fornece endpoints para diferentes fluxos de trabalho:

### Fluxo Clínico
- `POST /api/clinico/consulta/` - Criar consulta
- `POST /api/clinico/internacao/` - Registrar internação
- `POST /api/clinico/alta/` - Registrar alta
- `GET /api/clinico/status/{task_id}` - Verificar status

### Fluxo Exames
- `POST /api/exames/` - Solicitar exame genérico
- `POST /api/exames/hemograma/` - Solicitar hemograma
- `POST /api/exames/imagem/{tipo_exame}` - Solicitar exame de imagem
- `GET /api/exames/status/{task_id}` - Verificar status

### Fluxo OPME
- `POST /api/opme/` - Solicitar OPME genérico
- `POST /api/opme/protese/` - Solicitar prótese
- `POST /api/opme/material/` - Solicitar material especial
- `GET /api/opme/status/{task_id}` - Verificar status

### Fluxo Ingestão
- `POST /api/ingestao/` - Iniciar ingestão genérica
- `POST /api/ingestao/pacientes/` - Ingerir dados de pacientes
- `POST /api/ingestao/medicos/` - Ingerir dados de médicos
- `GET /api/ingestao/status/{task_id}` - Verificar status

Documentação completa disponível em: `/docs` (Swagger UI)

## Workers Disponíveis

O sistema oferece duas opções de workers:

### 1. Worker Baseado em Pika (`dramatiq_worker_simple.py`)

- **Tecnologia**: Usa Pika diretamente para comunicação com RabbitMQ
- **Vantagens**: Simplicidade, compatibilidade direta com filas existentes
- **Recursos**: Multiprocessamento, reconexão automática, monitoramento de processos
- **Uso**: `python -m workers.dramatiq_worker_simple`

### 2. Worker Híbrido (`final_dramatiq_worker.py`)

- **Tecnologia**: Usa Pika para comunicação e integra alguns recursos do Dramatiq
- **Vantagens**: Compatibilidade com filas existentes, benefícios de monitoramento do Dramatiq
- **Recursos**: Multiprocessamento, retentativas com backoff, métricas
- **Uso**: `python -m workers.final_dramatiq_worker`

## Processamento com CrewAI

O sistema utiliza o CrewAI para processamento inteligente das tarefas:

1. **Agentes**: Especialistas virtuais com papéis específicos (médicos, analistas, etc.)
2. **Tarefas**: Instruções detalhadas para os agentes
3. **Crew**: Equipe de agentes que trabalham juntos para resolver problemas complexos

Por exemplo, para analisar um hemograma:
- Um agente "Laboratory Analyst" analisa os parâmetros do sangue
- Um agente "Hematologist" interpreta os resultados clinicamente

## Características do Sistema

### Robustez

- **Reconexão Automática**: Recuperação automática em caso de falhas de conexão
- **Tratamento de Erros**: Gerenciamento adequado de erros com retentativas
- **Monitoramento de Processos**: Detecção e reinício de workers que falham

### Escalabilidade

- **Arquitetura Multiprocesso**: Um processo por virtual host
- **Balanceamento de Carga**: Prefetch configurável para controlar o fluxo de mensagens
- **Escala Horizontal**: Adicione mais instâncias de workers conforme necessário

### Integração

- **Filas Existentes**: Compatibilidade com filas quorum existentes no RabbitMQ
- **Serialização Robusta**: Suporte a diversos tipos de dados, incluindo datetimes
- **API Flexível**: Endpoints por domínio de negócio

## Notas sobre Dependências

As dependências estão divididas em dois arquivos:

1. **requirements.api.txt**:
   ```
   fastapi==0.103.1
   uvicorn==0.23.2
   pydantic==2.3.0
   pika==1.3.2
   python-dotenv==1.0.0
   ```

2. **requirements.worker.txt**:
   ```
   pika==1.3.2
   python-dotenv==1.0.0
   dramatiq[rabbitmq,watch]==1.15.0
   crewai==0.28.0
   langchain>=0.1.10,<0.2.0
   langchain-openai>=0.0.2
   setuptools
   ```

## Desenvolvimento

### Adicionar Nova Tarefa

1. Defina o modelo na API (`api/models/schemas.py`)
2. Adicione o endpoint no router apropriado
3. Implemente o handler específico em `workers/crewai_handlers/`
4. Atualize o mapeamento em `shared/config.py`

### Considerações para Serialização

O sistema inclui um serializador personalizado para lidar com objetos como `datetime` ao converter para JSON:

```python
def json_serializer(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")
```

Use este serializador ao trabalhar com tipos complexos de dados.

## Considerações Finais

Este sistema combina:
- **RabbitMQ**: Mensageria robusta e escalável
- **Pika/Dramatiq**: Gerenciamento eficiente de workers
- **CrewAI**: Processamento inteligente com agentes de IA

Esta arquitetura é ideal para sistemas que precisam processar tarefas complexas em larga escala, com alta disponibilidade e resiliência a falhas.