import unittest
import os
import pandas as pd
from dotenv import load_dotenv

# Garante que o ambiente carregue as credenciais antes do import do módulo
load_dotenv()

from src.extraction.instagram_posts import extrair_ultimos_posts_instagram

class TestInstagramPostsExtraction(unittest.TestCase):
    """Conjunto de testes funcionais para validação da Extração Master de posts do Instagram."""

    def setUp(self):
        """Configura o cenário de teste antes de cada execução."""
        # Recupera o token para validar se o ambiente de teste está configurado
        self.token = os.getenv("APIFY_TOKEN")
        
        # Perfil público alvo para o teste funcional (Tarcísio)
        self.perfil_teste = "https://www.instagram.com/tarcisiogdf"
        self.limite_posts = 2

    def test_ambiente_possui_token_apify(self):
        """Valida se o token da Apify está devidamente configurado no arquivo .env."""
        self.assertIsNotNone(self.token, "❌ O APIFY_API_TOKEN não foi encontrado no arquivo .env.")
        self.assertNotEqual(self.token, "seu_token_aqui_da_apify", "❌ O token no .env ainda está com o texto padrão.")

    def test_extração_retorna_dataframe_valido(self):
        """Dispara a API real e valida se a estrutura do DataFrame gerado está correta."""
        if not self.token:
            self.skipTest("Ignorando teste: APIFY_API_TOKEN ausente.")

        # Executa a função core
        df_resultado = extrair_ultimos_posts_instagram(self.perfil_teste, limite_posts=self.limite_posts)

        # 1. Valida se retornou um objeto DataFrame do Pandas
        self.assertIsInstance(df_resultado, pd.DataFrame, "O retorno da função deve ser um pd.DataFrame.")

        # 2. Valida se o DataFrame não veio vazio
        self.assertFalse(df_resultado.empty, "O DataFrame retornado está vazio. Verifique o log ou os créditos da Apify.")

        # 3. Valida se o limite de posts configurado foi respeitado
        self.assertLessEqual(len(df_resultado), self.limite_posts, f"O DataFrame retornou mais de {self.limite_posts} registros.")

        # 4. Valida se as colunas essenciais para o Passo 2 e para o Looker Studio estão presentes
        colunas_obrigatorias = [
            "post_id", "shortcode", "tipo_midia", "url_post", 
            "total_curtidas", "total_comentarios", "autor_perfil"
        ]
        for coluna in colunas_obrigatorias:
            with self.subTest(coluna=coluna):
                self.assertIn(coluna, df_resultado.columns, f"A coluna obrigatória '{coluna}' está ausente no DataFrame final.")

        # 5. Valida se os shortcodes coletados são strings válidas (essencial para o passo de comentários)
        for sc in df_resultado["shortcode"].dropna():
            self.assertIsInstance(sc, str, "O shortcode coletado deve ser do tipo string.")
            self.assertTrue(len(sc) > 0, "O shortcode coletado não pode ser uma string vazia.")

        print(f"\n✅ Teste de extração concluído com sucesso! Amostra do shortcode coletado: {df_resultado['shortcode'].iloc[0]}")


if __name__ == "__main__":
    unittest.main()