import json
import pandas as pd
from pathlib import Path
from config.settings import logger

# Importa a sua função centralizada, que agora já possui todo o poder híbrido
from src.transformation.sentiment import aplicar_analise_sentimento_dataframe

import warnings
# Silencia os avisos chatos de encerramento de recursos e depreciamento
warnings.filterwarnings("ignore", category=ResourceWarning)
warnings.filterwarnings("ignore", message=".*resource_tracker.*")

# --- CONFIGURAÇÃO DE CAMINHOS ---
JSON_PATH = Path("dataset_instagram-scraper_2026-07-11_02-59-45-309.json")
OUTPUT_CSV_PATH = Path("reports/governo_sp/data_source/2026_07_instagram_processado.csv")

def orquestrar_pipeline_instagram():
    """
    Orquestrador focado no fluxo de dados do Instagram.
    Carrega o JSON bruto da Apify, dispara a esteira unificada de NLP
    e exporta o resultado estruturado para o Looker Studio.
    """
    if not JSON_PATH.exists():
        logger.error(f"❌ [ETL] Arquivo bruto {JSON_PATH} não foi encontrado na raiz do projeto.")
        return

    logger.info(f"📦 [ETL] Carregando dados locais extraídos do Instagram...")
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        posts_data = json.load(f)

    comentarios_pipeline = []

    # Extrai e achata a árvore estrutural do nó de comentários da Apify
    for post in posts_data:
        shortcode = post.get("shortCode")
        data_post = post.get("timestamp")
        comentarios_lista = post.get("latestComments", [])
        
        for comment in comentarios_lista:
            comentarios_pipeline.append({
                "post_id": shortcode,
                "data_post": data_post,
                "autor_comentario": comment.get("ownerUsername"),
                "texto": comment.get("text"),
                "data_comentario": comment.get("timestamp")
            })

    # Cria o DataFrame inicial
    df_instagram = pd.DataFrame(comentarios_pipeline)
    
    if df_instagram.empty:
        logger.warning("⚠️ [ETL] O DataFrame extraído do JSON está vazio. Encerrando o fluxo.")
        return

    try:
        # Invoca a função core do projeto passando o parâmetro obrigatório 'coluna_texto'
        # Toda a mágica de separar emojis puros e rodar o BERT acontece lá dentro!
        df_processado = aplicar_analise_sentimento_dataframe(df_instagram, coluna_texto="texto")
        
        # --- SALVAMENTO DOS DADOS PARA O LOOKER STUDIO ---
        OUTPUT_CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
        df_processado.to_csv(OUTPUT_CSV_PATH, sep=";", index=False, encoding="utf-8")
        
        logger.info(f"💾 [ETL] Arquivo final com sentimentos consolidado em: {OUTPUT_CSV_PATH}")
        print(f"\n✨ Esteira finalizada! Resultados salvos com sucesso em {OUTPUT_CSV_PATH}")

    except Exception as e:
        logger.error(f"❌ [ETL] Erro crítico durante o processamento do lote do Instagram: {str(e)}")


if __name__ == "__main__":
    print("🎬 Iniciando pipeline de orquestração do Instagram...")
    orquestrar_pipeline_instagram()