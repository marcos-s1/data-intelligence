import os
import json
import pandas as pd
from apify_client import ApifyClient
from config.settings import logger

def estruturar_dados_instagram(items_json: list) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Processa o JSON bruto da Apify e divide em dois DataFrames estruturados:
    1. Posts (com variáveis de vídeo, hashtags, engajamento)
    2. Comentários (com apoio para sentimento e engajamento individual)
    """
    posts_estruturados = []
    comentarios_estruturados = []

    for item in items_json:
        shortcode = item.get("shortCode") or item.get("id")
        likes = item.get("likesCount", 0) or 0
        views = item.get("videoPlayCount", 0) or 0
        comments_count = item.get("commentsCount", 0) or 0
        
        # --- DADOS DOS POSTS ---
        hashtags = item.get("hashtags", []) or []
        mentions = item.get("mentions", []) or []
        duration = item.get("videoDuration", 0) or 0
        
        # Métrica Derivada: Taxa de Retenção do Vídeo (Likes / Views)
        retencao_video = (likes / views * 100) if views > 0 else 0.0

        posts_estruturados.append({
            "post_id": shortcode,
            "shortcode": shortcode,
            "tipo_midia": item.get("type"),
            "url": item.get("url"),
            "legenda": item.get("caption"),
            "total_curtidas": likes,
            "total_comentarios": comments_count,
            "visualizacoes_video": views,
            "duracao_video_segundos": duration,
            "taxa_retencao_video": round(retencao_video, 2),
            "qtd_hashtags": len(hashtags),
            "qtd_mencoes": len(mentions),
            "timestamp_publicacao": item.get("timestamp"),
            "autor_perfil": item.get("ownerUsername")
        })

        # --- DADOS DOS COMENTÁRIOS (Nó latestComments) ---
        latest_comments = item.get("latestComments", []) or []
        for com in latest_comments:
            texto_comentario = com.get("text", "")
            comentarios_estruturados.append({
                "post_id": shortcode,
                "url_post": item.get("url"),
                "comentario_id": com.get("id"),
                "texto": texto_comentario,
                "qtd_caracteres": len(texto_comentario) if texto_comentario else 0,
                "curtidas_comentario": com.get("likesCount", 0) or 0,
                "data_comentario": com.get("timestamp"),
                "autor_comentario": com.get("ownerUsername")
            })

    df_posts = pd.DataFrame(posts_estruturados)
    df_comentarios = pd.DataFrame(comentarios_estruturados)

    logger.info(f"🎯 [ESTRUTURAÇÃO] Sucesso! Processados {len(df_posts)} posts e {len(df_comentarios)} comentários.")
    return df_posts, df_comentarios


def extrair_posts_e_comentarios_instagram(perfil_url: str, limite_posts: int = 30) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Extrai os posts recentes de um perfil do Instagram e captura os comentários nativos (latestComments).

    Args:
        perfil_url (str): URL ou handle do perfil (ex: 'tarcisiogdf').
        limite_posts (int, optional): Quantidade de posts a extrair. Padrão 30.

    Returns:
        tuple[pd.DataFrame, pd.DataFrame]: (df_posts, df_comentarios_iniciais)
    """
    apify_token = os.getenv("APIFY_TOKEN")
    if not apify_token:
        logger.error("❌ [EXTRAÇÃO] APIFY_TOKEN não configurado no .env!")
        return pd.DataFrame(), pd.DataFrame()

    perfil_url_limpa = perfil_url.strip()
    if not perfil_url_limpa.startswith("http://") and not perfil_url_limpa.startswith("https://"):
        handle = perfil_url_limpa.replace("@", "")
        perfil_url_limpa = f"https://www.instagram.com/{handle}"
    
    if perfil_url_limpa.endswith("/"):
        perfil_url_limpa = perfil_url_limpa.rstrip("/")

    client = ApifyClient(apify_token)

    run_input = {
        "resultsType": "posts",
        "directUrls": [perfil_url_limpa],
        "resultsLimit": limite_posts,
        "onlyPostsNewerThan": "30 days",
        "searchType": "hashtag",
        "searchLimit": 1,
        "addParentData": False,
        "proxyConfiguration": {
            "useApifyProxy": True,
            "apifyProxyGroups": ["RESIDENTIAL"]
        },
        "customHeaders": {
            "user-agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1"
        }
    }

    try:
        logger.info(f"🚀 [EXTRAÇÃO UNIFICADA] Buscando os últimos {limite_posts} posts e comentários de: {perfil_url_limpa}")
        run = client.actor("shu8hvrXbJbY3Eb9W").call(run_input=run_input)
        
        dataset_id = getattr(run, "default_dataset_id", None)
        if not dataset_id and hasattr(run, "data") and isinstance(run.data, dict):
            dataset_id = run.data.get("defaultDatasetId") or run.data.get("default_dataset_id")

        if not dataset_id:
            logger.error("❌ [EXTRAÇÃO UNIFICADA] 'defaultDatasetId' não localizado no retorno.")
            return pd.DataFrame(), pd.DataFrame()

        dataset_items = client.dataset(dataset_id).list_items().items

        if not dataset_items:
            logger.warning("⚠️ [EXTRAÇÃO UNIFICADA] Nenhum item retornado.")
            return pd.DataFrame(), pd.DataFrame()

        return estruturar_dados_instagram(dataset_items)

    except Exception as e:
        logger.error(f"❌ [EXTRAÇÃO UNIFICADA] Falha na chamada da API: {str(e)}")
        return pd.DataFrame(), pd.DataFrame()