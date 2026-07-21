import pytest
import pandas as pd
from pathlib import Path
from unittest.mock import patch
from src.utils.io_manager import salvar_dados_consolidados

def carregar_massa_utils():
    caminho = Path(__file__).parent / "fixtures" / "massa_utils.csv"
    if not caminho.exists(): return []
    # Forçando o encoding correto aqui
    with open(caminho, "r", encoding="utf-8") as f:
        return list(pd.read_csv(f, sep=";").itertuples(index=False, name=None))

@pytest.mark.parametrize("cliente_id, tipo_dado, nome_esperado", carregar_massa_utils())
def test_infraestrutura_io_em_lote_50_cenarios(tmp_path, cliente_id, tipo_dado, nome_esperado):
    """Valida gravação segura no disco contra 50 variações de caracteres especiais de municípios."""
    df_falso = pd.DataFrame([{"dados_municipais": "Validação de Escrita Líquida"}])
    
    with patch('src.utils.io_manager.REPORTS_DIR', tmp_path):
        sucesso = salvar_dados_consolidados(df_falso, cliente_id, tipo_dado)
        assert sucesso is True
        
        # Valida se a pasta com o ID complexo foi gerada fisicamente
        pasta_verificacao = tmp_path / cliente_id / "data_source"
        assert pasta_verificacao.exists()
        
        # Garante que o arquivo correspondente está salvo
        arquivos_gerados = [f.name for f in pasta_verificacao.glob("*.csv")]
        assert any(tipo_dado in nome for nome in arquivos_gerados)