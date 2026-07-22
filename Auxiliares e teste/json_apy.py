import json
import pandas as pd
from pathlib import Path

def parsear_json_apify(caminho_json: str | Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Lê um arquivo JSON bruto da Apify e converte em dois DataFrames limpos:
    - df_posts: Tabela dimensão dos posts
    - df_comentarios: Tabela fato dos comentários contidos em 'latestComments'
    """
    with open(caminho_json, "r", encoding="utf-8") as f:
        items_json = json.load(f)

    posts_list = []
    comentarios_list = []

    for item in items_json:
        shortcode = item.get("shortCode") or item.get("id")
        likes = item.get("likesCount", 0) or 0
        views = item.get("videoPlayCount", 0) or 0
        comments_count = item.get("commentsCount", 0) or 0
        
        # 1. Estruturação da Tabela de Posts
        posts_list.append({
            "post_id": shortcode,
            "shortcode": shortcode,
            "tipo_midia": item.get("type"),
            "url": item.get("url"),
            "legenda": item.get("caption"),
            "total_curtidas": likes,
            "total_comentarios": comments_count,
            "visualizacoes_video": views,
            "duracao_video_segundos": item.get("videoDuration", 0) or 0,
            "timestamp_publicacao": item.get("timestamp"),
            "autor_perfil": item.get("ownerUsername") or "tarcisiogdf"
        })

        # 2. Desempacotamento dos Comentários em 'latestComments'
        for com in item.get("latestComments", []) or []:
            comentarios_list.append({
                "post_id": shortcode,
                "url_post": item.get("url"),
                "comentario_id": str(com.get("id")),
                "texto": com.get("text", ""),
                "curtidas_comentario": com.get("likesCount", 0) or 0,
                "data_comentario": com.get("timestamp"),
                "autor_comentario": com.get("ownerUsername")
            })

    df_posts = pd.DataFrame(posts_list)
    df_comentarios = pd.DataFrame(comentarios_list)

    return df_posts, df_comentarios


# ==============================================================================
# 🚀 EXEMPLO DE USO RÁPIDO:
# ==============================================================================
if __name__ == "__main__":
    caminho_json = r"C:\Users\manto\Downloads\politica-data-intelligence\Auxiliares e teste\dataset_instagram-scraper_2026-07-21_21-53-22-288.json"
    
    # 1. Converte o JSON em DataFrames
    df_posts, df_comentarios = parsear_json_apify(caminho_json)

    # 2. Salva os CSVs prontos na pasta de destino do relatório
    df_posts.to_csv("2026_07_posts_brutos.csv", index=False, encoding="utf-8-sig")
    df_comentarios.to_csv("2026_07_instagram_bruto.csv", index=False, encoding="utf-8-sig")

    print(f"✅ Processamento concluído!")
    print(f"📊 Posts gerados: {len(df_posts)}")
    print(f"💬 Comentários gerados: {len(df_comentarios)}")