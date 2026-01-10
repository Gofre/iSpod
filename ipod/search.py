import pygame
from config import *
from utils import cargar_fuente, dibujar_header, truncar_texto

class SearchScreen:
    def __init__(self, sp_client):
        self.sp = sp_client
        self.font_small = cargar_fuente(TEXT_SMALL)
        self.font_big = cargar_fuente(TEXT_BIG)
        
        # Caracteres disponibles para rotar
        self.caracteres = " ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
        self.char_idx = 1 # El espacio está incluido el primero, pero empezamos en la 'A'
        
        self.query = "" # El texto ya confirmado
        self.resultados = []
        self.idx_res = 0
        self.modo_foco = 'busqueda' # 'busqueda' (editando texto) o 'lista'
        
        self.scroll_inicio = 0
        self.items_visibles = 7

    def buscar(self):
        # Concatenamos la query confirmada + el caracter actual para buscar en tiempo real
        busqueda_actual = self.query + self.caracteres[self.char_idx]
        if not busqueda_actual.strip():
            self.resultados = []
            return
        
        try:
            # Buscamos por categorias como hace dupontgu
            res = self.sp.search(q=busqueda_actual, limit=10, type='track,artist,album,playlist')
            self.resultados = []
            
            # Categorias
            for cat_key, label in [('artists', 'ARTISTS'), ('tracks', 'SONGS'), ('albums', 'ALBUMS'), ('playlists', 'PLAYLISTS')]:
                items = res.get(cat_key, {}).get('items', [])
                if items:
                    self.resultados.append({'tipo': 'header', 'nombre': label})
                    for i in items:
                        nombre = i['name']
                        if cat_key == 'tracks': nombre += f" - {i['artists'][0]['name']}"
                        self.resultados.append({
                            'tipo': 'item', 
                            'nombre': nombre, 
                            'uri': i['uri'], 
                            'subtipo': cat_key[:-1]
                        })
            self.idx_res = 0
            self.scroll_inicio = 0
        except:
            pass

    def mover_arriba(self):
        if self.modo_foco == 'busqueda':
            # Rotar letras hacia atras
            self.char_idx = (self.char_idx - 1) % len(self.caracteres)
            self.buscar()
        else:
            # Moverse por la lista de resultados
            if self.idx_res > 0:
                self.idx_res -= 1
                # Saltar headers
                if self.resultados[self.idx_res]['tipo'] == 'header' and self.idx_res > 0:
                    self.idx_res -= 1
                if self.idx_res < self.scroll_inicio:
                    self.scroll_inicio = self.idx_res

    def mover_abajo(self):
        if self.modo_foco == 'busqueda':
            # Rotar letras hacia adelante
            self.char_idx = (self.char_idx + 1) % len(self.caracteres)
            self.buscar()
        else:
            if self.idx_res < len(self.resultados) - 1:
                self.idx_res += 1
                if self.resultados[self.idx_res]['tipo'] == 'header':
                    self.idx_res += 1
                if self.idx_res >= self.scroll_inicio + self.items_visibles:
                    self.scroll_inicio += 1

    def avanzar_caracter(self):
        """Confirmar letra actual y pasar a la siguiente (Flecha Derecha)"""
        if self.modo_foco == 'busqueda':
            self.query += self.caracteres[self.char_idx]
            self.char_idx = 1 # Volver a la 'A' para la siguiente posición
            self.buscar()

    def borrar_caracter(self):
        """Borrar última letra confirmada (Flecha Izquierda)"""
        if self.modo_foco == 'busqueda' and len(self.query) > 0:
            self.query = self.query[:-1]
            self.buscar()

    def pulsar_enter(self):
        if self.modo_foco == 'busqueda':
            if self.resultados:
                self.modo_foco = 'lista'
                # Buscamos el primer item real (saltando el header si existe)
                self.idx_res = 0
                if self.resultados[0]['tipo'] == 'header' and len(self.resultados) > 1:
                    self.idx_res = 1
            return None
        else:
            return self.resultados[self.idx_res]

    def retroceder(self):
        if self.modo_foco == 'lista':
            self.modo_foco = 'busqueda'
            return False # Se queda en Search pero sube al texto
        return True # Sale al menú anterior

    def dibujar(self, pantalla, estado_play):
        pantalla.fill(NEGRO)
        
        # --- 1. FONDO Y LÍNEA DEL HEADER ---
        pygame.draw.rect(pantalla, NEGRO, (0, 0, ANCHO, ALTURA_HEADER))
        pygame.draw.line(pantalla, VERDE_SPOTIFY, (0, ALTURA_HEADER), (ANCHO, ALTURA_HEADER), 2)
        
        # --- 2. ICONOS (Recuperados) ---
        
        # A) Batería (Derecha)
        pygame.draw.rect(pantalla, VERDE_SPOTIFY, (290, 8, 22, 10), 1) 
        pygame.draw.rect(pantalla, VERDE_SPOTIFY, (312, 10, 2, 6))
        pygame.draw.rect(pantalla, VERDE_SPOTIFY, (292, 10, 15, 6))
        
        # B) Play/Pause (Izquierda)
        # Usamos las mismas coordenadas que en ipod_utils
        if estado_play is True: # Play (Triángulo)
            puntos = [(10, 9), (10, 19), (20, 14)]
            pygame.draw.polygon(pantalla, VERDE_SPOTIFY, puntos)
        elif estado_play is False: # Pause (Barras)
            pygame.draw.rect(pantalla, VERDE_SPOTIFY, (10, 9, 3, 10))
            pygame.draw.rect(pantalla, VERDE_SPOTIFY, (16, 9, 3, 10))

        # --- 3. TEXTO DE BÚSQUEDA (Centrado y con Resalte) ---
        
        font_header = self.font_big
        char_actual = self.caracteres[self.char_idx]
        visual_char = char_actual
        
        # Renderizamos las dos partes por separado para medir
        # 1. Parte confirmada (Query)
        query_surf = font_header.render(self.query, ANTIALIASING, VERDE_SPOTIFY)
        
        # 2. Parte activa (Carácter giratorio)
        if self.modo_foco == 'busqueda':
            # Letra negra para luego ponerle fondo
            char_surf = font_header.render(visual_char, ANTIALIASING, NEGRO)
        else:
            # Letra verde normal
            char_surf = font_header.render(visual_char, ANTIALIASING, VERDE_SPOTIFY)
            
        # --- CÁLCULO DEL CENTRO ---
        # Ancho total = ancho de lo escrito + ancho de la letra actual
        ancho_total = query_surf.get_width() + char_surf.get_width()
        
        # Coordenada X donde debe empezar todo el bloque para estar centrado
        start_x = (ANCHO // 2) - (ancho_total // 2)
        center_y = ALTURA_HEADER // 2
        
        # --- PINTAR TEXTOS ---
        
        # A) Pintar la Query confirmada
        query_rect = query_surf.get_rect(midleft=(start_x, center_y))
        pantalla.blit(query_surf, query_rect)
        
        # B) Pintar el carácter activo
        char_x = query_rect.right # Pegado al final de la query
        char_rect = char_surf.get_rect(midleft=(char_x, center_y))
        
        if self.modo_foco == 'busqueda':
            # DIBUJAR EL RESALTE (Caja Verde)
            # Hacemos la caja un poco más ancha que la letra para que quede bonito
            bg_rect = char_rect.inflate(4, 6) 
            bg_rect.centery = center_y - 1 # Ajuste fino vertical
            
            pygame.draw.rect(pantalla, VERDE_SPOTIFY, bg_rect)
            
            # Pintar la letra NEGRA encima
            pantalla.blit(char_surf, char_rect)
        else:
            # Pintar la letra VERDE normal
            pantalla.blit(char_surf, char_rect)

        # --- 4. RESULTADOS (Igual que antes) ---
        if not self.resultados:
            msg = self.font_small.render("Rotate to search...", ANTIALIASING, GRIS_TEXTO)
            pantalla.blit(msg, (ANCHO//2 - msg.get_width()//2, 60))
        else:
            inicio_y = ALTURA_HEADER + 10
            altura_linea = 28
            vista = self.resultados[self.scroll_inicio : self.scroll_inicio + self.items_visibles]
            
            for i, item in enumerate(vista):
                pos_y = inicio_y + (i * altura_linea)
                idx_real = i + self.scroll_inicio
                
                if item['tipo'] == 'header':
                    s = self.font_small.render(item['nombre'], ANTIALIASING, VERDE_SPOTIFY)
                    pygame.draw.line(pantalla, VERDE_SPOTIFY, (5, pos_y + 18), (45, pos_y + 18), 1)
                    pantalla.blit(s, (10, pos_y + 4))
                else:
                    txt = truncar_texto(item['nombre'], MAX_CARACTERES_MENU)
                    if idx_real == self.idx_res and self.modo_foco == 'lista':
                        pygame.draw.rect(pantalla, VERDE_SPOTIFY, (0, pos_y, ANCHO, altura_linea))
                        s = self.font_small.render(txt, ANTIALIASING, NEGRO)
                    else:
                        color = VERDE_SPOTIFY if self.modo_foco == 'lista' else GRIS_TEXTO
                        s = self.font_small.render(txt, ANTIALIASING, color)
                    pantalla.blit(s, (20, pos_y + 6))