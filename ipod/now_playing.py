import pygame
from config import *
from utils import cargar_fuente, procesar_caratula_retro, dibujar_header

class PantallaNowPlaying:
    def __init__(self, sp_client):
        self.sp = sp_client
        self.font_big = cargar_fuente(TEXT_BIG)
        self.font_small = cargar_fuente(TEXT_SMALL)
        
        self.track = "Pausado"
        self.artist = "..."
        self.cover_surf = None
        self.cover_url = ""
        self.progress = 0
        self.duration = 1
        
        self.last_check = 0
        self.check_interval = 2000 # 2 segundos

    def update(self):
        now = pygame.time.get_ticks()
        # Solo consultamos a Spotify cada X segundos para no saturar
        if now - self.last_check < self.check_interval: return
        
        try:
            pb = self.sp.current_playback()
            if pb and pb['item']:
                self.track = pb['item']['name']
                self.artist = pb['item']['artists'][0]['name']
                self.progress = pb['progress_ms']
                self.duration = pb['item']['duration_ms']
                
                # Gestion de caratula
                if len(pb['item']['album']['images']) > 1:
                    url = pb['item']['album']['images'][1]['url']
                    if url != self.cover_url:
                        self.cover_url = url
                        self.cover_surf = procesar_caratula_retro(url)
            else:
                self.track = "Silencio"
                self.is_playing = False
                
        except Exception as e:
            print(f"Error API NowPlaying: {e}")
            
        self.last_check = now

    def dibujar(self, pantalla, estado_play):
        self.update()
        pantalla.fill(NEGRO)
        
        dibujar_header(pantalla, "Now Playing", estado_play)
	
        # 1. Caratula Retro (Izquierda)
        if self.cover_surf:
            pantalla.blit(self.cover_surf, (10, 50))
            pygame.draw.rect(pantalla, VERDE_SPOTIFY, (10, 50, 140, 140), 1)
        else:
            # Cuadrado vac�o si no hay caratula
            pygame.draw.rect(pantalla, GRIS_PIXEL, (10, 50, 140, 140), 1)
        
        # 2. Textos (Derecha)
        def cut(t): return t[:14]+".." if len(t)>14 else t
        
        pantalla.blit(self.font_big.render(cut(self.track), False, VERDE_SPOTIFY), (160, 60))
        pantalla.blit(self.font_small.render(cut(self.artist), False, VERDE_SPOTIFY), (160, 90))
        
        # 3. Barra de progreso
        if self.duration > 0:
            pct = self.progress / self.duration
        else:
            pct = 0
            
        pygame.draw.rect(pantalla, GRIS_PIXEL, (160, 160, 140, 8)) # Fondo
        pygame.draw.rect(pantalla, VERDE_SPOTIFY, (160, 160, int(140*pct), 8)) # Relleno