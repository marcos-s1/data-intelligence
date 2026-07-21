from .google_news import coletar_noticias_politico
from .instagram import coletar_comentarios_instagram

# O __all__ define exatamente o que será exportado quando alguém der um 'import *'
__all__ = [
    "coletar_noticias_politico",
    "coletar_comentarios_instagram"
]