import pygame
from config import *
from utils import cargar_fuente, dibujar_header

class MenuPantalla:
    def __init__(self, titulo, opciones, sp_client=None, tipo_carga=None):
        self.titulo = titulo
        self.opciones = opciones 
        self.seleccionado = 0
        self.indice_inicio = 0 # Scroll
        self.items_visibles = 7
        self.sp = sp_client
        self.tipo_carga = tipo_carga # 'artistas', 'playlists'
        self.datos_cargados = False
        
        self.font_item = cargar_fuente(TEXT_BIG)

    def cargar_datos(self):
        # Evitamos cargar si ya tenemos datos o no hay cliente Spotify
        if self.datos_cargados or not self.sp: return
        
        try:
            nuevas = []
            if self.tipo_carga == 'artistas':
                print("Descargando artistas...")
                res = self.sp.current_user_followed_artists(limit=50)
                nuevas = [{'nombre': i['name'], 'uri': i['uri']} for i in res['artists']['items']]
            elif self.tipo_carga == 'playlists':
                print("Descargando playlists...")
                res = self.sp.current_user_playlists(limit=50)
                nuevas = [{'nombre': i['name'], 'uri': i['uri']} for i in res['items']]
            
            if nuevas: self.opciones = nuevas
        except Exception as e:
            print(f"Error cargando lista: {e}")
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
            t = self.font_item.render("Loading...", False, VERDE_SPOTIFY)
            pantalla.blit(t, (100, 100))
            pygame.display.flip() # Forzamos refresco para que se vea el "Loading"
            self.cargar_datos()

        pantalla.fill(NEGRO)
        
        # Header
        dibujar_header(pantalla, self.titulo, estado_play)
        
        # Lista
        inicio_y = 32
        vista = self.opciones[self.indice_inicio : self.indice_inicio + self.items_visibles]
        
        for i, op in enumerate(vista):
            pos_y = inicio_y + (i * 28)
            # Extraemos el nombre si es un diccionario
            txt = op['nombre'] if isinstance(op, dict) else op
            
            # Chequeamos seleccion real (indice relativo + offset)
            if (i + self.indice_inicio) == self.seleccionado:
                pygame.draw.rect(pantalla, VERDE_SPOTIFY, (0, pos_y, ANCHO, 28))
                r = self.font_item.render(txt, False, NEGRO)
                # Flechita >
                pantalla.blit(self.font_item.render(">", False, NEGRO), (ANCHO-15, pos_y+6))
            else:
                r = self.font_item.render(txt, False, VERDE_SPOTIFY)
            
            pantalla.blit(r, (10, pos_y+6))