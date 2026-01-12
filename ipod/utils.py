import pygame
import os
import urllib.request
import io
import numpy as np
from config import *

_fuente_header_cache = None

def cargar_fuente(tamano):
    try:
        ruta = os.path.join(os.path.dirname(__file__), 'Chicago.ttf')
        fuente = pygame.font.Font(ruta, tamano)

        if NEGRITA:
            fuente.set_bold(True)

        return fuente
    except FileNotFoundError:
        return pygame.font.SysFont("arial", tamano, bold=True)

def truncar_texto(texto, limite):
    """
    Corta el texto si supera el límite de caracteres
    y añade '...' al final.
    """
    if len(texto) > limite:
        # Cortamos un poco antes del límite para que quepan los puntos
        return texto[:limite-3] + "..."
    return texto

def formato_tiempo(ms):
    """Convierte milisegundos a formato MM:SS"""
    if ms is None: return "00:00"

    total_seconds = int(ms / 1000)
    
    seconds = total_seconds % 60
    minutes = (total_seconds % 3600) // 60
    hours = total_seconds // 3600
    
    if hours > 0:
        # Si hay horas, usamos formato H:MM:SS
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    else:
        # Si no, mantenemos el clásico MM:SS
        return f"{minutes:02d}:{seconds:02d}"

# --- NUEVA FUNCIÓN HEADER FLEXIBLE ---
def dibujar_header(pantalla, contenido, estado_play):
    """
    Dibuja la barra superior, iconos y el contenido central.
    'contenido' puede ser:
       - str: Texto simple (se renderiza en verde).
       - pygame.Surface: Una imagen ya renderizada (se centra automáticamente).
    """
    global _fuente_header_cache
    if _fuente_header_cache is None:
        _fuente_header_cache = cargar_fuente(TEXT_BIG)

    # 1. Fondo y Línea
    pygame.draw.rect(pantalla, NEGRO, (0, 0, ANCHO, ALTURA_HEADER))
    pygame.draw.line(pantalla, VERDE_SPOTIFY, (0, ALTURA_HEADER), (ANCHO, ALTURA_HEADER), 2)
    
    # 2. Contenido Central (Texto o Surface)
    if isinstance(contenido, str):
        # Es texto normal
        surf = _fuente_header_cache.render(contenido, ANTIALIASING, VERDE_SPOTIFY)
    else:
        # Es una Surface (imagen) personalizada (ej: búsqueda con colores)
        surf = contenido
        
    rect_titulo = surf.get_rect(center=(ANCHO//2, ALTURA_HEADER//2))
    pantalla.blit(surf, rect_titulo)
    
    # 3. Icono Batería
    pygame.draw.rect(pantalla, VERDE_SPOTIFY, (290, 8, 22, 10), 1) 
    pygame.draw.rect(pantalla, VERDE_SPOTIFY, (312, 10, 2, 6))
    pygame.draw.rect(pantalla, VERDE_SPOTIFY, (292, 10, 15, 6))
    
    # 4. Icono Play/Pause
    if estado_play is True:
        puntos = [(10, 9), (10, 19), (20, 14)]
        pygame.draw.polygon(pantalla, VERDE_SPOTIFY, puntos)
    elif estado_play is False: # Pause
        pygame.draw.rect(pantalla, VERDE_SPOTIFY, (10, 9, 3, 10))
        pygame.draw.rect(pantalla, VERDE_SPOTIFY, (16, 9, 3, 10))

def dibujar_lista_elementos(pantalla, opciones, seleccion, inicio_scroll, items_visibles, fuente, tiene_foco=True):
    """
    Dibuja una lista estándar estilo iPod.
    - pantalla: Surface destino.
    - opciones: Lista de diccionarios (con 'nombre', 'tipo'...) o strings.
    - seleccion: Índice del elemento seleccionado.
    - inicio_scroll: Índice del primer elemento visible.
    - items_visibles: Cuántos caben en pantalla.
    - fuente: La fuente a usar (grande o pequeña).
    - tiene_foco: Si False, el elemento seleccionado se pinta en gris/verde oscuro (no activo).
    """
    
    # 1. Cálculos de zona
    total_items = len(opciones)
    hay_scroll = total_items > items_visibles
    
    # Si hay scroll, restamos el ancho de la barra y el separador
    ancho_zona = ANCHO - (ANCHO_SCROLLBAR + ANCHO_SEPARADOR) if hay_scroll else ANCHO
    
    inicio_y = INICIO_VERTICAL_LISTA
    altura_linea = 28
    
    # 2. Slice de elementos visibles
    vista = opciones[inicio_scroll : inicio_scroll + items_visibles]
    
    for i, op in enumerate(vista):
        pos_y = inicio_y + (i * altura_linea)
        idx_real = i + inicio_scroll
        
        # Normalizar datos: puede ser un dict (Search) o un str (Menu simple)
        if isinstance(op, dict):
            nombre = op['nombre']
            es_header = op.get('tipo') == 'header'
        else:
            nombre = str(op)
            es_header = False
            
        # A) CASO HEADER (Títulos de sección)
        if es_header:
            texto_render = fuente.render(nombre, ANTIALIASING, COLOR_HEADER_SECCION)
            # Usamos OFFSET_TEXTO_LISTA para el ajuste vertical fino
            pantalla.blit(texto_render, (10, pos_y + OFFSET_TEXTO_LISTA))
            
        # B) CASO ÍTEM NORMAL
        else:
            # Truncamos según el ancho disponible (ajuste manual o global)
            # Si usamos fuente grande, caben menos caracteres (aprox 18). Si es pequeña, config global.
            #limite_chars = 18 if fuente.get_height() > 20 else MAX_CARACTERES_MENU
            limite_chars = MAX_CARACTERES_MENU
            txt_mostrar = truncar_texto(nombre, limite_chars)
            
            es_seleccionado = (idx_real == seleccion)
            
            if es_seleccionado and tiene_foco:
                # Fondo Verde
                pygame.draw.rect(pantalla, VERDE_SPOTIFY, (0, pos_y, ancho_zona, altura_linea))
                # Texto Negro
                r = fuente.render(txt_mostrar, ANTIALIASING, NEGRO)
                # Flechita '>'
                flecha = fuente.render(">", ANTIALIASING, NEGRO)
                pantalla.blit(flecha, (ancho_zona - 15, pos_y + OFFSET_TEXTO_LISTA))
            else:
                # Texto Verde (o Gris si no tiene foco y es el seleccionado "fantasma")
                color = VERDE_SPOTIFY
                if es_seleccionado and not tiene_foco:
                    color = (0, 100, 0) # Verde oscuro para indicar "última posición" sin foco
                elif not tiene_foco:
                    color = GRIS_TEXTO # Ítems inactivos
                
                r = fuente.render(txt_mostrar, ANTIALIASING, color)
            
            pantalla.blit(r, (10, pos_y + OFFSET_TEXTO_LISTA))
    
    # 3. Dibujar Scrollbar
    dibujar_scrollbar(pantalla, total_items, items_visibles, inicio_scroll)

# --- NUEVA FUNCIÓN SCROLLBAR COMÚN ---
def dibujar_scrollbar(pantalla, total_items, visibles, indice_inicio):
    """
    Dibuja la barra de scroll a la derecha si es necesario.
    Usa las constantes de config para posición y estilo.
    """
    if total_items <= visibles:
        return # No hace falta scroll

    # Coordenadas
    sb_x = ANCHO - ANCHO_SCROLLBAR
    sb_y = ALTURA_HEADER
    sb_h = ALTO - ALTURA_HEADER
    
    # A) Marco (Caja)
    pygame.draw.rect(pantalla, VERDE_SPOTIFY, (sb_x, sb_y, ANCHO_SCROLLBAR, sb_h), GROSOR_CAJA_SCROLL)
    
    # B) Thumb (Barra interior)
    margen_interno = GROSOR_CAJA_SCROLL + MARGEN_INTERNO_CAJA_SCROLL
    ancho_thumb = ANCHO_SCROLLBAR - (margen_interno * 2)
    altura_util = sb_h - (margen_interno * 2)

    # Evitar errores si los márgenes son tan grandes que el thumb desaparece
    if ancho_thumb < 1: ancho_thumb = 1
    if altura_util < 1: altura_util = 1
    
    # Cálculo proporcional
    thumb_height = max(10, int((visibles / total_items) * altura_util))
    max_scroll = total_items - visibles
    scroll_ratio = indice_inicio / max_scroll
    espacio_recorrido = altura_util - thumb_height
    pos_y_thumb = sb_y + margen_interno + int(scroll_ratio * espacio_recorrido)

    # Dibujar Thumb
    pygame.draw.rect(pantalla, VERDE_SPOTIFY, 
                     (sb_x + margen_interno, pos_y_thumb, ancho_thumb, thumb_height))

def procesar_caratula_fallback(imagen):
    # Metodo alternativo si falla el moderno
    img_copy = imagen.copy()
    capa_verde = pygame.Surface(img_copy.get_size())
    capa_verde.fill(VERDE_SPOTIFY)
    img_copy.blit(capa_verde, (0, 0), special_flags=pygame.BLEND_MULT)
    return img_copy

def procesar_caratula_retro(surface_original, paleta_base):
    """
    Convierte una Surface a un estilo retro de 4 tonos (2-bit dithering).
    paleta_base: Tupla (NEGRO, VERDE_SPOTIFY). Se usa para derivar los tonos intermedios.
    """
    # 1. Definir la paleta de 4 colores (Simulación LCD)
    # Nivel 0: Negro
    c0 = np.array([0, 0, 0]) 
    # Nivel 1: Verde muy oscuro (sombra)
    c1 = np.array([10, 55, 25]) 
    # Nivel 2: Verde Spotify (medio)
    c2 = np.array([30, 215, 96]) 
    # Nivel 3: Verde muy claro / Blanco verdoso (brillo)
    c3 = np.array([210, 255, 220]) 
    
    palette_colors = np.array([c0, c1, c2, c3])

    # 2. Reducir tamaño
    tamano_pixel = (64, 64) # Resolución interna pixelada
    small = pygame.transform.scale(surface_original, tamano_pixel)
    
    # 3. Obtener píxeles como array de floats para cálculos
    pixels = pygame.surfarray.pixels3d(small).astype(np.float32)
    ancho, alto, _ = pixels.shape
    
    # 4. Convertir a Escala de Grises (Luminancia)
    # Usamos la fórmula de luminancia perceptiva: 0.299R + 0.587G + 0.114B
    grayscale = pixels[:, :, 0] * 0.299 + pixels[:, :, 1] * 0.587 + pixels[:, :, 2] * 0.114
    
    # Preparamos el array de salida (3 canales RGB)
    output = np.zeros((ancho, alto, 3), dtype=np.uint8)

    # 5. Algoritmo Floyd-Steinberg ajustado a 4 niveles
    # Los niveles de gris objetivo son: 0, 85, 170, 255
    
    for y in range(alto):
        for x in range(ancho):
            old_pixel = grayscale[x, y]
            
            # Cuantizar: Encontrar el nivel más cercano (0, 1, 2, 3)
            # Normalizamos 0-255 a 0-3
            level = np.round(old_pixel / 85.0)
            level = np.clip(level, 0, 3)
            
            # Asignar el nuevo valor de gris cuantizado (para calcular el error)
            new_pixel_val = level * 85.0
            
            # Guardamos el COLOR correspondiente en la imagen final
            output[x, y] = palette_colors[int(level)]
            
            # Calcular el error (diferencia de brillo)
            error = old_pixel - new_pixel_val
            
            # Difundir el error a los vecinos (solo en el mapa de grises)
            if x + 1 < ancho:
                grayscale[x+1, y] += error * 0.5 # Derecha
            if y + 1 < alto:
                grayscale[x, y+1] += error * 0.5 # Abajo
                
            # Nota: He simplificado la difusión a solo 2 vecinos (Derecha y Abajo)
            # con factor 0.5 para que sea más rápido y el patrón sea más limpio
            # estilo "Bayer" o ordenado, que queda mejor en pixelart.

    # 6. Crear superficie final
    surface_final = pygame.surfarray.make_surface(output)
    
    return pygame.transform.scale(surface_final, (128, 128))