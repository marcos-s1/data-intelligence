import os
from pathlib import Path

def criar_arquitetura_projeto():
    # Define o diretório raiz do projeto (onde o script está rodando)
    raiz = Path(__file__).parent.resolve()
    
    print(f"🚀 Iniciando a criação da estrutura em: {raiz}\n")

    # 1. Definição de todas as pastas que precisam ser criadas
    diretorios = [
        "config",
        "docs",
        "reports",
        "src",
        "src/extraction",
        "src/transformation",
        "src/utils"
    ]

    # Criação das pastas
    for pasta in diretorios:
        caminho_pasta = raiz / pasta
        caminho_pasta.mkdir(parents=True, exist_ok=True)
        print(f"📁 Pasta criada/verificada: {pasta}")

    print("\n" + "-"*40 + "\n")

    # 2. Definição dos arquivos base a serem gerados
    # Mapeia o caminho relativo e o conteúdo inicial padrão (se houver)
    arquivos_base = {
        ".gitignore": "__pycache__/\n*.pyc\n.env\nreports/**/data_source/*.csv\nreports/**/data_source/*.json\n",
        "README.md": "# Politica Data Intelligence\n\nFramework modular para análise de dados e inteligência de mandato para prefeituras e deputados.",
        "requirements.txt": "pygooglenews\ninstaloader\npandas\nspacy\ntransformers\ntorch\npyyaml\n",
        "main.py": 'if __name__ == "__main__":\n    print("Orquestrador principal iniciado.")\n',
        "config/__init__.py": "",
        "config/settings.py": "# Configurações globais de caminhos e parâmetros do sistema\n",
        "docs/dicionario_dados.md": "# Dicionário de Dados\n\nDocumentação dos schemas de entrada e saída das tabelas processadas.",
        "docs/manual_operacao.md": "# Manual de Operação\n\nInstruções de execução e deploy do pipeline de dados.",
        "src/__init__.py": "",
        "src/extraction/__init__.py": "",
        "src/extraction/instagram.py": "# Módulo de extração de dados do Instagram\n",
        "src/extraction/google_news.py": "# Módulo de extração de dados do Google News\n",
        "src/transformation/__init__.py": "",
        "src/transformation/nlp_engine.py": "# Módulo de processamento de linguagem natural (Lematização/Frequência)\n",
        "src/transformation/sentiment.py": "# Módulo de classificação de sentimento (Hugging Face Pipeline)\n",
        "src/utils/__init__.py": "",
        "src/utils/helpers.py": "# Funções auxiliares gerais\n",
        "src/utils/io_manager.py": "# Gerenciador de leitura/escrita de arquivos e diretórios dinâmicos\n",
    }

    # Conteúdo específico e estruturado para o arquivo de configuração dos clientes
    conteudo_yaml = """# Cadastro de clientes ativos para processamento em lote
clientes:
  - id: "cliente_01_alesp"
    nome: "Deputado Fulano"
    tipo: "estadual"
    termo_busca: '"Deputado Fulano" OR "Assembleia Legislativa"'
    instagram: "deputado_fulano_oficial"
    
  - id: "prefeitura_salvaterra"
    nome: "Prefeitura de Salvaterra"
    tipo: "prefeitura"
    termo_busca: '"Prefeitura de Salvaterra" OR "Prefeito de Salvaterra"'
    instagram: "prefeiturasalvaterra"
"""
    arquivos_base["config/clientes.yaml"] = conteudo_yaml

    # Criação dos arquivos
    for arquivo, conteudo in arquivos_base.items():
        caminho_arquivo = raiz / arquivo
        
        # Só cria o arquivo se ele não existir para evitar sobrescrever códigos futuros
        if not caminho_arquivo.exists():
            caminho_arquivo.write_text(conteudo, encoding='utf-8')
            print(f"📄 Arquivo criado: {arquivo}")
        else:
            print(f"⚠️ Arquivo já existente (ignorado): {arquivo}")

    print("\n✅ Estrutura de Engenharia de Dados montada com sucesso e pronta para uso!")

if __name__ == "__main__":
    criar_arquitetura_projeto()