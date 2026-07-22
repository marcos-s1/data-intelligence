import os
from pathlib import Path
from dotenv import load_dotenv

# Configuração de diretórios e variáveis de ambiente
RAIZ_PROJETO = Path(__file__).resolve().parent
CAMINHO_ENV = RAIZ_PROJETO / '.env'

if CAMINHO_ENV.exists():
    load_dotenv(dotenv_path=CAMINHO_ENV)
    print(f"🔧 [.ENV] Variáveis de ambiente carregadas a partir de: {CAMINHO_ENV}")
else:
    print(f"⚠️ [.ENV] Arquivo .env não encontrado em {CAMINHO_ENV}. Utilizando variáveis do sistema.")

import yaml
import pandas as pd
from config.settings import logger, DIAS_HISTORICO_PADRAO

# Importações dos módulos de extração, transformação e utilitários
# from src.extraction.instagram_posts import extrair_posts_instagram
from src.extraction.instagram_comments import extrair_comentarios_lote_instagram
from src.extraction import coletar_noticias_politico  
from src.transformation import (
    aplicar_analise_sentimento_dataframe, 
    extrair_pautas_quentes, 
    converter_ranking_para_df
)
from src.utils import salvar_dados_consolidados

# ==============================================================================
# 🎛️ CONTROLE DE EXECUÇÃO: FLAGS DE API INDEPENDENTES
# True  -> Executa chamadas de API externas
# False -> Carrega os arquivos CSV já gravados no disco (reports/<cliente>/data_source)
# ==============================================================================
USAR_API_INSTAGRAM = os.getenv("USAR_API_INSTAGRAM", "False").lower() in ("true", "1", "t")
USAR_API_NOTICIAS = os.getenv("USAR_API_NOTICIAS", "False").lower() in ("true", "1", "t")


def carregar_csv_existente(cliente_id: str, tipo_dado: str) -> pd.DataFrame:
    """Carrega CSVs do disco tratando inconsistências de colunas e enquadramentos de texto."""
    caminho_arquivo = RAIZ_PROJETO / "reports" / cliente_id / "data_source" / f"2026_07_{tipo_dado}.csv"
    logger.debug(f"🔍 [MODO OFFLINE] Checando arquivo local: {caminho_arquivo}")

    if caminho_arquivo.exists():
        try:
            # on_bad_lines='skip' e engine='python' garantem resiliência contra quebras no CSV
            df = pd.read_csv(
                caminho_arquivo, 
                encoding="utf-8-sig", 
                on_bad_lines="skip", 
                engine="python"
            )
            logger.info(f"📂 [MODO OFFLINE] Sucesso ao carregar '{tipo_dado}' ({len(df)} registros) de: {caminho_arquivo.name}")
            return df
        except Exception as e:
            logger.error(f"❌ [MODO OFFLINE] Falha ao ler {caminho_arquivo.name}: {str(e)}")
            return pd.DataFrame()
    else:
        logger.warning(f"⚠️ [MODO OFFLINE] Arquivo não localizado no disco: {caminho_arquivo.name}")
        return pd.DataFrame()

def normalizar_colunas_comentarios(df: pd.DataFrame) -> pd.DataFrame:
    """Garante que a coluna do texto do comentário sempre se chame 'texto'."""
    if df.empty:
        return df

    mapeamento_colunas = {
        "text": "texto",
        "comment": "texto",
        "comment_text": "texto",
        "text_comment": "texto"
    }
    
    # Renomeia se encontrar aliases conhecidos
    df = df.rename(columns=mapeamento_colunas)
    
    if "texto" not in df.columns:
        logger.warning("⚠️ Coluna 'texto' não encontrada no DataFrame do Instagram. Criando coluna vazia...")
        df["texto"] = ""
        
    return df

def carregar_clientes() -> list:
    """Lê as configurações dos clientes no arquivo YAML."""
    from config.settings import CLIENTES_CONFIG_PATH
    logger.info(f"📄 [CONFIG] Lendo arquivo de clientes: {CLIENTES_CONFIG_PATH}")
    
    try:
        with open(CLIENTES_CONFIG_PATH, "r", encoding="utf-8") as file:
            config = yaml.safe_load(file)
            clientes = config.get("clientes", [])
            logger.info(f"🎯 [CONFIG] Encontrados {len(clientes)} cliente(s) mapeados.")
            return clientes
    except Exception as e:
        logger.error(f"❌ [CONFIG] Erro ao ler {CLIENTES_CONFIG_PATH}: {str(e)}")
        return []


def orquestrar_pipeline():
    """Orquestra o pipeline com controle individual de APIs para Notícias e Instagram."""
    logger.info("==================================================")
    logger.info("🎬 INICIANDO PIPELINE DE INTELIGÊNCIA POLÍTICA")
    logger.info(f"⚙️ NOTÍCIAS : {'🌐 ONLINE (Google News API)' if USAR_API_NOTICIAS else '📂 OFFLINE (CSV Local)'}")
    logger.info(f"⚙️ INSTAGRAM: {'🌐 ONLINE (Apify Scraper)' if USAR_API_INSTAGRAM else '📂 OFFLINE (CSV Local)'}")
    logger.info("==================================================")
    
    lista_clientes = carregar_clientes()
    if not lista_clientes:
        logger.error("🚫 [FLUXO ABORTADO] Nenhum cliente válido encontrado.")
        return

    for idx, cliente in enumerate(lista_clientes, start=1):
        cliente_id = cliente.get("id")
        nome_cliente = cliente.get("nome")
        
        logger.info("--------------------------------------------------")
        logger.info(f"🚀 [{idx}/{len(lista_clientes)} PROCESSANDO] Cliente: {nome_cliente} ({cliente_id})")
        logger.info("--------------------------------------------------")
        
        # ------------------------------------------------------------------
        # 1. NOTÍCIAS (GOOGLE NEWS)
        # ------------------------------------------------------------------
        if USAR_API_NOTICIAS:
            logger.info("📰 [NOTÍCIAS - ONLINE] Buscando matérias recentes via Google News...")
            df_noticias = coletar_noticias_politico(
                termo_busca=cliente.get("termo_busca"), 
                dias=DIAS_HISTORICO_PADRAO
            )
            logger.info(f"📊 [NOTÍCIAS - ONLINE] Mapeadas {len(df_noticias)} notícias.")
        else:
            logger.info("📂 [NOTÍCIAS - OFFLINE] Carregando notícias a partir do CSV local...")
            df_noticias = carregar_csv_existente(cliente_id, "noticias_brutas")

        # ------------------------------------------------------------------
        # 2. INSTAGRAM (POSTS + COMENTÁRIOS)
        # ------------------------------------------------------------------
        if USAR_API_INSTAGRAM:
            logger.info("📸 [INSTAGRAM - ONLINE] Disparando raspagem no Apify...")
            
            # 2.1 Posts + Comentários Nativos
            df_posts, df_coment_iniciais = extrair_posts_instagram(
                perfil_url=cliente.get("instagram"),
                limite_posts=30
            )
            logger.info(f"📊 [INSTAGRAM - ONLINE] Mapeados {len(df_posts)} posts e {len(df_coment_iniciais)} comentários nativos.")

            # 2.2 Lote Expandido de Comentários + Deduplicação
            df_comentarios_consolidados = pd.DataFrame()
            if not df_posts.empty:
                urls_posts = df_posts["url"].dropna().tolist()
                logger.info(f"💬 [INSTAGRAM - ONLINE] Solicitando lote expandido para {len(urls_posts)} URLs...")
                
                df_coment_lote = extrair_comentarios_lote_instagram(
                    lista_urls_posts=urls_posts,
                    limite_comentarios_por_post=250
                )
                logger.info(f"📊 [INSTAGRAM - ONLINE] Retornados {len(df_coment_lote)} comentários em lote.")

                # União das duas fontes de comentários
                logger.info("🔗 [INSTAGRAM] Consolidando comentários nativos e em lote...")
                df_comentarios_consolidados = pd.concat([df_coment_iniciais, df_coment_lote], ignore_index=True)
                
                # Deduplicação por 'comentario_id'
                if not df_comentarios_consolidados.empty:
                    qtd_bruta = len(df_comentarios_consolidados)
                    logger.info(f"🧼 [DEDUPLICAÇÃO] Limpando base bruta de {qtd_bruta} comentários...")
                    
                    df_comentarios_consolidados["comentario_id"] = df_comentarios_consolidados["comentario_id"].astype(str)
                    df_comentarios_consolidados = (
                        df_comentarios_consolidados
                        .drop_duplicates(subset=["comentario_id"])
                        .reset_index(drop=True)
                    )
                    
                    qtd_limpa = len(df_comentarios_consolidados)
                    logger.info(f"✨ [DEDUPLICAÇÃO CONCLUÍDA] {qtd_bruta - qtd_limpa} duplicatas removidas. Total limpo: {qtd_limpa} comentários.")
            else:
                logger.warning("⚠️ [INSTAGRAM] Nenhum post extraído. Etapa de comentários cancelada.")

        else:
            logger.info("📂 [INSTAGRAM - OFFLINE] Carregando posts e comentários dos CSVs locais...")
            df_posts = carregar_csv_existente(cliente_id, "posts_brutos")
            df_comentarios_consolidados = carregar_csv_existente(cliente_id, "instagram_bruto")

        # ------------------------------------------------------------------
        # 3. TRANSFORMAÇÃO E INTELIGÊNCIA ARTIFICIAL (BERT / NLP)
        # ------------------------------------------------------------------
        logger.info("🧠 [IA & NLP] Processando análise de sentimento e extração de pautas...")
        
        # IA em Notícias
        if not df_noticias.empty:
            logger.info("🧠 [IA - NOTÍCIAS] Classificando sentimento dos títulos...")
            df_noticias = aplicar_analise_sentimento_dataframe(df_noticias, "titulo")
            
            logger.info("🏷️ [NLP - NOTÍCIAS] Mapeando pautas mais frequentes da imprensa...")
            df_pautas_noticias = converter_ranking_para_df(extrair_pautas_quentes(df_noticias["titulo"].tolist()))
        else:
            logger.warning("⚠️ [IA - NOTÍCIAS] Sem registros para análise.")
            df_pautas_noticias = converter_ranking_para_df([])

        # IA em Comentários
        if not df_comentarios_consolidados.empty:
            logger.info(f"🧠 [IA - INSTAGRAM] Inferindo sentimento (BERT) para {len(df_comentarios_consolidados)} comentários...")
            df_comentarios_consolidados = aplicar_analise_sentimento_dataframe(
                df_comentarios_consolidados, "texto"
            )
            
            logger.info("🏷️ [NLP - INSTAGRAM] Mapeando pautas e demandas da população...")
            df_pautas_instagram = converter_ranking_para_df(
                extrair_pautas_quentes(df_comentarios_consolidados["texto"].tolist())
            )
        else:
            logger.warning("⚠️ [IA - INSTAGRAM] Sem comentários para análise.")
            df_pautas_instagram = converter_ranking_para_df([])

        # ------------------------------------------------------------------
        # 4. PERSISTÊNCIA DOS DADOS (CSV)
        # ------------------------------------------------------------------
        logger.info(f"💾 [PERSISTÊNCIA] Atualizando/Salvando arquivos de output para '{cliente_id}'...")
        
        salvar_dados_consolidados(df_noticias, cliente_id, "noticias_brutas")
        salvar_dados_consolidados(df_pautas_noticias, cliente_id, "pautas_imprensa")
        
        if not df_posts.empty:
            salvar_dados_consolidados(df_posts, cliente_id, "posts_brutos")
            
        if not df_comentarios_consolidados.empty:
            salvar_dados_consolidados(df_comentarios_consolidados, cliente_id, "instagram_bruto")
            salvar_dados_consolidados(df_pautas_instagram, cliente_id, "pautas_populacao")
        
        logger.info(f"✨ [CONCLUÍDO] Cliente '{nome_cliente}' processado com sucesso!")

    logger.info("==================================================")
    logger.info("🏁 PIPELINE DE INTELIGÊNCIA POLÍTICA FINALIZADO COM SUCESSO!")
    logger.info("==================================================")

if __name__ == "__main__":
    orquestrar_pipeline()