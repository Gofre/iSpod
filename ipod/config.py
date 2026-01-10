# config.py
import pygame

# Spotify API
CLIENT_ID = ''
CLIENT_SECRET = ''
REDIRECT_URI = 'http://127.0.0.1:8888/callback/spotify'

# Rutas
CACHE_PATH = '.spotify_cache'

### INTERFAZ ###
ANCHO = 320
ALTO = 240
FPS = 30

ALTURA_HEADER = 28
ANCHO_SCROLLBAR = 14
ANCHO_SEPARADOR = 2
GROSOR_CAJA_SCROLL = 2
MARGEN_INTERNO_CAJA_SCROLL = 2

# Límites de Texto
# Ajusta este número entre 20 y 23.
MAX_CARACTERES_MENU = 20

# Texto
TEXT_SMALL = 12
TEXT_BIG = 22
OFFSET_TEXTO_LISTA = 0
ANTIALIASING = True
NEGRITA = False

# Paleta de Colores
NEGRO = (0, 0, 0)
VERDE_SPOTIFY = (30, 215, 96)  # El verde clasico
GRIS_PIXEL = (20, 20, 20)      # Para tramas oscuras