import pygame
from config import *
from utils import cargar_fuente, dibujar_header, truncar_texto

class MenuPantalla:
    def __init__(self, titulo, opciones, sp_client=None, tipo_carga=None, id_padre=None):
        self.titulo = titulo
        self.opciones = opciones 
        self.seleccionado = 0
        self.indice_inicio = 0 # Scroll
        self.items_visibles = 7
        self.sp = sp_client
        self.tipo_carga = tipo_carga # 'artistas', 'playlists'
        self.id_padre = id_padre
        self.datos_cargados = False
        
        self.font_item = cargar_fuente(TEXT_BIG)

    def cargar_datos(self):
        # Evitamos cargar si ya tenemos datos o no hay cliente Spotify
        if self.datos_cargados or not self.sp: return
        
        try:
            nuevas = []

            # --- FAV ARTISTS ---
            if self.tipo_carga == 'artistas':
                print("Descargando artistas...")
                res = self.sp.current_user_followed_artists(limit=50)
                nuevas = [{'nombre': i['name'], 'uri': i['uri'], 'type': 'artist'} for i in res['artists']['items']]
            
            # --- FAV ALBUMS ---
            elif self.tipo_carga == 'albums':
                print("Descargando albumes guardados...")
                res = self.sp.current_user_saved_albums(limit=50)
                # OJO: Aqui la estructura es item['album']['name']
                nuevas = [{'nombre': i['album']['name'], 'uri': i['album']['uri'], 'type': 'album'} for i in res['items']]

            # --- MY PLAYLISTS ---
            elif self.tipo_carga == 'playlists':
                print("Descargando playlists...")
                res = self.sp.current_user_playlists(limit=50)
                nuevas = [{'nombre': i['name'], 'uri': i['uri'], 'type': 'playlist'} for i in res['items']]
            
            # --- NEW RELEASES ---
            elif self.tipo_carga == 'new_releases':
                print("Descargando novedades...")
                res = self.sp.new_releases(limit=50)
                # Aqui la estructura es res['albums']['items']
                nuevas = [{'nombre': i['name'], 'uri': i['uri'], 'type': 'album'} for i in res['albums']['items']]
            
            # --- ALBUMS (ARTIST) ---
            elif self.tipo_carga == 'artist_albums' and self.id_padre:
                print(f"Cargando albumes del artista {self.id_padre}...")
                # include_groups='album,single' para filtrar un poco
                res = self.sp.artist_albums(self.id_padre, limit=50, country="ES", include_groups='album,single')
                nuevas = [{'nombre': i['name'], 'uri': i['uri'], 'type': 'album'} for i in res['items']]

            # --- SONGS (ALBUM) ---
            elif self.tipo_carga == 'album_tracks' and self.id_padre:
                print(f"Cargando canciones del album {self.id_padre}...")
                res = self.sp.album_tracks(self.id_padre, limit=50)
                # Las canciones son 'track', listas para reproducir
                nuevas = [{'nombre': i['name'], 'uri': i['uri'], 'type': 'track'} for i in res['items']]

            # --- SONGS (PLAYLIST) ---
            elif self.tipo_carga == 'playlist_tracks' and self.id_padre:
                print(f"Cargando canciones de playlist {self.id_padre}...")
                res = self.sp.playlist_items(self.id_padre, limit=50)
                # En playlist, la cancion esta dentro de 'track'
                nuevas = []
                for item in res['items']:
                    if item.get('track'): # Verificacion de seguridad # A veces hay items vacios
                        t = item['track']
                        nuevas.append({'nombre': t['name'], 'uri': t['uri'], 'type': 'track'})

            if nuevas:
                self.opciones = nuevas
            else:
                self.opciones = ["Vacío"] # Para saber si cargo pero no habia nada
        
        except Exception as e:
            print(f"Error cargando {self.tipo_carga}: {e}")
            self.opciones = ["Error de conexion"]
            
        self.datos_cargados = True

    def mover_arriba(self):
        if self.seleccionado > 0:
            self.seleccionado -= 1
            if self.seleccionado < self.indice_inicio:
                self.indice_inicio = self.seleccionado

    def mover_abajo(self):
        if self.seleccionado < len(self.opciones) - 1:
            self.seleccionado += 1
            if self.seleccionado >= self.indice_inicio + self.items_visibles:
                self.indice_inicio += 1

    def obtener_seleccion(self):
        if not self.opciones: return None
        return self.opciones[self.seleccionado]

    def dibujar(self, pantalla, estado_play):
        # Si es un menu dinamico y esta vacio, cargamos
        if self.tipo_carga and not self.datos_cargados:
            pantalla.fill(NEGRO)
            dibujar_header(pantalla, self.titulo, estado_play)
            t = self.font_item.render("Loading...", ANTIALIASING, VERDE_SPOTIFY)
            pantalla.blit(t, (100, 100))
            pygame.display.flip() # Forzamos refresco para que se vea el "Loading"
            self.cargar_datos()

        pantalla.fill(NEGRO)
        
        # Header
        dibujar_header(pantalla, self.titulo, estado_play)
        
        # Lista
        inicio_y = 32
        altura_linea = 28
        total_items = len(self.opciones)
        hay_scroll = total_items > self.items_visibles

        # --- CÁLCULO DEL ANCHO DEL MENÚ ---
        if hay_scroll:
            # Si hay scroll: Ancho Total - (Ancho Scroll + Franja Negra Separadora)
            ancho_zona_menu = ANCHO - (ANCHO_SCROLLBAR + ANCHO_SEPARADOR)
        else:
            ancho_zona_menu = ANCHO # Ocupa todo

        vista = self.opciones[self.indice_inicio : self.indice_inicio + self.items_visibles]
        
        for i, op in enumerate(vista):
            pos_y = inicio_y + (i * altura_linea)
            # Extraemos el nombre si es un diccionario
            nombre_completo = op['nombre'] if isinstance(op, dict) else op

            nombre_truncado = truncar_texto(nombre_completo, MAX_CARACTERES_MENU)
            
            # Chequeamos seleccion real (indice relativo + offset)
            if (i + self.indice_inicio) == self.seleccionado:

                # Barra de selección
                pygame.draw.rect(pantalla, VERDE_SPOTIFY, (0, pos_y, ancho_zona_menu, altura_linea))

                # Texto seleccionado (Negro sobre Verde)
                r = self.font_item.render(nombre_truncado, ANTIALIASING, NEGRO)

                # Flechita >
                pos_flecha_x = ancho_zona_menu - 15
                flecha = self.font_item.render(">", ANTIALIASING, NEGRO)
                pantalla.blit(flecha, (pos_flecha_x, pos_y + OFFSET_TEXTO_LISTA))
            else:
                r = self.font_item.render(nombre_truncado, ANTIALIASING, VERDE_SPOTIFY)
            
            # --- AJUSTE EJE Y ---
            # Aquí usamos la variable OFFSET_TEXTO_LISTA que definimos en config.py
            # Si quieres que suba, baja el valor en config (ej: 4 o 5).
            pantalla.blit(r, (10, pos_y + OFFSET_TEXTO_LISTA))

        # 4. DIBUJAR BARRA DE SCROLL (Solo si hace falta)
        if hay_scroll:
            # Coordenadas del área de scroll (Barra derecha)
            sb_x = ANCHO - ANCHO_SCROLLBAR
            sb_y = ALTURA_HEADER # Empieza debajo del header
            sb_h = ALTO - ALTURA_HEADER # Altura disponible
            sb_w = ANCHO_SCROLLBAR - 4 # Ancho de la barra
            
            # A) EL MARCO VERDE (Caja contenedora)
            # El último parámetro '1' indica el grosor de la línea (solo borde)
            pygame.draw.rect(pantalla, VERDE_SPOTIFY, (sb_x, sb_y, ANCHO_SCROLLBAR, sb_h), GROSOR_CAJA_SCROLL)

            # B) EL THUMB (La parte que se mueve)
            # Dejamos un pequeño margen de 2px dentro de la caja para que no toque el borde
            margen_interno = GROSOR_CAJA_SCROLL + MARGEN_INTERNO_CAJA_SCROLL
            ancho_thumb = ANCHO_SCROLLBAR - (margen_interno * 2)

            # Altura útil dentro de la caja (restamos los bordes superior e inferior)
            altura_util_caja = sb_h - (margen_interno * 2)

            # Cálculo del tamaño del "Thumb" (la parte que se mueve)
            # Proporción: (Items Visibles / Total Items)
            thumb_height = max(10, int((self.items_visibles / total_items) * altura_util_caja))
            
            # Cálculo de la posición Y del "Thumb"
            # Proporción: (Índice Inicio / (Total - Visibles))
            max_scroll = total_items - self.items_visibles
            scroll_ratio = self.indice_inicio / max_scroll

            # Espacio útil vertical dentro de la caja
            espacio_util_y = altura_util_caja - thumb_height

            pos_y_thumb = sb_y + margen_interno + int(scroll_ratio * espacio_util_y)

            # Dibujar el Thumb (Verde sólido)
            pygame.draw.rect(pantalla, VERDE_SPOTIFY, (sb_x + margen_interno, pos_y_thumb, ancho_thumb, thumb_height))