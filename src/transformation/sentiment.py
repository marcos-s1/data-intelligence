import re
import os
import pandas as pd
from config.settings import logger, MODELO_SENTIMENTO

# ==============================================================================
# 🎯 CONFIGURAÇÕES E MAPAS DA CAMADA DE REDES SOCIAIS (HEURÍSTICAS)
# ==============================================================================

# Listas de emojis com representação unicode expandida e tons de pele (skin tones).
EMOJIS_POSITIVOS: list[str] = ["👏", "👍", "🙌", "❤️", "🇧🇷", "✅", "🚀", "😍", "💪", "🔥", "🏼", "🏽", "🏾", "🏿", "🏻"]
EMOJIS_NEGATIVOS: list[str] = ["👎", "❌", "🤮", "🤡", "💩", "🤬", "😠", "🗑️", "👺", "👹"]

# Dicionários de alta prioridade para o cenário político brasileiro
TERMOS_POSITIVOS_FORCADOS = [
    "parabéns", "parabens", "melhor governador", "meu voto", "futuro presidente", 
    "mito", "lindo", "orgulho", "deus abençoe", "excelente gestão", "estou com você"
]

TERMOS_NEGATIVOS_FORCADOS = [
    "fora", "ladrão", "ladrao", "pior", "enganador", "mentira", "vergonha", 
    "decepção", "decepsao", "traidor", "esquerda maldita", "comunista"
]

# Expressões Regulares pré-compiladas em memória para otimizar o processamento em lote
REGEX_URL: re.Pattern = re.compile(r"https?://[^\s]+")  # Captura links http/https
REGEX_QUEBRAS: re.Pattern = re.compile(r"[\n\r\t]+")   # Captura quebras de linha, retornos e tabs
REGEX_MENTIONS: re.Pattern = re.compile(r"@[^\s]+")   # Captura marcações de perfis (@usuario)


def _higienizar_texto_rede_social(texto: str) -> str:
    """Aplica regras de higienização digital para preparação de textos de redes sociais.

    Esta função atua como um limpador de ruídos estruturais típicos de ambientes virtuais.
    Ela normaliza URLs para evitar que o tokenizador quebre strings de endereços web, 
    elimina tabulações e quebras de linha que corrompem a exportação de arquivos CSV, 
    e remove espaços duplicados gerados durante as substituições.

    Args:
        texto (str): O texto bruto capturado diretamente da rede social (comentário ou legenda).

    Returns:
        str: O texto sanitizado, contínuo (em uma única linha) e normalizado para processamento.
    """
    if not isinstance(texto, str):
        return ""
        
    # 1. Substitui hiperlinks longos por uma tag canônica e previsível
    texto_limpo = REGEX_URL.sub("[URL]", texto)
    
    # 2. Transforma quebras de linha, retornos de carro e tabs em espaços simples
    texto_limpo = REGEX_QUEBRAS.sub(" ", texto_limpo)
    
    # 3. Mantém o texto limpo de espaços extras nas extremidades ou duplicados no meio
    return " ".join(texto_limpo.split())


def _classificar_por_emoji_puro(texto: str) -> str | None:
    """Executa a triagem heurística baseada em reações visuais puras de emoticons.

    Analisa se uma string limpa é composta estritamente por repetições de emojis contidos
    nas listas de mapeamento positivo ou negativo. Caso o usuário tenha respondido apenas 
    com reações visuais (sem conteúdo textual complexo), a função mata a análise sem 
    necessidade de acionar redes neurais profundas.

    Args:
        texto (str): O texto previamente higienizado e contínuo.

    Returns:
        str | None: Retorna a tag de sentimento correspondente ('POSITIVO' ou 'NEGATIVO')
            se o comentário se enquadrar na regra de emojis puros. Retorna 'None' caso 
            o comentário contenha texto misto ou palavras a serem interpretadas.
    """
    if not isinstance(texto, str):
        return None
        
    texto_limpo = texto.strip()
    if not texto_limpo:
        return None

    # Teste de reações positivas puras: remove todas as ocorrências mapeadas
    t_pos = texto_limpo
    for emoji in EMOJIS_POSITIVOS:
        t_pos = t_pos.replace(emoji, "")
    # Se a string resultante estiver vazia, o comentário continha apenas emojis positivos
    if len(t_pos.strip()) == 0:
        return "POSITIVO"

    # Teste de reações negativas puras: remove todas as ocorrências mapeadas
    t_neg = texto_limpo
    for emoji in EMOJIS_NEGATIVOS:
        t_neg = t_neg.replace(emoji, "")
    # Se a string resultante estiver vazia, o comentário continha apenas emojis negativos
    if len(t_neg.strip()) == 0:
        return "NEGATIVO"

    return None


# ==============================================================================
# 🧠 CORE PIPELINE: ORQUESTRADOR HÍBRIDO (HEURÍSTICA + DEEP LEARNING)
# ==============================================================================
def aplicar_analise_sentimento_dataframe(df: pd.DataFrame, coluna_texto: str = "titulo") -> pd.DataFrame:
    """Orquestra o pipeline híbrido e unificado de NLP (Natural Language Processing).

    Esta é a função principal do módulo de transformação. Ela processa um lote de dados 
    em duas camadas consecutivas de inteligência:
    1. Camada de Heurística (Filtro Passa-Alta): Limpa o texto e resolve reações puras de 
       emojis de forma instantânea.
    2. Camada Cognitiva (Deep Learning): Isola o que sobrou de texto complexo e submete 
       ao modelo Transformer/BERT (`pysentimiento`) carregado sob demanda.

    O fluxo garante alta performance em lote, economia de hardware e blindagem contra 
    quebras de exportação do CSV para o Looker Studio.

    Args:
        df (pd.DataFrame): O DataFrame original do Pandas contendo a base de dados.
        coluna_texto (str, optional): O nome da coluna que contém os textos a serem 
            analisados (Ex: 'titulo' para notícias, 'texto' para redes sociais). 
            O padrão é "titulo".

    Returns:
        pd.DataFrame: Uma cópia do DataFrame enriquecida com a coluna 'sentimento' 
            preenchida com os valores categóricos standard: 'POSITIVO', 'NEGATIVO' ou 'NEUTRO'.
    """
    if df.empty:
        logger.warning("🚨 [NLP] O DataFrame recebido está vazio. Ignorando o pipeline de sentimento.")
        return df

    if coluna_texto not in df.columns:
        logger.error(f"❌ [NLP] A coluna alvo '{coluna_texto}' não existe no DataFrame. Processamento abortado.")
        return df

    # Cria uma cópia profunda para evitar mutação indesejada no DataFrame original (Passagem por referência)
    df_trabalho = df.copy()
    
    logger.info(f"🧼 [NLP] Higienizando textos e padronizando quebras/URLs na coluna '{coluna_texto}'...")
    df_trabalho[coluna_texto] = df_trabalho[coluna_texto].apply(_higienizar_texto_rede_social)
    
    logger.info(f"⚡ [NLP] Aplicando triagem de emojis puros...")
    df_trabalho['sentimento'] = df_trabalho[coluna_texto].apply(_classificar_por_emoji_puro)
    
    # Segmentação do DataFrame para otimização de performance
    df_resolvido_regra = df_trabalho[df_trabalho['sentimento'].notna()].copy()
    df_para_ia = df_trabalho[df_trabalho['sentimento'].isna()].copy()
    
    logger.info(f"🎯 [NLP] Heurística isolou {len(df_resolvido_regra)} registros de reações puros.")

    # Se restarem linhas que a heurística não matou, invoca a rede neural
    if not df_para_ia.empty:
        try:
            logger.info(f"🧠 [NLP] Enviando {len(df_para_ia)} registros complexos para inferência via IA.")
            logger.info(f"🤖 [NLP] Inicializando modelo: {MODELO_SENTIMENTO}")
            
            # Remove a coluna temporária para que a predição da IA a recrie sem conflitos
            df_para_ia = df_para_ia.drop(columns=['sentimento'])
            
            # Lazy Loading: O import do PySentimiento ocorre aqui para poupar RAM se o lote for 100% emojis
            from pysentimiento import create_analyzer
            analyzer = create_analyzer(task="sentiment", lang="pt")
            
            # Converte a coluna para lista nativa (vetorização melhora o processamento no PyTorch/HuggingFace)
            textos_lote = df_para_ia[coluna_texto].astype(str).tolist()
            # O .predict() do pysentimiento retorna um objeto com os resultados
            # Processamos cada texto individualmente na lista para garantir compatibilidade total
            resultados = [analyzer.predict(t) for t in textos_lote]
            
            # Dicionário de tradução e padronização das saídas do modelo
            mapeamento_sentimentos = {
                "POS": "POSITIVO",
                "NEG": "NEGATIVO",
                "NEU": "NEUTRO"
            }
            
            # Popula a coluna de sentimento baseado no resultado gerado pelo BERT
            # Extrai o output (ex: 'POS') de cada objeto de predição
            sentimentos_finais = [mapeamento_sentimentos.get(res.output, "NEUTRO") for res in resultados]
            df_para_ia['sentimento'] = sentimentos_finais
            
            # Reúne as duas metades da esteira mantendo os índices consistentes
            df_final = pd.concat([df_resolvido_regra, df_para_ia], ignore_index=True)
            return df_final
            
        except Exception as e:
            logger.error(f"❌ [NLP] Falha crítica no motor de inferência da IA: {str(e)}")
            # Fallback de Segurança: Preenche os sobreviventes da IA com NEUTRO para não estourar o dashboard
            df_para_ia['sentimento'] = "NEUTRO"
            return pd.concat([df_resolvido_regra, df_para_ia], ignore_index=True)
            
    # Se a heurística limpou o lote completo (ex: post de sorteio ou só palmas), retorna imediatamente
    return df_resolvido_regra