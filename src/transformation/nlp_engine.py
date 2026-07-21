# Módulo de processamento de linguagem natural (Lematização/Frequência)
import pandas as pd
import spacy
from collections import Counter
from typing import List, Tuple
from config.settings import logger, MODELO_SPACY

# Inicialização global do modelo do spaCy (Lazy Loading)
_nlp = None

def _inicializar_spacy():
    """
    Carrega o modelo do spaCy em português de forma segura e encapsulada na memória.
    """
    global _nlp
    if _nlp is None:
        logger.info(f"Carregando modelo SpaCy: {MODELO_SPACY}")
        try:
            _nlp = spacy.load(MODELO_SPACY)
            logger.info("Modelo SpaCy carregado com sucesso.")
        except OSError:
            logger.error(f"Modelo '{MODELO_SPACY}' não encontrado. Certifique-se de executar: python -m spacy download {MODELO_SPACY}")
            raise OSError(f"Modelo {MODELO_SPACY} ausente.")

def extrair_pautas_quentes(lista_textos: List[str], top_n: int = 15) -> List[Tuple[str, int]]:
    """
    Processa uma lista de textos, remove pontuações, numerais e stopwords,
    lematiza os termos e retorna um ranking das palavras mais frequentes (Substantivos e Verbos).
    
    Args:
        lista_textos (List[str]): Lista com os textos (notícias ou comentários) coletados.
        top_n (int): Quantidade de termos que devem retornar no ranking.
        
    Returns:
        List[Tuple[str, int]]: Lista de tuplas contendo (termo, frequência), pronta para virar um gráfico.
    """
    if not lista_textos:
        logger.warning("Lista de textos vazia enviada para o NLP Engine.")
        return []
        
    _inicializar_spacy()
    
    palavras_chave = []
    logger.info(f"Iniciando extração de tópicos para {len(lista_textos)} registros de texto...")
    
    # Utilizamos o nlp.pipe para processamento eficiente em lote (multithreading nativo do spaCy)
    for doc in _nlp.pipe(lista_textos, batch_size=50, disable=["ner", "parser"]):
        for token in doc:
            # Filtros de limpeza:
            # 1. Ignora stopwords, pontuações, espaços e numerais
            # 2. Mantém apenas Substantivos (NOUN) e Verbos (VERB) - que carregam o significado da pauta
            if (token.is_alpha and 
                not token.is_stop and 
                not token.is_space and 
                token.pos_ in ['NOUN', 'VERB'] and 
                len(token.text) > 2): # Ignora fragmentos menores que 2 letras
                
                # Coleta o lema minúsculo (simplificação gramatical)
                palavras_chave.append(token.lemma_.lower())
                
    # Realiza a contagem de frequência dos termos agrupados
    contador = Counter(palavras_chave)
    ranking = contador.most_common(top_n)
    
    logger.info(f"Extração concluída. Top 5 termos detectados: {ranking[:5]}")
    return ranking

def converter_ranking_para_df(ranking: List[Tuple[str, int]]) -> pd.DataFrame:
    """
    Função auxiliar para transformar a lista de tuplas em um DataFrame estruturado,
    facilitando a exportação via io_manager.
    """
    if not ranking:
        return pd.DataFrame(columns=['termo', 'frequencia'])
    return pd.DataFrame(ranking, columns=['termo', 'frequencia'])

if __name__ == "__main__":
    # Teste local isolado (Sanity Check)
    print("🧪 Executando teste isolado do módulo nlp_engine.py...")
    
    textos_teste = [
        "Os buracos na estrada vicinal estão gerando acidentes graves na entrada da cidade.",
        "Prefeito prometeu tapar os buracos da rua principal mas nada foi feito até agora.",
        "Moradores reclamam de buraco e falta de asfalto perto do posto de saúde municipal.",
        "A prefeitura começou a asfaltar a avenida central ontem pela manhã."
    ]
    
    resultado_ranking = extrair_pautas_quentes(textos_teste, top_n=5)
    df_ranking = converter_ranking_para_df(resultado_ranking)
    print("\n", df_ranking)