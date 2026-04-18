# ============================================================
#  reconocer_gestos.py  —  Test en tiempo real (sin GUI)
# ============================================================
import cv2, numpy as np, time
from config import CAMERA_INDEX, FRAME_WIDTH, FRAME_HEIGHT
from utils.detector_mano import DetectorMano
from core.reconocedor    import ReconocedorGestos

def hex2bgr(h):
    h=h.lstrip('#'); return (int(h[4:6],16),int(h[2:4],16),int(h[0:2],16))

CYAN=hex2bgr('#00D4AA'); ORANGE=hex2bgr('#FF6B35'); GREEN=hex2bgr('#3FB950')
GRAY=(110,110,110); WHITE=(220,220,220); DARK=(22,27,34)

def main():
    det = DetectorMano(); rec = ReconocedorGestos()
    print('\n'+'═'*50+'\n  TEST RECONOCIMIENTO  |  Q=salir\n'+'═'*50)
    if not rec.cargar():
        print('\n  ✗ Modelo no encontrado.\n  Ejecuta: python entrenar_modelo.py\n'); return
    print('  ✓ Modelo listo\n')

    cap=cv2.VideoCapture(CAMERA_INDEX)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
    t0=time.time(); fps_n=0; fps_v=0

    while True:
        ret,frame=cap.read()
        if not ret: continue
        frame=cv2.flip(frame,1)
        frame,res=det.procesar_frame(frame)
        lm=det.extraer_landmarks(res)
        frame=det.dibujar_landmarks(frame,res)

        W=FRAME_WIDTH
        panel=np.full((205,W,3),DARK,np.uint8)

        if lm is not None and rec.listo:
            top=rec.todas_las_probs(lm) or []
            for i,(g,p) in enumerate(top[:7]):
                y=26+i*26
                bw=int((W-200)*p)
                col=CYAN if i==0 else (50,70,70)
                cv2.rectangle(panel,(140,y-13),(140+bw,y+4),col,-1)
                cv2.putText(panel,f'{g:12s}',(5,y),cv2.FONT_HERSHEY_SIMPLEX,0.46,(200,200,200),1)
                cv2.putText(panel,f'{p*100:5.1f}%',(W-62,y),cv2.FONT_HERSHEY_SIMPLEX,0.46,(150,150,150),1)
            gesto,conf=rec.predecir(lm)
            if gesto:
                msg=rec.obtener_mensaje(gesto)
                cv2.putText(panel,f'→ {gesto.upper()} ({conf*100:.0f}%)',(5,195),
                            cv2.FONT_HERSHEY_SIMPLEX,0.65,CYAN,2)
                print(f'  [{time.strftime("%H:%M:%S")}]  {gesto} ({conf*100:.0f}%)  →  {msg}')
        else:
            cv2.putText(panel,'Sin mano',(15,100),cv2.FONT_HERSHEY_SIMPLEX,0.6,GRAY,1)

        fps_n+=1
        if time.time()-t0>=1.0:
            fps_v=fps_n; fps_n=0; t0=time.time()
        cv2.putText(frame,f'FPS {fps_v}',(W-75,24),cv2.FONT_HERSHEY_SIMPLEX,0.5,GRAY,1)

        cv2.imshow('Test Gestos  |  Q=salir',np.vstack([panel,frame]))
        if cv2.waitKey(1)&0xFF==ord('q'): break

    cap.release(); cv2.destroyAllWindows()

if __name__=='__main__': main()
