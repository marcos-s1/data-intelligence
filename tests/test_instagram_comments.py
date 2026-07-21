import unittest
import os
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

from src.extraction.instagram_comments import extrair_comentarios_lote_instagram

class TestInstagramCommentsExtraction(unittest.TestCase):
    """Conjunto de testes para validação do Passo 2 - Coleta de Comentários."""

    def setUp(self):
        self.token = os.getenv("APIFY_TOKEN")
        # URL real do post usado no seu exemplo de anexo
        self.urls_teste = ["https://www.instagram.com/p/DasPImoR6I-/"]

    def test_extracao_comentarios_lote(self):
        if not self.token:
            self.skipTest("Mapeamento abortado: APIFY_API_TOKEN ausente.")

        # Executa a extração de comentários
        df_comentarios = extrair_comentarios_lote_instagram(self.urls_teste, limite_comentarios_por_post=15)

        self.assertIsInstance(df_comentarios, pd.DataFrame)
        self.assertFalse(df_comentarios.empty, "O DataFrame de comentários veio vazio.")
        
        # Checa o contrato de colunas estruturadas
        colunas_esperadas = ["post_id", "url_post", "comentario_id", "texto", "data_comentario", "autor_comentario"]
        for col in colunas_esperadas:
            self.assertIn(col, df_comentarios.columns, f"A coluna '{col}' está ausente.")

        print(f"\n✅ Passo 2 Testado! Primeiro comentário capturado: '{df_comentarios['texto'].iloc[0]}'")

if __name__ == "__main__":
    unittest.main()