# ================================================================
#  utils/detector_mano.py — MediaPipe wrapper
# ================================================================
import cv2, mediapipe as mp, numpy as np
from typing import Optional

class DetectorMano:
    def __init__(self, min_det=0.70, min_track=0.70):
        self.mp_h = mp.solutions.hands
        self.mp_d = mp.solutions.drawing_utils
        self.hands = self.mp_h.Hands(
            static_image_mode=False, max_num_hands=1,
            min_detection_confidence=min_det,
            min_tracking_confidence=min_track)
        self._lm = self.mp_d.DrawingSpec(color=(0,212,170), thickness=2, circle_radius=3)
        self._cn = self.mp_d.DrawingSpec(color=(255,107,53), thickness=2)

    def procesar_frame(self, frame):
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        rgb.flags.writeable = False
        res = self.hands.process(rgb)
        rgb.flags.writeable = True
        return frame, res

    def dibujar_landmarks(self, frame, res):
        if res.multi_hand_landmarks:
            for lm in res.multi_hand_landmarks:
                self.mp_d.draw_landmarks(frame, lm, self.mp_h.HAND_CONNECTIONS, self._lm, self._cn)
        return frame

    def extraer_landmarks(self, res) -> Optional[np.ndarray]:
        if not res.multi_hand_landmarks:
            return None
        hand = res.multi_hand_landmarks[0]
        pts  = [(lm.x, lm.y, lm.z) for lm in hand.landmark]
        ox,oy,oz = pts[0]
        norm = [(x-ox, y-oy, z-oz) for x,y,z in pts]
        md   = max(np.sqrt(x**2+y**2+z**2) for x,y,z in norm) or 1.0
        flat = []
        for x,y,z in norm:
            flat.extend([x/md, y/md, z/md])
        return np.array(flat, dtype=np.float32)

    def hay_mano(self, res): return res.multi_hand_landmarks is not None

    def __del__(self):
        try: self.hands.close()
        except: pass
