import pygame
import spotipy
from spotipy.oauth2 import SpotifyOAuth

# Importamos nuestros modulos propios
from config import *
from menu_principal import MenuPantalla
from now_playing import PantallaNowPlaying
from search import SearchScreen

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
search = SearchScreen(sp)
menu_artistas = MenuPantalla("Artists", [], sp, 'artistas')
menu_albums   = MenuPantalla("Albums", [], sp, 'albums')
menu_playlists = MenuPantalla("Playlists", [], sp, 'playlists')
menu_releases = MenuPantalla("New Releases", [], sp, 'new_releases')
menu_shows = MenuPantalla("Shows", [], sp, 'shows')
menu_settings = MenuPantalla("Settings", [], sp, 'settings')

# MAIN MENU
home_opts = [
    {'nombre': 'Artists', 'destino': menu_artistas},
    {'nombre': 'Albums', 'destino': menu_albums},
    {'nombre': 'Playlists', 'destino': menu_playlists},
    {'nombre': 'New Releases', 'destino': menu_releases},
    {'nombre': 'Shows', 'destino': menu_shows},
    {'nombre': 'Search', 'destino': search},
    {'nombre': 'Now Playing', 'destino': now_playing},
    {'nombre': 'Settings', 'destino': menu_settings}
]
home = MenuPantalla("iSpod", home_opts)

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

            # TECLAS DE NAVEGACION
            curr = stack[-1] # Pantalla actual
            
            # --- 1. MENU ---
            if isinstance(curr, MenuPantalla):
                if e.key == pygame.K_UP: curr.mover_arriba()
                if e.key == pygame.K_DOWN: curr.mover_abajo()
                if e.key == pygame.K_ESCAPE:
                    if len(stack) > 1: stack.pop()
                
                # TECLA ENTER (Seleccionar)
                if e.key == pygame.K_RETURN:
                    sel = curr.obtener_seleccion()
                    
                    if not sel: continue # Seguridad por si está vacío

                    # 1. Extraemos datos básicos
                    tipo = sel.get('type')
                    uri = sel.get('uri') # Usamos .get() para que no falle si no existe
                    nombre = sel.get('nombre')

                    print(f"DEBUG: Enter en -> {tipo}")

                    # --- PRIORIDAD 1: ACCIONES DE SISTEMA (No requieren URI) ---
                    
                    # A. Cambiar Dispositivo (Tu problema actual)
                    if tipo == 'device_action':
                        print(f"Intentando cambiar al ID: {sel['id']}")
                        try:
                            sp.transfer_playback(device_id=sel['id'], force_play=True)
                            stack.pop() # Volver atrás
                        except Exception as e:
                            print(f"Error cambiando dispositivo: {e}")

                    # B. Abrir lista de dispositivos
                    elif tipo == 'menu_devices_list':
                        stack.append(MenuPantalla("Devices", [], sp, 'devices_list'))

                    # C. Toggle de Settings (Shuffle)
                    elif tipo == 'setting_toggle':
                        if sel.get('setting_key') == 'shuffle':
                            nuevo_estado = not sel['current_val']
                            try:
                                sp.shuffle(nuevo_estado)
                                # Actualización visual inmediata
                                txt = "Shuffle: ON" if nuevo_estado else "Shuffle: OFF"
                                curr.opciones[curr.seleccionado]['nombre'] = txt
                                curr.opciones[curr.seleccionado]['current_val'] = nuevo_estado
                            except Exception as e:
                                print(f"Error Shuffle: {e}")

                    # D. Abrir Settings Menu
                    elif tipo == 'menu_settings':
                        stack.append(MenuPantalla(nombre, [], sp, 'settings'))

                    # --- PRIORIDAD 2: NAVEGACIÓN DE MENÚS PROPIOS ---
                    elif isinstance(sel, dict) and sel.get('destino'):
                        stack.append(sel['destino'])
                    
                    # --- PRIORIDAD 3: CONTENIDO SPOTIFY (Requiere URI) ---
                    elif uri: 
                        # -> ARTISTA
                        if tipo == 'artist':
                            stack.append(MenuPantalla(nombre, [], sp, 'artist_albums', id_padre=uri))
                        
                        # -> ALBUM
                        elif tipo == 'album':
                            stack.append(MenuPantalla(nombre, [], sp, 'album_tracks', id_padre=uri))
                            
                        # -> PLAYLIST
                        elif tipo == 'playlist':
                            stack.append(MenuPantalla(nombre, [], sp, 'playlist_tracks', id_padre=uri))
                        
                        # -> SHOW (Podcast)
                        elif tipo == 'show':
                            # OJO: Aquí usamos el ID que guardaste en menu_principal, no solo URI
                            el_id = sel.get('id', uri) 
                            stack.append(MenuPantalla(nombre, [], sp, 'show_episodes', id_padre=el_id))

                        # -> REPRODUCIR (Track o Episode)
                        elif tipo == 'track' or tipo == 'episode':
                            print(f"Reproduciendo: {nombre}")
                            try:
                                sp.start_playback(uris=[uri])
                                stack.append(now_playing)
                            except Exception as err:
                                print(f"Error Playback: {err}")
            
            # --- 2. SEARCH ---
            elif isinstance(curr, SearchScreen):
                if e.key == pygame.K_UP:
                    curr.mover_arriba()
                if e.key == pygame.K_DOWN:
                    curr.mover_abajo()
                if e.key == pygame.K_RIGHT:
                    curr.avanzar_caracter()
                if e.key == pygame.K_LEFT:
                    curr.borrar_caracter()
                if e.key == pygame.K_ESCAPE:
                    if curr.retroceder(): stack.pop()
                if e.key == pygame.K_RETURN:
                    res = curr.pulsar_enter()
                    if res and res['tipo'] == 'item':

                        # Lógica idéntica al menú principal para navegar/reproducir
                        uri = res['uri']
                        tipo = res['subtipo']
                        nombre = res['nombre']

                        if tipo == 'track':
                            try:
                                sp.start_playback(uris=[uri])
                                stack.append(now_playing)
                            except: print("Error Playback Search")
                        elif tipo == 'artist':
                            stack.append(MenuPantalla(nombre, [], sp, 'artist_albums', id_padre=uri))
                        elif tipo == 'album':
                            stack.append(MenuPantalla(nombre, [], sp, 'album_tracks', id_padre=uri))
                        elif tipo == 'playlist':
                            stack.append(MenuPantalla(nombre, [], sp, 'playlist_tracks', id_padre=uri))
                        elif tipo == 'show':
                            stack.append(MenuPantalla(nombre, [], sp, 'show_episodes', id_padre=uri))
                        elif tipo == 'show':
                            # Usamos res['id'] porque show_episodes requiere el ID, no la URI
                            # (Asegúrate de haber guardado 'id' en menu_search.py como hablamos antes)
                            stack.append(MenuPantalla(nombre, [], sp, 'show_episodes', id_padre=res['id']))
                        elif tipo == 'episode':
                            try:
                                sp.start_playback(uris=[uri])
                                stack.append(now_playing)
                            except: print("Error Playback Episode")
        
            # --- 3. NOW PLAYING ---
            elif isinstance(curr, PantallaNowPlaying):
                if e.key == pygame.K_ESCAPE:
                    stack.pop()
                
                if e.key == pygame.K_RETURN:
                    curr.cambiar_vista()
                # Aquí añadiremos controles de pausa/next en el futuro
                        
            # Si estamos en Now Playing, Enter o Clickwheel central podria pausar (futuro)

    # 3. Dibujar
    stack[-1].dibujar(pantalla, global_is_playing)
    
    # 3. Refrescar
    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()