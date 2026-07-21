import os
import pandas as pd
from apify_client import ApifyClient
from config.settings import logger

def extrair_comentarios_lote_instagram(lista_urls_posts: list, limite_comentarios_por_post: int = 250) -> pd.DataFrame:
    """Consome a API da Apify para extrair os comentários de múltiplos posts em lote.

    Esta função lê uma lista de URLs de publicações (geradas pelo campo 'url' do Passo 1),
    dispara o Actor configurado para coletar nós do tipo 'comments' e unifica os resultados.

    Args:
        lista_urls_posts (list): Lista contendo as URLs canônicas das postagens (campo 'url').
        limite_comentarios_por_post (int, optional): Limite de comentários por post. Padrão 250.

    Returns:
        pd.DataFrame: DataFrame unificado com todos os comentários dos posts informados.
    """
    if not lista_urls_posts:
        logger.warning("⚠️ [EXTRAÇÃO COMENTÁRIOS] Lista de URLs de posts enviada está vazia.")
        return pd.DataFrame()

    apify_token = os.getenv("APIFY_TOKEN")
    if not apify_token:
        logger.error("❌ [EXTRAÇÃO COMENTÁRIOS] APIFY_API_TOKEN não configurado no .env!")
        return pd.DataFrame()

    client = ApifyClient(apify_token)
    
    # Payload de entrada do Actor focado em comentários
    run_input = {
        "addParentData": False,
        "directUrls": lista_urls_posts,
        "resultsLimit": limite_comentarios_por_post,
        "resultsType": "comments",
        "searchLimit": limite_comentarios_por_post,
        "searchType": "hashtag"
    }

    try:
        logger.info(f"🚀 [EXTRAÇÃO COMENTÁRIOS] Disparando lote de comentários para {len(lista_urls_posts)} posts.")
        
        # Executa o Actor focado em comentários
        run = client.actor("shu8hvrXbJbY3Eb9W").call(run_input=run_input)
        
        # Desempacotamento seguro do objeto ActorRun do SDK Python
        dataset_id = None
        if hasattr(run, "default_dataset_id"):
            dataset_id = getattr(run, "default_dataset_id")
        elif hasattr(run, "data") and isinstance(run.data, dict):
            dataset_id = run.data.get("defaultDatasetId") or run.data.get("default_dataset_id")
            
        if not dataset_id:
            logger.error("❌ [EXTRAÇÃO COMENTÁRIOS] defaultDatasetId não localizado no retorno.")
            return pd.DataFrame()

        logger.info("📦 [EXTRAÇÃO COMENTÁRIOS] Coleta finalizada na nuvem. Baixando itens...")
        dataset_items = client.dataset(dataset_id).list_items().items

        if not dataset_items:
            logger.warning("⚠️ [EXTRAÇÃO COMENTÁRIOS] Nenhum comentário foi capturado no lote.")
            return pd.DataFrame()

        comentarios_pipeline = []

        # Parseamento baseado estritamente no contrato do anexo de comentários
        for item in dataset_items:
            # Captura a URL da postagem de origem vinda do nó do comentário
            post_url = item.get("postUrl", "")
            
            # Isola o shortcode de identificação do post de forma segura
            shortcode = "unknown"
            if "/p/" in post_url:
                shortcode = post_url.split("/p/")[-1].replace("/", "")
            elif "/clips/" in post_url:
                shortcode = post_url.split("/clips/")[-1].replace("/", "")

            comentarios_pipeline.append({
                "post_id": shortcode,
                "url_post": post_url,
                "comentario_id": item.get("id"),
                "texto": item.get("text"),
                "data_comentario": item.get("timestamp"),
                "autor_comentario": item.get("ownerUsername")
            })

        df_comentarios = pd.DataFrame(comentarios_pipeline)
        logger.info(f"🎯 [EXTRAÇÃO COMENTÁRIOS] Sucesso! Coletados {len(df_comentarios)} comentários em lote.")
        return df_comentarios

    except Exception as e:
        logger.error(f"❌ [EXTRAÇÃO COMENTÁRIOS] Erro ao rodar extração em lote: {str(e)}")
        return pd.DataFrame()