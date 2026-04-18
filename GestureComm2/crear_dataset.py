# ============================================================
#  crear_dataset.py  —  Captura el dataset de los 9 gestos
# ============================================================
"""
CONTROLES:
  ESPACIO → captura manual (1 muestra)
  A       → toggle captura automática (cada 300 ms)
  N / P   → siguiente / anterior gesto
  R       → reiniciar conteo de este gesto
  Q       → guardar y salir

GUÍA DE GESTOS (mantén la mano frente a la cámara):
  hola      → 5 dedos extendidos (saludo)
  comprar   → pulgar arriba 👍
  gracias   → palma abierta hacia afuera
  ayuda     → puño cerrado ✊
  menu      → solo índice apuntando arriba ☝
  papas     → dos dedos (✌)
  dulces    → tres dedos (índice + medio + anular)
  bebidas   → cuatro dedos (sin pulgar)
  chocolate → solo meñique extendido
"""
import cv2, csv, os, time
import numpy as np
from config import GESTOS, DATASET_FILE, MUESTRAS_OBJ, CAMERA_INDEX, FRAME_WIDTH, FRAME_HEIGHT
from utils.detector_mano import DetectorMano

GUIA = {
    "hola":      "5 dedos extendidos  —  saludo",
    "comprar":   "Pulgar arriba  👍",
    "gracias":   "Palma abierta hacia afuera",
    "ayuda":     "Puno cerrado  ✊",
    "menu":      "Solo indice arriba  ☝",
    "papas":     "Dos dedos  ✌",
    "dulces":    "Tres dedos (indice, medio, anular)",
    "bebidas":   "Cuatro dedos (sin pulgar)",
    "chocolate": "Solo menique extendido",
}

def hex2bgr(h):
    h=h.lstrip('#'); return (int(h[4:6],16),int(h[2:4],16),int(h[0:2],16))

CYAN   = hex2bgr('#00D4AA'); ORANGE = hex2bgr('#FF6B35')
GREEN  = hex2bgr('#3FB950'); RED    = hex2bgr('#F85149')
WHITE  = (230,230,230);      GRAY   = (110,110,110)
DARK   = (22,27,34)

def put(img,t,pos,s=0.55,c=WHITE,g=1):
    cv2.putText(img,t,pos,cv2.FONT_HERSHEY_SIMPLEX,s,c,g,cv2.LINE_AA)

def barra(img,x,y,w,h,v,tot,col):
    p=min(v/max(tot,1),1.0)
    cv2.rectangle(img,(x,y),(x+w,y+h),(45,45,45),-1)
    cv2.rectangle(img,(x,y),(x+int(w*p),y+h),col,-1)
    cv2.rectangle(img,(x,y),(x+w,y+h),GRAY,1)

def cargar_conteos():
    c={g:0 for g in GESTOS}
    if os.path.exists(DATASET_FILE):
        with open(DATASET_FILE) as f:
            r=csv.reader(f); next(r,None)
            for row in r:
                if row and row[-1] in c: c[row[-1]]+=1
    return c

def main():
    os.makedirs(os.path.dirname(DATASET_FILE), exist_ok=True)
    nuevo = not os.path.exists(DATASET_FILE)
    fcsv  = open(DATASET_FILE,'a',newline='')
    wtr   = csv.writer(fcsv)
    if nuevo:
        cab=[f'{e}{i}' for i in range(21) for e in('x','y','z')]
        wtr.writerow(cab+['gesto'])

    det    = DetectorMano()
    cap    = cv2.VideoCapture(CAMERA_INDEX)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)

    cnt    = cargar_conteos()
    idx    = 0; auto = False; t_auto = 0; flash = 0

    print('\n'+'═'*52)
    print('  CAPTURA DE DATASET')
    print('  ESPACIO=manual  A=auto  N/P=gesto  R=reset  Q=salir')
    print('═'*52)

    while True:
        ret,frame = cap.read()
        if not ret: continue
        frame = cv2.flip(frame,1)
        frame,res = det.procesar_frame(frame)
        lm        = det.extraer_landmarks(res)
        frame     = det.dibujar_landmarks(frame,res)

        g   = GESTOS[idx]
        c   = cnt[g]
        ph  = 135
        pan = np.full((ph,FRAME_WIDTH,3),DARK,np.uint8)

        # Nombre gesto grande
        cv2.putText(pan,g.upper(),(14,42),cv2.FONT_HERSHEY_SIMPLEX,1.1,CYAN,2,cv2.LINE_AA)
        put(pan,f'Gesto {idx+1}/{len(GESTOS)}',(14,62),0.45,GRAY)
        put(pan,GUIA.get(g,''),(14,82),0.49,ORANGE)
        barra(pan,14,96,FRAME_WIDTH-130,18,c,MUESTRAS_OBJ,GREEN if c>=MUESTRAS_OBJ else CYAN)
        put(pan,f'{c}/{MUESTRAS_OBJ}',(FRAME_WIDTH-112,111),0.49,WHITE)
        put(pan,'AUTO ON' if auto else 'AUTO OFF',(FRAME_WIDTH-105,80),0.48,GREEN if auto else GRAY)
        if c>=MUESTRAS_OBJ:
            put(pan,'COMPLETADO ✓',(FRAME_WIDTH//2-70,123),0.55,GREEN,2)

        # Flash captura
        if flash>0:
            ov=frame.copy(); cv2.rectangle(ov,(0,0),(FRAME_WIDTH,FRAME_HEIGHT),CYAN,-1)
            cv2.addWeighted(ov,0.15,frame,0.85,0,frame); flash-=1

        # Indicador mano
        col_m = GREEN if det.hay_mano(res) else RED
        put(frame,'MANO OK' if det.hay_mano(res) else 'Sin mano',(12,FRAME_HEIGHT-14),0.48,col_m)

        # Auto captura
        if auto and det.hay_mano(res) and lm is not None:
            if time.time()-t_auto>=0.30:
                wtr.writerow(lm.tolist()+[g]); cnt[g]+=1; t_auto=time.time(); flash=3

        # Mini resumen lateral
        for i,gi in enumerate(GESTOS):
            ci  = cnt[gi]
            col = GREEN if ci>=MUESTRAS_OBJ else (CYAN if gi==g else GRAY)
            mk  = '>' if gi==g else (' ' if ci<MUESTRAS_OBJ else '✓')
            put(frame,f'{mk}{gi[:7]:7s}{ci:3d}',(FRAME_WIDTH-145,18+i*22),0.40,col)

        combined = np.vstack([pan,frame])
        cv2.imshow('Captura Dataset  |  A=auto  N=sig  Q=salir', combined)
        k = cv2.waitKey(1)&0xFF

        if   k==ord('q'): break
        elif k==ord(' '):
            if lm is not None:
                wtr.writerow(lm.tolist()+[g]); cnt[g]+=1; flash=4
                print(f'  + {g}: {cnt[g]}')
            else: print('  ⚠ Sin mano')
        elif k==ord('a'): auto=not auto; print(f'  Auto: {"ON" if auto else "OFF"}')
        elif k==ord('n'): idx=(idx+1)%len(GESTOS);  print(f'  → {GESTOS[idx]}')
        elif k==ord('p'): idx=(idx-1)%len(GESTOS);  print(f'  ← {GESTOS[idx]}')
        elif k==ord('r'): cnt[g]=0; print(f'  Reset: {g}')

    cap.release(); cv2.destroyAllWindows(); fcsv.close()
    print('\n'+'═'*52+'  RESUMEN')
    total=0
    for gi in GESTOS:
        ci=cnt[gi]; total+=ci
        ok='✓' if ci>=MUESTRAS_OBJ else '✗'
        print(f'  {ok} {gi:12s} {ci:3d}/{MUESTRAS_OBJ}  {"█"*(ci*25//MUESTRAS_OBJ)}')
    print(f'\n  Total: {total} muestras  →  python entrenar_modelo.py\n')

if __name__=='__main__': main()
