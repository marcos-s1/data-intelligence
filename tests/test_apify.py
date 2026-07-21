import os
import json
import time
import requests
import pandas as pd
from dotenv import load_dotenv

# Carrega o token secreto do arquivo .env
load_dotenv()
APIFY_TOKEN = os.getenv("APIFY_TOKEN")
INSTAGRAM_PROFILE = "tarcisiogdf"
MAX_POSTS = 3  # Avalia as 3 publicações mais recentes do feed

if not APIFY_TOKEN:
    print("❌ ERRO: Defina a variável APIFY_TOKEN dentro do seu arquivo .env!")
    exit()

# URL do Actor correto para raspagem de perfil e comentários acoplados
run_actor_url = f"https://api.apify.com/v2/acts/apify~instagram-scraper/runs?token={APIFY_TOKEN}"

# Payload exato exigido pelo modelo de perfil completo da Apify
payload = {
    "username": [INSTAGRAM_PROFILE],
    "resultsLimit": MAX_POSTS,
    "scrapeType": "posts"
}
headers = {"Content-Type": "application/json"}

print(f"🚀 [APIFY] Iniciando requisição para o perfil: @{INSTAGRAM_PROFILE}...")
response = requests.post(run_actor_url, headers=headers, data=json.dumps(payload))

if response.status_code == 201:
    run_data = response.json()
    run_id = run_data["data"]["id"]
    dataset_id = run_data["data"]["defaultDatasetId"]
    print(f"✔️ Tarefa iniciada na nuvem da Apify! Run ID: {run_id}")
    
    # LOOP DE MONITORAMENTO: Espera o Scraper terminar na nuvem
    print("⏳ Aguardando processamento dos proxies residenciais da Apify...")
    while True:
        status_url = f"https://api.apify.com/v2/actor-runs/{run_id}?token={APIFY_TOKEN}"
        status_res = requests.get(status_url).json()
        status = status_res["data"]["status"]
        
        if status == "SUCCEEDED":
            print("🏁 Extração concluída com sucesso na nuvem!")
            break
        elif status in ["FAILED", "ABORTED", "TIMED-OUT"]:
            print(f"❌ Ocorreu uma falha no Actor da Apify. Status: {status}")
            exit()
            
        time.sleep(5)  # Aguarda 5 segundos antes de checar novamente
        
    # Baixa os resultados consolidados do Dataset
    fetch_data_url = f"https://api.apify.com v2/datasets/{dataset_id}/items?token={APIFY_TOKEN}"
    posts_data = requests.get(fetch_data_url).json()
    
    # PARSE DOS DADOS: Mapeando a opinião popular (comentários) para DataFrame
    comentarios_pipeline = []
    
    for post in posts_data:
        shortcode = post.get("shortCode")
        data_post = post.get("timestamp")
        # Vasculha a lista interna de 'latestComments' enviada pela Apify
        comentarios_lista = post.get("latestComments", [])
        
        for comment in comentarios_lista:
            comentarios_pipeline.append({
                "post_id": shortcode,
                "data_post": data_post,
                "autor_comentario": comment.get("ownerUsername"),
                "texto": comment.get("text"),
                "data_comentario": comment.get("timestamp")
            })
            
    # Cria o DataFrame estruturado exatamente como o seu pipeline original espera
    df_instagram = pd.DataFrame(comentarios_pipeline)
    
    print(f"\n📊 --- SUCESSO COLETADO VIA CÓDIGO ---")
    print(f"Total de comentários extraídos: {len(df_instagram)}")
    print(df_instagram.head(5))

else:
    print(f"❌ Falha ao acionar a Apify. Status Code: {response.status_code}")
    print(response.text)