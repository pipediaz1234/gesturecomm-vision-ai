# ================================================================
#  sistema_comunicacion.py  — VERSION FINAL (1 sola camara)
#  La misma camara sirve para gestos Y para señalar numeros
#  Cuando dice "ok" / "listo" / "dale" → vuelve a EN ESPERA
# ================================================================
import os, time, threading, queue, logging
from enum import Enum, auto
from typing import Optional

import cv2, numpy as np
from PIL import Image, ImageTk
import tkinter as tk
from tkinter import font as tkfont

from config import *
from utils.detector_mano import DetectorMano
from core.reconocedor    import ReconocedorGestos
from utils.voz           import SintesisVoz, ReconocimientoVoz

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s [%(levelname)s] %(message)s')


class Estado(Enum):
    INICIANDO           = auto()
    ESPERANDO_CLIENTE   = auto()
    HABLANDO            = auto()
    CUENTA_REGRESIVA    = auto()
    ESCUCHANDO          = auto()
    MOSTRANDO_RESPUESTA = auto()
    ELIGIENDO_CANTIDAD  = auto()
    ERROR               = auto()


# ================================================================
#  DETECCION DEDO INDICE
# ================================================================
def obtener_punta_indice(results, fw, fh):
    if not results.multi_hand_landmarks:
        return None
    lm = results.multi_hand_landmarks[0].landmark[8]
    return (int(lm.x * fw), int(lm.y * fh))


def indice_apuntando(results):
    if not results.multi_hand_landmarks:
        return False
    lm = results.multi_hand_landmarks[0].landmark
    return (lm[8].y < lm[6].y and
            lm[12].y > lm[10].y and
            lm[16].y > lm[14].y)


# ================================================================
#  VENTANA: Imagen de producto
# ================================================================
class VentanaProducto(tk.Toplevel):
    def __init__(self, parent, gesto, titulo, ruta_img):
        super().__init__(parent)
        self.title(titulo)
        self.configure(bg=COLOR_BG)
        self.resizable(False, False)
        self.attributes('-topmost', True)
        self.geometry('460x500')
        self.update_idletasks()
        x = (self.winfo_screenwidth()  - 460) // 2
        y = (self.winfo_screenheight() - 500) // 2
        self.geometry(f'460x500+{x}+{y}')
        self._construir(gesto, titulo, ruta_img)
        self.after(8000, lambda: self.destroy()
                   if self.winfo_exists() else None)

    def _construir(self, gesto, titulo, ruta_img):
        hdr = tk.Frame(self, bg=COLOR_SURFACE, height=52)
        hdr.pack(fill='x'); hdr.pack_propagate(False)
        color_h = {
            'menu': COLOR_ACCENT, 'papas': '#FFB347',
            'dulces': '#FF69B4', 'bebidas': '#87CEEB',
            'chocolate': '#D2691E',
        }.get(gesto, COLOR_ACCENT)
        tk.Label(hdr, text=titulo.upper(), fg=color_h,
                 bg=COLOR_SURFACE,
                 font=tkfont.Font(family='Helvetica',
                                  size=14, weight='bold')
                 ).pack(expand=True)
        img_f = tk.Frame(self, bg=COLOR_BG)
        img_f.pack(fill='both', expand=True, padx=12, pady=8)
        if ruta_img and os.path.exists(ruta_img):
            try:
                img = Image.open(ruta_img).resize(
                    (436, 360), Image.LANCZOS)
                self._img_tk = ImageTk.PhotoImage(img)
                tk.Label(img_f, image=self._img_tk,
                         bg=COLOR_BG).pack()
            except Exception:
                tk.Label(img_f, text='Sin imagen',
                         fg=COLOR_TEXT_DIM, bg=COLOR_BG,
                         font=tkfont.Font(size=14)).pack(expand=True)
        ft = tk.Frame(self, bg=COLOR_SURFACE, height=36)
        ft.pack(fill='x'); ft.pack_propagate(False)
        self._lbl_t = tk.Label(ft, text='Se cierra en 8 s',
                                fg=COLOR_TEXT_DIM, bg=COLOR_SURFACE,
                                font=tkfont.Font(size=9))
        self._lbl_t.pack(side='left', padx=10)
        tk.Button(ft, text='Cerrar', command=self.destroy,
                  bg=COLOR_SURFACE, fg=COLOR_ERROR,
                  font=tkfont.Font(size=9), bd=0,
                  relief='flat', cursor='hand2'
                  ).pack(side='right', padx=10)
        self._c = 8
        self._tick()

    def _tick(self):
        self._c -= 1
        if self._c <= 0:
            return
        try:
            self._lbl_t.config(text=f'Se cierra en {self._c} s')
            self.after(1000, self._tick)
        except Exception:
            pass


# ================================================================
#  VENTANA: Texto grande del vendedor
# ================================================================
class VentanaTextoGrande(tk.Toplevel):
    def __init__(self, parent, texto):
        super().__init__(parent)
        self.title('El vendedor dice...')
        self.configure(bg=COLOR_BG)
        self.resizable(False, False)
        self.attributes('-topmost', True)
        W, H = 720, 300
        x = (self.winfo_screenwidth()  - W) // 2
        y = (self.winfo_screenheight() - H) // 2
        self.geometry(f'{W}x{H}+{x}+{y}')
        hdr = tk.Frame(self, bg=COLOR_ACCENT2, height=48)
        hdr.pack(fill='x'); hdr.pack_propagate(False)
        tk.Label(hdr, text='  El vendedor dice:',
                 fg='white', bg=COLOR_ACCENT2,
                 font=tkfont.Font(family='Helvetica',
                                  size=14, weight='bold')
                 ).pack(side='left', pady=10)
        tk.Label(self, text=texto,
                 fg=COLOR_TEXT, bg=COLOR_BG,
                 font=tkfont.Font(family='Helvetica',
                                  size=24, weight='bold'),
                 wraplength=680, justify='center'
                 ).pack(expand=True, padx=20)
        tk.Button(self, text='Entendido', command=self.destroy,
                  bg=COLOR_ACCENT2, fg='white',
                  font=tkfont.Font(family='Helvetica',
                                   size=13, weight='bold'),
                  bd=0, relief='flat', cursor='hand2',
                  padx=30, pady=10).pack(pady=(0, 16))
        self.after(12000, lambda: self.destroy()
                   if self.winfo_exists() else None)


# ================================================================
#  WIDGET: Cuenta regresiva circular
# ================================================================
class CuentaRegresivaWidget(tk.Canvas):
    def __init__(self, parent, segundos=5, callback_fin=None, **kw):
        super().__init__(parent, width=90, height=90,
                         bg=COLOR_BG, bd=0,
                         highlightthickness=0, **kw)
        self._total    = segundos
        self._resto    = segundos
        self._callback = callback_fin
        self._activo   = False
        self._dibujar(segundos)

    def iniciar(self):
        self._resto  = self._total
        self._activo = True
        self._tick()

    def detener(self):
        self._activo = False

    def _tick(self):
        if not self._activo:
            return
        self._dibujar(self._resto)
        if self._resto <= 0:
            self._activo = False
            if self._callback:
                self._callback()
            return
        self._resto -= 1
        self.after(1000, self._tick)

    def _dibujar(self, n):
        self.delete('all')
        self.create_oval(8, 8, 82, 82,
                         outline=COLOR_BORDER, width=5,
                         fill=COLOR_CARD)
        if self._total > 0:
            pct = n / self._total
            self.create_arc(8, 8, 82, 82,
                            start=90, extent=pct * 360,
                            outline=COLOR_ACCENT if n > 2 else COLOR_ACCENT2,
                            width=5, style='arc')
        col = COLOR_ACCENT if n > 2 else COLOR_ACCENT2
        self.create_text(45, 45, text=str(n), fill=col,
                         font=('Helvetica', 22, 'bold'))


# ================================================================
#  PANTALLA OVERLAY: Numeros para señalar (sobre la camara principal)
# ================================================================
class OverlayNumeros(tk.Toplevel):
    """
    Ventana sin bordes encima de la camara principal.
    Muestra los numeros 1-5 y detecta donde apunta el dedo
    usando los frames que le pasa el loop principal de camara.
    NO abre una segunda camara.
    """
    def __init__(self, parent, callback_elegir):
        super().__init__(parent)
        self.overrideredirect(True)          # sin bordes
        self.attributes('-topmost', True)
        self.attributes('-alpha', 0.95)

        SW = self.winfo_screenwidth()
        SH = self.winfo_screenheight()
        self.geometry(f'{SW}x{SH}+0+0')
        self.configure(bg='#0D1117')

        self._callback    = callback_elegir
        self._confirmado  = False
        self._num_hover   = -1
        self._frames_over = 0
        self._frames_conf = 25          # ~1.5 seg a 20 fps
        self._zonas       = {}
        self._SW          = SW
        self._SH          = SH

        self._build_ui(SW, SH)

    def _build_ui(self, SW, SH):
        self._canvas = tk.Canvas(self, bg='#0D1117',
                                  bd=0, highlightthickness=0)
        self._canvas.pack(fill='both', expand=True)

        N      = 5
        margen = 60
        esp    = (SW - margen * 2) // N
        cy     = SH // 2
        alto   = 260

        for i, num in enumerate(range(1, 6)):
            x1 = margen + i * esp
            x2 = x1 + esp - 20
            y1 = cy - alto // 2
            y2 = cy + alto // 2
            self._zonas[num] = (x1, y1, x2, y2)

        self._canvas.create_text(
            SW // 2, 55,
            text='Senala con el dedo indice el numero que quieres',
            fill='#00D4AA',
            font=('Helvetica', 22, 'bold'),
            anchor='center')

        self._canvas.create_text(
            SW // 2, 100,
            text='Manten el dedo 1.5 segundos sobre el numero',
            fill='#8B949E',
            font=('Helvetica', 14),
            anchor='center')

        self._lbl_estado = tk.Label(
            self, text='Senala un numero',
            fg='#8B949E', bg='#0D1117',
            font=('Helvetica', 18, 'bold'))
        self._lbl_estado.place(x=SW // 2, y=SH - 50, anchor='center')

        tk.Button(self, text='Cancelar',
                  command=self._cancelar,
                  bg='#161B22', fg='#8B949E',
                  font=('Helvetica', 12),
                  bd=0, relief='flat', cursor='hand2',
                  padx=16, pady=8
                  ).place(x=20, y=SH - 60)

        self._dibujar(- 1, 0)

    def _dibujar(self, hover, progreso):
        self._canvas.delete('nums')
        nombres = {1:'uno', 2:'dos', 3:'tres', 4:'cuatro', 5:'cinco'}

        for num, (x1, y1, x2, y2) in self._zonas.items():
            cx = (x1 + x2) // 2
            cy = (y1 + y2) // 2
            es = (num == hover)

            bg  = ('#0D3320' if progreso < 0.5 else '#0D2D00') if es else '#1C2128'
            brd = ('#00D4AA' if progreso < 0.5 else '#3FB950') if es else '#30363D'
            txt = ('#00FF99' if progreso < 0.5 else '#3FB950') if es else '#00D4AA'

            r = 16
            self._canvas.create_rectangle(
                x1+r, y1, x2-r, y2,
                fill=bg, outline='', tags='nums')
            self._canvas.create_rectangle(
                x1, y1+r, x2, y2-r,
                fill=bg, outline='', tags='nums')
            for cx2, cy2 in [
                (x1+r, y1+r), (x2-r, y1+r),
                (x1+r, y2-r), (x2-r, y2-r),
            ]:
                self._canvas.create_oval(
                    cx2-r, cy2-r, cx2+r, cy2+r,
                    fill=bg, outline='', tags='nums')
            self._canvas.create_rectangle(
                x1+1, y1+1, x2-1, y2-1,
                fill='', outline=brd, width=3, tags='nums')

            self._canvas.create_text(
                cx, cy - 20, text=str(num),
                fill=txt,
                font=('Helvetica', 90, 'bold'),
                tags='nums', anchor='center')
            self._canvas.create_text(
                cx, cy + 70, text=nombres[num],
                fill=brd if not es else txt,
                font=('Helvetica', 16),
                tags='nums', anchor='center')

            if es and progreso > 0:
                bw = int((x2 - x1 - 20) * progreso)
                self._canvas.create_rectangle(
                    x1+10, y2-30, x1+10+bw, y2-10,
                    fill=brd, outline='', tags='nums')
                self._canvas.create_rectangle(
                    x1+10, y2-30, x2-10, y2-10,
                    fill='', outline='#30363D',
                    width=1, tags='nums')
                self._canvas.create_text(
                    cx, y2-20,
                    text=f'{int(progreso*100)}%',
                    fill='white',
                    font=('Helvetica', 11, 'bold'),
                    tags='nums', anchor='center')

    def procesar_frame(self, res, frame_w, frame_h):
        """
        Llamado desde el loop principal de camara con cada frame.
        Detecta donde apunta el dedo y confirma si se mantiene.
        Retorna True cuando confirma una seleccion.
        """
        if self._confirmado:
            return True

        punta         = obtener_punta_indice(res, frame_w, frame_h)
        esta_senalando= indice_apuntando(res)
        num_sel       = -1

        if punta and esta_senalando:
            px, py = punta
            sx = int(px / frame_w * self._SW)
            sy = int(py / frame_h * self._SH)

            for num, (x1, y1, x2, y2) in self._zonas.items():
                if x1 <= sx <= x2 and y1 <= sy <= y2:
                    num_sel = num
                    break

            try:
                self._canvas.delete('cursor')
                r = 24
                self._canvas.create_oval(
                    sx-r, sy-r, sx+r, sy+r,
                    fill='#00D4AA', outline='white',
                    width=3, tags='cursor')
            except Exception:
                pass
        else:
            try:
                self._canvas.delete('cursor')
            except Exception:
                pass

        if num_sel >= 1:
            if num_sel == self._num_hover:
                self._frames_over += 1
            else:
                self._frames_over = 0
                self._num_hover   = num_sel

            progreso = min(self._frames_over / self._frames_conf, 1.0)

            try:
                self._dibujar(num_sel, progreso)
                self._lbl_estado.config(
                    text=f'Senalando: {num_sel}  —  {int(progreso*100)}%',
                    fg='#FF6B35' if progreso > 0.5 else '#00D4AA')
            except Exception:
                pass

            if self._frames_over >= self._frames_conf:
                self._confirmado = True
                nombres = {1:'uno', 2:'dos', 3:'tres',
                           4:'cuatro', 5:'cinco'}
                nombre  = nombres.get(num_sel, str(num_sel))
                try:
                    self._dibujar(num_sel, 1.0)
                    self._lbl_estado.config(
                        text=f'CONFIRMADO: {num_sel} ({nombre})',
                        fg='#3FB950')
                except Exception:
                    pass
                if self._callback:
                    self._callback(num_sel, nombre)
                # Cerrar ventana inmediatamente
                self.after(0, self.cerrar)
                return True
        else:
            if self._num_hover != -1:
                self._num_hover   = -1
                self._frames_over = 0
                try:
                    self._dibujar(-1, 0)
                    self._lbl_estado.config(
                        text='Senala un numero con el dedo indice',
                        fg='#8B949E')
                except Exception:
                    pass

        return False

    def _cancelar(self):
        self._confirmado = True
        if self._callback:
            self._callback(-1, '')
        try:
            self.destroy()
        except Exception:
            pass

    def cerrar(self):
        try:
            self.destroy()
        except Exception:
            pass


# ================================================================
#  APLICACION PRINCIPAL
# ================================================================
class GestureCommApp:

    def __init__(self):
        self.root = tk.Tk()
        self.root.title('GestureComm')
        self.root.configure(bg=COLOR_BG)
        self.root.resizable(False, False)

        self._q = queue.Queue()

        self.detector = DetectorMano()
        self.rec      = ReconocedorGestos()
        self.tts      = SintesisVoz()
        self.stt      = ReconocimientoVoz()

        self._estado        = Estado.INICIANDO
        self._post_cantidad = False

        self._cap    = None
        self._activo = False

        # Ventanas flotantes
        self._win_prod   = None
        self._win_texto  = None
        self._overlay_num= None   # OverlayNumeros — NO tiene camara propia

        self._build_ui()
        self._cargar_modelo()
        self._init_cam()
        self.root.after(33, self._tick_ui)

    # ════════════════════════════════════════════════════════════
    #  UI
    # ════════════════════════════════════════════════════════════
    def _build_ui(self):
        FT    = tkfont.Font
        W, H  = FRAME_WIDTH, FRAME_HEIGHT
        PW, P = 390, 14
        self.root.geometry(f'{W+PW+P*3}x{H+P*2+54}')

        self.fBig  = FT(family='Helvetica', size=15, weight='bold')
        self.fLbl  = FT(family='Helvetica', size=10, weight='bold')
        self.fTxt  = FT(family='Helvetica', size=12)
        self.fSm   = FT(family='Helvetica', size=9)
        self.fMono = FT(family='Courier',   size=9)

        hdr = tk.Frame(self.root, bg=COLOR_SURFACE, height=50)
        hdr.pack(fill='x'); hdr.pack_propagate(False)
        tk.Label(hdr, text='●', fg=COLOR_ACCENT, bg=COLOR_SURFACE,
                 font=FT(size=15)).pack(side='left', padx=(16,6), pady=6)
        tk.Label(hdr,
                 text='GESTURECOMM  —  Sistema de Comunicacion por Gestos',
                 fg=COLOR_TEXT, bg=COLOR_SURFACE,
                 font=self.fLbl).pack(side='left')
        self._lbl_est = tk.Label(hdr, text='INICIANDO...',
                                  fg=COLOR_WARNING, bg=COLOR_SURFACE,
                                  font=self.fSm)
        self._lbl_est.pack(side='right', padx=16)

        body = tk.Frame(self.root, bg=COLOR_BG)
        body.pack(fill='both', expand=True, padx=P, pady=(P, 0))

        cw = tk.Frame(body, bg=COLOR_BORDER, bd=1, relief='solid')
        cw.pack(side='left', anchor='n')
        self._lbl_cam = tk.Label(cw, bg='#000', width=W, height=H)
        self._lbl_cam.pack()

        pan = tk.Frame(body, bg=COLOR_BG)
        pan.pack(side='left', fill='both', expand=True,
                 padx=(P, 0), anchor='n')

        cc = self._card(pan, 'CLIENTE', '👋', COLOR_ACCENT)
        cc.pack(fill='x', pady=(0, 8))
        ic = cc._in
        rg = tk.Frame(ic, bg=COLOR_CARD)
        rg.pack(fill='x', pady=(4, 2))
        self._lbl_gesto = tk.Label(rg, text='—',
                                    fg=COLOR_ACCENT, bg=COLOR_CARD,
                                    font=self.fBig, anchor='w')
        self._lbl_gesto.pack(side='left')
        self._lbl_mini = tk.Label(rg, bg=COLOR_CARD)
        self._lbl_mini.pack(side='right')
        self._lbl_msg = tk.Label(ic,
                                  text='Realiza un gesto frente a la camara.',
                                  fg=COLOR_TEXT_DIM, bg=COLOR_CARD,
                                  font=self.fTxt, anchor='w',
                                  wraplength=PW-40, justify='left')
        self._lbl_msg.pack(fill='x')
        self._cnv_conf = tk.Canvas(ic, height=6, bg=COLOR_SURFACE,
                                    bd=0, highlightthickness=0)
        self._cnv_conf.pack(fill='x', pady=(6, 0))

        rt = tk.Frame(ic, bg=COLOR_CARD)
        rt.pack(fill='x', pady=(8, 0))
        self._countdown = CuentaRegresivaWidget(
            rt, segundos=5,
            callback_fin=self._iniciar_escucha_real)
        self._countdown.pack(side='left')
        inf = tk.Frame(rt, bg=COLOR_CARD)
        inf.pack(side='left', fill='x', expand=True, padx=(12, 0))
        self._lbl_fase = tk.Label(inf, text='',
                                   fg=COLOR_TEXT_DIM, bg=COLOR_CARD,
                                   font=self.fLbl, anchor='w')
        self._lbl_fase.pack(fill='x')
        self._lbl_sub = tk.Label(inf, text='',
                                  fg=COLOR_TEXT_DIM, bg=COLOR_CARD,
                                  font=self.fSm, anchor='w',
                                  wraplength=260)
        self._lbl_sub.pack(fill='x')

        cv_ = self._card(pan, 'VENDEDOR', '🎙', COLOR_ACCENT2)
        cv_.pack(fill='x', pady=(0, 8))
        self._lbl_resp = tk.Label(cv_._in, text='—',
                                   fg=COLOR_ACCENT2, bg=COLOR_CARD,
                                   font=self.fTxt, anchor='w',
                                   wraplength=PW-40, justify='left')
        self._lbl_resp.pack(fill='x', pady=(4, 0))

        ch = self._card(pan, 'HISTORIAL', '📋', COLOR_TEXT_DIM)
        ch.pack(fill='both', expand=True, pady=(0, 8))
        self._hist = tk.Text(ch._in, bg=COLOR_SURFACE, fg=COLOR_TEXT,
                              font=self.fMono, bd=0, relief='flat',
                              state='disabled', height=7, wrap='word')
        self._hist.pack(fill='both', expand=True)
        self._hist.tag_config('cliente',  foreground=COLOR_ACCENT)
        self._hist.tag_config('vendedor', foreground=COLOR_ACCENT2)
        self._hist.tag_config('sistema',  foreground=COLOR_TEXT_DIM)
        self._hist.tag_config('cantidad', foreground=COLOR_GOLD)

        br = tk.Frame(pan, bg=COLOR_BG)
        br.pack(fill='x', pady=(0, P))
        self._btn(br, '🎙  VENDEDOR HABLA',
                  self._escucha_manual, COLOR_ACCENT2
                  ).pack(side='left', fill='x', expand=True, padx=(0, 6))
        self._btn(br, '🖼  VER MENU',
                  self._mostrar_menu_manual, COLOR_GOLD
                  ).pack(side='left', padx=(0, 6))
        self._btn(br, '🗑  LIMPIAR',
                  self._limpiar, COLOR_TEXT_DIM).pack(side='left')

        sb = tk.Frame(self.root, bg=COLOR_SURFACE, height=26)
        sb.pack(fill='x', side='bottom'); sb.pack_propagate(False)
        self._lbl_status = tk.Label(sb, text='',
                                     fg=COLOR_TEXT_DIM,
                                     bg=COLOR_SURFACE, font=self.fSm)
        self._lbl_status.pack(side='left', padx=10)
        self._lbl_fps = tk.Label(sb, text='FPS: —',
                                  fg=COLOR_TEXT_DIM,
                                  bg=COLOR_SURFACE, font=self.fSm)
        self._lbl_fps.pack(side='right', padx=10)

    def _card(self, parent, titulo, icono, color):
        f = tk.Frame(parent, bg=COLOR_CARD,
                     highlightbackground=COLOR_BORDER,
                     highlightthickness=1)
        h = tk.Frame(f, bg=COLOR_SURFACE); h.pack(fill='x')
        tk.Label(h, text=f'  {icono}  {titulo}',
                 fg=color, bg=COLOR_SURFACE,
                 font=self.fLbl, anchor='w'
                 ).pack(side='left', padx=8, pady=6)
        inner = tk.Frame(f, bg=COLOR_CARD)
        inner.pack(fill='both', expand=True, padx=12, pady=8)
        f._in = inner; return f

    def _btn(self, parent, txt, cmd, fg):
        b = tk.Button(parent, text=txt, command=cmd,
                      bg=COLOR_SURFACE, fg=fg,
                      activebackground=COLOR_CARD,
                      activeforeground=fg,
                      font=self.fSm, bd=0, relief='flat',
                      cursor='hand2', padx=10, pady=8)
        b.bind('<Enter>', lambda e: b.config(bg=COLOR_CARD))
        b.bind('<Leave>', lambda e: b.config(bg=COLOR_SURFACE))
        return b

    # ════════════════════════════════════════════════════════════
    #  CAMARA UNICA — hace todo
    # ════════════════════════════════════════════════════════════
    def _init_cam(self):
        self._cap = cv2.VideoCapture(CAMERA_INDEX)
        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH,  FRAME_WIDTH)
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
        self._activo = True
        threading.Thread(target=self._loop_cam, daemon=True).start()

    def _loop_cam(self):
        t0 = time.time(); fn = 0

        while self._activo:
            ret, frame = self._cap.read()
            if not ret:
                continue
            frame = cv2.flip(frame, 1)
            frame, res = self.detector.procesar_frame(frame)
            lm         = self.detector.extraer_landmarks(res)
            frame      = self.detector.dibujar_landmarks(frame, res)

            estado = self._estado   # leer una vez por frame

            if estado == Estado.ESPERANDO_CLIENTE:
                # Modo normal: reconocer gestos
                if self.rec.listo and lm is not None:
                    g, c = self.rec.predecir(lm)
                    if g:
                        self._q.put(('gesto', g, c))
                    top = self.rec.todas_las_probs(lm)
                    if top:
                        self._q.put(('conf', top[0][1]))

            elif estado == Estado.ELIGIENDO_CANTIDAD:
                # Modo selector: pasar frame al overlay
                overlay = self._overlay_num
                if overlay is not None:
                    try:
                        confirmado = overlay.procesar_frame(
                            res, FRAME_WIDTH, FRAME_HEIGHT)
                        if confirmado:
                            self._overlay_num = None
                    except Exception:
                        pass

            # HUD
            self._dibujar_hud(frame, lm, estado)

            # Enviar frame a UI principal
            rgb   = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            imgtk = ImageTk.PhotoImage(image=Image.fromarray(rgb))
            self._q.put(('frame', imgtk))

            fn += 1
            if time.time() - t0 >= 1.0:
                self._q.put(('fps', fn))
                fn = 0; t0 = time.time()

    def _dibujar_hud(self, frame, lm, estado):
        info = {
            Estado.INICIANDO:           ('INICIANDO',        (200, 200, 0)),
            Estado.ESPERANDO_CLIENTE:   ('EN ESPERA',        (0, 212, 170)),
            Estado.HABLANDO:            ('HABLANDO...',      (255, 200, 0)),
            Estado.CUENTA_REGRESIVA:    ('PREPARATE...',     (255, 107, 53)),
            Estado.ESCUCHANDO:          ('ESCUCHANDO',       (255, 107, 53)),
            Estado.MOSTRANDO_RESPUESTA: ('RESPUESTA LISTA',  (63, 185, 80)),
            Estado.ELIGIENDO_CANTIDAD:  ('SENALA NUMERO',    (255, 215, 0)),
            Estado.ERROR:               ('ERROR',            (248, 81, 73)),
        }
        txt, col = info.get(estado, ('—', (255, 255, 255)))
        cv2.putText(frame, txt, (10, 26),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.58, col, 2, cv2.LINE_AA)
        dot = (0, 212, 170) if lm is not None else (80, 80, 80)
        cv2.circle(frame, (FRAME_WIDTH-22, 22), 7, dot, -1)

    # ════════════════════════════════════════════════════════════
    #  COLA UI
    # ════════════════════════════════════════════════════════════
    def _tick_ui(self):
        try:
            while True:
                ev = self._q.get_nowait()
                t  = ev[0]
                if   t == 'frame':
                    self._lbl_cam.configure(image=ev[1])
                    self._lbl_cam.image = ev[1]
                elif t == 'fps':
                    self._lbl_fps.config(text=f'FPS: {ev[1]}')
                elif t == 'gesto':
                    self._on_gesto(ev[1], ev[2])
                elif t == 'conf':
                    self._update_conf(ev[1])
                elif t == 'stt':
                    self._on_respuesta(ev[1])
                elif t == 'status':
                    self._lbl_status.config(text=ev[1])
                elif t == 'set_estado':
                    self._set_estado(ev[1])
                elif t == 'fase':
                    self._lbl_fase.config(text=ev[1], fg=ev[2])
                elif t == 'sub':
                    self._lbl_sub.config(text=ev[1])
                elif t == 'countdown_start':
                    self._countdown.iniciar()
                elif t == 'countdown_stop':
                    self._countdown.detener()
                elif t == 'mini_img':
                    self._mostrar_mini(ev[1])
                elif t == 'clear_mini':
                    self._lbl_mini.config(image='')
                    self._lbl_mini.image = None
                elif t == 'texto_grande':
                    self._abrir_texto_grande(ev[1])
                elif t == 'abrir_cantidad':
                    self._abrir_selector_cantidad()
                elif t == 'cantidad_elegida':
                    self._procesar_cantidad(ev[1], ev[2], ev[3])
                elif t == 'reset':
                    self._hacer_reset()
        except queue.Empty:
            pass
        finally:
            self.root.after(33, self._tick_ui)

    # ════════════════════════════════════════════════════════════
    #  LOGICA
    # ════════════════════════════════════════════════════════════
    def _cargar_modelo(self):
        def _r():
            self._q.put(('status', 'Cargando modelo...'))
            ok = self.rec.cargar()
            if ok:
                self._q.put(('set_estado', Estado.ESPERANDO_CLIENTE))
                self._q.put(('status',
                             'Modelo listo  ·  Realiza un gesto'))
            else:
                self._q.put(('set_estado', Estado.ERROR))
                self._q.put(('status', 'Modelo no encontrado'))
        threading.Thread(target=_r, daemon=True).start()

    def _on_gesto(self, gesto, conf):
        if self._estado != Estado.ESPERANDO_CLIENTE:
            return
        self._set_estado(Estado.HABLANDO)
        msg      = self.rec.obtener_mensaje(gesto)
        ruta     = IMAGEN_GESTO.get(gesto)
        tiene_img= (gesto in GESTOS_CON_IMAGEN
                    and ruta and os.path.exists(ruta))

        self._lbl_gesto.config(
            text=f'GESTO: {gesto.upper()}', fg=COLOR_ACCENT)
        self._lbl_msg.config(text=msg, fg=COLOR_TEXT)
        self._update_conf(conf)
        self._log('cliente', f'[{gesto.upper()}] {msg}')
        if tiene_img:
            self._mostrar_mini(ruta)

        def _flujo():
            self._q.put(('fase', 'Reproduciendo...', COLOR_GOLD))
            self._q.put(('sub', msg))
            self._q.put(('status', f'Hablando: {msg}'))
            self.tts.hablar(msg)
            if tiene_img:
                self.root.after(300, lambda: self._abrir_popup(
                    gesto, gesto.capitalize(), ruta))
            time.sleep(max(1.5, len(msg) * 0.065))
            self._q.put(('set_estado', Estado.CUENTA_REGRESIVA))
            self._q.put(('fase', 'Preparate vendedor...', COLOR_ACCENT2))
            self._q.put(('sub', 'Tienes 5 segundos para responder'))
            self._q.put(('status', 'Esperando vendedor...'))
            self._q.put(('countdown_start', None))
        threading.Thread(target=_flujo, daemon=True).start()

    def _iniciar_escucha_real(self):
        self._set_estado(Estado.ESCUCHANDO)
        self._lbl_fase.config(
            text='Escuchando al vendedor...', fg=COLOR_ACCENT2)
        self._lbl_sub.config(text='Habla ahora — 8 segundos')
        self._lbl_status.config(text='Escuchando...')
        self.stt.escuchar_async(
            lambda txt: self._q.put(('stt', txt)))

    def _on_respuesta(self, texto):
        self._q.put(('countdown_stop', None))

        if texto:
            texto_lower = texto.lower().strip()
            print(f'\n>>> VENDEDOR: "{texto}"')

            self._lbl_resp.config(text=texto, fg=COLOR_ACCENT2)
            self._log('vendedor', texto)
            self._lbl_status.config(text='Respuesta recibida')
            self._lbl_fase.config(
                text='Vendedor dijo:', fg=COLOR_ACCENT2)
            self._lbl_sub.config(text=texto[:80])
            self._abrir_texto_grande(texto)

            # Palabras que activan el selector de cantidad
            palabras = [
                'cuantos', 'cuantas', 'cuanto', 'cuanta',
                'cantidad', 'necesitas', 'deseas',
                'cuantas quieres', 'cuantas necesitas',
                'cuantos quieres', 'cuantos necesitas',
                'que cantidad', 'cuantas unidades',
            ]
            # Palabras que confirman y cierran el flujo
            palabras_ok = [
                'ok', 'listo', 'dale', 'claro', 'perfecto',
                'de acuerdo', 'bien', 'ya', 'voy', 'traigo',
                'enseguida', 'ahorita', 'momento', 'espera',
            ]

            es_cantidad = (
                any(p in texto_lower for p in palabras)
                and not self._post_cantidad
            )
            es_ok = any(p in texto_lower for p in palabras_ok)

            print(f'>>> CANTIDAD={es_cantidad} '
                  f'OK={es_ok} POST={self._post_cantidad}')

            if es_cantidad:
                self._set_estado(Estado.ELIGIENDO_CANTIDAD)
                self.root.after(2000, lambda: self._q.put(
                    ('abrir_cantidad', None)))
            elif es_ok and self._post_cantidad:
                # Vendedor confirmo — resetear directamente
                print('>>> Vendedor confirmo con ok/listo — reseteando')
                self._post_cantidad = False
                self._set_estado(Estado.MOSTRANDO_RESPUESTA)
                self.root.after(3000, lambda: self._q.put(('reset', None)))
            else:
                if self._post_cantidad:
                    self._post_cantidad = False
                self._set_estado(Estado.MOSTRANDO_RESPUESTA)
                self.root.after(4000, lambda: self._q.put(('reset', None)))
        else:
            self._lbl_resp.config(
                text='No se entendio — intenta de nuevo.',
                fg=COLOR_TEXT_DIM)
            self._log('sistema', '— Sin respuesta —')
            self._lbl_fase.config(text='Sin respuesta', fg=COLOR_TEXT_DIM)
            self._set_estado(Estado.MOSTRANDO_RESPUESTA)
            self.root.after(4000, lambda: self._q.put(('reset', None)))

    def _abrir_selector_cantidad(self):
        """Crea el overlay de numeros — SIN camara propia."""
        try:
            if self._overlay_num and self._overlay_num.winfo_exists():
                self._overlay_num.cerrar()
        except Exception:
            pass

        self._set_estado(Estado.ELIGIENDO_CANTIDAD)
        self._lbl_fase.config(
            text='Senala el numero con el dedo', fg=COLOR_GOLD)
        self._lbl_sub.config(
            text='Apunta con el indice al numero en la pantalla')

        # Callback del overlay → encola para hilo principal
        def _cb(numero, nombre):
            if numero > 0:
                msg = f'Quiero {numero}, {nombre} por favor'
                self._q.put(('cantidad_elegida', numero, nombre, msg))
            else:
                # Cancelado — reset
                self._q.put(('reset', None))

        self._overlay_num = OverlayNumeros(self.root, _cb)

    def _procesar_cantidad(self, numero, nombre, msg):
        """Ejecutado en hilo principal."""
        print(f'>>> CANTIDAD: {numero} ({nombre})')

        # Cerrar overlay
        try:
            if self._overlay_num and self._overlay_num.winfo_exists():
                self._overlay_num.cerrar()
        except Exception:
            pass
        self._overlay_num = None

        self._lbl_resp.config(
            text=f'Cliente eligio: {numero} ({nombre})',
            fg=COLOR_GOLD)
        self._log('cantidad',
                  f'Cantidad senalada con dedo: {numero} ({nombre})')
        self._lbl_fase.config(
            text=f'Elegiste {numero} — {nombre}', fg=COLOR_GOLD)
        self._lbl_sub.config(
            text='Esperando respuesta del vendedor...')
        self._lbl_status.config(text=f'Cantidad: {numero}')

        self._post_cantidad = True

        def _flujo():
            self.tts.hablar(msg)
            time.sleep(max(1.5, len(msg) * 0.07))
            self._q.put(('set_estado', Estado.CUENTA_REGRESIVA))
            self._q.put(('fase', 'Preparate vendedor...', COLOR_ACCENT2))
            self._q.put(('sub', 'Responde al cliente'))
            self._q.put(('status', 'Esperando respuesta final...'))
            self._q.put(('countdown_start', None))
        threading.Thread(target=_flujo, daemon=True).start()

    # ════════════════════════════════════════════════════════════
    #  RESET UNICO
    # ════════════════════════════════════════════════════════════
    def _hacer_reset(self):
        """Reset completo. Solo corre en hilo principal via cola."""
        print('>>> RESET → EN ESPERA')
        self._post_cantidad = False

        # Cerrar overlay de numeros
        try:
            if self._overlay_num and self._overlay_num.winfo_exists():
                self._overlay_num.cerrar()
        except Exception:
            pass
        self._overlay_num = None

        # Cerrar ventanas flotantes
        for attr in ['_win_prod', '_win_texto']:
            try:
                w = getattr(self, attr, None)
                if w and w.winfo_exists():
                    w.destroy()
            except Exception:
                pass

        # Resetear estado
        self._estado = Estado.ESPERANDO_CLIENTE
        self._lbl_est.config(text='EN ESPERA', fg=COLOR_SUCCESS)
        self._lbl_fase.config(text='', fg=COLOR_TEXT_DIM)
        self._lbl_sub.config(text='')
        self._lbl_status.config(
            text='Modelo listo  ·  Realiza un gesto')
        self._countdown.detener()
        self._cnv_conf.delete('all')
        try:
            self._lbl_mini.config(image='')
            self._lbl_mini.image = None
        except Exception:
            pass
        self.rec.resetear()
        print('>>> Listo para nuevo gesto')

    # ════════════════════════════════════════════════════════════
    #  HELPERS
    # ════════════════════════════════════════════════════════════
    def _set_estado(self, e):
        self._estado = e
        info = {
            Estado.INICIANDO:           ('INICIANDO...',   COLOR_WARNING),
            Estado.ESPERANDO_CLIENTE:   ('EN ESPERA',      COLOR_SUCCESS),
            Estado.HABLANDO:            ('HABLANDO',       COLOR_GOLD),
            Estado.CUENTA_REGRESIVA:    ('PREPARATE',      COLOR_ACCENT2),
            Estado.ESCUCHANDO:          ('ESCUCHANDO',     COLOR_ACCENT2),
            Estado.MOSTRANDO_RESPUESTA: ('RESPUESTA',      COLOR_SUCCESS),
            Estado.ELIGIENDO_CANTIDAD:  ('SENALA NUMERO',  COLOR_GOLD),
            Estado.ERROR:               ('ERROR',          COLOR_ERROR),
        }
        txt, col = info.get(e, ('—', COLOR_TEXT_DIM))
        self._lbl_est.config(text=txt, fg=col)

    def _update_conf(self, conf):
        self._cnv_conf.update_idletasks()
        w = self._cnv_conf.winfo_width() or 300
        self._cnv_conf.delete('all')
        p   = max(0.0, min(float(conf), 1.0))
        col = (COLOR_SUCCESS if p > 0.90
               else COLOR_WARNING if p > 0.75
               else COLOR_ERROR)
        self._cnv_conf.create_rectangle(
            0, 0, int(w*p), 6, fill=col, outline='')

    def _log(self, rol, txt):
        ts = time.strftime('%H:%M:%S')
        self._hist.config(state='normal')
        self._hist.insert('end', f'[{ts}] {txt}\n', rol)
        self._hist.see('end')
        self._hist.config(state='disabled')

    def _mostrar_mini(self, ruta):
        try:
            img = Image.open(ruta).resize((70, 58), Image.LANCZOS)
            tk_img = ImageTk.PhotoImage(img)
            self._lbl_mini.config(image=tk_img)
            self._lbl_mini.image = tk_img
        except Exception:
            pass

    def _abrir_texto_grande(self, texto):
        try:
            if self._win_texto and self._win_texto.winfo_exists():
                self._win_texto.destroy()
        except Exception:
            pass
        self._win_texto = VentanaTextoGrande(self.root, texto)

    def _abrir_popup(self, gesto, titulo, ruta):
        try:
            if self._win_prod and self._win_prod.winfo_exists():
                self._win_prod.destroy()
        except Exception:
            pass
        self._win_prod = VentanaProducto(self.root, gesto, titulo, ruta)

    def _mostrar_menu_manual(self):
        ruta = IMAGEN_GESTO.get('menu', '')
        if ruta and os.path.exists(ruta):
            self._abrir_popup('menu', 'Menu', ruta)

    def _escucha_manual(self):
        if self._estado in (Estado.ESPERANDO_CLIENTE,
                             Estado.MOSTRANDO_RESPUESTA):
            self._set_estado(Estado.ESCUCHANDO)
            self._lbl_fase.config(
                text='Escuchando al vendedor...', fg=COLOR_ACCENT2)
            self._lbl_sub.config(text='Habla ahora — 8 segundos')
            self._lbl_status.config(text='Escuchando...')
            self.stt.escuchar_async(
                lambda txt: self._q.put(('stt', txt)))

    def _limpiar(self):
        self._hacer_reset()
        self._lbl_gesto.config(text='—', fg=COLOR_ACCENT)
        self._lbl_msg.config(
            text='Realiza un gesto frente a la camara.',
            fg=COLOR_TEXT_DIM)
        self._lbl_resp.config(text='—', fg=COLOR_ACCENT2)
        self._hist.config(state='normal')
        self._hist.delete('1.0', 'end')
        self._hist.config(state='disabled')
        self._lbl_status.config(text='Pantalla limpiada')

    def run(self):
        self.root.protocol('WM_DELETE_WINDOW', self._close)
        self.root.mainloop()

    def _close(self):
        self._activo = False
        if self._cap:
            self._cap.release()
        self.tts.detener()
        self.root.destroy()


if __name__ == '__main__':
    GestureCommApp().run()