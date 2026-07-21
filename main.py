from pathlib import Path
from dotenv import load_dotenv

RAIZ_PROJETO = Path(__file__).resolve().parent
CAMINHO_ENV = RAIZ_PROJETO / '.env'
load_dotenv(dotenv_path=CAMINHO_ENV)

import yaml
import pandas as pd
from config.settings import logger, DIAS_HISTORICO_PADRAO
# Importação das duas etapas sequenciais que validamos nos testes
from src.extraction.instagram_posts import extrair_ultimos_posts_instagram
from src.extraction.instagram_comments import extrair_comentarios_lote_instagram
# Mantendo a estrutura original para imprensa e utilitários
from src.extraction import coletar_noticias_politico  
from src.transformation import (
    aplicar_analise_sentimento_dataframe, 
    extrair_pautas_quentes, 
    converter_ranking_para_df
)
from src.utils import salvar_dados_consolidados

def carregar_clientes():
    """
    Lê o arquivo de configuração de clientes (clientes.yaml) de forma segura.
    """
    from config.settings import CLIENTES_CONFIG_PATH
    try:
        with open(CLIENTES_CONFIG_PATH, "r", encoding="utf-8") as file:
            config = yaml.safe_load(file)
            return config.get("clientes", [])
    except Exception as e:
        logger.error(f"Erro crítico ao ler o arquivo de configuração de clientes: {str(e)}")
        return []

def processar_esteira_instagram(perfil_alvo: str) -> pd.DataFrame:
    """Orquestra a extração Master-Detail do Instagram para alimentar o BERT.

    Etapa 1: Coleta metadados e URLs dos últimos 30 posts (campo 'url').
    Etapa 2: Passa a lista de URLs em lote para sugar centenas de comentários.
    """
    logger.info(f"📸 [INSTAGRAM] Iniciando varredura sequencial para o perfil: {perfil_alvo}")
    
    # PASSO 1: Coleta o índice de posts recentes (Traz colunas: id, url, likesCount, etc)
    df_posts = extrair_ultimos_posts_instagram(perfil_alvo, limite_posts=30)
    
    if df_posts.empty or "url" not in df_posts.columns:
        logger.warning(f"⚠️ [INSTAGRAM] Nenhum post recente localizado para {perfil_alvo}. Pulando sub-rotina.")
        return pd.DataFrame(), pd.DataFrame()
        
    # Extrai a lista de links contida especificamente no campo 'url' conforme validado
    lista_urls = df_posts["url"].dropna().tolist()
    
    # PASSO 2: Executa a chamada em lote para extrair os comentários de todas as URLs coletadas
    df_comentarios = extrair_comentarios_lote_instagram(lista_urls, limite_comentarios_por_post=200)
    
    return df_posts, df_comentarios

def orquestrar_pipeline():
    """
    Orquestrador principal que executa a coleta, transformação e carga 
    para todos os políticos cadastrados no sistema.
    """
    logger.info("==================================================")
    logger.info("🎬 INICIANDO PIPELINE DE INTELIGÊNCIA POLÍTICA")
    logger.info("==================================================")
    
    lista_clientes = carregar_clientes()
    
    if not lista_clientes:
        logger.warning("Nenhum cliente ativo encontrado para processamento no arquivo de configuração.")
        return

    logger.info(f"Total de {len(lista_clientes)} clientes mapeados para processamento.")

    # Loop principal que garante o processamento em lote (Batch Processing)
    for cliente in lista_clientes:
        cliente_id = cliente.get("id")
        nome_cliente = cliente.get("nome")
        
        logger.info(f"\n🚀 [PROCESSANDO] Iniciando rotinas para: {nome_cliente} ({cliente_id})")
        
        # ----------------------------------------------------------------------
        # ETAPA 1: EXTRAÇÃO DE DADOS (IMPRENSA E REDES SOCIAIS SEQUENCIAIS)
        # ----------------------------------------------------------------------
        # Coleta de Notícias (Google News)
        df_noticias = coletar_noticias_politico(
            termo_busca=cliente.get("termo_busca"), 
            dias=DIAS_HISTORICO_PADRAO
        )
        
        # Coleta de Redes Sociais usando a nova esteira Master-Detail de 2 passos
        df_posts, df_instagram = processar_esteira_instagram(perfil_alvo=cliente.get("instagram"))
        
        # ----------------------------------------------------------------------
        # ETAPA 2: TRANSFORMAÇÃO DE DADOS (INTELIGÊNCIA ARTIFICIAL / BERT NLP)
        # ----------------------------------------------------------------------
        # Se houver notícias coletadas, processa sentimento e extrai pautas quentes
        if not df_noticias.empty:
            logger.info(f"Processando Inteligência Artificial para as notícias de {nome_cliente}...")
            df_noticias = aplicar_analise_sentimento_dataframe(df_noticias, "titulo")
            
            # NLP: Extração de Pautas Quentes dos títulos das notícias
            ranking_noticias = extrair_pautas_quentes(df_noticias["titulo"].tolist())
            df_pautas_noticias = converter_ranking_para_df(ranking_noticias)
        else:
            df_pautas_noticias = converter_ranking_para_df([])

        # Se houver comentários extraídos via Apify, tritura no modelo BERT híbrido
        if not df_instagram.empty:
            logger.info(f"Processando Inteligência Artificial (BERT) para {len(df_instagram)} comentários de {nome_cliente}...")
            # BERT tritura a coluna "texto" gerando rótulos de sentimento e scores de confiança
            df_instagram = aplicar_analise_sentimento_dataframe(df_instagram, "texto")
            
            # NLP: Extração de Pautas Quentes dos comentários da população
            ranking_instagram = extrair_pautas_quentes(df_instagram["texto"].tolist())
            df_pautas_instagram = converter_ranking_para_df(ranking_instagram)
        else:
            df_pautas_instagram = converter_ranking_para_df([])

        # ----------------------------------------------------------------------
        # ETAPA 3: PERSISTÊNCIA (SALVAMENTO DOS ARQUIVOS EM DISCO)
        # ----------------------------------------------------------------------
        logger.info(f"Iniciando gravação dos outputs históricos para {nome_cliente}...")
        
        # Salva as tabelas completas com as classificações de sentimento para o Looker Studio
        salvar_dados_consolidados(df_noticias, cliente_id, "noticias_brutas")
        salvar_dados_consolidados(df_instagram, cliente_id, "instagram_bruto")

        if not df_posts.empty:
            salvar_dados_consolidados(df_posts, cliente_id, "posts_brutos") # O NOVO ARQUIVO!
        
        # Salva os rankings consolidados de pautas (essenciais para construir as nuvens de palavras)
        salvar_dados_consolidados(df_pautas_noticias, cliente_id, "pautas_imprensa")
        salvar_dados_consolidados(df_pautas_instagram, cliente_id, "pautas_populacao")
        
        logger.info(f"✨ [CONCLUÍDO] Todos os dados de {nome_cliente} foram processados com sucesso.")
        
    logger.info("\n==================================================")
    logger.info("🏁 PIPELINE COMPLETO EXECUTADO COM SUCESSO!")
    logger.info("==================================================")

if __name__ == "__main__":
    orquestrar_pipeline()