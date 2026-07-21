import pytest
import pandas as pd
from pathlib import Path
from src.transformation import aplicar_analise_sentimento_dataframe, extrair_pautas_quentes

def carregar_massa_transform():
    caminho = Path(__file__).parent / "fixtures" / "massa_transform.csv"
    if not caminho.exists(): return []
    # Forçando o encoding correto aqui
    with open(caminho, "r", encoding="utf-8") as f:
        return list(pd.read_csv(f, sep=";").itertuples(index=False, name=None))

@pytest.mark.parametrize("texto, sentimento, lemma", carregar_massa_transform())
def test_ia_e_nlp_em_lote_50_cenarios(texto, sentimento, lemma):
    """Executa testes cruzados de IA e lematização gramatical para 50 variações de texto."""
    # 1. Valida Sentimento (IA)
    df = pd.DataFrame({"texto": [texto]})
    df_res = aplicar_analise_sentimento_dataframe(df, "texto")
    assert df_res.loc[0, "sentimento"] == sentimento
    
    # 2. Valida Extração de Pautas (NLP)
    ranking = extrair_pautas_quentes([texto], top_n=5)
    termos_extraidos = [item[0] for item in ranking]
    assert lemma in termos_extraidos