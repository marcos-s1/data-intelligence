# 🏛️ Pipeline de Inteligência Digital & Sentimento Público

Um ecossistema avançado de **Data Science e Inteligência Artificial** focado em análise de redes sociais, monitoramento de imprensa e auditoria de sentimento público. Projetado para fornecer inteligência competitiva de nível C-Level para figuras públicas, governos e campanhas políticas.

---

## 🎯 Visão Geral

Este projeto automatiza a extração de dados do Instagram (Posts e Comentários) e do Google News, aplicando processamento de linguagem natural (NLP) para transformar o engajamento bruto em direcionamentos estratégicos de comunicação. 

O pipeline finaliza sua execução gerando um **Relatório Executivo em Markdown**, acompanhado de gráficos estatísticos, dispensando a necessidade de trabalho manual de compilação.

## 🚀 Principais Funcionalidades (Features)

* **🤖 Análise de Sentimento (NLP/BERT):** Classificação automatizada de milhares de comentários em Positivo, Neutro ou Negativo, extraindo o **Net Sentiment Score (NSS)** e o Índice de Polarização (Controversy Score).
* **📊 Matriz BCG de Pautas:** Posicionamento estratégico de temas (Segurança, Saúde, Educação) cruzando Volume de Postagens vs. Taxa de Aprovação Popular.
* **🗣️ Share of Voice (SoV):** Monitoramento de competitividade digital contra adversários políticos, avaliando quem detém a hegemonia da narrativa na rede.
* **☁️ Nuvens de Palavras Triplas:** Extração semântica dividida em Visão Geral, Pontos Fortes (Apoio) e Matriz de Riscos (Dores/Reclamações).
* **📈 NPS Político:** Mapeamento da base segmentando os usuários entre Promotores (Militância/Apoio), Neutros e Detratores (Oposição Ativa).
* **⏱️ Lag & Ressonância:** Análise de desalinhamento de narrativas, cruzando o volume de pautas da imprensa oficial (Google News) com a real demanda da população no Instagram.

---

## 🛠️ Stack Tecnológico

* **Linguagem:** Python 3.10+
* **Manipulação de Dados:** `pandas`, `numpy`
* **Visualização:** `matplotlib`, `seaborn`, `wordcloud`
* **Extração de Dados:** [Apify](https://apify.com/) (Instagram Scraper)
* **NLP & IA:** Integração nativa para modelos de Análise de Sentimento (Hugging Face / BERT)

---

## 📁 Estrutura do Projeto

```text
📦 inteligencia-digital-politica
 ┣ 📂 config
 ┃ ┣ 📜 clientes.yaml        # Configuração de clientes, @s oficiais e concorrentes
 ┃ ┗ 📜 settings.py          # Variáveis globais e setup de logs
 ┣ 📂 reports                # Output dos relatórios gerados automaticamente
 ┃ ┗ 📂 governo_sp           # Exemplo de pasta de cliente
 ┃   ┣ 📂 data_source        # CSVs brutos (posts, comentários, notícias, concorrentes)
 ┃   ┣ 📜 relatorio.md       # Relatório final gerado
 ┃   ┗ 📜 *.png              # Gráficos (BCG, Heatmap, SoV, Nuvens)
 ┣ 📂 src
 ┃ ┣ 📂 extraction           # Scripts de extração (Apify, Google News)
 ┃ ┣ 📂 transformation       # Limpeza, Engenharia de Features e NLP
 ┃ ┗ 📂 utils                # Utilitários de salvamento e formatação
 ┣ 📜 .env                   # Variáveis de ambiente (Tokens API)
 ┣ 📜 pipeline.py            # Orquestrador central (Extração -> IA -> Salvamento)
 ┣ 📜 gerar_relatorio.py     # Motor de cálculos matemáticos e geração do Markdown/Gráficos
 ┗ 📜 README.md
```

 ## ⚙️ Configuração e Instalação

 
* **1. Clone o repositório e instale as dependências** 
Crie um arquivo .env na raiz do projeto com suas credenciais:

```text
git clone [https://github.com/seu-usuario/inteligencia-digital.git](https://github.com/seu-usuario/inteligencia-digital.git)
cd inteligencia-digital
pip install -r requirements.txt
```

* **2. Configure as Variáveis de Ambiente** 
Crie um arquivo .env na raiz do projeto com suas credenciais:

```text
APIFY_TOKEN=seu_token_apify_aqui
USAR_API_INSTAGRAM=True
USAR_API_NOTICIAS=True
```

* **3. Mapeie seus Clientes e Concorrentes** 
Edite o arquivo config/clientes.yaml:

```text
clientes:
  - id: "governo_sp"
    nome: "Governo do Estado de São Paulo"
    termo_busca: '"Governo de São Paulo" OR "Tarcísio de Freitas" OR "Governo do Estado de São Paulo" OR "Governo SP" OR "Política São Paulo" OR "Governo paulista" OR "Governo do Estado de SP" OR "polemica política São Paulo" OR "Acusação de corrupção Governador" OR "Governo paulista" OR "Governo do Estado de SP" OR "polemica política São Paulo" OR "Acusação de corrupção São Paulo"'
    instagram: "tarcisiogdf"
    concorrentes: ["fernandohaddadoficial", "guilhermeboulos.oficial", "rodrigogarcia"]
```

 ## 🏃 Como Executar

 O fluxo foi desenhado para ser modular. Você pode rodar a extração e a geração do relatório de forma independente.

 * **Passo 1: Rodar o Pipeline de Extração e IA** 

    Faz a requisição aos servidores (Apify/News), limpa os dados, aplica análise de sentimento e salva os arquivos localmente em reports/cliente/data_source/.

    ```text
    python main.py
    ```

    (Nota: Se as flags no .env estiverem como False, o pipeline pulará a extração online e lerá os CSVs pré-existentes na pasta).

 * **Passo 2: Gerar o Relatório Executivo** 

    Consome os arquivos gerados, calcula os KPIs avançados, plota os gráficos e compõe o Markdown final.

    ```text
    python gerar_relatorio.py
    ```

 ## 📊 Outputs Gerados
* **relatorio_executivo.md:** Relatorio com as informações coletadas e pronto para conversão em PDF corporativo.
* **Graficos e informações auxiliares utilizados para montagem do relatorio** 


 ## 🔒 Segurança e Limitações

 Blindagem de Erros: O código possui fallbacks automáticos. Se um CSV estiver ausente ou uma coluna mudar de nome no extrator, o pipeline cria dummies dinâmicos para garantir que a geração do relatório não quebre.

 Privacidade: Não expõe senhas ou tokens (geridos estritamente via .env).

 Sazonalidade: Resultados preditivos sujeitos a alterações no algoritmo da Meta (Instagram). Recomenda-se cadência de execução quinzenal.