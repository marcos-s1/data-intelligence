import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from wordcloud import WordCloud, STOPWORDS
import datetime

# --- LISTA EXAUSTIVA DE STOPWORDS (CONECTIVOS E TERMOS DE RUÍDO) ---
STOPWORDS_PORTUGUES = {
    # Conectivos, preposições, artigos e pronomes
    'e', 'de', 'do', 'da', 'dos', 'das', 'em', 'no', 'na', 'nos', 'nas', 
    'por', 'pelo', 'pela', 'pelos', 'pelas', 'para', 'pra', 'pro', 'pras', 'pros',
    'com', 'como', 'que', 'que é', 'e que', 'o', 'a', 'os', 'as', 'um', 'uma', 'uns', 'umas',
    'se', 'ou', 'mas', 'mais', 'tambem', 'também', 'ele', 'ela', 'eles', 'elas', 
    'seu', 'sua', 'seus', 'suas', 'meu', 'minha', 'meus', 'minhas', 'nosso', 'nossa',
    
    # Advérbios e vícios de linguagem/redes sociais
    'ai', 'aí', 'ja', 'já', 'aqui', 'ali', 'lá', 'entao', 'então', 'assim', 'muito', 
    'muita', 'muitos', 'muitas', 'qualquer', 'algum', 'alguma', 'alguns', 'algumas',
    'isso', 'isto', 'aquilo', 'este', 'esta', 'estao', 'estão', 'era', 'eram', 'vai', 
    'vao', 'vão', 'ter', 'tem', 'temos', 'têm', 'tinha', 'tinham', 'fazer', 'faz',
    'vc', 'você', 'voces', 'vocês', 'tb', 'pq', 'porque', 'porq', 'kkk', 'kkkk', 'kkkkk',
    
    # Palavras genéricas/ônibus do contexto do perfil que poluem a nuvem
    'tarcisio', 'tarcísio', 'governo', 'governador', 'sp', 'são paulo', 'sao paulo', 
    'estado', 'povo', 'presidente', 'brasil', 'brasileiro', 'ser', 'tudo', 'dia'
}


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
            
    return [{"id": "governo_sp", "nome": "Governo do Estado de São Paulo", "instagram": "tarcisiogdf"}]


def definir_tema(legenda):
    """Categoriza o tema estratégico da postagem."""
    legenda = str(legenda).lower()
    if any(x in legenda for x in ['segurança', 'polícia', 'crime', 'pm', 'ssp', 'choque', 'copom', 'baep']): return 'Segurança Pública'
    if any(x in legenda for x in ['saúde', 'hospital', 'médico', 'vacina', 'sus', 'leito', 'remédio']): return 'Saúde & Bem-Estar'
    if any(x in legenda for x in ['escola', 'educação', 'aluno', 'professor', 'ensino', 'provão', 'faculdade']): return 'Educação & Futuro'
    if any(x in legenda for x in ['obra', 'estrada', 'infraestrutura', 'asfalto', 'transporte', 'metrô', 'rodovia', 'ponte']): return 'Infraestrutura'
    if any(x in legenda for x in ['saneamento', 'esgoto', 'água', 'sabesp', 'fundo']): return 'Saneamento & Meio Ambiente'
    if any(x in legenda for x in ['emprego', 'investimento', 'turismo', 'economia', 'sp']): return 'Desenvolvimento Econômico'
    return 'Institucional / Comunicação Geral'


def carregar_csv_flexivel(caminho):
    """Lê CSV suportando separadores de vírgula ou ponto e vírgula."""
    try:
        df = pd.read_csv(caminho, sep=';', encoding='utf-8-sig', on_bad_lines='skip')
        if len(df.columns) <= 1:
            df = pd.read_csv(caminho, sep=',', encoding='utf-8-sig', on_bad_lines='skip')
        return df
    except Exception as e:
        print(f"⚠️ Erro ao ler {caminho}: {e}")
        return pd.DataFrame()


def gerar_nuvem_palavras(texto_lista, caminho_saida, titulo, colormap='viridis'):
    """Gera e salva uma nuvem de palavras limpando conectivos e stopwords."""
    texto_completo = " ".join([str(t) for t in texto_lista if pd.notna(t) and len(str(t).strip()) > 2])
    if len(texto_completo.strip()) > 10:
        stopwords_finais = STOPWORDS.union(STOPWORDS_PORTUGUES)
        wc = WordCloud(
            width=800, height=400, 
            background_color='white', 
            colormap=colormap, 
            max_words=80,
            stopwords=stopwords_finais,
            collocations=False
        ).generate(texto_completo)
        
        plt.figure(figsize=(10, 5))
        plt.imshow(wc, interpolation='bilinear')
        plt.axis('off')
        plt.title(titulo, fontsize=14, fontweight='bold', pad=15)
        plt.savefig(caminho_saida, dpi=150, bbox_inches='tight')
        plt.close()


def gerar_relatorio_cliente(cliente):
    cliente_id = cliente.get("id")
    nome_cliente = cliente.get("nome")
    pasta_data_source = os.path.join('reports', cliente_id, 'data_source') if os.path.exists(os.path.join('reports', cliente_id)) else '.'
    pasta_saida = os.path.join('reports', cliente_id) if os.path.exists(os.path.join('reports', cliente_id)) else '.'
    
    # --- 1. LEITURA E TRATAMENTO DA BASE COM BLINDAGEM COMPLETA ---
    csv_posts, csv_insta, csv_imprensa, csv_populacao, csv_noticias = None, None, None, None, None
    
    procurar_pastas = [pasta_data_source, '.']
    for pasta in procurar_pastas:
        if not os.path.exists(pasta): continue
        for f in os.listdir(pasta):
            if 'posts_brutos' in f and not csv_posts: csv_posts = os.path.join(pasta, f)
            elif 'instagram_bruto' in f and not csv_insta: csv_insta = os.path.join(pasta, f)
            elif 'pautas_imprensa' in f and not csv_imprensa: csv_imprensa = os.path.join(pasta, f)
            elif 'pautas_populacao' in f and not csv_populacao: csv_populacao = os.path.join(pasta, f)
            elif 'noticias_brutas' in f and not csv_noticias: csv_noticias = os.path.join(pasta, f)

    if not csv_posts:
        print(f"⚠️ Arquivo de posts brutos não encontrado para {nome_cliente}.")
        return

    df_posts_raw = carregar_csv_flexivel(csv_posts)
    df_sentimento = carregar_csv_flexivel(csv_insta) if csv_insta else pd.DataFrame()
    df_pautas_imprensa = carregar_csv_flexivel(csv_imprensa) if csv_imprensa else pd.DataFrame(columns=['termo', 'frequencia'])
    df_pautas_populacao = carregar_csv_flexivel(csv_populacao) if csv_populacao else pd.DataFrame(columns=['termo', 'frequencia'])
    df_noticias = carregar_csv_flexivel(csv_noticias) if csv_noticias else pd.DataFrame()

    if df_posts_raw.empty:
        print(f"⚠️ Base de posts vazia para {nome_cliente}.")
        return

    # Estruturação e Mapeamento de Colunas
    df_posts = pd.DataFrame()
    df_posts['post_id'] = df_posts_raw.get('shortcode', df_posts_raw.get('post_id', ''))
    df_posts['url'] = df_posts_raw.get('url', '')
    
    col_data = 'timestamp_publicacao' if 'timestamp_publicacao' in df_posts_raw.columns else 'timestamp'
    df_posts['data'] = pd.to_datetime(df_posts_raw.get(col_data, pd.Series())).dt.tz_localize(None)
    
    df_posts['curtidas'] = pd.to_numeric(df_posts_raw.get('total_curtidas', df_posts_raw.get('curtidas', 0)), errors='coerce').fillna(0)
    df_posts['comentarios'] = pd.to_numeric(df_posts_raw.get('total_comentarios', df_posts_raw.get('comentarios', 0)), errors='coerce').fillna(0)
    df_posts['views'] = pd.to_numeric(df_posts_raw.get('visualizacoes_video', df_posts_raw.get('views', 0)), errors='coerce').fillna(0)
    df_posts['duracao_video'] = pd.to_numeric(df_posts_raw.get('duracao_video_segundos', df_posts_raw.get('videoDuration', 0)), errors='coerce').fillna(0)
    df_posts['tipo_midia'] = df_posts_raw.get('tipo_midia', df_posts_raw.get('type', 'Video')).fillna('Video')
    
    col_legenda = 'legenda' if 'legenda' in df_posts_raw.columns else 'caption'
    df_posts['legenda'] = df_posts_raw.get(col_legenda, '').fillna('')
    df_posts['tema'] = df_posts['legenda'].apply(definir_tema)
    
    df_posts = df_posts.sort_values('data').reset_index(drop=True)
    df_posts['dia_semana'] = df_posts['data'].dt.day_name()
    df_posts['hora'] = df_posts['data'].dt.hour
    
    mapa_dias = {
        'Monday': 'Segunda', 'Tuesday': 'Terça', 'Wednesday': 'Quarta',
        'Thursday': 'Quinta', 'Friday': 'Sexta', 'Saturday': 'Sábado', 'Sunday': 'Domingo'
    }
    df_posts['dia_semana_pt'] = df_posts['dia_semana'].map(mapa_dias)

    # METADADOS TEMPORAIS DA AUDITORIA
    data_inicio = df_posts['data'].min()
    data_fim = df_posts['data'].max()
    dias_totais = (data_fim - data_inicio).days if pd.notna(data_inicio) and pd.notna(data_fim) else 30
    dias_totais = max(dias_totais, 1)

    # CÁLCULOS DE SCORES E INDICADORES AVANÇADOS
    df_posts['raw_score'] = df_posts['curtidas'] + (df_posts['comentarios'] * 10)
    max_raw = df_posts['raw_score'].max() if not df_posts['raw_score'].empty else 0
    df_posts['score_1000'] = (df_posts['raw_score'] / max_raw * 1000).astype(int) if max_raw > 0 else 0
    
    df_posts['eng_rate'] = np.where(df_posts['views'] > 0, ((df_posts['curtidas'] + df_posts['comentarios']) / df_posts['views']) * 100, 0)
    df_posts['virality_index'] = np.where(df_posts['views'] > 0, (df_posts['curtidas'] / df_posts['views']) * 100, 0)
    df_posts['prop_comentarios'] = np.where(df_posts['curtidas'] > 0, (df_posts['comentarios'] / df_posts['curtidas']) * 100, 0)

    # ACUMULADOS E KPIS GERAIS
    curtidas_totais = df_posts['curtidas'].sum()
    comentarios_totais = df_posts['comentarios'].sum()
    views_totais = df_posts['views'].sum()
    score_acumulado_total = df_posts['raw_score'].sum()
    frequencia_postagem_diaria = len(df_posts) / dias_totais

    qtd_top_20 = max(int(len(df_posts) * 0.2), 1)
    score_top_20 = df_posts.sort_values('raw_score', ascending=False).head(qtd_top_20)['raw_score'].sum()
    concentracao_pareto = (score_top_20 / score_acumulado_total * 100) if score_acumulado_total > 0 else 0

    # KPIS TEMPORAIS (15d e 30d / MoM)
    data_atual = df_posts['data'].max() if not df_posts.empty else datetime.datetime.now()
    df_15d_atuais = df_posts[df_posts['data'] > (data_atual - pd.Timedelta(days=15))]
    df_15d_anteriores = df_posts[(df_posts['data'] <= (data_atual - pd.Timedelta(days=15))) & (df_posts['data'] > (data_atual - pd.Timedelta(days=30)))]
    df_30d_atuais = df_posts[df_posts['data'] > (data_atual - pd.Timedelta(days=30))]
    df_30d_anteriores = df_posts[(df_posts['data'] <= (data_atual - pd.Timedelta(days=30))) & (df_posts['data'] > (data_atual - pd.Timedelta(days=60)))]
    
    qtd_posts_15d = len(df_15d_atuais)
    curtidas_15d = df_15d_atuais['curtidas'].sum()
    comentarios_15d = df_15d_atuais['comentarios'].sum()
    views_15d = df_15d_atuais['views'].sum()
    score_total_15d = df_15d_atuais['raw_score'].sum()
    score_total_15d_anterior = df_15d_anteriores['raw_score'].sum()
    
    crescimento_quinzenal = ((score_total_15d / score_total_15d_anterior) - 1) * 100 if score_total_15d_anterior > 0 else 0
    indicador_quinzena = "Crescimento Acelerado" if crescimento_quinzenal > 5 else "Queda" if crescimento_quinzenal < -5 else "Estavel"
    
    score_mes_atual = df_30d_atuais['raw_score'].sum()
    score_mes_anterior = df_30d_anteriores['raw_score'].sum()
    mom_engajamento = ((score_mes_atual / score_mes_anterior) - 1) * 100 if score_mes_anterior > 0 else 0
    indicador_mom = "Crescimento" if mom_engajamento > 5 else "Retracao" if mom_engajamento < -5 else "Estavel"

    # NET SENTIMENT SCORE (NSS) E AUDITORIA DE USUÁRIOS
    col_sent = 'sentimento' if 'sentimento' in df_sentimento.columns else 'sentiment'
    col_texto_coment = 'texto' if 'texto' in df_sentimento.columns else 'text'
    col_autor_coment = 'autor_comentario' if 'autor_comentario' in df_sentimento.columns else 'ownerUsername'
    
    top_autores_df = pd.DataFrame()
    if not df_sentimento.empty and col_sent in df_sentimento.columns:
        total_sent = len(df_sentimento)
        positivos = len(df_sentimento[df_sentimento[col_sent].astype(str).str.upper() == 'POSITIVO'])
        negativos = len(df_sentimento[df_sentimento[col_sent].astype(str).str.upper() == 'NEGATIVO'])
        neutros = len(df_sentimento[df_sentimento[col_sent].astype(str).str.upper() == 'NEUTRO'])
        nss = ((positivos - negativos) / total_sent) * 100 if total_sent > 0 else 0

        score_controversia = (negativos / (positivos + 1))

        if col_autor_coment in df_sentimento.columns:
            top_autores_df = df_sentimento[col_autor_coment].value_counts().head(5).reset_index()
            top_autores_df.columns = ['Usuario', 'Comentarios']
    else:
        total_sent, positivos, negativos, neutros, nss, score_controversia = 0, 0, 0, 0, 0, 0

    media_eng_rate = df_posts[df_posts['eng_rate'] > 0]['eng_rate'].mean() if 'eng_rate' in df_posts.columns else 0
    media_eng_rate = media_eng_rate if pd.notna(media_eng_rate) else 0

    media_virality_index = df_posts[df_posts['virality_index'] > 0]['virality_index'].mean() if 'virality_index' in df_posts.columns else 0
    media_virality_index = media_virality_index if pd.notna(media_virality_index) else 0

    prop_coment_media = df_posts['prop_comentarios'].mean() if 'prop_comentarios' in df_posts.columns else 0
    prop_coment_media = prop_coment_media if pd.notna(prop_coment_media) else 0

    # --- 2. NUVENS DE PALAVRAS TRIPLAS (INCLUINDO A GERAL DA POPULAÇÃO) ---
    if not df_sentimento.empty and col_texto_coment in df_sentimento.columns:
        gerar_nuvem_palavras(
            df_sentimento[col_texto_coment].tolist(),
            os.path.join(pasta_saida, 'nuvem_palavras_geral.png'),
            'Nuvem Geral: Termos Mais Frequentes da Populacao', colormap='Blues_r'
        )
        df_pos = df_sentimento[df_sentimento[col_sent].astype(str).str.upper() == 'POSITIVO']
        gerar_nuvem_palavras(
            df_pos[col_texto_coment].tolist(),
            os.path.join(pasta_saida, 'nuvem_palavras_positiva.png'),
            'Nuvem Positiva: Pautas de Maior Apoio e Elogios', colormap='Greens_r'
        )
        df_neg = df_sentimento[df_sentimento[col_sent].astype(str).str.upper() == 'NEGATIVO']
        gerar_nuvem_palavras(
            df_neg[col_texto_coment].tolist(),
            os.path.join(pasta_saida, 'nuvem_palavras_negativa.png'),
            'Nuvem Negativa: Dores, Reclamacoes e Cobrancas', colormap='Reds_r'
        )

    # --- 3. GERAÇÃO DOS GRÁFICOS AVANÇADOS ---
    sns.set_theme(style="whitegrid")
    
    # A. Heatmap Horários
    dias_ordem = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo']
    pivot_heatmap = df_posts.pivot_table(index='dia_semana_pt', columns='hora', values='score_1000', aggfunc='mean').reindex(dias_ordem).fillna(0)
    
    plt.figure(figsize=(12, 6))
    sns.heatmap(pivot_heatmap, cmap="YlGnBu", annot=True, fmt=".0f", linewidths=.5, cbar_kws={'label': 'Score Médio de Engajamento'})
    plt.title('Mapa de Calor: Janela Otima de Publicacao (Score de Engajamento)', fontsize=14, fontweight='bold', pad=15)
    plt.xlabel('Hora do Dia (h)'); plt.ylabel('')
    plt.savefig(os.path.join(pasta_saida, 'heatmap_melhor_horario.png'), dpi=150, bbox_inches='tight')
    plt.close()

    melhor_dia, melhor_hora = "N/A", "N/A"
    if not pivot_heatmap.empty and pivot_heatmap.max().max() > 0:
        max_idx = pivot_heatmap.stack().idxmax()
        melhor_dia, melhor_hora = max_idx[0], f"{max_idx[1]}:00h"

    # B. MATRIZ BCG DE PAUTAS POLÍTICAS (AJUSTADO E ALINHADO)
    df_bcg = df_posts.groupby('tema').agg(
        frequencia=('post_id', 'count'),
        score_medio=('score_1000', 'mean')
    ).reset_index()

    if not df_bcg.empty:
        plt.figure(figsize=(10, 6))
        sns.scatterplot(data=df_bcg, x='frequencia', y='score_medio', hue='tema', s=350, palette='Set2')
        mediana_freq = df_bcg['frequencia'].median()
        mediana_score = df_bcg['score_medio'].median()
        
        plt.axvline(mediana_freq, color='gray', linestyle='--', alpha=0.6)
        plt.axhline(mediana_score, color='gray', linestyle='--', alpha=0.6)
        
        # Define limites limpos nos eixos para acomodar os textos confortavelmente
        plt.xlim(1, 9)
        plt.ylim(50, 420)
        
        # Posicionamento perfeitamente alinhado dentro da área útil do gráfico
        plt.text(mediana_freq - 0.7, 395, 'OPORTUNIDADES\n(Baixa Freq x Alto Score)', fontsize=9, fontweight='bold', color='blue', ha='center', va='center')
        plt.text(mediana_freq + 2.0, 395, 'PAUTAS DE OURO\n(Alta Freq x Alto Score)', fontsize=9, fontweight='bold', color='green', ha='center', va='center')
        
        for _, r in df_bcg.iterrows():
            plt.text(r['frequencia'] + 0.1, r['score_medio'] + 5, r['tema'], fontsize=9, fontweight='bold')
            
        plt.title('Matriz BCG de Pautas: Frequencia vs Resposta do Eleitorado', fontsize=14, fontweight='bold', pad=15)
        plt.xlabel('Frequencia de Postagens (Volume)'); plt.ylabel('Score Médio de Resposta (0-1000)')
        plt.savefig(os.path.join(pasta_saida, 'matriz_bcg_pautas.png'), dpi=150, bbox_inches='tight')
        plt.close()

    # C. RETENÇÃO x DURAÇÃO DO VÍDEO
    df_videos = df_posts[df_posts['duracao_video'] > 0].copy()
    if not df_videos.empty:
        plt.figure(figsize=(9, 5))
        sns.regplot(data=df_videos, x='duracao_video', y='virality_index', color='#8e44ad', scatter_kws={'s': 90})
        plt.title('Matriz de Retencao Visual: Duracao do Video (s) vs Virality Index (%)', fontsize=13, fontweight='bold', pad=15)
        plt.xlabel('Duracao do Video em Segundos'); plt.ylabel('Virality Index (Likes / Views %)')
        plt.savefig(os.path.join(pasta_saida, 'retencao_vs_duracao.png'), dpi=150, bbox_inches='tight')
        plt.close()

    # D. CURVA DE VIDA DA NOTÍCIA x RESSONÂNCIA (LAG CORRIGIDO)
    if not df_noticias.empty:
        col_data_noticia = 'data_publicacao' if 'data_publicacao' in df_noticias.columns else 'data'
        if col_data_noticia in df_noticias.columns:
            df_noticias['dt_noticia'] = pd.to_datetime(df_noticias[col_data_noticia], errors='coerce').dt.date
            df_noticias_dia = df_noticias.groupby('dt_noticia').size().reset_index(name='qtd_noticias')
            
            df_posts['dt_post'] = pd.to_datetime(df_posts['data'], errors='coerce').dt.date
            df_posts_dia = df_posts.groupby('dt_post')['comentarios'].sum().reset_index(name='comentarios_redes')
            
            df_lag = pd.merge(df_noticias_dia, df_posts_dia, left_on='dt_noticia', right_on='dt_post', how='outer').fillna(0)
            df_lag['data_unificada'] = pd.to_datetime(df_lag['dt_noticia'].combine_first(df_lag['dt_post']))
            df_lag = df_lag.sort_values('data_unificada')
            
            if not df_lag.empty:
                fig, ax1 = plt.subplots(figsize=(11, 5))
                ax1.plot(df_lag['data_unificada'], df_lag['qtd_noticias'], color='#2980b9', linewidth=2, marker='o', label='Matérias na Imprensa')
                ax1.set_ylabel('Notícias Mídia', color='#2980b9', fontweight='bold')
                ax2 = ax1.twinx()
                ax2.plot(df_lag['data_unificada'], df_lag['comentarios_redes'], color='#e67e22', linewidth=2, linestyle='--', marker='s', label='Comentários Redes')
                ax2.set_ylabel('Comentários Instagram', color='#e67e22', fontweight='bold')
                plt.title('Analise de Lag & Ressonancia: Imprensa vs Reacao do Publico', fontsize=13, fontweight='bold', pad=15)
                fig.tight_layout()
                plt.savefig(os.path.join(pasta_saida, 'lag_ressonancia.png'), dpi=150, bbox_inches='tight')
                plt.close()

    # E. Pizza Sentimento
    if not df_sentimento.empty and col_sent in df_sentimento.columns:
        plt.figure(figsize=(7, 5))
        cores_sentimento = {'POSITIVO': '#2ecc71', 'NEUTRO': '#f1c40f', 'NEGATIVO': '#e74c3c'}
        contagem_sent = df_sentimento[col_sent].astype(str).str.upper().value_counts()
        cores_finais = [cores_sentimento.get(x, '#95a5a6') for x in contagem_sent.index]
        plt.pie(contagem_sent, labels=contagem_sent.index, autopct='%1.1f%%', colors=cores_finais, startangle=90, wedgeprops={'edgecolor': 'white', 'linewidth': 2})
        plt.title('Auditoria de Percepcao e Sentimento Popular', fontsize=13, fontweight='bold')
        plt.savefig(os.path.join(pasta_saida, 'sentimento_instagram.png'), dpi=150, bbox_inches='tight')
        plt.close()

    # F. Formatos
    plt.figure(figsize=(8, 4))
    eng_por_formato = df_posts.groupby('tipo_midia')['score_1000'].mean().sort_values(ascending=False).reset_index()
    if not eng_por_formato.empty:
        sns.barplot(x='tipo_midia', y='score_1000', data=eng_por_formato, palette='magma')
        plt.title('Performance Relativa por Tipo de Formato', fontsize=13, fontweight='bold')
        plt.xlabel(''); plt.ylabel('Score Médio')
        plt.savefig(os.path.join(pasta_saida, 'engajamento_formatos.png'), dpi=150, bbox_inches='tight')
        plt.close()

    # G. Comparativo Pautas
    if not df_pautas_imprensa.empty and not df_pautas_populacao.empty:
        fig, axes = plt.subplots(1, 2, figsize=(15, 6))
        sns.barplot(x='frequencia', y='termo', data=df_pautas_imprensa.head(10), ax=axes[0], palette='Blues_r')
        axes[0].set_title('Agenda da Imprensa (Google News)', fontweight='bold')
        sns.barplot(x='frequencia', y='termo', data=df_pautas_populacao.head(10), ax=axes[1], palette='Oranges_r')
        axes[1].set_title('Demandas da População (Instagram)', fontweight='bold')
        plt.suptitle('Desalinhamento de Narrativas: Mídia Oficial vs. Voz do Cidadão', fontsize=16, fontweight='bold')
        plt.tight_layout()
        plt.savefig(os.path.join(pasta_saida, 'comparativo_pautas.png'), dpi=150, bbox_inches='tight')
        plt.close()
    
    # H. Linha do Tempo
    df_grafico = df_posts.tail(10).copy()
    if not df_grafico.empty:
        fig, ax1 = plt.subplots(figsize=(12, 6))
        x = range(len(df_grafico))
        ax1.plot(x, df_grafico['comentarios'], marker='s', color='#e67e22', linewidth=2.5, label='Comentários', zorder=3)
        ax1.set_ylabel('Comentários (Engajamento Ativo)', color='#e67e22', fontweight='bold')
        ax2 = ax1.twinx()
        ax2.bar(x, df_grafico['curtidas'], color='#3498db', alpha=0.3, label='Curtidas', width=0.6, zorder=1)
        ax2.set_ylabel('Curtidas (Aprovação Passiva)', color='#3498db', fontweight='bold')
        ax1.set_xticks(x); ax1.set_xticklabels(df_grafico['data'].dt.strftime('%d/%m'))
        ax1.grid(False); ax2.grid(False)
        plt.title('Evolução das Interações nos Últimos 10 Posts', fontsize=14, fontweight='bold')
        fig.tight_layout()
        plt.savefig(os.path.join(pasta_saida, 'linha_tempo_posts.png'), dpi=150, bbox_inches='tight')
        plt.close()

    top_posts = df_posts.sort_values('score_1000', ascending=False).head(3)
    bottom_posts = df_posts.sort_values('score_1000', ascending=True).head(3)

    # --- 4. ESCRITA DO MARKDOWN ENTERPRISE C-LEVEL ---
    md = f"""# RELATÓRIO EXECUTIVO DE INTELIGÊNCIA DIGITAL & SENTIMENTO PÚBLICO
**CLIENTE:** {nome_cliente.upper()} | **MÓDULO:** AUDITORIA DE REDES SOCIAIS & IMPRENSA

---

## METADADOS DA AUDITORIA TEMPORAL
* **Período Total do Estudo:** {data_inicio.strftime('%d/%m/%Y')} a {data_fim.strftime('%d/%m/%Y')} ({dias_totais} dias auditados)
* **Ponto Focal de Referência (Data de Corte):** {data_atual.strftime('%d/%m/%Y %H:%M')}
* **Amostragem Mapeada:** {len(df_posts)} publicações oficiais do feed/Reels
* **Volume Absoluto de Audiência:** {views_totais:,.0f} visualizações auditadas
* **Volume de Interações Diretas:** {curtidas_totais + comentarios_totais:,.0f} ações registradas
* **Total de Comentários Auditados via IA:** {total_sent} comentários processados pelo modelo BERT

---

## GUIA METODOLÓGICO: COMO LER ESTES INDICADORES

Esta auditoria utiliza métricas avançadas de Data Science para transformar dados brutos de redes sociais em decisões estratégicas de comunicação pública:

1. **Score Ponderado de Engajamento (0 a 1000):** Indicador central do estudo. Aplica peso **10x superior** ao comentário devido ao esforço ativo do usuário:
   $$\\text{{Raw Score}} = \\text{{Curtidas}} + (\\text{{Comentários}} \\times 10)$$
2. **Virality Index (Taxa de Retenção do Reels):** Calculado por $(\\text{{Curtidas}} / \\text{{Visualizações}}) \\times 100$. Indica a capacidade do vídeo de converter espectadores em apoiadores.
3. **Net Sentiment Score (NSS):** Saldo líquido da reputação digital:
   $$\\text{{NSS}} = \\frac{{\\text{{Comentários Positivos}} - \\text{{Comentários Negativos}}}}{{\\text{{Total de Comentários Auditados}}}} \\times 100$$
4. **Controversy Score (Índice de Controvérsia):** Mede o grau de atrito de uma pauta. Calculado por $\\frac{{\\text{{Críticas}}}}{{\\text{{Elogios}} + 1}}$. Valores acima de **1.0** sinalizam pautas que dividem a opinião pública.

---

## 1. PANORAMA EXECUTIVO & COMPARAÇÃO TEMPORAL (KPIS CONSOLIDADOS)

### Visão Geral do Período Histórico Acumulado ({dias_totais} dias auditados)
* **Volume Total de Publicações:** **{len(df_posts)} posts**
* **Frequência Média de Postagem:** **{frequencia_postagem_diaria:.1f} posts/dia**
* **Volume Total de Curtidas:** **{curtidas_totais:,.0f}**
* **Volume Total de Comentários:** **{comentarios_totais:,.0f}**
* **Alcance Bruto em Vídeo:** **{views_totais:,.0f} reproduções**
* **Score de Engajamento Acumulado Total:** **{score_acumulado_total:,.0f} pts**
* **Concentração de Impacto (Pareto 80/20):** **{concentracao_pareto:.1f}%** *(engajamento vindo dos top 20% melhores posts)*

### Comparativo da Última Quinzena (Últimos 15 Dias)
* **Total de Publicações (15d):** **{qtd_posts_15d} posts**
* **Volume de Curtidas (15d):** **{curtidas_15d:,.0f}**
* **Volume de Comentários (15d):** **{comentarios_15d:,.0f}**
* **Visualizações de Vídeo (15d):** **{views_15d:,.0f}**
* **Score Quinzenal Acumulado:** **{score_total_15d:,.0f} pts** *(vs {score_total_15d_anterior:,.0f} pts da quinzena anterior)*
* **Crescimento Quinzenal:** **{crescimento_quinzenal:+.1f}%** *(aceleração nos últimos 15 dias)* [{indicador_quinzena}]

### Crescimento de Médio Prazo (Month-over-Month - 30d)
* **Score Mensal Atual (Últimos 30d):** **{score_mes_atual:,.0f} pts**
* **Score Mensal Anterior (30d Anteriores):** **{score_mes_anterior:,.0f} pts**
* **Growth Month-over-Month (MoM):** **{mom_engajamento:+.1f}%** *(variação percentual de crescimento mensal)* [{indicador_mom}]

---

## 2. MATRIZ BCG DE PAUTAS POLÍTICAS & RETENÇÃO DE VÍDEO

Análise combinada de volume de postagens vs. aprovação popular do tema:

![Matriz BCG de Pautas](matriz_bcg_pautas.png)

* **Taxa Média de Engajamento por Alcance:** **{media_eng_rate:.1f}%**
* **Virality Index Médio (Likes/Views):** **{media_virality_index:.1f}%**
* **Índice de Provocação de Debate (Comentários/Curtidas):** **{prop_coment_media:.1f}%**

![Retenção x Duração](retencao_vs_duracao.png)
![Formatos de Mídia](engajamento_formatos.png)

---

## 3. ANÁLISE TEMPORAL E JANELA ÓTIMA DE PUBLICAÇÃO

* **Dia de Ouro:** **{melhor_dia}** *(dia com maior taxa de resposta do algoritmo)*
* **Horário de Ouro:** **{melhor_hora}** *(janela de pico de engajamento popular)*

![Mapa de Calor Horários](heatmap_melhor_horario.png)

---

## 4. ANÁLISE QUALITATIVA DE SENTIMENTO, POLARIZAÇÃO & AUDIÊNCIA (IA / BERT)

* **Net Sentiment Score (NSS):** **{nss:+.1f}%**
* **Controversy Score (Taxa de Polarização):** **{score_controversia:.2f}** *(Valores > 1.0 indicam pautas sensíveis/atrito)*
* **Sentimento Positivo:** {positivos} comentários ({positivos/total_sent*100 if total_sent>0 else 0:.1f}% do total)
* **Sentimento Neutro:** {neutros} comentários ({neutros/total_sent*100 if total_sent>0 else 0:.1f}% do total)
* **Sentimento Negativo:** {negativos} comentários ({negativos/total_sent*100 if total_sent>0 else 0:.1f}% do total)

![Gráfico de Pizza Sentimento](sentimento_instagram.png)

### Mapeamento de Usuários Super-Engajados (Militância / Base Ativa)
| Usuário | Qtd. Comentários Deixados no Período |
|:---|:---|
{chr(10).join([f"| @{r['Usuario']} | **{r['Comentarios']} comentários** |" for _, r in top_autores_df.iterrows()]) if not top_autores_df.empty else "| N/A | Nenhum perfil recorrente isolado |"}

### ANÁLISE SEMÂNTICA EM TRÊS NÍVEIS (NUVENS DE PALAVRAS)

#### 1. Nuvem Geral da População
Visão holística de todos os termos com maior repetição nos comentários:
![Nuvem Geral](nuvem_palavras_geral.png)

#### 2. Nuvem Positiva (Pontos Fortes & Validação)
Termos associados a elogios, apoio político e reconhecimento das ações de governo:
![Nuvem Positiva](nuvem_palavras_positiva.png)

#### 3. Nuvem Negativa (Matriz de Riscos & Críticas)
Isolamento das dores da população, cobranças por serviços públicos e pautas sensíveis:
![Nuvem Negativa](nuvem_palavras_negativa.png)

---

## 5. ANÁLISE DE LAG & RESSONÂNCIA (IMPRENSA vs. POPULAÇÃO)

Análise do tempo de resposta (*Lag*) entre a cobertura de notícias na imprensa e a reação do eleitorado nas redes sociais:

![Lag e Ressonância](lag_ressonancia.png)
![Comparativo Pautas](comparativo_pautas.png)

---

## 6. AUDITORIA DE CONTEÚDO: DESTAQUES x ALERTAS

### TOP 3 PUBLICAÇÕES DE MAIOR IMPACTO (BEST PRACTICES)
| Post Shortcode | Pauta Temática | Formato | Curtidas | Comentários | Score (0-1000) |
|:---|:---|:---|:---|:---|:---|
{chr(10).join([f"| [{r['post_id']}]({r['url']}) | {r['tema']} | {r['tipo_midia']} | {r['curtidas']:,.0f} | {r['comentarios']:,.0f} | **{r['score_1000']}** |" for _, r in top_posts.iterrows()])}

### BOTTOM 3 PUBLICAÇÕES DE MENOR RESSONÂNCIA (PONTOS DE ATENÇÃO)
| Post Shortcode | Pauta Temática | Formato | Curtidas | Comentários | Score (0-1000) |
|:---|:---|:---|:---|:---|:---|
{chr(10).join([f"| [{r['post_id']}]({r['url']}) | {r['tema']} | {r['tipo_midia']} | {r['curtidas']:,.0f} | {r['comentarios']:,.0f} | **{r['score_1000']}** |" for _, r in bottom_posts.iterrows()])}

---

## 7. HISTÓRICO RECENTE DE INTERAÇÕES

![Linha do Tempo](linha_tempo_posts.png)

---

## 8. DIRETRIZES E RECOMENDAÇÕES ESTRATÉGICAS

1. **Aproveitamento da Janela Ouro:** Concentrar as postagens de maior relevância política na **{melhor_dia} às {melhor_hora}**.
2. **Atuação Preventiva na Matriz de Riscos:** Monitorar ativamente os termos em destaque na **Nuvem Negativa** e o **Controversy Score ({score_controversia:.2f})**.
3. **Escalonamento via Matriz BCG:** Manter o foco de investimento nas pautas posicionadas como **Pautas de Ouro** (alta resposta com alto apelo comunitário).

---
*Relatório de Inteligência Digital e Sentimento Popular gerado automaticamente via pipeline Python de alta precisão.*
"""
    with open(os.path.join(pasta_saida, 'relatorio_executivo.md'), 'w', encoding='utf-8') as f:
        f.write(md)
    print(f"✅ Relatório executivo completo gerado com sucesso em '{pasta_saida}/relatorio_executivo.md'")


def main():
    for cliente in carregar_clientes():
        gerar_relatorio_cliente(cliente)

if __name__ == '__main__':
    main()