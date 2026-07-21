import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from wordcloud import WordCloud
import datetime

def carregar_clientes():
    """Carrega os clientes da configuração ou mapeia baseado no diretório de relatórios."""
    caminhos_possiveis = ["config/clientes.yaml", "clientes.yaml", "../config/clientes.yaml"]
    for caminho in caminhos_possiveis:
        if os.path.exists(caminho):
            try:
                clientes = []
                cliente_atual = {}
                with open(caminho, "r", encoding="utf-8") as file:
                    for line in file:
                        line = line.strip()
                        if not line or line.startswith("#"): continue
                        if line.startswith("- id:") or line.startswith("id:"):
                            if cliente_atual: clientes.append(cliente_atual)
                            val = line.split(":", 1)[1].strip().strip('"').strip("'")
                            cliente_atual = {"id": val}
                        elif ":" in line and cliente_atual:
                            key, val = line.split(":", 1)
                            key = key.strip().replace("-", "").strip()
                            val = val.strip().strip('"').strip("'")
                            cliente_atual[key] = val
                    if cliente_atual: clientes.append(cliente_atual)
                if clientes: return clientes
            except Exception as e:
                print(f"⚠️ Erro ao decodificar {caminho}: {e}")
                
    if os.path.exists('reports'):
        pastas = [p for p in os.listdir('reports') if os.path.isdir(os.path.join('reports', p))]
        clientes = []
        for p in pastas:
            if os.path.exists(os.path.join('reports', p, 'data_source')):
                clientes.append({"id": p, "nome": p.replace('_', ' ').title(), "instagram": "perfil"})
        if clientes: return clientes
            
    return [{"id": "governo_sp", "nome": "Governo de SP", "instagram": "tarcisiogdf"}]


def definir_tema(legenda):
    """Lê a legenda real do Apify e categoriza o tema para o gráfico."""
    legenda = str(legenda).lower()
    if any(x in legenda for x in ['segurança', 'polícia', 'crime', 'pm', 'ssp']): return 'Segurança'
    if any(x in legenda for x in ['saúde', 'hospital', 'médico', 'vacina', 'sus']): return 'Saúde'
    if any(x in legenda for x in ['escola', 'educação', 'aluno', 'professor', 'ensino']): return 'Educação'
    if any(x in legenda for x in ['obra', 'estrada', 'infraestrutura', 'asfalto', 'transporte']): return 'Infraestrutura'
    return 'Institucional/Outros'


def gerar_relatorio_cliente(cliente):
    cliente_id = cliente.get("id")
    nome_cliente = cliente.get("nome")
    pasta_data_source = os.path.join('reports', cliente_id, 'data_source')
    pasta_saida = os.path.join('reports', cliente_id)
    
    if not os.path.exists(pasta_data_source): return
        
    # --- 1. LEITURA DOS DADOS REAIS DO CSV ---
    # Encontra os arquivos na pasta
    csv_posts, csv_insta, csv_imprensa, csv_populacao = None, None, None, None
    for f in os.listdir(pasta_data_source):
        if 'posts_brutos' in f: csv_posts = os.path.join(pasta_data_source, f)
        elif 'instagram_bruto' in f: csv_insta = os.path.join(pasta_data_source, f)
        elif 'pautas_imprensa' in f: csv_imprensa = os.path.join(pasta_data_source, f)
        elif 'pautas_populacao' in f: csv_populacao = os.path.join(pasta_data_source, f)

    if not csv_posts or not csv_insta:
        print(f"⚠️ Faltam arquivos base para {nome_cliente}.")
        return

    df_posts_raw = pd.read_csv(csv_posts, sep=';')
    df_sentimento = pd.read_csv(csv_insta, sep=';')
    df_pautas_imprensa = pd.read_csv(csv_imprensa, sep=';') if csv_imprensa else pd.DataFrame(columns=['termo', 'frequencia'])
    df_pautas_populacao = pd.read_csv(csv_populacao, sep=';') if csv_populacao else pd.DataFrame(columns=['termo', 'frequencia'])

    # TRADUZINDO COLUNAS DO APIFY PARA O RELATÓRIO
    df_posts = pd.DataFrame()
    df_posts['post_id'] = df_posts_raw['shortcode']
    df_posts['url'] = df_posts_raw['url']
    df_posts['data'] = pd.to_datetime(df_posts_raw['timestamp_publicacao']).dt.tz_localize(None)
    df_posts['curtidas'] = pd.to_numeric(df_posts_raw['total_curtidas'], errors='coerce').fillna(0)
    df_posts['comentarios'] = pd.to_numeric(df_posts_raw['total_comentarios'], errors='coerce').fillna(0)
    df_posts['views'] = pd.to_numeric(df_posts_raw['visualizacoes_video'], errors='coerce').fillna(0)
    df_posts['tipo_midia'] = df_posts_raw['tipo_midia'].fillna('Image')
    df_posts['tema'] = df_posts_raw['legenda'].apply(definir_tema)
    
    # Ordenar cronologicamente
    df_posts = df_posts.sort_values('data').reset_index(drop=True)

    # CÁLCULOS BASE
    df_posts['raw_score'] = df_posts['curtidas'] + (df_posts['comentarios'] * 10)
    max_raw = df_posts['raw_score'].max()
    df_posts['score_1000'] = (df_posts['raw_score'] / max_raw * 1000).astype(int) if max_raw > 0 else 0
    
    # Eng Rate (Tratando posts sem views)
    df_posts['eng_rate'] = np.where(df_posts['views'] > 0, ((df_posts['curtidas'] + df_posts['comentarios']) / df_posts['views']) * 100, 0)
    df_posts['prop_comentarios'] = np.where(df_posts['curtidas'] > 0, (df_posts['comentarios'] / df_posts['curtidas']) * 100, 0)
    
    # --- 2. CÁLCULO DE MÉTRICAS MoM ---
    data_atual = df_posts['data'].max()
    df_15d_atuais = df_posts[df_posts['data'] > (data_atual - pd.Timedelta(days=15))]
    df_15d_anteriores = df_posts[(df_posts['data'] <= (data_atual - pd.Timedelta(days=15))) & (df_posts['data'] > (data_atual - pd.Timedelta(days=30)))]
    df_30d_atuais = df_posts[df_posts['data'] > (data_atual - pd.Timedelta(days=30))]
    df_30d_anteriores = df_posts[(df_posts['data'] <= (data_atual - pd.Timedelta(days=30))) & (df_posts['data'] > (data_atual - pd.Timedelta(days=60)))]
    
    # Quinzenal
    qtd_posts_15d = len(df_15d_atuais)
    curtidas_15d = df_15d_atuais['curtidas'].sum()
    comentarios_15d = df_15d_atuais['comentarios'].sum()
    score_total_15d = df_15d_atuais['raw_score'].sum()
    score_total_15d_anterior = df_15d_anteriores['raw_score'].sum()
    
    crescimento_quinzenal = ((score_total_15d / score_total_15d_anterior) - 1) * 100 if score_total_15d_anterior > 0 else 0
    indicador_quinzena = "🟢" if crescimento_quinzenal > 5 else "🔴" if crescimento_quinzenal < -5 else "🟡"
    
    # MoM
    score_mes_atual = df_30d_atuais['raw_score'].sum()
    score_mes_anterior = df_30d_anteriores['raw_score'].sum()
    mom_engajamento = ((score_mes_atual / score_mes_anterior) - 1) * 100 if score_mes_anterior > 0 else 0
    indicador_mom = "🟢" if mom_engajamento > 5 else "🔴" if mom_engajamento < -5 else "🟡"

    # Net Sentiment Score (NSS)
    if 'sentimento' in df_sentimento.columns:
        total_sent = len(df_sentimento)
        positivos = len(df_sentimento[df_sentimento['sentimento'] == 'POSITIVO'])
        negativos = len(df_sentimento[df_sentimento['sentimento'] == 'NEGATIVO'])
        nss = ((positivos - negativos) / total_sent) * 100 if total_sent > 0 else 0
    else:
        nss = 0

    # Eficiência Média (Excluindo 0s para não distorcer)
    media_eng_rate = df_posts[df_posts['eng_rate'] > 0]['eng_rate'].mean()
    media_eng_rate = media_eng_rate if not pd.isna(media_eng_rate) else 0
    media_prop_comentarios = df_posts['prop_comentarios'].mean()

    # --- 3. GERAÇÃO DOS GRÁFICOS ---
    sns.set_theme(style="whitegrid")
    
    # A. Sentimento
    if not df_sentimento.empty and 'sentimento' in df_sentimento.columns:
        plt.figure(figsize=(8, 6))
        cores_sentimento = {'POSITIVO': '#2ecc71', 'NEUTRO': '#f1c40f', 'NEGATIVO': '#e74c3c'}
        contagem_sent = df_sentimento['sentimento'].value_counts()
        cores_finais = [cores_sentimento.get(x, '#95a5a6') for x in contagem_sent.index]
        plt.pie(contagem_sent, labels=contagem_sent.index, autopct='%1.1f%%', colors=cores_finais, startangle=90, wedgeprops={'edgecolor': 'white', 'linewidth': 2})
        plt.title('Distribuição de Sentimento', fontsize=14, fontweight='bold')
        plt.savefig(os.path.join(pasta_saida, 'sentimento_instagram.png'), dpi=150, bbox_inches='tight')
        plt.close()

    # B. Temas com Mais Engajamento
    plt.figure(figsize=(10, 5))
    eng_por_tema = df_posts.groupby('tema')['score_1000'].mean().sort_values(ascending=False).reset_index()
    if not eng_por_tema.empty:
        sns.barplot(x='score_1000', y='tema', data=eng_por_tema, palette='viridis')
        plt.title('Temas com Maior Engajamento Médio', fontsize=14, fontweight='bold')
        plt.xlabel('Score Médio'); plt.ylabel('')
        plt.savefig(os.path.join(pasta_saida, 'engajamento_temas.png'), dpi=150, bbox_inches='tight')
        plt.close()

    # C. Desempenho por Formato
    plt.figure(figsize=(10, 5))
    eng_por_formato = df_posts.groupby('tipo_midia')['score_1000'].mean().sort_values(ascending=False).reset_index()
    if not eng_por_formato.empty:
        sns.barplot(x='tipo_midia', y='score_1000', data=eng_por_formato, palette='magma')
        plt.title('Performance por Formato', fontsize=14, fontweight='bold')
        plt.xlabel(''); plt.ylabel('Score Médio')
        plt.savefig(os.path.join(pasta_saida, 'engajamento_formatos.png'), dpi=150, bbox_inches='tight')
        plt.close()

    # D. Comparativo de Pautas
    if not df_pautas_imprensa.empty and not df_pautas_populacao.empty:
        fig, axes = plt.subplots(1, 2, figsize=(15, 6))
        sns.barplot(x='frequencia', y='termo', data=df_pautas_imprensa.head(10), ax=axes[0], palette='Blues_r')
        axes[0].set_title('Imprensa', fontweight='bold')
        sns.barplot(x='frequencia', y='termo', data=df_pautas_populacao.head(10), ax=axes[1], palette='Oranges_r')
        axes[1].set_title('População', fontweight='bold')
        plt.suptitle('Comparativo de Narrativas', fontsize=16, fontweight='bold')
        plt.tight_layout()
        plt.savefig(os.path.join(pasta_saida, 'comparativo_pautas.png'), dpi=150, bbox_inches='tight')
        plt.close()
    
    # E. Linha do Tempo
    df_grafico = df_posts.tail(5).copy()
    if not df_grafico.empty:
        fig, ax1 = plt.subplots(figsize=(12, 7))
        x = range(len(df_grafico))
        color_comments = '#e67e22'
        ax1.plot(x, df_grafico['comentarios'], marker='s', color=color_comments, linewidth=2.5, label='Comentários', zorder=3)
        ax1.set_ylabel('Comentários', color=color_comments, fontweight='bold')
        ax2 = ax1.twinx()
        color_likes = '#3498db'
        ax2.bar(x, df_grafico['curtidas'], color=color_likes, alpha=0.3, label='Curtidas', width=0.8, zorder=1)
        ax2.set_ylabel('Curtidas', color=color_likes, fontweight='bold')
        ax1.set_xticks(x); ax1.set_xticklabels(df_grafico['data'].dt.strftime('%d/%m/%Y'))
        ax1.grid(False); ax2.grid(False)
        for i, row in df_grafico.iterrows():
            offset = 20 if i % 2 == 0 else -30 
            ax1.annotate(row['tema'], xy=(i, row['comentarios']), xytext=(0, offset), textcoords="offset points", ha='center', fontsize=9, fontweight='bold', bbox=dict(boxstyle="round,pad=0.3", fc="#fcf8e3", ec="#fbeed5", alpha=0.9), arrowprops=dict(arrowstyle="->", connectionstyle="arc3,rad=.2"))
        plt.title('Evolução do Engajamento dos Últimos Posts', fontsize=14, fontweight='bold', pad=30)
        fig.tight_layout()
        plt.savefig(os.path.join(pasta_saida, 'linha_tempo_posts.png'), dpi=150, bbox_inches='tight')
        plt.close()

    # --- 4. MARKDOWN ---
    md = f"""# 📊 RELATÓRIO DE INTELIGÊNCIA: {nome_cliente.upper()}

## 🚀 TRAÇÃO E CRESCIMENTO (KPIs)
Abaixo acompanhamos os indicadores de aceleração e saúde da base.

**Métricas dos Últimos 15 Dias:**
* 📝 **Total de Postagens:** {qtd_posts_15d} posts
* ❤️ **Volume de Curtidas:** {curtidas_15d:,.0f} 
* 💬 **Volume de Comentários:** {comentarios_15d:,.0f}
* 🎯 **Score Quinzenal Acumulado:** {score_total_15d:,.0f} pts
* {indicador_quinzena} **Evolução Quinzenal:** {crescimento_quinzenal:+.1f}% *(vs 15 dias anteriores)*

**Crescimento de Médio Prazo:**
* {indicador_mom} **Month-over-Month (MoM):** {mom_engajamento:+.1f}% *(vs 30 dias anteriores)*

---

## ⚡ EFICIÊNCIA E VIRALIZAÇÃO
Entendendo a qualidade da entrega do algoritmo:
* **Taxa Média de Engajamento por Alcance (Reels/Vídeos):** {media_eng_rate:.1f}%
* **Proporção Comentário/Curtida:** {media_prop_comentarios:.1f}% 

### Desempenho por Formato e Tema
![Formatos](engajamento_formatos.png)
![Temas](engajamento_temas.png)

---

## 📈 EVOLUÇÃO TEMPORAL (ÚLTIMOS POSTS)
* **Média de Curtidas no período:** {df_grafico['curtidas'].mean():,.0f}
* **Média de Comentários no período:** {df_grafico['comentarios'].mean():,.0f}

![Linha do Tempo](linha_tempo_posts.png)

### 📊 Detalhamento de Performance
| URL | Tema | Mídia | Curtidas | Comentários | Score |
|:---|:---|:---|:---|:---|:---|
{chr(10).join([f"| [{r['post_id']}]({r['url']}) | {r['tema']} | {r['tipo_midia']} | {r['curtidas']:,.0f} | {r['comentarios']:,.0f} | {r['score_1000']} |" for _, r in df_grafico.iterrows()])}

---

## 💬 MÉTRICAS QUALITATIVAS (SENTIÊNCIA E PAUTAS)
* **Net Sentiment Score (NSS):** {nss:+.1f}% *(Positivos - Negativos)*.

![Distribuição de Sentimento](sentimento_instagram.png)
![Comparativo de Pautas](comparativo_pautas.png)

🏁 *Fim do relatório de inteligência.*
"""
    with open(os.path.join(pasta_saida, 'relatorio_executivo.md'), 'w', encoding='utf-8') as f:
        f.write(md)
    print(f"✅ Relatório integrado aos dados do Apify gerado em '{pasta_saida}/'")


def main():
    for cliente in carregar_clientes():
        gerar_relatorio_cliente(cliente)

if __name__ == '__main__':
    main()