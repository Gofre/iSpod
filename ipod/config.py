# config.py
import pygame

# Spotify API
CLIENT_ID = 'c6c67240c9bd4e8b94ff8e20a6350f35'
CLIENT_SECRET = 'bbbbf867c87e4788bbf799612dea164d'
REDIRECT_URI = 'http://127.0.0.1:8888/callback/spotify'

# Visual
ANCHO = 320
ALTO = 240
FPS = 30

# Tamaño texto
TEXT_SMALL = 12
TEXT_BIG = 24

# Paleta de Colores
NEGRO = (0, 0, 0)
VERDE_SPOTIFY = (30, 215, 96)  # El verde clasico
GRIS_PIXEL = (20, 20, 20)      # Para tramas oscuras

# Rutas
CACHE_PATH = '.spotify_cache'