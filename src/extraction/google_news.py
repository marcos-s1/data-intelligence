# Módulo de extração de dados do Google News
import pandas as pd
from pygooglenews import GoogleNews
from config.settings import logger, DIAS_HISTORICO_PADRAO

def coletar_noticias_politico(termo_busca: str, dias: int = DIAS_HISTORICO_PADRAO) -> pd.DataFrame:
    """
    Realiza uma busca refinada por notícias recentes no Google News 
    restringindo o escopo temporal e geográfico (Brasil / PT).
    
    Args:
        termo_busca (str): Expressão lógica de busca (ex: '"Prefeitura de Salvaterra"').
        dias (int): Janela de dias retroativos para a coleta.
        
    Returns:
        pd.DataFrame: DataFrame contendo título, link, data e fonte das notícias.
    """
    logger.info(f"Iniciando coleta no Google News para a query: {termo_busca} nos últimos {dias} dias.")
    
    try:
        # Inicializa a engine do Google News configurada para o Brasil em Português
        gn = GoogleNews(lang='pt', country='BR')
        
        # Monta a query utilizando o operador de tempo do Google (when:Xd)
        query_completa = f"{termo_busca} when:{dias}d"
        
        # Executa a busca na API de RSS
        busca = gn.search(query_completa)
        entries = busca.get('entries', [])
        
        logger.info(f"Busca concluída. Encontradas {len(entries)} entradas de notícias.")
        
        if not entries:
            logger.warning(f"Nenhuma notícia encontrada para o termo: {termo_busca}")
            return pd.DataFrame(columns=['titulo', 'link', 'data_publicacao', 'fonte'])
            
        # Faz o parse dos dados brutos da estrutura XML/RSS para dicionários limpos
        dados_noticias = []
        for item in entries:
            dados_noticias.append({
                'titulo': item.get('title'),
                'link': item.get('link'),
                'data_publicacao': item.get('published'),
                'fonte': item.get('source', {}).get('text', 'Fonte Desconhecida')
            })
            
        # Converte em DataFrame estruturado
        df_noticias = pd.DataFrame(dados_noticias)
        
        # Boa prática: Garante uma limpeza básica inicial removendo possíveis duplicatas de URL
        df_noticias.drop_duplicates(subset=['link'], inplace=True)
        df_noticias.reset_index(drop=True, inplace=True)
        
        logger.info(f"Processamento concluído com sucesso. {len(df_noticias)} notícias únicas prontas.")
        return df_noticias
        
    except Exception as e:
        logger.error(f"Erro crítico durante a coleta do Google News: {str(e)}")
        # Em caso de falha, retorna um DataFrame vazio com as colunas mapeadas para não quebrar o pipeline
        return pd.DataFrame(columns=['titulo', 'link', 'data_publicacao', 'fonte'])

if __name__ == "__main__":
    # Teste local e isolado do módulo (Sanity Check)
    print("🧪 Executando teste isolado do módulo google_news.py...")
    termo_teste = '"Assembleia Legislativa"'
    df_teste = coletar_noticias_politico(termo_teste, dias=7)
    print(df_teste.head())