import pygame
import spotipy
from spotipy.oauth2 import SpotifyOAuth

# Importamos nuestros modulos propios
from config import *
from menu_principal import MenuPantalla
from now_playing import PantallaNowPlaying

# --- INICIALIZAR API ---
def iniciar_spotify():
    scope = "user-library-read user-read-playback-state user-modify-playback-state user-follow-read"
    return spotipy.Spotify(auth_manager=SpotifyOAuth(
        client_id=CLIENT_ID, 
        client_secret=CLIENT_SECRET, 
        redirect_uri=REDIRECT_URI,
        scope=scope, 
        open_browser=False, 
        cache_path=CACHE_PATH
    ))

# --- CONFIGURACION INICIAL ---
pygame.init()
pygame.mouse.set_visible(False)
pantalla = pygame.display.set_mode((ANCHO, ALTO))
pygame.display.set_caption("WafflePod")

# Conectamos
print("Conectando a Spotify...")
sp = iniciar_spotify()

# --- ESTADO GLOBAL ---
global_is_playing = False # Estado inicial
last_global_check = 0
GLOBAL_CHECK_INTERVAL = 3000 # Comprobar estado cada 3 seg (menos agresivo)

# --- DEFINICION DE PANTALLAS ---
# Creamos las instancias de las pantallas
now_playing = PantallaNowPlaying(sp)
menu_artistas = MenuPantalla("Artists", [], sp, 'artistas')
menu_playlists = MenuPantalla("Playlists", [], sp, 'playlists')

# Definimos el menu Home
home_opts = [
    {'nombre': 'Now Playing', 'destino': now_playing},
    {'nombre': 'Artists', 'destino': menu_artistas},
    {'nombre': 'Playlists', 'destino': menu_playlists},
    {'nombre': 'Settings', 'destino': None} # Futuro: Settings
]
home = MenuPantalla("iPod", home_opts)

# Pila de navegacion (Stack)
stack = [home]

# --- BUCLE PRINCIPAL ---
clock = pygame.time.Clock()
running = True

while running:
    # 1. ACTUALIZAR ESTADO GLOBAL (PLAY/PAUSE)
    tiempo_actual = pygame.time.get_ticks()
    if tiempo_actual - last_global_check > GLOBAL_CHECK_INTERVAL:
        try:
            # Hacemos una llamada ligera solo para ver si suena
            pb = sp.current_playback()
            if pb:
                global_is_playing = pb['is_playing']
            else:
                global_is_playing = False
        except:
            pass # Si falla (internet, etc), mantenemos el último estado conocido
        last_global_check = tiempo_actual

    # 2. Gestion de Eventos
    for e in pygame.event.get():
        if e.type == pygame.QUIT: 
            running = False
        
        if e.type == pygame.KEYDOWN:
            # TECLA ESCAPE (Atras / Menu)
            if e.key == pygame.K_ESCAPE:
                if len(stack) > 1: stack.pop()
            
            # TECLAS DE NAVEGACION
            curr = stack[-1] # Pantalla actual
            
            # Solo si es un MENU (tiene lista) podemos subir/bajar
            if isinstance(curr, MenuPantalla):
                if e.key == pygame.K_UP: curr.mover_arriba()
                if e.key == pygame.K_DOWN: curr.mover_abajo()
                
                # TECLA ENTER (Seleccionar)
                if e.key == pygame.K_RETURN:
                    sel = curr.obtener_seleccion()
                    
                    # Caso A: Es un submenu (tiene 'destino')
                    if isinstance(sel, dict) and sel.get('destino'):
                        stack.append(sel['destino'])
                        
                    # Caso B: Es un item final (ej. un artista) -> Ir a Now Playing
                    # (Mas adelante aqui pondremos "Reproducir Artista")
                    else:
                        stack.append(now_playing)
                        
            # Si estamos en Now Playing, Enter o Clickwheel central podria pausar (futuro)

    # 3. Dibujar
    stack[-1].dibujar(pantalla, global_is_playing)
    
    # 3. Refrescar
    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()