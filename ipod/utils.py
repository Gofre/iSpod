import pygame
import os
import urllib.request
import io
from config import *

_fuente_header_cache = None

def cargar_fuente(tamano):
    try:
        ruta = os.path.join(os.path.dirname(__file__), 'Chicago.ttf')
        return pygame.font.Font(ruta, tamano)
    except FileNotFoundError:
        return pygame.font.SysFont("arial", tamano, bold=True)

def procesar_caratula_retro(url):
    """
    Descarga una imagen desde una URL y la convierte a 
    estilo monocromatico verde (Matrix/Fosforo).
    """
    try:
        # 1. Descargar imagen usando libreria estandar (sin instalar nada extra)
        with urllib.request.urlopen(url) as response:
            image_data = response.read()
            
        # 2. Cargar en Pygame
        imagen_original = pygame.image.load(io.BytesIO(image_data))
        imagen_original = pygame.transform.scale(imagen_original, (140, 140))
        
        # 3. Convertir a Escala de Grises (Desaturar)
        # Creamos una superficie gris
        imagen_gris = pygame.Surface(imagen_original.get_size()).convert()
        # Blit con BLEND_RGBA_MULT o usamos transform si la versi�n de pygame lo permite
        # Metodo compatible: Promedio RGB o simplemente convertir
        # Un truco rapido para gris en pygame antiguo es pintar blanco y usar BLEND_RGB_MULT
        # pero vamos a usar un metodo manual robusto:
        
        arr = pygame.surfarray.pixels3d(imagen_original)
        # Promedio simple de canales para obtener luminosidad
        mean_arr = arr.mean(axis=2)
        
        # Ahora creamos la superficie tintada
        # Mapeamos: Blanco -> VERDE_SPOTIFY, Negro -> NEGRO
        surface = pygame.Surface((140, 140))
        surface.fill(VERDE_SPOTIFY) # Base verde
        
        # Usamos la imagen gris como "mascara de luminosidad" multiplicandola
        # Pero Pygame lo hace mas facil con BLEND_MULT
        
        # Manera Simplificada Pygame:
        # 1. Copia gris
        gris = pygame.transform.grayscale(imagen_original) # Solo Pygame 2.1.4+
        
        # 2. Capa Verde Solida
        capa_verde = pygame.Surface(imagen_original.get_size())
        capa_verde.fill(VERDE_SPOTIFY)
        
        # 3. Multiplicamos: (Gris * Verde) = Verde oscurecido por el gris
        gris.blit(capa_verde, (0,0), special_flags=pygame.BLEND_MULT)
        return gris

    except AttributeError:
        # Si falla transform.grayscale (pygame viejo), usamos fallback
        return procesar_caratula_fallback(imagen_original)
    except Exception as e:
        print(f"Error procesando imagen: {e}")
        return None

def procesar_caratula_fallback(imagen):
    # Metodo alternativo si falla el moderno
    img_copy = imagen.copy()
    capa_verde = pygame.Surface(img_copy.get_size())
    capa_verde.fill(VERDE_SPOTIFY)
    img_copy.blit(capa_verde, (0, 0), special_flags=pygame.BLEND_MULT)
    return img_copy

def dibujar_header(pantalla, titulo, es_play=None):
    """Dibuja la barra superior comun para todas las pantallas"""
    global _fuente_header_cache
    
    # Cargar fuente solo la primera vez (Optimizacion)
    if _fuente_header_cache is None:
        _fuente_header_cache = cargar_fuente(TEXT_BIG)

    # 1. Fondo Negro y Linea Verde
    pygame.draw.rect(pantalla, NEGRO, (0, 0, ANCHO, 28))
    pygame.draw.line(pantalla, VERDE_SPOTIFY, (0, 28), (ANCHO, 28), 2)
    
    # 2. Titulo Centrado
    texto = _fuente_header_cache.render(titulo, False, VERDE_SPOTIFY)
    rect_titulo = texto.get_rect(center=(ANCHO//2, 14))
    pantalla.blit(texto, rect_titulo)
    
    # 3. Icono de Bateria (Decorativo) en la esquina derecha
    # Cuerpo bateria
    pygame.draw.rect(pantalla, VERDE_SPOTIFY, (290, 8, 22, 10), 1) 
    # Polo positivo (puntito)
    pygame.draw.rect(pantalla, VERDE_SPOTIFY, (312, 10, 2, 6))
    # Relleno (Simulando 75%)
    pygame.draw.rect(pantalla, VERDE_SPOTIFY, (292, 10, 15, 6))
    
    # 4. Icono Play/Pause (Podriamos ponerlo a la izquierda en el futuro)
    if es_play is True:
        # Dibujar TRIANGULO (Play)
        # Puntos: (x, y), (x, y+h), (x+w, y+h/2)
        puntos = [(10, 8), (10, 18), (20, 13)]
        pygame.draw.polygon(pantalla, VERDE_SPOTIFY, puntos)
        
    elif es_play is False:
        # Dibujar DOS BARRAS (Pause)
        pygame.draw.rect(pantalla, VERDE_SPOTIFY, (10, 8, 3, 10))
        pygame.draw.rect(pantalla, VERDE_SPOTIFY, (16, 8, 3, 10))