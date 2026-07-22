# Configurações globais de caminhos e parâmetros do sistema
import os
import logging
from pathlib import Path
from dotenv import load_dotenv

# Carrega as variáveis do arquivo .env
load_dotenv()

# --- Configurações da API ---
APIFY_API_TOKEN = os.getenv("APIFY_TOKEN")
if not APIFY_API_TOKEN:
    raise ValueError("APIFY_TOKEN não encontrado. Defina a variável de ambiente ou crie um arquivo .env")


# ==============================================================================
# 1. GERENCIAMENTO DE DIRETÓRIOS (PATHS)
# ==============================================================================
# Caminho absoluto para a raiz do projeto
BASE_DIR = Path(__file__).parent.parent.resolve()

# Caminhos para as pastas de configuração e dados
CONFIG_DIR = BASE_DIR / "config"
DOCS_DIR = BASE_DIR / "docs"
REPORTS_DIR = BASE_DIR / "reports"
SRC_DIR = BASE_DIR / "src"

# Garante que o diretório de relatórios exista
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# Arquivo de mapeamento dos clientes
CLIENTES_CONFIG_PATH = CONFIG_DIR / "clientes.yaml"


# ==============================================================================
# 2. PARÂMETROS DOS MODELOS DE INTELIGÊNCIA ARTIFICIAL (NLP / SENTIMENTO)
# ==============================================================================
# Modelo leve em português do Hugging Face para análise de sentimento de tweets/redes
MODELO_SENTIMENTO = "pysentimiento/bertweet-pt-sentiment"

# Modelo do Spacy para Processamento de Linguagem Natural (Lematização e Stopwords)
MODELO_SPACY = "pt_core_news_sm"

# Limite máximo de tokens/caracteres para evitar quebra em textos muito longos
MAX_TEXT_LENGTH = 512


# ==============================================================================
# 3. CONFIGURAÇÕES DE EXTRAÇÃO (APIs E SCRAPING)
# ==============================================================================
# Janela padrão de busca de dados históricos (em dias) caso não especificado
DIAS_HISTORICO_PADRAO = 30

# Limite padrão de posts do Instagram a serem analisados por execução no MVP
MAX_POSTS_INSTAGRAM = 5


# ==============================================================================
# 4. SISTEMA DE LOGGING (MONITORAMENTO DO PIPELINE)
# ==============================================================================
def configurar_logging():
    """
    Configura o sistema de logs para exibir o status do pipeline no terminal
    e salvar o histórico fisicamente no disco em logs/pipeline.log.
    Útil para monitorar execuções em lote e identificar falhas de scraping remotamente.
    """
    # Garante a criação da pasta de logs se ela não existir
    logs_dir = BASE_DIR / "logs"
    logs_dir.mkdir(exist_ok=True)
    log_file_path = logs_dir / "pipeline.log"

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.FileHandler(log_file_path, encoding="utf-8"), # Força a criação e gravação do arquivo log
            logging.StreamHandler()                               # Exibe os logs direto no console/terminal
        ]
    )

# Inicializa a configuração de logs assim que o módulo é importado
configurar_logging()
logger = logging.getLogger("PoliticaDataIntelligence")