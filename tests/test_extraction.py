import pytest
import pandas as pd
from pathlib import Path
from unittest.mock import patch, MagicMock
from src.extraction import coletar_noticias_politico

def carregar_massa_extraction():
    caminho = Path(__file__).parent / "fixtures" / "massa_extraction.csv"
    if not caminho.exists(): return []
    # O segredo está em abrir especificando o encoding UTF-8
    with open(caminho, "r", encoding="utf-8") as f:
        return list(pd.read_csv(f, sep=";").itertuples(index=False, name=None))

@pytest.mark.parametrize("termo, instagram, fonte", carregar_massa_extraction())
@patch('src.extraction.google_news.GoogleNews')
def test_pipeline_extracao_em_lote_50_cenarios(mock_gn, termo, instagram, fonte):
    """Garante resiliência de parse e estrutura para 50 inputs de provedores diferentes."""
    instance = mock_gn.return_value
    instance.search.return_value = {
        'entries': [{'title': f'Report sobre {termo}', 'link': 'http://link.com', 'published': '2026-07', 'source': {'text': fonte}}]
    }
    
    df = coletar_noticias_politico(termo, dias=7)
    assert isinstance(df, pd.DataFrame)
    assert not df.empty
    assert df.loc[0, 'fonte'] == fonte