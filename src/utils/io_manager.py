# Gerenciador de leitura/escrita de arquivos e diretórios dinâmicos
import pandas as pd
from datetime import datetime
from pathlib import Path
from config.settings import logger, REPORTS_DIR

def garantir_diretorio_cliente(cliente_id: str) -> Path:
    """
    Garante que a estrutura de pastas para o cliente e para o mês atual exista.
    Padrão criado: reports/nome_do_cliente/data_source/
    
    Args:
        cliente_id (str): ID único do cliente vindo do arquivo de configuração.
        
    Returns:
        Path: Caminho do diretório 'data_source' pronto para salvar arquivos.
    """
    # Define o caminho base do cliente dentro da pasta reports
    pasta_cliente = REPORTS_DIR / cliente_id / "data_source"
    
    # Cria os diretórios caso não existam (parents=True garante a criação em cadeia)
    pasta_cliente.mkdir(parents=True, exist_ok=True)
    
    return pasta_cliente

def salvar_dados_consolidados(df: pd.DataFrame, cliente_id: str, tipo_dado: str) -> bool:
    """
    Salva o DataFrame processado em formato CSV dentro da pasta correta do cliente,
    adicionando um sufixo com o ano e mês atual para controle histórico.
    
    Args:
        df (pd.DataFrame): Dados coletados/processados.
        cliente_id (str): ID do cliente no sistema.
        tipo_dado (str): Identificador do tipo de dado (ex: 'noticias', 'instagram').
        
    Returns:
        bool: True se o arquivo foi salvo com sucesso, False caso contrário.
    """
    if df.empty:
        logger.warning(f"O DataFrame de '{tipo_dado}' para o cliente '{cliente_id}' está vazio. Nenhuma gravação realizada.")
        return False
        
    try:
        # Garante a existência da pasta e recupera o caminho correto
        diretorio_salvamento = garantir_diretorio_cliente(cliente_id)
        
        # Gera o sufixo com o ano e mês atual (ex: 2026_07)
        competencia_atual = datetime.now().strftime("%Y_%m")
        
        # Monta o nome do arquivo final (ex: 2026_07_instagram.csv)
        nome_arquivo = f"{competencia_atual}_{tipo_dado}.csv"
        caminho_final = diretorio_salvamento / nome_arquivo
        
        # Salva o arquivo em formato CSV usando boas práticas (UTF-8 com BOM para abrir direto no Excel se necessário)
        df.to_csv(caminho_final, index=False, encoding='utf-8-sig', sep=';')
        
        logger.info(f"Dados salvos com sucesso em: {caminho_final}")
        return True
        
    except Exception as e:
        logger.error(f"Erro ao salvar os dados de '{tipo_dado}' para o cliente '{cliente_id}': {str(e)}")
        return False

if __name__ == "__main__":
    # Teste local isolado (Sanity Check)
    print("🧪 Executando teste isolado do módulo io_manager.py...")
    df_teste = pd.DataFrame([{"teste": 123, "nome": "Validação"}])
    salvar_dados_consolidados(df_teste, "cliente_teste_venda", "teste_io")