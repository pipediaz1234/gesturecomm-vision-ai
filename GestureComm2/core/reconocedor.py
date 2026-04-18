import os, time, numpy as np
from collections import deque, Counter
from typing import Optional, Tuple
import logging
from config import (MODEL_FILE, LABEL_FILE, CONFIDENCE_THRESHOLD,
                    SMOOTHING_FRAMES, COOLDOWN_SECONDS, MENSAJES_GESTO)

log = logging.getLogger(__name__)

class ReconocedorGestos:
    def __init__(self):
        self.modelo = None
        self.clases = None
        self._buf = deque(maxlen=SMOOTHING_FRAMES)
        self._ug = None
        self._ut = 0.0
        self._ok = False

    def cargar(self):
        import tensorflow as tf
        keras = tf.keras
        if not os.path.exists(MODEL_FILE):
            log.error(f'Modelo no encontrado: {MODEL_FILE}')
            return False
        if not os.path.exists(LABEL_FILE):
            log.error(f'Etiquetas no encontradas: {LABEL_FILE}')
            return False
        try:
            self.modelo = keras.models.load_model(MODEL_FILE)
            self.clases = np.load(LABEL_FILE, allow_pickle=True)
            self._ok = True
            log.info(f'Modelo OK clases: {list(self.clases)}')
            return True
        except Exception as e:
            log.error(f'Error: {e}')
            return False

    @property
    def listo(self):
        return self._ok

    def predecir(self, lm):
        if not self._ok or lm is None:
            return None, 0.0
        probs = self.modelo.predict(lm.reshape(1,-1).astype(np.float32), verbose=0)[0]
        idx = int(np.argmax(probs))
        conf = float(probs[idx])
        clase = self.clases[idx]
        self._buf.append(clase if conf >= CONFIDENCE_THRESHOLD else None)
        votos = [v for v in self._buf if v is not None]
        if not votos:
            return None, conf
        g, freq = Counter(votos).most_common(1)[0]
        if freq < len(self._buf) * 0.5:
            return None, conf
        ahora = time.time()
        if g == self._ug and ahora - self._ut < COOLDOWN_SECONDS:
            return None, conf
        self._ug = g
        self._ut = ahora
        self._buf.clear()
        return g, conf

    def todas_las_probs(self, lm):
        if not self._ok or lm is None:
            return None
        probs = self.modelo.predict(lm.reshape(1,-1).astype(np.float32), verbose=0)[0]
        return sorted(zip(self.clases, probs.tolist()), key=lambda t: t[1], reverse=True)

    def obtener_mensaje(self, g):
        return MENSAJES_GESTO.get(g, g)

    def forzar_cooldown(self):
        self._ut = time.time()

    def resetear(self):
        self._buf.clear()
        self._ug = None
        self._ut = 0.0
        