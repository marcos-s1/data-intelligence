import os
import sys
from pathlib import Path
from dotenv import load_dotenv

print("-" * 50)
print(f"🐍 Interpretador Python Atual: {sys.executable}")
print(f"📁 Pasta onde o terminal está rodando (CWD): {os.getcwd()}")
print(f"📍 Pasta onde este script está salvo: {Path(__file__).resolve().parent}")

# Força o caminho absoluto do .env baseado na localização do script
caminho_env = Path(__file__).resolve().parent / ".env"
print(f"🔍 Procurando arquivo .env em: {caminho_env}")
print(f"❓ O arquivo .env existe nesse local? {'✅ SIM' if caminho_env.exists() else '❌ NÃO'}")

# Carrega e testa o token
load_dotenv(dotenv_path=caminho_env)
token = os.getenv("APIFY_TOKEN")

if token:
    print(f"🔑 Token carregado com sucesso! Início do Token: {token[:8]}...")
else:
    print("❌ Falha: O token APIFY_API_TOKEN continua retornando None.")
print("-" * 50)