import os
import pandas as pd
from apify_client import ApifyClient
from config.settings import logger

def extrair_ultimos_posts_instagram(perfil_url: str, limite_posts: int = 5) -> pd.DataFrame:
    """Dispara o Instagram Scraper para coletar o cabeçalho e métricas dos posts recentes.

    Esta função faz a chamada Master na API do Apify utilizando uma conta ativa,
    trazendo dados estruturados de curtidas, visualizações, legenda e shortcodes
    dos posts mais recentes do perfil informado. Aceita links completos ou usernames.

    Args:
        perfil_url (str): URL canônica ou handle do perfil (Ex: 'tarcisiogdf' ou 'https://www.instagram.com/tarcisiogdf').
        limite_posts (int, optional): Quantidade de posts a retornar. O padrão é 5.

    Returns:
        pd.DataFrame: DataFrame contendo as métricas agregadas e identificadores dos posts.
    """
    apify_token = os.getenv("APIFY_TOKEN")
    if not apify_token:
        logger.error("❌ [EXTRAÇÃO MASTER] APIFY_API_TOKEN não configurado no arquivo .env!")
        return pd.DataFrame()

    # --- ENGENHARIA DE ENTRADA INTELIGENTE ---
    perfil_url_limpa = perfil_url.strip()

    # Se o usuário passou apenas o handle (ex: 'tarcisiogdf' ou '@tarcisiogdf'), monta a URL padrão exigida pela Apify
    if not perfil_url_limpa.startswith("http://") and not perfil_url_limpa.startswith("https://"):
        handle = perfil_url_limpa.replace("@", "")
        perfil_url_limpa = f"https://www.instagram.com/{handle}"
    
    # Garante a remoção de barras extras no final para evitar quebra de regex na API
    if perfil_url_limpa.endswith("/"):
        perfil_url_limpa = perfil_url_limpa.rstrip("/")

    client = ApifyClient(apify_token)

    # Configuração de entrada com a URL garantida no padrão Regex da Apify
    run_input = {
        "resultsType": "posts",
        "directUrls": [perfil_url_limpa],
        "resultsLimit": limite_posts,
        "onlyPostsNewerThan": "30 days",  # Filtro de segurança de recência
        "searchType": "hashtag",
        "searchLimit": 1,
        "addParentData": False,
       # Estas configurações enganam o Instagram fazendo o robô parecer um celular real
        "proxyConfiguration": {
            "useApifyProxy": True, 
            "apifyProxyGroups": ["RESIDENTIAL"] # IP de casa, não de datacenter
        },
        "customHeaders": {
            "user-agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1"
        }
    }

    try:
        logger.info(f"🚀 [EXTRAÇÃO MASTER] Buscando os últimos {limite_posts} posts de: {perfil_url_limpa}")
        
        # Executa o Actor 'shu8hvrXbJbY3Eb9W' (Instagram Scraper)
        run = client.actor("shu8hvrXbJbY3Eb9W").call(run_input=run_input)
        
        logger.info("📦 [EXTRAÇÃO MASTER] Download do lote concluído. Iniciando estruturação...")
        
        # --- DESEMPACOTAMENTO SEGURO DO SDK APIFY (ActorRun) ---
        dataset_id = None
        
        # 1. Tenta formato snake_case do SDK nativo (objeto ActorRun do Python)
        if hasattr(run, "default_dataset_id"):
            dataset_id = getattr(run, "default_dataset_id")
        
        # 2. Tenta formato camelCase via dicionário de dados interno (.data)
        if not dataset_id and hasattr(run, "data") and isinstance(run.data, dict):
            dataset_id = run.data.get("defaultDatasetId") or run.data.get("default_dataset_id")
            
        # 3. Tenta formato dicionário puro (fallback se o retorno for dict)
        if not dataset_id and isinstance(run, dict):
            dataset_id = run.get("defaultDatasetId") or run.get("default_dataset_id")

        if not dataset_id:
            logger.error("❌ [EXTRAÇÃO MASTER] Não foi possível encontrar o 'defaultDatasetId' no retorno da Apify.")
            return pd.DataFrame()

        # Baixa os itens coletados usando o ID do Dataset extraído
        dataset_items = client.dataset(dataset_id).list_items().items

        if not dataset_items:
            logger.warning("⚠️ [EXTRAÇÃO MASTER] Nenhum post foi retornado para este perfil.")
            return pd.DataFrame()

        posts_estruturados = []

        # Realiza o parse baseando-se estritamente na estrutura real retornada pelo Actor
        for item in dataset_items:
            posts_estruturados.append({
                "post_id": item.get("id"),
                "shortcode": item.get("shortCode"),
                "tipo_midia": item.get("type"),
                "url": item.get("url"),
                "legenda": item.get("caption"),
                "total_curtidas": item.get("likesCount"),
                "total_comentarios": item.get("commentsCount"),
                "visualizacoes_video": item.get("videoPlayCount"),
                "timestamp_publicacao": item.get("timestamp"),
                "autor_perfil": item.get("ownerUsername")
            })

        df_posts = pd.DataFrame(posts_estruturados)
        
        if not df_posts.empty:
            logger.info(f"🎯 [EXTRAÇÃO MASTER] Sucesso! Mapeados {len(df_posts)} posts de @{df_posts['autor_perfil'].iloc[0]}.")
            
        return df_posts

    except Exception as e:
        logger.error(f"❌ [EXTRAÇÃO MASTER] Falha crítica na chamada da API: {str(e)}")
        return pd.DataFrame()