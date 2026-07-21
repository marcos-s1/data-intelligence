import json
import pandas as pd
from pathlib import Path

# Caminho para o arquivo JSON que você acabou de baixar
# (Ajuste o nome do arquivo se ele estiver em outra pasta, ex: Reports ou Downloads)
JSON_PATH = Path("dataset_instagram-scraper_2026-07-11_02-59-45-309.json")

if not JSON_PATH.exists():
    print(f"❌ Arquivo {JSON_PATH} não encontrado na raiz do projeto.")
    exit()

print(f"📦 Carregando dados locais do Instagram...")
with open(JSON_PATH, "r", encoding="utf-8") as f:
    posts_data = json.load(f)

comentarios_pipeline = []

# Varre os posts contidos no arquivo JSON
for post in posts_data:
    shortcode = post.get("shortCode")
    data_post = post.get("timestamp")
    # Acessa o nó de comentários que a Apify estruturou
    comentarios_lista = post.get("latestComments", [])
    
    for comment in comentarios_lista:
        comentarios_pipeline.append({
            "post_id": shortcode,
            "data_post": data_post,
            "autor_comentario": comment.get("ownerUsername"),
            "texto": comment.get("text"),
            "data_comentario": comment.get("timestamp")
        })

# Transforma a lista de dicionários em um DataFrame estruturado do Pandas
df_instagram = pd.DataFrame(comentarios_pipeline)

print(f"\n📊 --- ANÁLISE DOS DADOS PROCESSADOS ---")
print(f"Total de posts lidos do arquivo: {len(posts_data)}")
print(f"Total de comentários extraídos: {len(df_instagram)}")

if not df_instagram.empty:
    print("\n💡 Amostra dos 5 primeiros comentários estruturados:")
    print(df_instagram[["autor_comentario", "texto"]].head(5))
    
    # Simula a gravação do arquivo que alimentará a IA e o Looker Studio
    output_path = Path("reports/governo_sp/data_source/2026_07_instagram_bruto.csv")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df_instagram.to_csv(output_path, sep=";", index=False, encoding="utf-8")
    print(f"\n💾 Arquivo salvo com sucesso em: {output_path}")