"""
Carregamento de variáveis de ambiente para o projeto
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Definir o diretório base do projeto (pasta raiz)
BASE_DIR = Path(__file__).resolve().parent.parent

# Carregar variáveis do arquivo .env
dotenv_path = os.path.join(BASE_DIR, '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)
else:
    print(f"Arquivo .env não encontrado em {dotenv_path}. Usando variáveis de ambiente do sistema.")

# Função para obter variável de ambiente com valor padrão
def get_env(key, default=None):
    """
    Retorna o valor de uma variável de ambiente, ou o valor padrão se não existir
    
    Args:
        key: Nome da variável de ambiente
        default: Valor padrão caso a variável não exista
        
    Returns:
        Valor da variável de ambiente ou o valor padrão
    """
    return os.environ.get(key, default)