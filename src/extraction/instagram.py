# Módulo de extração de dados do Instagram
import pandas as pd
import instaloader
from datetime import datetime, timezone
from config.settings import logger, MAX_POSTS_INSTAGRAM, DIAS_HISTORICO_PADRAO

def coletar_comentarios_instagram(perfil_alvo: str, 
                                 max_posts: int = MAX_POSTS_INSTAGRAM, 
                                 dias_limite: int = DIAS_HISTORICO_PADRAO) -> pd.DataFrame:
    """
    Raspa os comentários dos posts mais recentes de um perfil público do Instagram
    dentcia de uma janela de tempo específica.
    
    Args:
        perfil_alvo (str): Username do perfil do político (limpa o '@' automaticamente).
        max_posts (int): Limite máximo de posts a analisar para evitar bloqueios.
        dias_limite (int): Janela de dias retroativos tolerada para os posts.
        
    Returns:
        pd.DataFrame: DataFrame estruturado com os textos dos comentários.
    """
    # --------------------------------------------------------------------------
    # HIGIENIZAÇÃO DA STRING: Garante que o username vá limpo para a API do Instagram
    # --------------------------------------------------------------------------
    perfil_alvo = perfil_alvo.replace("@", "").strip()

    logger.info(f"Iniciando raspagem no Instagram para o perfil: @{perfil_alvo}")
    
    # Inicializa a engine do Instaloader
    L = instaloader.Instaloader(
        download_pictures=False, 
        download_videos=False, 
        download_geotags=False,
        download_comments=True,
        save_metadata=False
    )
    
    # Define o limite de tempo consciente do fuso horário (timezone-aware)
    data_limite = datetime.now(timezone.utc) - pd.Timedelta(days=dias_limite)
    comentarios_coletados = []
    
    try:
        # Carrega o perfil do político utilizando a string limpa
        profile = instaloader.Profile.from_username(L.context, perfil_alvo)
        posts_analisados = 0
        
        for post in profile.get_posts():
            # Critério de parada 1: Limite máximo de posts configurado atingido
            if posts_analisados >= max_posts:
                break
                
            # Como os posts vêm em ordem cronológica inversa (mais novos primeiro),
            # se o post for mais antigo que a nossa janela de dias, podemos parar o loop.
            post_date_utc = post.date_utc.replace(tzinfo=timezone.utc)
            if post_date_utc < data_limite:
                logger.info(f"Alcançado post fora da janela de {dias_limite} dias. Interrompendo coleta de posts antigos.")
                break
                
            posts_analisados += 1
            logger.info(f"Processando post [{post.shortcode}] publicado em {post.date_utc}. Coletando comentários...")
            
            # Varre os comentários públicos do post específico
            try:
                for comment in post.get_comments():
                    comentarios_coletados.append({
                        'post_id': post.shortcode,
                        'data_post': post.date_utc,
                        'autor_comentario': comment.owner.username,
                        'texto': comment.text,
                        'data_comentario': comment.created_at_utc
                    })
            except Exception as e_comment:
                logger.warning(f"Não foi possível extrair comentários do post {post.shortcode}: {str(e_comment)}")
                continue
                
        logger.info(f"Raspagem finalizada para @{perfil_alvo}. Total de posts analisados: {posts_analisados}.")
        
        if not comentarios_coletados:
            logger.warning(f"Nenhum comentário coletado para o perfil @{perfil_alvo}")
            return pd.DataFrame(columns=['post_id', 'data_post', 'autor_comentario', 'texto', 'data_comentario'])
            
        df_comentarios = pd.DataFrame(comentarios_coletados)
        logger.info(f"Sucesso! {len(df_comentarios)} comentários únicos extraídos e estruturados.")
        return df_comentarios
        
    except instaloader.exceptions.ProfileNotExistsException:
        logger.error(f"O perfil @{perfil_alvo} não existe ou foi digitado incorretamente.")
        return pd.DataFrame(columns=['post_id', 'data_post', 'autor_comentario', 'texto', 'data_comentario'])
    except Exception as e:
        logger.error(f"Erro crítico ao raspar o Instagram de @{perfil_alvo}: {str(e)}")
        return pd.DataFrame(columns=['post_id', 'data_post', 'autor_comentario', 'texto', 'data_comentario'])


if __name__ == "__main__":
    # Teste local rápido (Sanity Check)
    print("🧪 Executando teste isolado do módulo instagram.py...")
    # Testando com um perfil de grande relevância institucional para garantir que há dados públicos
    df_teste = coletar_comentarios_instagram("governodazonafranca", max_posts=1, dias_limite=5)
    print(df_teste.head())