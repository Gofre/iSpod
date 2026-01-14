import pygame
import threading
import time
import requests
import io
import traceback
import numpy as np
from config import *
from utils import cargar_fuente, dibujar_header, truncar_texto, formato_tiempo, procesar_caratula_retro

class PantallaNowPlaying:
    def __init__(self, sp_client):
        self.sp = sp_client
        self.font_big = cargar_fuente(TEXT_BIG)
        self.font_small = cargar_fuente(TEXT_SMALL)
        
        # Datos de la canción
        self.track = "Loading..."
        self.artist = ""
        self.album = ""       # NUEVO
        self.track_no = 0     # NUEVO
        self.total_tracks = 0 # NUEVO
        
        self.cover_img = None
        self.cover_url = ""
        self.duration = 0
        self.progress = 0
        self.is_playing = False
        
        # Control de actualización
        self.last_update = 0
        self.update_interval = 1000 
        
        # MODO DE VISTA: 0 = Carátula, 1 = Texto Detallado (Estilo iPod Clásico)
        self.modo_vista = 1 

    def update(self):
        current_time = pygame.time.get_ticks()
        if current_time - self.last_update > self.update_interval:
            try:
                pb = self.sp.current_playback(additional_types='track,episode')
                if pb and pb.get('item'):
                    item = pb['item']
                    self.is_playing = pb['is_playing']
                    self.progress = pb['progress_ms']
                    self.duration = item['duration_ms']
                    
                    item_type = item.get('type') # track/episode

                    if item_type == 'track':

                        self.track = item['name']
                        self.artist = item['artists'][0]['name']
                        self.album = item['album']['name']
                        self.track_no = item['track_number']
                        self.total_tracks = item['album']['total_tracks']
                        images = item['album']['images']
                        
                    
                    elif item_type == 'episode':
                        self.track = item['name']
                        self.artist = item['show']['publisher']
                        self.album = item['show']['name']
                        images = item['images'] # A veces están en el root del item
                        if not images:
                            images = item['show']['images'] # A veces en el show
                        
                        self.track_no = 0 # No suelen tener número de pista fiable
                        self.total_tracks = 0
                    
                    # Carátula (Solo descargamos si cambia)
                    url = images[0]['url'] if images else None
                    if url and url != self.cover_url:
                        self.cover_url = url
                        self.descargar_caratula(url)
                else:
                    self.is_playing = False
                    
            except Exception as e:
                print(f"Error update: {e}")
            
            self.last_update = current_time

    """
    def descargar_caratula(self, url):
        def _load():
            try:
                r = requests.get(url)
                data = io.BytesIO(r.content)
                img = pygame.image.load(data)
                self.cover_img = pygame.transform.scale(img, (140, 140))
            except: pass
        threading.Thread(target=_load, daemon=True).start()
    """

    def descargar_caratula(self, url):
        def _load():
            try:
                r = requests.get(url)
                data = io.BytesIO(r.content)
                
                # 1. Cargar imagen original (color)
                img_original = pygame.image.load(data)
                
                # 2. Procesar al estilo RETRO (Dithering)
                # Pasamos la paleta de colores que queremos usar
                self.cover_img = procesar_caratula_retro(img_original, (NEGRO, VERDE_SPOTIFY))
                
            except Exception as e:
                print(f"Error procesando carátula: {e}")
                self.cover_img = None
                
        threading.Thread(target=_load, daemon=True).start()
    
    def cambiar_vista(self):
        """Alterna entre ver la carátula o ver el texto detallado"""
        self.modo_vista = 1 if self.modo_vista == 0 else 0

    def dibujar_barra_progreso(self, pantalla, y_pos, ancho_barra=ANCHO-40):
        altura_barra = 11
        radio_borde = 3
        grosor_outline = 1 # Grosor de la línea de la caja

        x_pos = (ANCHO - ancho_barra) // 2
        # Rectángulo total que ocupará la barra
        rect_contenedor = (x_pos, y_pos, ancho_barra, altura_barra)
        
        # --- 1. DIBUJAR EL RELLENO (Primero, y cuadrado) ---
        if self.duration > 0 and self.progress > 0:
            pct = self.progress / self.duration
            ancho_relleno = int(ancho_barra * pct)
            
            # Para que quede perfecto, el relleno rectangular debe dibujarse 
            # ligeramente por dentro del outline.
            # Desplazamos X e Y por el grosor, y reducimos ancho y alto por el doble del grosor.
            rect_relleno = (
                x_pos + grosor_outline, 
                y_pos + grosor_outline,
                max(0, ancho_relleno - (grosor_outline * 2)), # Asegurar que no sea negativo
                altura_barra - (grosor_outline * 2)
            )

            # Dibujamos solo si tiene anchura válida.
            # border_radius=0 (por defecto) asegura esquinas rectas.
            if rect_relleno[2] > 0:
                pygame.draw.rect(pantalla, VERDE_SPOTIFY, rect_relleno)

        # --- 2. DIBUJAR LA CAJA OUTLINE (Encima, y redondeada) ---
        # Usamos 'width=grosor_outline' para que sea hueca
        # Al dibujarla después, "recorta" visualmente las esquinas del relleno.
        pygame.draw.rect(pantalla, VERDE_SPOTIFY, rect_contenedor, width=grosor_outline, border_radius=radio_borde)
            
        # --- TIEMPOS (IGUAL QUE ANTES) ---
        alineado_y = 15 # Un poco más abajo de la barra
        
        # Tiempo actual
        txt_actual = formato_tiempo(self.progress)
        s_actual = self.font_big.render(txt_actual, ANTIALIASING, VERDE_SPOTIFY)
        pantalla.blit(s_actual, (x_pos, y_pos + alineado_y))
        
        # Tiempo restante
        restante = self.duration - self.progress
        txt_restante = "-" + formato_tiempo(restante)
        s_restante = self.font_big.render(txt_restante, ANTIALIASING, VERDE_SPOTIFY)
        pantalla.blit(s_restante, (x_pos + ancho_barra - s_restante.get_width(), y_pos + alineado_y))

    def dibujar(self, pantalla, estado_play):
        self.update()
        pantalla.fill(NEGRO)
        
        # Título Contexto (Header)
        # En el iPod original solía poner el nombre del Album o "Now Playing"
        # Usaremos el nombre del Álbum si cabe, o "Now Playing"
        #titulo_header = self.album if len(self.album) < 20 else "Now Playing"
        titulo_header = "Now Playing"
        dibujar_header(pantalla, titulo_header, self.is_playing)

        # Contador de Pista (Esquina superior izquierda)
        # "1 of 53"
        txt_counter = f"{self.track_no} of {self.total_tracks}"
        s_counter = self.font_small.render(txt_counter, ANTIALIASING, VERDE_SPOTIFY)
        pantalla.blit(s_counter, (10, ALTURA_HEADER + 10))

        # --- VISTA 0: CARÁTULA (Tu diseño anterior) ---
        if self.modo_vista == 0:
            if self.cover_img:
                pantalla.blit(self.cover_img, (10, 58))
                pygame.draw.rect(pantalla, VERDE_SPOTIFY, (10, 58, 128, 128), 1)
            else:
                pygame.draw.rect(pantalla, GRIS_PIXEL, (10, 58, 128, 128), 1)
            
            # Textos laterales
            t_track = truncar_texto(self.track, 13)
            t_artist = truncar_texto(self.artist, 13)
            t_album = truncar_texto(self.album, 13)
            pantalla.blit(self.font_big.render(t_track, ANTIALIASING, VERDE_SPOTIFY), (150, 75))
            pantalla.blit(self.font_big.render(t_artist, ANTIALIASING, VERDE_SPOTIFY), (150, 75 + 32))
            pantalla.blit(self.font_big.render(t_album, ANTIALIASING, VERDE_SPOTIFY), (150, 75 + 32 + 32))
            
            # Barra simple
            """
            if self.duration > 0: pct = self.progress / self.duration
            else: pct = 0
            pygame.draw.rect(pantalla, GRIS_PIXEL, (160, 155, 140, 8))
            pygame.draw.rect(pantalla, VERDE_SPOTIFY, (160, 155, int(140*pct), 8))
            """

        # --- VISTA 1: DETALLE TEXTO (Estilo iPod Foto adjunta) ---
        elif self.modo_vista == 1:
            
            # Información Central (Título, Artista, Álbum)
            center_x = ANCHO // 2

            # Coordenadas equidistantes
            # Tenemos espacio entre Y=60 y Y=160 (aprox 100px)
            y_cancion = 80
            y_artista = y_cancion + 32  # +32px
            y_album   = y_artista + 32 # +32px

            start_y = 65 # Altura inicial

            # Limite caracteres más estricto por ser fuente grande
            limite_chars = 24
            
            # Título (Grande y Brillante)
            lbl_title = truncar_texto(self.track, limite_chars) # Un poco más de margen al no haber foto
            s_title = self.font_big.render(lbl_title, ANTIALIASING, VERDE_SPOTIFY)
            r_title = s_title.get_rect(center=(center_x, y_cancion))
            pantalla.blit(s_title, r_title)
            
            # Artista (Pequeño)
            lbl_artist = truncar_texto(self.artist, limite_chars)
            s_artist = self.font_big.render(lbl_artist, ANTIALIASING, VERDE_SPOTIFY)
            r_artist = s_artist.get_rect(center=(center_x, y_artista))
            pantalla.blit(s_artist, r_artist)
            
            # Álbum (Pequeño)
            lbl_album = truncar_texto(self.album, limite_chars)
            s_album = self.font_big.render(lbl_album, ANTIALIASING, VERDE_SPOTIFY) # Gris para diferenciar
            r_album = s_album.get_rect(center=(center_x, y_album))
            pantalla.blit(s_album, r_album)
        
        # Barra de Progreso y Tiempos
        # La ponemos abajo, estilo iPod classic
        self.dibujar_barra_progreso(pantalla, y_pos=195, ancho_barra=290)